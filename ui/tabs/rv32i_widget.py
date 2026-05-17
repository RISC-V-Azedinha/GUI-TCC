# ui/main_window.py
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QPlainTextEdit, QTextEdit, 
                             QFrame, QSplitter, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QAbstractItemView, 
                             QProgressBar, QSizePolicy) 
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QTextFormat, QTextCursor
import qtawesome as qta

from ..components.highlighter import RISCVHighlighter

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

# Dentro da classe RV32IWidget em ui/main_window.py

    def update_hardware_ui(self, regs: list, memory: dict, stage: int):
        # Atualiza Labels de Pipeline
        for i, lbl in enumerate(self.stage_labels):
            lbl.setProperty("class", "PipelineStageActive" if i == stage else "PipelineStage")
            lbl.style().unpolish(lbl)
            lbl.style().polish(lbl)

        # Atualiza Registradores com as cores do tema novo
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