# controllers/main_controller.py
from PyQt5.QtCore import QTimer
from core.emulator import RISCV_Emulator
from ui.main_window import RiscVEduApp
from core.serial_worker import FPGALoader  # Importação da nova classe Serial

import re

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

        # Pass 1: Mapear Labels e limpar o código
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

        # Pass 2: Gerar Machine Code
        machine_code = []
        pc = 0
        for line in clean_lines:
            parts = re.sub(r'[,()]', ' ', line).split()
            op = parts[0].lower()
            args = parts[1:]

            # --- Suporte a Pseudo-Instruções ---
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
                    # RISC-V J-Type immediate encoding é complexo, simplificando:
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
        
        self.run_timer = QTimer()
        self.run_timer.timeout.connect(self.handle_step)
        
        # Worker configurado para a porta correta
        self.fpga_worker = FPGALoader()
        
        # CONEXÕES DE SINAIS (Novas Pontes)
        self.view.request_reset_fpga.connect(self.on_click_reset_fpga)
        self.view.request_upload.connect(self.on_click_upload)
        self.view.request_sync_fpga.connect(self.request_hardware_sync)
        self.view.request_step.connect(self.handle_step)
        self.view.request_run_toggle.connect(self.handle_run_toggle)

        # Feedback do Worker para a UI
        self.fpga_worker.log_msg.connect(self.display_log)
        self.fpga_worker.progress_update.connect(self.view.progressBar.setValue)
        self.fpga_worker.telemetry_update.connect(self.on_telemetry_received)

        # Estado inicial
        self.handle_reset(self.view.editor.toPlainText())


    def on_click_reset_fpga(self):
        """Executa o reset sincronizado: Local (Simulador) e Remoto (Placa)."""
        # Reset Local
        self.handle_reset(self.view.editor.toPlainText())
        
        # Configura o worker para modo reset e dispara a thread
        self.fpga_worker.mode = 'reset'
        self.fpga_worker.start()

    def on_click_upload(self):
        asm_code = self.view.editor.toPlainText()
        instructions = MiniAssembler.assemble(asm_code)
        
        if not instructions:
            self.display_log("Erro: O Assembler não reconheceu alguma instrução.", "error")
            return

        binary_data = self.model.get_binary_image(instructions)
        self.view.progressBar.setValue(0)
        self.fpga_worker.set_payload(binary_data)
        self.fpga_worker.start()

    def on_telemetry_received(self, regs, pc_val):
        # Sincroniza o modelo local com o hardware real
        self.model.pc = pc_val
        self.model.regs = regs
        # Atualiza a interface (as cores de destaque já estão na View)
        self.view.update_hardware_ui(regs, self.model.memory, 0)
        
        current_line = self.model.get_current_line()
        self.view.highlight_line(current_line)
        self.display_log(f"Sincronizado! Hardware PC: 0x{pc_val:08X}", "success")

    def display_log(self, message, msg_type):
        colors = {"error": "#ef4444", "success": "#10b981", "info": "#38bdf8"}
        color = colors.get(msg_type, "#cbd5e1")
        self.view.log(f"[FPGA] {message}", color)

    def handle_reset(self, code_text: str):
        """Ao receber o código fonte, refaz o emulador."""
        self.run_timer.stop()
        self.view.set_run_state(False)
        self.model.parse_code(code_text)
        
        self.view.clear_log()
        self.view.log(">> Emulador Resetado. Estado da FSM e PC reiniciados.", "#10b981")
        
        # Atualiza a UI para o estado zerado
        self._sync_view()

    def handle_step(self):
        """Um tick manual de clock."""
        if self.model.halted:
            if self.run_timer.isActive():
                self.run_timer.stop()
                self.view.set_run_state(False)
                self.view.log(">> Execução Finalizada (Halt Acionado).", "#f59e0b")
            return
            
        success, msg, stage = self.model.clock_tick()
        self._sync_view()
        
        if msg:
            colors = ["#38bdf8", "#818cf8", "#c084fc", "#f472b6", "#fb923c"]
            color = colors[stage] if 0 <= stage <= 4 else "#cbd5e1"
            self.view.log(msg, color)
            
        if not success and not self.model.halted:
            self.run_timer.stop()
            self.view.set_run_state(False)
            self.view.log(">> CRASH: A execução foi interrompida.", "#ef4444")

# No controllers/main_controller.py

    def handle_run_toggle(self):
        """Liga ou desliga a execução contínua (Local e Hardware)."""
        if self.run_timer.isActive():
            # PARAR (PAUSE)
            self.run_timer.stop()
            self.view.set_run_state(False)
            
            # --- Hardware: Envia comando de HALT ---
            self.fpga_worker.mode = 'halt'
            self.fpga_worker.start()
            
            self.view.log(">> Clock Automático Pausado.", "#f59e0b")
        else:
            # RETOMAR (RUN)
            if self.model.halted:
                self.handle_reset(self.view.editor.toPlainText())
            
            # --- Hardware: Envia comando de RESUME ---
            self.fpga_worker.mode = 'resume'
            self.fpga_worker.start()

            # Simulador Local
            self.run_timer.start(100) # 10Hz
            self.view.set_run_state(True)
            self.view.log(">> Executando clock contínuo...", "#3b82f6")

    def _sync_view(self):
        """Força a View a ler os dados mais recentes do Model."""
        self.view.update_hardware_ui(self.model.regs, self.model.memory, self.model.stage)
        
        current_line = self.model.get_current_line()
        self.view.highlight_line(current_line)
    
    def request_hardware_sync(self):
        """Pede para o Worker pausar a CPU, ler os dados da FPGA e retomar"""
        self.display_log("Iniciando requisição de telemetria (Halt -> Dump -> Resume)...", "info")
        self.fpga_worker.mode = 'sync'
        self.fpga_worker.start()

    def on_telemetry_received(self, regs: list, pc_val: int):
        """Callback acionado quando o serial_worker termina de ler a UART"""
        # Atualiza a tabela com os registradores REAIS que vieram no silício
        self.view.update_hardware_ui(regs, {}, 0) 
        
        # Força o Emulador Local a apontar para a mesma linha de código (PC) da placa
        self.model.pc = pc_val
        current_line = self.model.get_current_line()
        self.view.highlight_line(current_line)