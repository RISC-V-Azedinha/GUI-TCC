# core/serial_worker.py
import serial
import time
import struct
from PyQt5.QtCore import QThread, pyqtSignal

class FPGALoader(QThread):
    progress_update = pyqtSignal(int)
    log_msg = pyqtSignal(str, str) 
    finished = pyqtSignal(bool)
    telemetry_update = pyqtSignal(list, int)

    def __init__(self, port="COM7", baud=921600): # Baud rate alto conforme main_controller
        super().__init__()
        self.port = port
        self.baud = baud
        self.payload = b''
        self.mode = 'upload' 

    def set_payload(self, data):
        self.payload = data
        self.mode = 'upload'

    def run(self):
        ser = None
        try:
            self.log_msg.emit(f"Conectando em {self.port} ({self.baud} baud)...", "info")
            # rtscts=False é vital para o controle manual do pino RTS
            ser = serial.Serial(self.port, self.baud, rtscts=False, dsrdtr=False, timeout=2)
            
            # Garante que o SoC comece rodando (RTS High costuma ser 0V em conversores, liberando o Reset)
            ser.rts = True 
            time.sleep(0.1)

            if self.mode == 'upload':
                self.execute_upload(ser)
            elif self.mode == 'reset':
                self.execute_reset(ser)
            elif self.mode == 'sync':
                self.execute_sync(ser)
            elif self.mode == 'halt':
                self.execute_halt(ser)
            elif self.mode == 'resume':
                self.execute_resume(ser)
            elif self.mode == 'step_hw':
                self.execute_step_hw(ser)
                
            self.finished.emit(True)
            
        except Exception as e:
            self.log_msg.emit(f"Erro: {str(e)}", "error")
            self.finished.emit(False)
        finally:
            if ser and ser.is_open:
                ser.close()

    def execute_reset(self, ser):
        self.log_msg.emit("Enviando sinal de Reset via Hardware...", "info")
        ser.rts = False # Ativa Reset (Geralmente 3.3V no pino)
        time.sleep(0.1)
        ser.write(b'\xCA\xFE\xBA\xBE') # Magic Word para o debug_controller
        ser.write(b'\x04')             # CMD_RESET
        time.sleep(0.1)
        ser.rts = True  # Libera CPU
        if self.mode == 'reset':
            self.log_msg.emit("Hardware Reset finalizado com sucesso.", "success")

    def execute_upload(self, ser):
        size = len(self.payload)
        
        # 1. Faz o auto-reset via Hardware Reset (Debug Controller)
        # Isso garante que o Bootloader da FPGA seja a primeira coisa a rodar
        self.execute_reset(ser)
        
        # 2. Aguarda o Bootloader da FPGA acordar e mandar "BOOT"
        self.log_msg.emit("Aguardando sinal 'BOOT' do processador...", "info")
        buffer = ""
        start_wait = time.time()
        boot_found = False
        
        while time.time() - start_wait < 4.0: # 4 segundos de timeout
            if ser.in_waiting:
                # Lemos o que estiver no buffer da UART
                raw_bytes = ser.read(ser.in_waiting)
                try:
                    char = raw_bytes.decode('utf-8', errors='ignore')
                    buffer += char
                except:
                    pass
                
                if "BOOT" in buffer:
                    boot_found = True
                    break
        
        if not boot_found:
            raise Exception("Timeout aguardando 'BOOT'. Certifique-se que a FPGA está ligada e o RTS configurado corretamente.")
            
        self.log_msg.emit("Bootloader detectado! Iniciando Handshake...", "success")
        
        # Limpa sujeiras do buffer antes de começar o protocolo binário
        time.sleep(0.1)
        ser.reset_input_buffer()
        
        # 3. Handshake de Bootloader
        # Enviamos a Magic Word para o Bootloader saber que o PC quer carregar um binário
        ser.write(b'\xCA\xFE\xBA\xBE')
        
        start_time = time.time()
        ack = b''
        while time.time() - start_time < 2.0:
            if ser.in_waiting:
                ack = ser.read(1)
                if ack == b'!': # O '!' é a confirmação do Bootloader VHDL
                    break
                    
        if ack != b'!':
            raise Exception(f"Sem resposta de Handshake. Recebido: {ack}")
            
        self.log_msg.emit(f"Handshake OK! Enviando binário ({size} bytes).", "info")
        
        # 4. Envia o tamanho do binário (4 bytes, Little Endian)
        ser.write(struct.pack('<I', size))
        time.sleep(0.05)

        # 5. Envio dos blocos (Chunks)
        chunk_size = 64
        for i in range(0, size, chunk_size):
            chunk = self.payload[i : i + chunk_size]
            ser.write(chunk)
            ser.flush()
            
            # Atualiza a barra de progresso na GUI
            progress = int(((i + len(chunk)) / size) * 100)
            self.progress_update.emit(progress)
            
            # Pequeno delay para não sobrecarregar o buffer de recepção da FPGA
            time.sleep(0.002) 
            
        self.log_msg.emit("Upload finalizado. Colocando CPU em standby...", "info")
        
        # ======================================================================
        # 6. ESTADO DE ESPERA (A chave para não rodar sozinho)
        # ======================================================================
        # Após o upload, enviamos um comando de HALT e seguramos o RTS.
        # Isso impede que o processador comece a iteração do Fibonacci antes do Run.
        
        ser.rts = False # Mantém o sinal de controle ativado
        time.sleep(0.05)
        ser.write(b'\xCA\xFE\xBA\xBE') # Magic Word
        ser.write(b'\x01')             # CMD_HALT (Sinaliza ao seu debug_controller para pausar)
        
        self.log_msg.emit("Sistema pronto. Clique em 'Run' para iniciar.", "success")

    def execute_sync(self, ser):
        ser.rts = False # Halt
        time.sleep(0.05)
        ser.write(b'\xCA\xFE\xBA\xBE')
        ser.write(b'\x10') # CMD_READ_REG
        
        dados = ser.read(132)
        ser.write(b'\x02') # CMD_RESUME
        ser.rts = True
        
        if len(dados) == 132:
            regs = [int.from_bytes(dados[i*4 : i*4+4], 'little') for i in range(32)]
            pc_val = int.from_bytes(dados[128:132], 'little')
            self.telemetry_update.emit(regs, pc_val)
    
    def execute_halt(self, ser):
        """Para a execução no hardware imediatamente."""
        ser.rts = False # Ativa o sinal de controle físico
        time.sleep(0.01)
        ser.write(b'\xCA\xFE\xBA\xBE')
        ser.write(b'\x01') # CMD_HALT
        self.log_msg.emit("Hardware: Execução Pausada.", "info")

    def execute_resume(self, ser):
        """Retoma a execução no hardware."""
        ser.write(b'\xCA\xFE\xBA\xBE')
        ser.write(b'\x02') # CMD_RESUME
        ser.rts = True  # Libera o processador
        self.log_msg.emit("Hardware: Execução Retomada.", "success")
    
    def execute_step_hw(self, ser):
        """Dá um único pulso de clock no hardware e força o retorno ao estado de pausa."""
        try:
            # 1. Garante que a CPU está em Halt/Reset antes de tentar o pulso
            ser.rts = False 
            time.sleep(0.01)
            ser.reset_input_buffer() # Limpa lixos da UART para a telemetria vir limpa

            # 2. Envia o comando de pulso único (0x08)
            # O seu debug_controller.vhd deve disparar apenas um ciclo de enable
            ser.write(b'\xCA\xFE\xBA\xBE')
            ser.write(b'\x08') 
            ser.flush()
            
            # 3. SEGURANÇA: Pequeno delay e comando de HALT explícito
            # Isso ajuda se o hardware não tiver um auto-stop por ciclo
            time.sleep(0.01) 
            ser.write(b'\xCA\xFE\xBA\xBE')
            ser.write(b'\x01') # CMD_HALT
            ser.flush()

            # 4. Pedimos a telemetria para atualizar a GUI com o estado real do silício
            ser.write(b'\xCA\xFE\xBA\xBE')
            ser.write(b'\x10') # CMD_READ_REG
            
            # Aguarda os 132 bytes (32 regs + PC)
            dados = ser.read(132)
            
            if len(dados) == 132:
                regs = []
                for i in range(32):
                    val = int.from_bytes(dados[i*4 : i*4+4], 'little')
                    regs.append(val)
                
                pc_val = int.from_bytes(dados[128:132], byteorder='little', signed=False)
                
                # Emite o sinal para o Controller sincronizar tudo
                self.telemetry_update.emit(regs, pc_val)
            else:
                self.log_msg.emit(f"Telemetria incompleta no Step: {len(dados)}/132 bytes", "error")
                
            # 5. Garante que o sinal físico de controle (RTS) continua travando a CPU
            ser.rts = False 
            
        except Exception as e:
            self.log_msg.emit(f"Erro no Step Hardware: {str(e)}", "error")