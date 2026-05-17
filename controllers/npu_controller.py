from PyQt5.QtCore import QTimer
import qtawesome as qta

from core.npu import NPUModel

class NPUController:
    """Controlador que reage aos cliques da aba da NPU."""
    def __init__(self, model: NPUModel, view):
        self.model = model
        self.view = view
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.handle_step)
        
        self.view.request_step.connect(self.handle_step)
        self.view.request_reset.connect(self.handle_reset)
        self.view.request_run.connect(self.handle_run)
        
        self.handle_reset()

    def handle_step(self):
        if self.model.cycle == 0:
            a_mat, b_mat = self.view.get_raw_matrices()
            self.model.reset(a_mat, b_mat)
            
        if not self.model.done:
            self.model.step()
            self.view.update_ui(self.model)
        else:
            self.timer.stop()
            if hasattr(self.view, 'btn_run'):
                self.view.btn_run.setText(" Auto Run")
                self.view.btn_run.setIcon(qta.icon('fa5s.play', color='white'))

    def handle_reset(self):
        self.timer.stop()
        if hasattr(self.view, 'btn_run'):
            self.view.btn_run.setText(" Auto Run")
            self.view.btn_run.setIcon(qta.icon('fa5s.play', color='white'))
            
        a_mat, b_mat = self.view.get_raw_matrices()
        self.model.reset(a_mat, b_mat)
        self.view.update_ui(self.model)

    def handle_run(self):
        if self.timer.isActive():
            self.timer.stop()
            if hasattr(self.view, 'btn_run'):
                self.view.btn_run.setText(" Auto Run")
                self.view.btn_run.setIcon(qta.icon('fa5s.play', color='white'))
        else:
            if self.model.done:
                self.handle_reset()
            self.timer.start(800)
            if hasattr(self.view, 'btn_run'):
                self.view.btn_run.setText(" Pause")
                self.view.btn_run.setIcon(qta.icon('fa5s.pause', color='white'))