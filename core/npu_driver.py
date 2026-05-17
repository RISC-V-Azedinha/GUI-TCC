# core/npu_driver.py
import serial
import struct
import time
import os
import numpy as np
from core.nn_model import empacotar_pesos_dma

class NPUDriverEdge:
    def __init__(self, port, baud=921600):
        # rtscts=False vital para controle manual do pino RTS (Reset)
        self.ser = serial.Serial(port, baud, rtscts=False, dsrdtr=False, timeout=2.0)
        self.ser.reset_input_buffer()

    def boot_app_bin(self, bin_path, progress_cb=None):
        """ Faz o Hard Reset da FPGA, aguarda Bootloader e envia o binário RISC-V """
        if progress_cb: progress_cb("Acionando Reset de Hardware...")
        self.ser.rts = False
        time.sleep(0.05)
        self.ser.write(b'\xCA\xFE\xBA\xBE')
        time.sleep(0.05)
        self.ser.write(b'\x09\x00\x00\x00\x00')
        time.sleep(0.01)
        self.ser.write(b'\x08')
        time.sleep(0.05)
        time.sleep(0.05)
        self.ser.reset_input_buffer()
        self.ser.rts = True

        if progress_cb: progress_cb("Aguardando sinal 'BOOT' do SoC...")
        buffer = ""
        start_time = time.time()
        while time.time() - start_time < 4.0:
            if self.ser.in_waiting:
                char = self.ser.read(1).decode('utf-8', errors='ignore')
                buffer += char
                if "BOOT" in buffer:
                    break
        else:
            raise Exception("Timeout aguardando Bootloader da FPGA.")

        if progress_cb: progress_cb("Handshake com o Bootloader...")
        time.sleep(0.1)
        self.ser.reset_input_buffer()
        self.ser.write(b'\xCA\xFE\xBA\xBE')
        
        start_time = time.time()
        ack = b''
        while time.time() - start_time < 2.0:
            if self.ser.in_waiting:
                ack = self.ser.read(1)
                break
                
        if ack != b'!':
            raise Exception(f"Sem resposta de Handshake. Recebido: {ack}")

        file_size = os.path.getsize(bin_path)
        self.ser.write(struct.pack('<I', file_size))
        time.sleep(0.05)

        if progress_cb: progress_cb(f"Enviando {bin_path} ({file_size} bytes)...")
        with open(bin_path, "rb") as f:
            payload = f.read()
            CHUNK_SIZE = 64
            for i in range(0, len(payload), CHUNK_SIZE):
                chunk = payload[i : i + CHUNK_SIZE]
                self.ser.write(chunk)
                self.ser.flush()
                time.sleep(0.002)

        if progress_cb: progress_cb("Servidor CNN iniciado com sucesso!")
        time.sleep(0.5) 
        self.ser.reset_input_buffer()

    def upload_modelo(self, w_conv, b_conv, w_fc, b_fc, progress_cb=None):
        """ Envia os pesos e bias da Conv2D e da camada Fully Connected para a NPU. """
        w_conv_packed = empacotar_pesos_dma(w_conv)
        w_fc_packed = empacotar_pesos_dma(w_fc)
        
        if progress_cb: progress_cb("A enviar W_conv (Conv2D Kernel)...")
        self.ser.write(struct.pack('>B', 0xAA))
        for val in w_conv_packed: self.ser.write(struct.pack('>I', val & 0xFFFFFFFF))
        assert self.ser.read(1) == b'A'

        if progress_cb: progress_cb("A enviar B_conv (Conv2D Bias)...")
        self.ser.write(struct.pack('>B', 0xBB))
        for val in b_conv: self.ser.write(struct.pack('>i', val))
        assert self.ser.read(1) == b'B'

        if progress_cb: progress_cb("A enviar W_fc (Fully Connected)...")
        self.ser.write(struct.pack('>B', 0xCC))
        for val in w_fc_packed: self.ser.write(struct.pack('>I', val & 0xFFFFFFFF))
        assert self.ser.read(1) == b'C'

        if progress_cb: progress_cb("A enviar B_fc (Classes Bias)...")
        b_fc_padded = np.pad(b_fc, (0, 12 - len(b_fc)), mode='constant')
        self.ser.write(struct.pack('>B', 0xDD))
        for val in b_fc_padded: self.ser.write(struct.pack('>i', val))
        assert self.ser.read(1) == b'D'
        
    def inferir(self, image_int8):
        self.ser.write(struct.pack('>B', 0xFF))
        self.ser.write(image_int8.tobytes())
        res = self.ser.read(10)
        return struct.unpack('>10b', res)

    def close(self): 
        if self.ser and self.ser.is_open:
            self.ser.close()