# core/serial_worker.py
import serial
import time
import struct
from PyQt5.QtCore import QThread, pyqtSignal

class FPGALoader(QThread):
    progress_update = pyqtSignal(int)
    log_msg = pyqtSignal(str, str) # Mensagem, Tipo (info, error, success)
    finished = pyqtSignal(bool)
    telemetry_update = pyqtSignal(list, int)

    def __init__(self, port="COM3", baud=115200):
        super().__init__()
        self.port = port
        self.baud = baud
        self.payload = b''
        self.mode = 'upload' # 'upload' ou 'reset'

    def set_payload(self, data):
        self.payload = data
        self.mode = 'upload'

    def run(self):
        ser = None
        try:
            self.log_msg.emit(f"Abrindo porta {self.port} a {self.baud} baud...", "info")
            
            # IMPORTANTE: rtscts=False e dsrdtr=False para não interferir na multiplexação do seu debug_controller
            ser = serial.Serial(self.port, self.baud, rtscts=False, dsrdtr=False, timeout=2)
            ser.rts = True # Garante que iniciamos no modo SoC (rodando livremente)
            time.sleep(0.1)

            if self.mode == 'upload':
                self.execute_upload(ser)
            elif self.mode == 'reset':
                self.execute_reset(ser)
            elif self.mode == 'sync':
                self.execute_sync(ser)     
                
            self.finished.emit(True)
            
        except serial.SerialException as e:
            self.log_msg.emit(f"Erro Serial: A porta {self.port} não foi encontrada, não está conectada ou está em uso.", "error")
            self.finished.emit(False)
        except Exception as e:
            self.log_msg.emit(f"Erro inesperado: {str(e)}", "error")
            self.finished.emit(False)
        finally:
            if ser and ser.is_open:
                ser.close()

    def execute_reset(self, ser):
        self.log_msg.emit("Acionando Hard Reset via RTS...", "info")
        
        # Sequência de Reset remoto do seu debug_controller.vhd
        ser.rts = False
        time.sleep(0.05)
        ser.write(b'\xCA\xFE\xBA\xBE') # Magic Word
        time.sleep(0.05)
        ser.write(b'\x04')             # CMD_RESET
        time.sleep(0.05)
        
        ser.reset_input_buffer()
        ser.rts = True                 # Devolve o processador para a execução
        
        if self.mode == 'reset':       # Só avisa se foi um reset manual do usuário
            self.log_msg.emit("Placa FPGA resetada remotamente com sucesso!", "success")

    def execute_upload(self, ser):
        size = len(self.payload)
        
        # 1. Faz o auto-reset (Hardware Reset via Debug Controller)
        self.execute_reset(ser)
        
        # 2. Aguarda o Bootloader da FPGA acordar e mandar "BOOT"
        self.log_msg.emit("Aguardando sinal 'BOOT' do processador...", "info")
        buffer = ""
        start_wait = time.time()
        boot_found = False
        
        while time.time() - start_wait < 4.0: # 4 segundos de timeout
            if ser.in_waiting:
                # DEBUG: Vamos ler os bytes crus para ver se é problema de Baud Rate!
                raw_bytes = ser.read(ser.in_waiting)
                self.log_msg.emit(f"RAW RX: {raw_bytes}", "info")
                
                char = raw_bytes.decode('utf-8', errors='ignore')
                buffer += char
                if "BOOT" in buffer:
                    boot_found = True
                    break
                
                if len(buffer) > 50: 
                    buffer = buffer[-20:] 
        
        if not boot_found:
            raise Exception("Timeout aguardando 'BOOT'. A placa não respondeu nada ou o baud rate está errado.")
            
        self.log_msg.emit("Bootloader detectado! Iniciando Handshake...", "success")
        
        # Dá um respiro e limpa sujeiras do buffer
        time.sleep(0.1)
        ser.reset_input_buffer()
        
        # 3. Handshake de Bootloader
        self.log_msg.emit("Enviando Magic Word (0xCAFEBABE) para o Bootloader...", "info")
        ser.write(b'\xCA\xFE\xBA\xBE')
        
        start_time = time.time()
        ack = b''
        while time.time() - start_time < 2.0:
            if ser.in_waiting:
                ack = ser.read(1)
                if ack == b'!':
                    break
                    
        if ack != b'!':
            raise Exception(f"Sem resposta do Bootloader. Recebido: {ack}")
            
        self.log_msg.emit(f"Handshake OK! Enviando tamanho do binário ({size} bytes).", "info")
        ser.write(struct.pack('<I', size))
        time.sleep(0.05)

        # 4. Envio dos blocos (Chunks)
        self.log_msg.emit("Transferindo binário para a FPGA...", "info")
        chunk_size = 64
        for i in range(0, size, chunk_size):
            chunk = self.payload[i : i + chunk_size]
            ser.write(chunk)
            ser.flush()
            
            progress = int(((i + len(chunk)) / size) * 100)
            self.progress_update.emit(progress)
            time.sleep(0.002) 
            
        self.log_msg.emit("Upload físico finalizado. Aguardando processador...", "info")
        
        # 5. Aguardar a FPGA confirmar que vai executar
        start_wait_app = time.time()
        while time.time() - start_wait_app < 3.0:
            if ser.in_waiting:
                c = ser.read(1).decode('utf-8', errors='ignore')
                if c == '>':
                    self.log_msg.emit("FPGA confirmou: Executando AXON-OS!", "success")
                    return
                    
        self.log_msg.emit("Upload feito, mas não recebi o '>' de confirmação de execução.", "error")
    
    def execute_sync(self, ser):
        """Pausa a CPU, lê os registradores e resume a execução."""
        # 1. Intercepta a CPU (Halt)
        ser.rts = False
        time.sleep(0.05)
        ser.write(b'\xCA\xFE\xBA\xBE')
        time.sleep(0.05) # Tempo para o processador bater no estágio de Fetch e congelar
        
        # 2. Pede o dump de memória (CMD_READ_REG)
        ser.reset_input_buffer()
        ser.write(b'\x10')
        
        # 3. Lê os 132 bytes
        dados = ser.read(132)
        
        # 4. Libera a CPU de volta para o SO (Resume)
        ser.write(b'\x02')
        time.sleep(0.05)
        ser.rts = True
        
        # 5. Processa os dados recebidos
        if len(dados) == 132:
            regs = []
            # Converte os 32 registradores (Little Endian)
            for i in range(32):
                val = int.from_bytes(dados[i*4 : i*4+4], byteorder='little')
                regs.append(val)
            
            # O último bloco de 4 bytes é o PC
            pc_val = int.from_bytes(dados[128:132], byteorder='little')
            
            # Manda pra interface!
            self.telemetry_update.emit(regs, pc_val)
            self.log_msg.emit(f"Telemetria recebida! PC Atual: 0x{pc_val:08X}", "info")
        else:
            self.log_msg.emit(f"Falha na telemetria. Recebidos {len(dados)}/132 bytes.", "error")