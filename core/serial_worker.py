# core/serial_worker.py
import time
import struct
from PyQt5.QtCore import QThread, pyqtSignal

class FPGALoader(QThread):
    progress_update = pyqtSignal(int)
    log_msg = pyqtSignal(str, str) 
    finished = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.payload = b''
        self.ser = None # Receberá do MainController

    def set_payload(self, data, ser_instance):
        self.payload = data
        self.ser = ser_instance

    def run(self):
        if not self.ser or not self.ser.is_open:
            self.log_msg.emit("Porta Serial não está aberta!", "error")
            self.finished.emit(False)
            return

        try:
            self.execute_upload(self.ser)
            self.finished.emit(True)
        except Exception as e:
            self.log_msg.emit(f"Erro no Upload: {str(e)}", "error")
            self.finished.emit(False)

    def execute_upload(self, ser):
        size = len(self.payload)
        
        self.log_msg.emit("Reiniciando FPGA para modo Bootloader (ROM)...", "info")
        ser.rts = False
        time.sleep(0.05)
        ser.write(b'\xCA\xFE\xBA\xBE')
        time.sleep(0.05)
        ser.write(b'\x09\x00\x00\x00\x00') # Boot = ROM
        time.sleep(0.01)
        ser.write(b'\x08') # Reset Halt
        time.sleep(0.05)
        ser.reset_input_buffer()
        ser.rts = True # Solta a placa para rodar a ROM
        
        self.log_msg.emit("Aguardando sinal 'BOOT'...", "info")
        buffer = ""
        start_wait = time.time()
        boot_found = False
        while time.time() - start_wait < 4.0:
            if ser.in_waiting:
                try:
                    buffer += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                except: pass
                if "BOOT" in buffer:
                    boot_found = True
                    break
                    
        if not boot_found:
            raise Exception("Timeout aguardando 'BOOT'.")
            
        time.sleep(0.1)
        ser.reset_input_buffer()
        
        ser.write(b'\xCA\xFE\xBA\xBE')
        start_time = time.time()
        ack = b''
        while time.time() - start_time < 2.0:
            if ser.in_waiting:
                ack = ser.read(1)
                if ack == b'!': break
                    
        if ack != b'!': raise Exception("Sem resposta de Handshake.")
            
        self.log_msg.emit(f"Handshake OK! Enviando binário ({size} bytes).", "info")
        ser.write(struct.pack('<I', size))
        time.sleep(0.05)

        for i in range(0, size, 64):
            chunk = self.payload[i : i + 64]
            ser.write(chunk)
            ser.flush()
            self.progress_update.emit(int(((i + len(chunk)) / size) * 100))
            time.sleep(0.002) 
            
        self.log_msg.emit("Upload finalizado. Configurando PC para a RAM...", "info")
        
        # Pós Upload: Vai para a RAM, Congela e Limpa os Resíduos
        ser.rts = False 
        time.sleep(0.05)
        ser.write(b'\xCA\xFE\xBA\xBE') 
        time.sleep(0.05)
        ser.write(b'\x09\x00\x08\x00\x80') # Boot = RAM
        time.sleep(0.01)
        ser.write(b'\x08') # Reset Halt
        time.sleep(0.05)
        ser.write(b'\x0A') # Limpa Regs (Ponto 4 que você pediu)
        ser.reset_input_buffer()
        
        self.log_msg.emit("Sistema pronto na RAM. Clique em 'Run' ou 'Step' para iniciar.", "success")