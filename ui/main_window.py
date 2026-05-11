# ui/main_window.py
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QPlainTextEdit, QTextEdit, 
                             QFrame, QSplitter, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QAbstractItemView, QStackedWidget, 
                             QProgressBar, QSizePolicy,
                             QDialog, QFormLayout, QLineEdit, QComboBox, QDialogButtonBox) # <-- Adicionados imports para o Dialog
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QUrl
from PyQt5.QtGui import QColor, QTextFormat, QTextCursor, QDesktopServices
from core.connection_manager import ConnectionManager
import qtawesome as qta

from .highlighter import RISCVHighlighter
from .npu_widget import NPUWidget 
from .os_console_widget import OSConsoleWidget 
from .io_widget import IOWidget
from .dma_widget import DMAWidget 
from .tiling_widget import TilingWidget
from .nn_widget import NNWidget


# ==========================================
# JANELA POP-UP DE CONFIGURAÇÃO (GLOBAL)
# ==========================================
class ConnectionConfigDialog(QDialog):
    """Janela Modal para alterar Porta e Baud Rate globalmente."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(" Configurações de Conexão")
        self.setFixedSize(320, 160)
        self.setStyleSheet("""
            QDialog { background-color: #0B0D12; }
            QLabel { color: #8B9BB4; font-weight: bold; font-family: 'Consolas', monospace; font-size: 12px;}
            QLineEdit, QComboBox {
                background-color: #12141A;
                color: #6CA1A2;
                border: 1px solid #2A2F3A;
                border-radius: 4px;
                padding: 6px;
                font-family: 'Consolas', monospace;
                font-weight: bold;
            }
            QPushButton {
                background-color: transparent;
                color: #E2E8F0;
                border: 1px solid #2A2F3A;
                border-radius: 4px;
                padding: 6px 15px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #12141A; border: 1px solid #6CA1A2; }
        """)

        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.conn_mgr = ConnectionManager()

        self.port_input = QLineEdit(self.conn_mgr.get_port())
        
        self.baud_input = QComboBox()
        self.baud_input.addItems(["9600", "115200", "460800", "921600", "1000000"])
        self.baud_input.setCurrentText(str(self.conn_mgr.get_baud()))

        layout.addRow("Porta Serial:", self.port_input)
        layout.addRow("Baud Rate:", self.baud_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        # Destaque no botão de salvar
        buttons.button(QDialogButtonBox.Save).setStyleSheet("color: #5DB373; border-color: #5DB373;")
        layout.addWidget(buttons)

    def get_values(self):
        return self.port_input.text(), int(self.baud_input.currentText())


# ==========================================
# WIDGET DO EMULADOR RV32I
# ==========================================
class RV32IWidget(QWidget):
    """Isolamos o layout do Emulador RV32I em um Widget próprio."""
    request_reset = pyqtSignal(str)
    request_reset_fpga = pyqtSignal()
    request_step = pyqtSignal()
    request_run_toggle = pyqtSignal()
    request_upload = pyqtSignal()     
    request_sync_fpga = pyqtSignal()

    def __init__(self):
        super().__init__()
        w_layout = QVBoxLayout(self)
        w_layout.setContentsMargins(30, 20, 30, 30)
        w_layout.setSpacing(20)
        
        # 1. Pipeline
        pipeline_frame = QFrame()
        pipeline_frame.setStyleSheet("background-color: #0B0D12; border: 1px solid #2A2F3A; border-radius: 4px; padding: 2px;")
        pipeline_frame.setFixedHeight(34)
        pipeline_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        pipe_layout = QHBoxLayout(pipeline_frame)
        pipe_layout.setContentsMargins(2, 2, 2, 2)
        pipe_layout.setSpacing(4)
        
        self.stage_labels = []
        for s in ["IF", "ID", "EX", "MEM", "WB"]:
            lbl = QLabel(s)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setProperty("class", "PipelineStage")
            lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.stage_labels.append(lbl)
            pipe_layout.addWidget(lbl)
            
        # 2. Botões de Emulação
        self.btn_reset = QPushButton(" Reset")
        self.btn_reset.setIcon(qta.icon('fa5s.sync-alt', color='#f8fafc'))
        self.btn_reset.setProperty("class", "ActionBtn")
        self.btn_reset.clicked.connect(self.request_reset_fpga.emit) 
        
        self.btn_step = QPushButton(" Step (Clock)")
        self.btn_step.setIcon(qta.icon('fa5s.step-forward', color='#f8fafc'))
        self.btn_step.setProperty("class", "ActionBtn")
        self.btn_step.clicked.connect(self.request_step.emit)
        
        self.btn_run = QPushButton(" Run")
        self.btn_run.setIcon(qta.icon('fa5s.play', color='white'))
        self.btn_run.setProperty("class", "ActionBtn PrimaryBtn")
        self.btn_run.clicked.connect(self.request_run_toggle.emit)
        
        self.btn_sync = QPushButton(" Sync Hardware")
        self.btn_sync.setIcon(qta.icon('fa5s.satellite-dish', color='white'))
        self.btn_sync.setProperty("class", "ActionBtn")
        self.btn_sync.setStyleSheet("background-color: #6366f1; color: white; border: none;")
        self.btn_sync.clicked.connect(self.request_sync_fpga.emit)

        # 3. Botão de Upload e Barra de Progresso
        self.btn_upload = QPushButton(" Upload FPGA")
        self.btn_upload.setIcon(qta.icon('fa5s.cloud-upload-alt', color='white'))
        self.btn_upload.setProperty("class", "ActionBtn SuccessBtn")
        self.btn_upload.setFixedHeight(34)
        self.btn_upload.clicked.connect(self.request_upload.emit)

        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.progressBar.setFixedHeight(34)
        self.progressBar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.progressBar.setStyleSheet("""
            QProgressBar { border: 1px solid #2A2F3A; border-radius: 4px; text-align: center; color: white; background-color: #0B0D12;}
            QProgressBar::chunk { background-color: #5DB373; border-radius: 3px; }
        """)

        # ==========================================
        # MONTAGEM DA ÁREA CENTRAL (Splitter)
        # ==========================================
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setHandleWidth(25)
        
        # --- PAINEL ESQUERDO ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        top_editor_layout = QHBoxLayout()
        editor_icon = QLabel()
        editor_icon.setPixmap(qta.icon('fa5s.file-code', color='#8B9BB4').pixmap(16, 16))
        top_editor_layout.addWidget(editor_icon)
        
        editor_label = QLabel("Código Assembly")
        editor_label.setStyleSheet("font-weight:700; color:#8B9BB4; background-color: transparent;")
        top_editor_layout.addWidget(editor_label)
        top_editor_layout.addStretch()
        top_editor_layout.addWidget(self.btn_reset)
        top_editor_layout.addWidget(self.btn_step)
        top_editor_layout.addWidget(self.btn_run)
        top_editor_layout.addWidget(self.btn_sync)
        
        left_layout.addLayout(top_editor_layout)
        
        self.editor = QPlainTextEdit()
        self.editor.setViewportMargins(15, 0, 0, 0)
        self.highlighter = RISCVHighlighter(self.editor.document())
        code = """# RISC-V Assembly - Fibonacci salvando em Memoria\n.global _start\n\n_start:\n    li t0, 0\n    li t1, 1\n    li t2, 10\n    li t3, 0\n    li t5, 0\n\nfib_loop:\n    beq t3, t2, end\n    sw t0, 0(t5)\n    add t4, t0, t1\n    mv t0, t1\n    mv t1, t4\n    addi t3, t3, 1\n    addi t5, t5, 4\n    j fib_loop\n\nend:\n    wfi"""
        self.editor.setPlainText(code)
        left_layout.addWidget(self.editor)
        
        bottom_editor_layout = QHBoxLayout()
        bottom_editor_layout.setContentsMargins(0, 10, 0, 0)
        bottom_editor_layout.addWidget(self.progressBar)
        bottom_editor_layout.addWidget(self.btn_upload)
        
        left_layout.addLayout(bottom_editor_layout)
        
        # --- PAINEL DIREITO ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        right_layout.addWidget(pipeline_frame)
        right_layout.addSpacing(10)
        
        hw_splitter = QSplitter(Qt.Vertical)
        
        tabela_moderna_css = """
            QTableWidget { border: none; background-color: transparent; }
            QHeaderView::section { background-color: transparent; color: #6CA1A2; border: none; border-bottom: 2px solid #6CA1A2; font-size: 12px; font-weight: bold; padding: 4px; }
            QTableWidget::item { border-bottom: 1px solid #1A1D24; }
        """
        
        reg_widget = QWidget()
        reg_layout = QVBoxLayout(reg_widget)
        reg_layout.setContentsMargins(0,0,0,0)
        reg_title = QLabel("📊 Banco de Registradores (RegFile)")
        reg_title.setStyleSheet("font-weight:700; color:#8B9BB4; margin-bottom: 5px; background-color: transparent;")
        reg_layout.addWidget(reg_title)
        
        self.reg_table = QTableWidget(32, 3)
        self.reg_table.setStyleSheet(tabela_moderna_css)
        self.reg_table.setHorizontalHeaderLabels(["Reg", "ABI", "Valor"])
        self.reg_table.verticalHeader().setVisible(False)
        self.reg_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.reg_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.reg_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.reg_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.abi_names = ["zero","ra","sp","gp","tp","t0","t1","t2","s0","s1","a0","a1","a2","a3","a4","a5","a6","a7","s2","s3","s4","s5","s6","s7","s8","s9","s10","s11","t3","t4","t5","t6"]
        
        for i in range(32):
            self.reg_table.setItem(i, 0, self._create_item(f"x{i}"))
            self.reg_table.setItem(i, 1, self._create_item(self.abi_names[i], "#8B9BB4"))
            self.reg_table.setItem(i, 2, self._create_item("0", "#6CA1A2"))
            
        reg_layout.addWidget(self.reg_table)
        
        mem_widget = QWidget()
        mem_layout = QVBoxLayout(mem_widget)
        mem_layout.setContentsMargins(0,0,0,0)
        mem_title = QLabel("🗄️ Memória RAM (Data)")
        mem_title.setStyleSheet("font-weight:700; color:#8B9BB4; margin-bottom: 5px; margin-top: 10px; background-color: transparent;")
        mem_layout.addWidget(mem_title)
        
        self.mem_table = QTableWidget(0, 2)
        self.mem_table.setStyleSheet(tabela_moderna_css)
        self.mem_table.setHorizontalHeaderLabels(["Endereço", "Valor"])
        self.mem_table.verticalHeader().setVisible(False)
        self.mem_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.mem_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.mem_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        mem_layout.addWidget(self.mem_table)
        
        hw_splitter.addWidget(reg_widget)
        hw_splitter.addWidget(mem_widget)
        hw_splitter.setStretchFactor(0, 1) 
        hw_splitter.setStretchFactor(1, 1) 
        
        right_layout.addWidget(hw_splitter)
        
        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(right_widget)
        
        main_splitter.setSizes([800, 350]) 
        main_splitter.setStretchFactor(0, 7) 
        main_splitter.setStretchFactor(1, 3)
        
        w_layout.addWidget(main_splitter, 1) 
        
        # ==========================================
        # CONSOLE INFERIOR
        # ==========================================
        console_label = QLabel(" OS Console / Execution Log")
        console_label.setStyleSheet("font-weight:700; color:#8B9BB4; background-color: transparent;")
        w_layout.addWidget(console_label)
        
        self.console = QTextEdit()
        self.console.setObjectName("TerminalOutput")
        self.console.setViewportMargins(15, 0, 0, 0)
        self.console.setReadOnly(True)
        self.console.setFixedHeight(140)
        self.console.append(">> Ambiente Emulador Multiciclo Inicializado com Sucesso.")
        w_layout.addWidget(self.console)

    def _create_item(self, text: str, color: str = "#e2e8f0") -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        item.setForeground(QColor(color))
        return item

    def log(self, msg: str, color: str = "#cbd5e1"):
        self.console.append(f"<span style='color:{color};'>{msg}</span>")
        sb = self.console.verticalScrollBar()
        sb.setValue(sb.maximum())
        
    def clear_log(self):
        self.console.clear()

    def set_run_state(self, is_running: bool):
        if is_running:
            self.btn_run.setText(" Pause")
            self.btn_run.setIcon(qta.icon('fa5s.pause', color='white'))
        else:
            self.btn_run.setText(" Run")
            self.btn_run.setIcon(qta.icon('fa5s.play', color='white'))

    def update_memory_view(self, address: int, value: int):
        addr_hex = f"0x{address:08X}" 
        for row in range(self.mem_table.rowCount()):
            item = self.mem_table.item(row, 0)
            if item and item.text() == addr_hex:
                self.mem_table.item(row, 1).setText(str(value))
                return

        row_idx = self.mem_table.rowCount()
        self.mem_table.insertRow(row_idx)
        self.mem_table.setItem(row_idx, 0, self._create_item(addr_hex, "#F3F3F3"))
        self.mem_table.setItem(row_idx, 1, self._create_item(str(value), "#6CA1A2"))
        self.mem_table.sortItems(0, Qt.AscendingOrder)

    def update_hardware_ui(self, regs: list, memory: dict, stage: int):
        for i, lbl in enumerate(self.stage_labels):
            lbl.setProperty("class", "PipelineStageActive" if i == stage else "PipelineStage")
            lbl.style().unpolish(lbl)
            lbl.style().polish(lbl)

        for i in range(32):
            current_val = regs[i]
            item = self.reg_table.item(i, 2)
            if int(item.text()) != current_val:
                item.setText(str(current_val))
                item.setBackground(QColor("#2A2F3A")) 
                item.setForeground(QColor("#DC673E")) 
            else:
                item.setBackground(QColor("transparent"))
                item.setForeground(QColor("#6CA1A2")) 

        for row in range(self.mem_table.rowCount()):
            addr_item = self.mem_table.item(row, 0)
            val_item = self.mem_table.item(row, 1)
            if addr_item and val_item:
                addr = int(addr_item.text(), 16)
                val = memory.get(addr, 0)
                if int(val_item.text()) != val:
                    val_item.setText(str(val))
                    val_item.setForeground(QColor("#DC673E"))

    def highlight_line(self, line_idx: int):
        extra_selections = []
        if line_idx >= 0:
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor("#1e293b")) 
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            cursor = self.editor.textCursor()
            cursor.setPosition(0)
            cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, line_idx)
            selection.cursor = cursor
            extra_selections.append(selection)
        self.editor.setExtraSelections(extra_selections)


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