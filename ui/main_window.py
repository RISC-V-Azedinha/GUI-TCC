# ui/main_window.py
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFrame, QStackedWidget, QDialog)
from PyQt5.QtCore import QSize, QUrl
from PyQt5.QtGui import QDesktopServices
from core.connection_manager import ConnectionManager
import qtawesome as qta

# === IMPORTS DOS SEUS COMPONENTES EXTRAÍDOS ===
from .components.connection_dialog import ConnectionConfigDialog
from .tabs.rv32i_widget import RV32IWidget
from .tabs.npu_widget import NPUWidget 
from .tabs.os_console_widget import OSConsoleWidget 
from .tabs.io_widget import IOWidget
from .tabs.dma_widget import DMAWidget 
from .tabs.tiling_widget import TilingWidget
from .tabs.nn_widget import NNWidget

# ==========================================
# JANELA PRINCIPAL DA APLICAÇÃO
# ==========================================
class RiscVEduApp(QMainWindow):
    """A Janela Global que abriga a Sidebar e o StackedWidget com os laboratórios."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plataforma Educacional RISC-V")
        self.resize(1400, 850)
        
        # Inicia o Gerenciador Global
        self.conn_mgr = ConnectionManager()
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.setup_sidebar()
        self.setup_main_area()

        # Inscreve-se nas atualizações de configuração
        self.conn_mgr.config_updated.connect(self.update_global_header)

    @property
    def request_reset(self): return self.rv32i_view.request_reset
    @property
    def request_reset_fpga(self): return self.rv32i_view.request_reset_fpga
    @property
    def request_step(self): return self.rv32i_view.request_step
    @property
    def request_run_toggle(self): return self.rv32i_view.request_run_toggle
    @property
    def request_upload(self): return self.rv32i_view.request_upload
    @property
    def request_sync_fpga(self): return self.rv32i_view.request_sync_fpga 
    @property
    def editor(self): return self.rv32i_view.editor
    @property
    def progressBar(self): return self.rv32i_view.progressBar

    def log(self, msg: str, color: str = "#cbd5e1"): 
        self.rv32i_view.log(msg, color)
    def clear_log(self): 
        self.rv32i_view.clear_log()
    def set_run_state(self, is_running: bool): 
        self.rv32i_view.set_run_state(is_running)
    def update_hardware_ui(self, regs: list, memory: dict, stage: int): 
        self.rv32i_view.update_hardware_ui(regs, memory, stage)
    def highlight_line(self, line_idx: int): 
        self.rv32i_view.highlight_line(line_idx)

    def setup_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(280)
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        title = QLabel("RISC-V Edu Platform")
        title.setObjectName("AppTitle")
        title.setStyleSheet("border-bottom: 1px solid #2A2F3A; border-right: 1px solid #2A2F3A; background-color: #0B0D12;")
        layout.addWidget(title)
        
        self.nav_buttons = []
        labs = [
            (" 1. Core RV32I", "fa5s.microchip", True, 0),
            (" 2. Drivers & I/O", "fa5s.plug", True, 1),
            (" 3. DMA Controller", "fa5s.bolt", True, 2),
            (" 4. NPU Micro-Arch", "fa5s.brain", True, 3),
            (" 5. Tiling & Scaling", "fa5s.layer-group", True, 4),
            (" 6. OS Console", "fa5s.terminal", True, 5),
            (" 7. Neural Network", "fa5s.project-diagram", True, 6)
        ]
        
        for name, icon_name, enabled, target_idx in labs:
            btn = QPushButton(name)
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setIcon(qta.icon(icon_name, color="#94a3b8"))
            btn.setIconSize(QSize(18, 18))
            
            if not enabled:
                btn.setEnabled(False)
            else:
                btn.clicked.connect(lambda checked, idx=target_idx, b=btn: self.switch_lab(idx, b))
                
            self.nav_buttons.append(btn)
            layout.addWidget(btn)
            
        layout.addStretch() 
        self.main_layout.addWidget(self.sidebar)

    def setup_main_area(self):
        self.main_content = QFrame()
        layout = QVBoxLayout(self.main_content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(70)
        header.setStyleSheet("border-bottom: 1px solid #2A2F3A; background-color: #12141A;")
        
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(30, 0, 30, 0)
        
        term_icon = QLabel()
        term_icon.setPixmap(qta.icon('fa5s.plug', color='#8B9BB4').pixmap(16, 16))
        term_icon.setStyleSheet("border: none; background: transparent;")
        h_layout.addWidget(term_icon)
        
        # AQUI usamos o ConnectionManager dinamicamente!
        self.term_info = QLabel(f"{self.conn_mgr.get_port()} @ {self.conn_mgr.get_baud()} baud")
        self.term_info.setStyleSheet("color: #8B9BB4; font-family: 'Consolas', monospace; font-weight: bold; border: none; background: transparent;")
        h_layout.addWidget(self.term_info)
        
        h_layout.addSpacing(25)
        
        status_icon = QLabel()
        status_icon.setPixmap(qta.icon('fa5s.circle', color='#10b981').pixmap(12, 12))
        status_icon.setStyleSheet("border: none; background: transparent;")
        h_layout.addWidget(status_icon)
        
        status_lbl = QLabel("FPGA SERIAL: CONNECTED")
        status_lbl.setStyleSheet("color: #10b981; font-size: 11px; font-weight: 800; border: none; background: transparent;")
        h_layout.addWidget(status_lbl)
        
        h_layout.addStretch()
        
        self.btn_save = QPushButton(" Save")
        self.btn_save.setIcon(qta.icon('fa5s.save', color='#8B9BB4'))
        self.btn_save.setProperty("class", "GhostBtn")
        h_layout.addWidget(self.btn_save)
        
        self.btn_load = QPushButton(" Load")
        self.btn_load.setIcon(qta.icon('fa5s.folder-open', color='#8B9BB4'))
        self.btn_load.setProperty("class", "GhostBtn")
        h_layout.addWidget(self.btn_load)
        
        # CONEXÃO DO BOTÃO CONFIG
        self.btn_config = QPushButton(" Config")
        self.btn_config.setIcon(qta.icon('fa5s.cog', color='#8B9BB4'))
        self.btn_config.setProperty("class", "GhostBtn")
        self.btn_config.clicked.connect(self.open_config_dialog)
        h_layout.addWidget(self.btn_config)
        
        self.btn_guide = QPushButton(" Guide")
        self.btn_guide.setIcon(qta.icon('fa5s.book-open', color='#8B9BB4'))
        self.btn_guide.setProperty("class", "GhostBtn")
        self.btn_guide.clicked.connect(self.open_guide)
        h_layout.addWidget(self.btn_guide)
        
        layout.addWidget(header)
        
        self.stacked_widget = QStackedWidget()
        
        self.rv32i_view = RV32IWidget()
        self.io_view = IOWidget()
        self.dma_view = DMAWidget()
        self.npu_view = NPUWidget()
        self.tiling_view = TilingWidget()
        self.os_console_view = OSConsoleWidget()
        self.nn_view = NNWidget()
        
        self.stacked_widget.addWidget(self.rv32i_view)      # Índice 0
        self.stacked_widget.addWidget(self.io_view)         # Índice 1
        self.stacked_widget.addWidget(self.dma_view)        # Índice 2
        self.stacked_widget.addWidget(self.npu_view)        # Índice 3
        self.stacked_widget.addWidget(self.tiling_view)     # Índice 4
        self.stacked_widget.addWidget(self.os_console_view) # Índice 5
        self.stacked_widget.addWidget(self.nn_view)         # Índice 6 
        
        layout.addWidget(self.stacked_widget)
        self.main_layout.addWidget(self.main_content)
        
        self.switch_lab(0, self.nav_buttons[0])

    def open_config_dialog(self):
        """Abre a janela de configurações e aplica os novos valores."""
        dialog = ConnectionConfigDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            porta, baud = dialog.get_values()
            # O save dispara automaticamente um evento que todas as abas vão escutar!
            self.conn_mgr.set_config(porta, baud)

    def update_global_header(self, port, baud):
        """Callback chamada pelo Manager sempre que a porta é alterada."""
        self.term_info.setText(f"{port} @ {baud} baud")

    def open_guide(self):
        url = QUrl("https://risc-v-azedinha.github.io/RISC-V/")
        if not url.isValid():
            self.log("[ERRO] URL inválida.", "#ef4444")
            return
        QDesktopServices.openUrl(url)

    def switch_lab(self, index, active_btn):
        self.stacked_widget.setCurrentIndex(index)
        for btn in self.nav_buttons:
            if btn != active_btn:
                btn.setChecked(False)
        active_btn.setChecked(True)