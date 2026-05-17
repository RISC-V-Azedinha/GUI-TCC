# controllers/main_controller.py
import re
import struct
import serial
import time
from PyQt5.QtCore import QTimer
import qtawesome as qta
from core.serial_worker import FPGALoader
from core.connection_manager import ConnectionManager

class MiniAssembler:
    """Traduz código Assembly RISC-V RV32I para Código de Máquina (Inteiros 32 bits)"""
    REGS = {
        'x0':0, 'zero':0, 'x1':1, 'ra':1, 'x2':2, 'sp':2, 'x3':3, 'gp':3,
        'x4':4, 'tp':4, 'x5':5, 't0':5, 'x6':6, 't1':6, 'x7':7, 't2':7,
        'x8':8, 's0':8, 'fp':8, 'x9':9, 's1':9, 'x10':10, 'a0':10,
        'x11':11, 'a1':11, 'x12':12, 'a2':12, 'x13':13, 'a3':13,
        'x14':14, 'a4':14, 'x15':15, 'a5':15, 'x16':16, 'a6':16,
        'x17':17, 'a7':17, 'x18':18, 's2':18, 'x19':19, 's3':19,
        'x20':20, 's4':20, 'x21':21, 's5':21, 'x22':22, 's6':22,
        'x23':23, 's7':23, 'x24':24, 's8':24, 'x25':25, 's9':25,
        'x26':26, 's10':26, 'x27':27, 's11':27, 'x28':28, 't3':28,
        'x29':29, 't4':29, 'x30':30, 't5':30, 'x31':31, 't6':31
    }

    @classmethod
    def assemble(cls, code_str):
        lines = code_str.split('\n')
        labels = {}
        clean_lines = []
        pc = 0

        for line in lines:
            line = line.split('#')[0].strip() 
            if not line or line.startswith('.'): continue
            if ':' in line:
                label, rest = line.split(':', 1)
                labels[label.strip()] = pc
                if rest.strip():
                    clean_lines.append(rest.strip())
                    pc += 4
            else:
                clean_lines.append(line)
                pc += 4

        machine_code = []
        pc = 0
        for line in clean_lines:
            parts = re.sub(r'[,()]', ' ', line).split()
            op = parts[0].lower()
            args = parts[1:]

            if op == 'li':   
                op = 'addi'
                args = [args[0], 'x0', args[1]]
            elif op == 'mv': 
                op = 'addi'
                args = [args[0], args[1], '0']
            elif op == 'j':  
                op = 'jal'
                args = ['x0', args[0]]

            instr_bin = 0
            try:
                if op == 'addi':
                    rd, rs1, imm = cls.REGS[args[0]], cls.REGS[args[1]], int(args[2], 0) & 0xFFF
                    instr_bin = (imm << 20) | (rs1 << 15) | (0 << 12) | (rd << 7) | 0x13
                elif op == 'add':
                    rd, rs1, rs2 = cls.REGS[args[0]], cls.REGS[args[1]], cls.REGS[args[2]]
                    instr_bin = (0 << 25) | (rs2 << 20) | (rs1 << 15) | (0 << 12) | (rd << 7) | 0x33
                elif op == 'sw': 
                    rs2, imm, rs1 = cls.REGS[args[0]], int(args[1], 0) & 0xFFF, cls.REGS[args[2]]
                    imm11_5 = (imm >> 5) & 0x7F
                    imm4_0 = imm & 0x1F
                    instr_bin = (imm11_5 << 25) | (rs2 << 20) | (rs1 << 15) | (2 << 12) | (imm4_0 << 7) | 0x23
                elif op in ['beq', 'bne']:
                    rs1, rs2 = cls.REGS[args[0]], cls.REGS[args[1]]
                    offset = (labels[args[2]] - pc) & 0x1FFF
                    imm12 = (offset >> 12) & 1
                    imm11 = (offset >> 11) & 1
                    imm10_5 = (offset >> 5) & 0x3F
                    imm4_1 = (offset >> 1) & 0xF
                    funct3 = 0x0 if op == 'beq' else 0x1
                    instr_bin = (imm12 << 31) | (imm10_5 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (imm4_1 << 8) | (imm11 << 7) | 0x63
                elif op == 'lui':
                    rd, imm = cls.REGS[args[0]], int(args[1], 0) & 0xFFFFF
                    instr_bin = (imm << 12) | (rd << 7) | 0x37
                elif op == 'jal':
                    rd = cls.REGS[args[0]]
                    offset = (labels[args[1]] - pc) & 0xFFFFF
                    imm20 = (offset >> 20) & 1
                    imm10_1 = (offset >> 1) & 0x3FF
                    imm11 = (offset >> 11) & 1
                    imm19_12 = (offset >> 12) & 0xFF
                    instr_bin = (imm20 << 31) | (imm10_1 << 21) | (imm11 << 20) | (imm19_12 << 12) | (rd << 7) | 0x6F
                elif op == 'wfi':
                    instr_bin = 0x10500073
                else:
                    print(f"Instrução {op} não suportada pelo MiniAssembler.")
                    return []

                machine_code.append(instr_bin)
                pc += 4
            except Exception as e:
                print(f"Erro ao montar '{line}': {e}")
                return []
        return machine_code


class MainController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        
        # MÁQUINA DE ESTADOS DO CONTROLADOR (A chave para não misturar!)
        self.exec_mode = 'SIM' # Modos: 'SIM' ou 'HW'
        self.hw_running = False
        
        self.run_timer = QTimer()
        self.run_timer.timeout.connect(self.handle_step)
        
        self.conn_mgr = ConnectionManager()
        self.fpga_worker = FPGALoader()
        self.debug_ser = None 
        
        # CONEXÕES DE SINAIS
        self.view.request_upload.connect(self.on_click_upload)
        self.view.request_step.connect(self.handle_step)
        self.view.request_run_toggle.connect(self.handle_run_toggle)
        self.view.request_reset_fpga.connect(self.handle_hw_reset) 
        self.view.request_set_bkp.connect(self.handle_set_bkp)
        self.view.request_clr_bkp.connect(self.handle_clr_bkp)

        self.view.btn_sync.setText(" Disconnect HW")
        self.view.btn_sync.setIcon(qta.icon('fa5s.unlink', color='white'))
        self.view.btn_sync.setStyleSheet("background-color: #ef4444; color: white; border: none;")
        self.view.request_sync_fpga.connect(self.close_serial)

        self.fpga_worker.log_msg.connect(self.display_log)
        self.fpga_worker.progress_update.connect(self.view.progressBar.setValue)
        self.fpga_worker.finished.connect(self.on_upload_finished)

        self.loaded_code = "" # NOVA VARIÁVEL
        self.handle_reset(self.view.editor.toPlainText())

    # ==========================================
    # GERENCIADOR DE CONEXÃO PERSISTENTE 
    # ==========================================
    def _get_serial(self):
        if self.debug_ser is None or not self.debug_ser.is_open:
            port = self.conn_mgr.get_port()
            baud = self.conn_mgr.get_baud()
            try:
                self.debug_ser = serial.Serial(port, baud, rtscts=False, dsrdtr=False, timeout=0.1)
                self.debug_ser.rts = False
                time.sleep(0.05)
                self.debug_ser.write(b'\xCA\xFE\xBA\xBE')
                self.display_log("Debugger Conectado. HW Interceptado.", "info")
            except Exception as e:
                self.display_log(f"Erro ao abrir porta de debug: {e}", "error")
                return None
        return self.debug_ser

    def close_serial(self):
        """Volta forçadamente para o Modo de Simulação Local."""
        if self.debug_ser and self.debug_ser.is_open:
            self.debug_ser.rts = True 
            self.debug_ser.close()
            self.debug_ser = None
            
        self.exec_mode = 'SIM'
        self.hw_running = False
        self.run_timer.stop()
        self.view.set_run_state(False)
        self.display_log("Conexão Serial Liberada. Retornando ao Modo de Simulação.", "info")

    def _auto_sync(self):
        ser = self._get_serial()
        if ser:
            ser.reset_input_buffer()
            ser.write(b'\x10') # CMD_READ_REG
            dados = ser.read(132)
            if len(dados) == 132:
                regs = [int.from_bytes(dados[i*4 : i*4+4], 'little') for i in range(32)]
                hw_pc = int.from_bytes(dados[128:132], 'little')
                
                if hw_pc >= 0x80000800:
                    logical_pc = (hw_pc - 0x80000800) // 4
                else:
                    logical_pc = 0
                
                self.model.pc = logical_pc
                self.model.stage = 0 
                self.model.halted = False 
                
                if logical_pc >= len(self.model.instructions):
                    self.model.halted = True
                
                self.view.update_hardware_ui(regs, self.model.memory, 0)
                self.view.highlight_line(self.model.get_current_line())

    def on_tab_changed(self, index):
        """Disparado quando a aba do QStackedWidget muda."""
        # Se o usuário saiu da aba do Core RV32I (Índice 0)
        if index != 0:
            # 1. Interrompe cronômetros e timers de execução em background
            self.run_timer.stop()
            self.hw_running = False
            self.view.set_run_state(False)
            
            # 2. Zera a barra de progresso de upload e limpa o histórico de logs da UI
            self.view.progressBar.setValue(0)
            self.view.clear_log()
            
            # 3. Remove marcações visuais de linhas executadas (highlighter roxo)
            if hasattr(self.view, 'clear_highlight'):
                self.view.clear_highlight()
            else:
                self.view.highlight_line(-1) # Força um índice inválido para remover o destaque
                
            # 4. Remove os break-points do hardware e aciona rotinas de limpeza visual
            self.handle_clr_bkp()
            if hasattr(self.view, 'clear_breakpoints_ui'):
                self.view.clear_breakpoints_ui()
            
            # 5. Restabelece o hardware para o estado inicial se estivesse conectado em modo placa
            if self.exec_mode == 'HW':
                ser = self._get_serial()
                if ser:
                    try:
                        ser.rts = False
                        ser.write(b'\x09\x00\x00\x00\x00') # Configura PC de Boot = ROM (0x00000000)
                        time.sleep(0.01)
                        ser.write(b'\x08')                 # Emite comando de Reset / Halt
                        time.sleep(0.01)
                        ser.write(b'\x0A')                 # Força limpeza física dos registradores
                        ser.reset_input_buffer()
                    except Exception as e:
                        print(f"Erro ao resetar hardware na troca de aba: {e}")
            
            # 6. Zera completamente o estado interno do emulador de simulação local
            self.model.regs = [0] * 32
            self.model.pc = 0
            self.model.stage = 0
            self.model.halted = False
            
            # Atualiza o painel de registradores e limpa o mapeamento de memória na interface
            self.view.update_hardware_ui(self.model.regs, {}, 0)
            
            # Retorna o estado operacional padrão para o modo de simulação local seguro
            self.exec_mode = 'SIM'

    def on_upload_finished(self, success):
        """Ao terminar de subir código, entramos oficialmente no Modo Hardware!"""
        if success:
            self.exec_mode = 'HW'
            self.hw_running = False
            self._auto_sync() 

    # ==========================================
    # LÓGICA DE CONTROLE DE FLUXO DO CORE
    # ==========================================
    def on_click_upload(self):
        asm_code = self.view.editor.toPlainText()
        self.handle_reset(asm_code) 
        
        instructions = MiniAssembler.assemble(asm_code) 
        if not instructions:
            self.display_log("Erro no Assembler.", "error")
            return

        binary_data = self.model.get_binary_image(instructions)
        self.view.progressBar.setValue(0)
        
        ser = self._get_serial()
        if not ser: return
        
        self.fpga_worker.set_payload(binary_data, ser)
        self.fpga_worker.start()

    def handle_hw_reset(self):
        """Se o usuário clicar em Reset, tenta conectar à FPGA. Se falhar, reseta apenas o local."""
        self.handle_reset(self.view.editor.toPlainText()) 
        ser = self._get_serial()
        if ser:
            self.exec_mode = 'HW'
            self.hw_running = False
            self.view.set_run_state(False)
            
            ser.rts = False
            time.sleep(0.02)
            ser.write(b'\x09\x00\x08\x00\x80') # Boot = RAM
            time.sleep(0.01)
            ser.write(b'\x08') # Reset Halt
            time.sleep(0.01)
            ser.write(b'\x0A') # Limpa Regs
            ser.reset_input_buffer()
            self.display_log("Hardware Resetado (PC = 0x80000800). Modo Placa ativo.", "success")
            self._auto_sync()
        else:
            self.exec_mode = 'SIM'

    def handle_step(self):
        # ----------------------------------------------------
        # STEP NA SIMULAÇÃO LOCAL
        # ----------------------------------------------------
        if self.exec_mode == 'SIM':
            self._check_code_changes() 
            if not self.model.halted:
                success, msg, stage = self.model.clock_tick()
                self.view.update_hardware_ui(self.model.regs, self.model.memory, self.model.stage)
                self.view.highlight_line(self.model.get_current_line())
                if msg:
                    self.view.log(msg, ["#38bdf8", "#818cf8", "#c084fc", "#f472b6", "#fb923c"][stage] if 0<=stage<=4 else "#cbd5e1")

        # ----------------------------------------------------
        # STEP / POLLING NO HARDWARE (FPGA)
        # ----------------------------------------------------
        elif self.exec_mode == 'HW':
            ser = self._get_serial()
            
            if self.hw_running:
                # Se estamos a rodar livremente, usamos os Ticks do Timer para "escutar" a placa
                if ser and ser.in_waiting:
                    try:
                        chunk = ser.read(ser.in_waiting)
                        if b'\xBB' in chunk: # A placa envia 0xBB quando bate no Breakpoint!
                            self.display_log("🚨 BREAKPOINT DE HARDWARE ATINGIDO!", "error")
                            
                            # Força a interface a entrar em Modo Pausa
                            self.run_timer.stop()
                            self.hw_running = False
                            self.view.set_run_state(False) # Muda a cor do botão de volta para Azul!
                            
                            # Assume o controlo físico
                            ser.rts = False
                            time.sleep(0.01)
                            ser.write(b'\xCA\xFE\xBA\xBE')
                            time.sleep(0.02)
                            
                            self._auto_sync() # Atualiza o Highlight roxo e os registradores
                    except:
                        pass
            else:
                # MODO PAUSADO: Executa um Step Limpo Manual (Agora funciona!)
                if ser:
                    ser.rts = False
                    ser.write(b'\x03') # CMD_STEP
                    time.sleep(0.01)   
                    self._auto_sync()

    def handle_run_toggle(self):
        # ----------------------------------------------------
        # RUN/PAUSE NA SIMULAÇÃO LOCAL
        # ----------------------------------------------------
        if self.exec_mode == 'SIM':
            self._check_code_changes() 
            if self.run_timer.isActive():
                self.run_timer.stop()
                self.view.set_run_state(False)
                self.view.log(">> Simulação Pausada.", "#f59e0b")
            else:
                if self.model.halted:
                    self.handle_reset(self.view.editor.toPlainText())
                self.run_timer.start(100) 
                self.view.set_run_state(True)
                self.view.log(">> Simulação contínua...", "#3b82f6")

        # ----------------------------------------------------
        # RUN/PAUSE NO HARDWARE (FPGA)
        # ----------------------------------------------------
        elif self.exec_mode == 'HW':
            if self.hw_running:
                # O BOTÃO PAUSE FOI CLICADO
                self.run_timer.stop() # <-- CORREÇÃO CRÍTICA: Desliga a metralhadora de steps
                self.hw_running = False
                self.view.set_run_state(False)
                ser = self._get_serial()
                if ser:
                    ser.rts = False
                    time.sleep(0.01)
                    ser.write(b'\xCA\xFE\xBA\xBE') # Assume o controlo da FSM
                    time.sleep(0.02)
                    self._auto_sync() # Atualiza a GUI com o PC atual
                self.view.log(">> Hardware Pausado.", "#f59e0b")
            else:
                # O BOTÃO RUN FOI CLICADO
                if self.model.halted:
                    self.handle_hw_reset()
                ser = self._get_serial()
                if ser:
                    self.hw_running = True
                    self.view.set_run_state(True)
                    ser.write(b'\x02') # CMD_RESUME
                    time.sleep(0.01)   
                    ser.rts = True     
                    self.run_timer.start(100) # Liga o timer para fazer o polling (ver abaixo)
                    self.view.log(">> Hardware em execução livre...", "#3b82f6")

    # ==========================================
    # ARMA/DESARMA BREAKPOINTS DE HARDWARE
    # ==========================================
    def handle_set_bkp(self, line_idx):
        addr = self._calculate_pc_from_line(self.view.editor.toPlainText(), line_idx)
        if addr is not None:
            ser = self._get_serial()
            if ser:
                self.exec_mode = 'HW' # Garante mudança de estado ao interagir com debug
                ser.rts = False
                ser.write(b'\x05') 
                ser.write(struct.pack('<I', addr))
                time.sleep(0.01)
                self.display_log(f"BKP Armado na RAM em 0x{addr:08X}", "error")
        else:
            self.display_log("Linha inválida para BKP.", "error")

    def handle_clr_bkp(self):
        ser = self._get_serial()
        if ser:
            ser.rts = False
            ser.write(b'\x06') 
            time.sleep(0.01)
            self.display_log("BKP Removido.", "success")

    def display_log(self, message, msg_type):
        colors = {"error": "#ef4444", "success": "#10b981", "info": "#38bdf8"}
        self.view.log(f"[FPGA] {message}", colors.get(msg_type, "#cbd5e1"))

    def handle_reset(self, code_text: str):
        self.loaded_code = code_text # <--- ATUALIZADO AQUI
        self.run_timer.stop()
        self.view.set_run_state(False)
        self.model.parse_code(code_text)
        self.view.clear_log()
        self.view.log(">> Emulador Resetado.", "#10b981")

    def _calculate_pc_from_line(self, text, target_line):
        lines = text.split('\n')
        pc = 0x80000800
        for i, raw_line in enumerate(lines):
            line = raw_line.split('#')[0].strip()
            if i == target_line:
                if not line or line.endswith(':') or line.startswith('.'): return None
                return pc
            if line and not line.endswith(':') and not line.startswith('.'):
                pc += 4
        return None
    
    def _check_code_changes(self):
        """Verifica se o usuário alterou o código e garante o sincronismo."""
        current_code = self.view.editor.toPlainText()
        if current_code != self.loaded_code:
            if self.exec_mode == 'SIM':
                self.handle_reset(current_code)
                self.display_log("Código editado. Simulação reiniciada automaticamente.", "info")
            elif self.exec_mode == 'HW':
                self.display_log("ALERTA: Código alterado! Faça um novo Upload para sincronizar com a FPGA.", "error")
                self.loaded_code = current_code # Atualiza para não dar spam de erro
                
    