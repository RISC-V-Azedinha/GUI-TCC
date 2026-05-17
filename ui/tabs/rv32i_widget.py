# ui/main_window.py
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QPlainTextEdit, QTextEdit, 
                             QFrame, QSplitter, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QAbstractItemView, 
                             QProgressBar, QSizePolicy, QMenu, QAction) 
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QTextFormat, QTextCursor
import qtawesome as qta

from ..components.highlighter import RISCVHighlighter
from artefacts import sample_code

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
    request_set_bkp = pyqtSignal(int)
    request_clr_bkp = pyqtSignal()

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
        code = sample_code.code
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
        
        # Setup do Context Menu para Breakpoints
        self.editor.setContextMenuPolicy(Qt.CustomContextMenu)
        self.editor.customContextMenuRequested.connect(self.show_editor_menu)
        self.bkp_line_idx = -1
        self.current_exec_line = -1

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
        """Altera o texto, ícone e cor do botão para refletir o estado."""
        if is_running:
            self.btn_run.setText(" Pause")
            self.btn_run.setIcon(qta.icon('fa5s.pause', color='white'))
            # Fundo Laranja (Alerta) quando está a rodar e o botão serve para pausar
            self.btn_run.setStyleSheet("background-color: #f59e0b; color: white; border: none; font-weight: bold; border-radius: 4px;")
        else:
            self.btn_run.setText(" Run")
            self.btn_run.setIcon(qta.icon('fa5s.play', color='white'))
            # Fundo Azul (Ação) quando está parado e o botão serve para rodar
            self.btn_run.setStyleSheet("background-color: #3b82f6; color: white; border: none; font-weight: bold; border-radius: 4px;")

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
        
    def show_editor_menu(self, position):
        menu = QMenu()
        menu.setStyleSheet("QMenu { background-color: #1A1D24; color: #E2E8F0; border: 1px solid #2A2F3A; } QMenu::item:selected { background-color: #3B82F6; }")
        
        toggle_bkp_action = QAction("🔴 Toggle Breakpoint nesta linha", self)
        toggle_bkp_action.triggered.connect(self.toggle_breakpoint)
        menu.addAction(toggle_bkp_action)
        
        # Adiciona a ação padrão de limpar BKP
        clear_bkp_action = QAction("⭕ Limpar Breakpoint", self)
        clear_bkp_action.triggered.connect(self.clear_breakpoint)
        menu.addAction(clear_bkp_action)
        
        menu.exec_(self.editor.viewport().mapToGlobal(position))

    def update_editor_highlights(self):
        """Renderizador unificado com posicionamento absoluto de bloco."""
        selections = []

        # 1. Pinta o Breakpoint (Vermelho Escuro)
        if self.bkp_line_idx >= 0:
            sel_bkp = QTextEdit.ExtraSelection()
            sel_bkp.format.setBackground(QColor("#451a1e"))
            sel_bkp.format.setProperty(QTextFormat.FullWidthSelection, True)
            cursor = self.editor.textCursor()
            # NOVA LÓGICA: Posicionamento absoluto e infalível
            cursor.setPosition(self.editor.document().findBlockByNumber(self.bkp_line_idx).position())
            sel_bkp.cursor = cursor
            selections.append(sel_bkp)

        # 2. Pinta a Linha de Execução Atual do PC (Azul Escuro)
        if self.current_exec_line >= 0:
            sel_exec = QTextEdit.ExtraSelection()
            if self.current_exec_line == self.bkp_line_idx:
                sel_exec.format.setBackground(QColor("#4c1d95")) 
            else:
                sel_exec.format.setBackground(QColor("#1e293b")) 
                
            sel_exec.format.setProperty(QTextFormat.FullWidthSelection, True)
            cursor = self.editor.textCursor()
            # NOVA LÓGICA: Posicionamento absoluto e infalível
            cursor.setPosition(self.editor.document().findBlockByNumber(self.current_exec_line).position())
            sel_exec.cursor = cursor
            selections.append(sel_exec)

        self.editor.setExtraSelections(selections)

    def highlight_line(self, line_idx: int):
        self.current_exec_line = line_idx
        self.update_editor_highlights()

    def toggle_breakpoint(self):
        cursor = self.editor.textCursor()
        self.bkp_line_idx = cursor.blockNumber()
        self.update_editor_highlights() 
        self.request_set_bkp.emit(self.bkp_line_idx)

    def clear_breakpoint(self):
        self.bkp_line_idx = -1
        self.update_editor_highlights() 
        self.request_clr_bkp.emit()

    