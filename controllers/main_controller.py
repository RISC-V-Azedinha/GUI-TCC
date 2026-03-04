# controllers/main_controller.py
from PyQt5.QtCore import QTimer
from core.emulator import RISCV_Emulator
from ui.main_window import RiscVEduApp

class MainController:
    """
    Controller (MVC): A ponte inteligente.
    Controla o timer, injeta o código do View no Model, dita as cores de log,
    e devolve os resultados do Model para a tela atualizar.
    """
    def __init__(self, model: RISCV_Emulator, view: RiscVEduApp):
        self.model = model
        self.view = view
        
        self.run_timer = QTimer()
        self.run_timer.timeout.connect(self.handle_step)
        
        # Conectar os sinais emitidos pela View aos métodos do Controller
        self.view.request_reset.connect(self.handle_reset)
        self.view.request_step.connect(self.handle_step)
        self.view.request_run_toggle.connect(self.handle_run_toggle)
        
        # Estado inicial
        self.handle_reset(self.view.editor.toPlainText())

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

    def handle_run_toggle(self):
        """Liga ou desliga a execução contínua."""
        if self.run_timer.isActive():
            self.run_timer.stop()
            self.view.set_run_state(False)
            self.view.log(">> Clock Automático Pausado.", "#f59e0b")
        else:
            if self.model.halted:
                # Se estiver parado no final, força um reset com o texto atual da view
                self.handle_reset(self.view.editor.toPlainText())
                
            self.run_timer.start(100) # 10Hz
            self.view.set_run_state(True)
            self.view.log(">> Executando clock contínuo (10Hz)...", "#3b82f6")

    def _sync_view(self):
        """Força a View a ler os dados mais recentes do Model."""
        self.view.update_hardware_ui(self.model.regs, self.model.memory, self.model.stage)
        
        current_line = self.model.get_current_line()
        self.view.highlight_line(current_line)