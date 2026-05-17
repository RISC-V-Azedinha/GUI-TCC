# ui/npu_widget.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFrame, QGridLayout, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIntValidator
import qtawesome as qta

# ==========================================
# PALETA OFICIAL DO PROJETO (Com Fundos Translúcidos)
# ==========================================
BG_PANEL = "#0B0D12"
BG_ELEMENT = "#12141A"
BORDER = "#2A2F3A"
TEXT_PRIMARY = "#E2E8F0"
TEXT_SECONDARY = "#8B9BB4"

# Cores Sólidas
TEAL = "#6CA1A2"
ORANGE = "#DC673E"
GREEN = "#5DB373"
MUSTARD = "#F2B845"
PURPLE = "#A855F7" # <-- Roxo de volta!

# Cores Translúcidas (15% de opacidade) para preencher os blocos
TEAL_DIM = "rgba(108, 161, 162, 0.15)"
ORANGE_DIM = "rgba(220, 103, 62, 0.15)"
GREEN_DIM = "rgba(93, 179, 115, 0.15)"
MUSTARD_DIM = "rgba(242, 184, 69, 0.15)"


class PPUToggle(QFrame):
    toggled = pyqtSignal(bool)
    
    def __init__(self, text, active=False):
        super().__init__()
        self.active = active
        self.setFixedHeight(40)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        self.lbl = QLabel(text)
        self.lbl.setStyleSheet("border: none; font-weight: bold;")
        
        self.dot = QLabel("●")
        self.dot.setStyleSheet("border: none; font-size: 16px;")
        
        layout.addWidget(self.lbl)
        layout.addStretch()
        layout.addWidget(self.dot)
        self.update_style()

    def mousePressEvent(self, event):
        self.active = not self.active
        self.update_style()
        self.toggled.emit(self.active)
        super().mousePressEvent(event)

    def update_style(self):
        # Usando Roxo (PURPLE) quando ativo, e fundo totalmente transparente
        color = PURPLE if self.active else TEXT_SECONDARY
        border = f"1px solid {color}" if self.active else f"1px dashed {BORDER}"
        self.setStyleSheet(f"background-color: transparent; border: {border}; border-radius: 6px;")
        self.lbl.setStyleSheet(f"color: {color}; border: none; font-weight: bold;")
        self.dot.setStyleSheet(f"color: {color}; border: none;")

class PEWidget(QFrame):
    def __init__(self, r, c):
        super().__init__()
        self.r = r
        self.c = c
        self.setObjectName("PEBox")
        
        self.setStyleSheet(f"""
            #PEBox {{ border: 2px solid {TEAL}; border-radius: 8px; background-color: {TEAL_DIM}; }}
            #PEBoxDone {{ border: 2px solid {GREEN}; border-radius: 8px; background-color: {GREEN_DIM}; }}
        """)
        self.setFixedSize(120, 120) 
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        h_layout = QHBoxLayout()
        lbl_name = QLabel(f"PE_{r}{c}")
        lbl_name.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 11px; border: none;")
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet(f"color: {TEAL}; font-size: 11px; font-weight: bold; border: none;")
        h_layout.addWidget(lbl_name)
        h_layout.addStretch()
        h_layout.addWidget(self.lbl_status)
        layout.addLayout(h_layout)
        
        self.lbl_mac = QLabel("---")
        self.lbl_mac.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 14px; border: none;")
        self.lbl_mac.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_mac)
        
        self.lbl_acc = QLabel("0")
        self.lbl_acc.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 28px; font-weight: bold; border: none;")
        self.lbl_acc.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_acc)
        
        self.progress = QFrame()
        self.progress.setFixedHeight(4)
        self.progress.setStyleSheet(f"background-color: {TEAL}; border-radius: 2px;")
        layout.addWidget(self.progress)

    def update_state(self, a, b, acc, done):
        self.lbl_mac.setText(f"{a}*{b}" if not done else "---")
        self.lbl_acc.setText(str(acc))
        if done:
            self.lbl_status.setText("DONE")
            self.lbl_acc.setStyleSheet(f"color: {GREEN}; font-size: 28px; font-weight: bold; border: none;")
            self.progress.setStyleSheet(f"background-color: {GREEN}; border-radius: 2px;")
            self.setObjectName("PEBoxDone")
        else:
            self.lbl_status.setText("")
            self.lbl_acc.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 28px; font-weight: bold; border: none;")
            self.progress.setStyleSheet(f"background-color: {TEAL}; border-radius: 2px;")
            self.setObjectName("PEBox")
            
        self.style().unpolish(self)
        self.style().polish(self)

class NPUWidget(QWidget):
    request_step = pyqtSignal()
    request_reset = pyqtSignal()
    request_run = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # CABEÇALHO DA NPU
        header = QHBoxLayout()
        title_icon = QLabel()
        title_icon.setPixmap(qta.icon('fa5s.brain', color=PURPLE).pixmap(24, 24)) # Cérebro roxo!
        header.addWidget(title_icon)
        
        title_texts = QVBoxLayout()
        lbl_title = QLabel("NPU Micro-Architecture")
        lbl_title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {TEXT_PRIMARY};")
        lbl_sub = QLabel("Systolic Array 3x3 • Output Stationary • PPU Pipeline")
        lbl_sub.setStyleSheet(f"font-size: 11px; color: {TEXT_SECONDARY};")
        title_texts.addWidget(lbl_title)
        title_texts.addWidget(lbl_sub)
        header.addLayout(title_texts)
        header.addStretch()
        
        lbl_clock_title = QLabel("Global Clock")
        lbl_clock_title.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        self.lbl_clock = QLabel("0")
        self.lbl_clock.setStyleSheet(f"color: {TEAL}; font-size: 24px; font-weight: bold;")
        
        clock_layout = QVBoxLayout()
        clock_layout.addWidget(lbl_clock_title)
        clock_layout.addWidget(self.lbl_clock)
        clock_layout.setAlignment(Qt.AlignRight)
        header.addLayout(clock_layout)
        header.addSpacing(20)
        
        self.btn_reset = QPushButton(" Reset")
        self.btn_reset.setIcon(qta.icon('fa5s.sync-alt', color=TEXT_PRIMARY))
        self.btn_reset.setProperty("class", "ActionBtn")
        self.btn_reset.clicked.connect(self.request_reset.emit)
        
        self.btn_step = QPushButton(" Step Clock")
        self.btn_step.setIcon(qta.icon('fa5s.step-forward', color=TEXT_PRIMARY))
        self.btn_step.setStyleSheet(f"background-color: {ORANGE}; color: {BG_ELEMENT}; border-radius: 6px; padding: 8px 16px; font-weight: bold;")
        self.btn_step.clicked.connect(self.request_step.emit)

        self.btn_run = QPushButton(" Auto Run")
        self.btn_run.setIcon(qta.icon('fa5s.play', color=TEXT_PRIMARY))
        self.btn_run.setStyleSheet(f"background-color: #6366f1; color: white; border-radius: 6px; padding: 8px 16px; font-weight: bold;")
        self.btn_run.clicked.connect(self.request_run.emit)
        
        header.addWidget(self.btn_reset)
        header.addWidget(self.btn_step)
        header.addWidget(self.btn_run)
        main_layout.addLayout(header)
        main_layout.addSpacing(20)
        
        # GRID PRINCIPAL E ALINHAMENTO
        panels_grid = QGridLayout()
        panels_grid.setSpacing(30) 
        
        frame_input, self.panel_input = self._create_panel("INPUT MEMORY (A)")
        frame_weight, self.panel_weight = self._create_panel("WEIGHT MEMORY (B)")
        frame_core, self.panel_core = self._create_panel("SYSTOLIC ARRAY (CORE)")
        
        self.grid_input = QGridLayout(self.panel_input)
        self.grid_weight = QGridLayout(self.panel_weight)
        self.grid_core = QGridLayout(self.panel_core)
        
        panels_grid.addWidget(frame_input, 1, 0, Qt.AlignTop | Qt.AlignRight)
        panels_grid.addWidget(frame_weight, 0, 1, Qt.AlignBottom | Qt.AlignHCenter)
        panels_grid.addWidget(frame_core, 1, 1, Qt.AlignTop | Qt.AlignHCenter)
        
        # PAINEL DIREITO CORRIGIDO
        col_right = QVBoxLayout()
        col_right.setContentsMargins(0, 0, 0, 0)
        col_right.setSpacing(20) # Espaço entre Output e PPU
        
        frame_output, self.panel_output = self._create_panel("OUTPUT MEMORY (C)")
        frame_output.setFixedWidth(280)
        self.grid_output = QGridLayout(self.panel_output)
        self.grid_output.setContentsMargins(0, 0, 0, 0) # <--- ADICIONE ESTA LINHA
        
        frame_ppu, self.panel_ppu = self._create_panel("PPU PIPELINE")
        frame_ppu.setFixedWidth(280)
        ppu_layout = QVBoxLayout(self.panel_ppu)
        ppu_layout.setContentsMargins(0, 0, 0, 0)
        
        self.ppu_bias = PPUToggle("Add Bias (+5)", active=False)
        self.ppu_relu = PPUToggle("ReLU Activation", active=True)
        self.ppu_quant = PPUToggle("Quantization (Int8)", active=False)
        
        self.ppu_bias.toggled.connect(self.force_update_output)
        self.ppu_relu.toggled.connect(self.force_update_output)
        self.ppu_quant.toggled.connect(self.force_update_output)
        
        ppu_layout.addWidget(self.ppu_bias)
        ppu_layout.addWidget(self.ppu_relu)
        ppu_layout.addWidget(self.ppu_quant)
        
        # Adiciona os frames à coluna direita
        col_right.addWidget(frame_output, 0, Qt.AlignTop) # Força Output pro topo
        col_right.addStretch() # Mola central
        col_right.addWidget(frame_ppu, 0, Qt.AlignBottom) # Força PPU pra base
        
        # O PONTO CRÍTICO: Adicionar o layout ao grid com ALINHAMENTO TOTAL (Fill)
        # Usamos o sinalizador Qt.Alignment() vazio para ele ocupar a altura total da célula
        panels_grid.addLayout(col_right, 1, 2) 
        
        # Ajuste fino: Se a PPU ainda parecer subir, podemos forçar o alinhamento 
        # da célula específica do grid para esticar
        panels_grid.setRowStretch(1, 1)

        wrapper = QHBoxLayout()
        wrapper.addStretch()
        wrapper.addLayout(panels_grid)
        wrapper.addStretch()
        
        main_layout.addStretch()
        main_layout.addLayout(wrapper)
        main_layout.addStretch()
        
        self.setup_grids()
        
    def _create_panel(self, title):
        frame = QFrame()
        frame.setStyleSheet(f"background-color: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 8px;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 15, 15, 15)
        
        lbl = QLabel(title)
        lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: bold; font-size: 12px; border: none; margin-bottom: 5px;")
        layout.addWidget(lbl)
        
        content = QWidget()
        content.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(content)
        return frame, content

    def setup_grids(self):
        CELL_SIZE = 120
        SPACING = 20

        self.grid_core.setSpacing(SPACING)
        self.grid_input.setVerticalSpacing(SPACING)
        self.grid_weight.setHorizontalSpacing(SPACING)

        for i in range(3):
            self.grid_core.setRowMinimumHeight(i, CELL_SIZE)
            self.grid_core.setColumnMinimumWidth(i, CELL_SIZE)
            self.grid_input.setRowMinimumHeight(i, CELL_SIZE)
            self.grid_weight.setColumnMinimumWidth(i, CELL_SIZE)

        # 1. Matriz de Entrada A
        self.a_inputs = [[QLineEdit() for _ in range(3)] for _ in range(3)]
        for r in range(3):
            lbl_row = QLabel(f"R{r}")
            lbl_row.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 10px; font-weight: bold;")
            self.grid_input.addWidget(lbl_row, r, 0, Qt.AlignVCenter | Qt.AlignRight)
            
            for c in range(3):
                le = self.a_inputs[r][c]
                le.setValidator(QIntValidator(-999, 999))
                le.setFixedSize(45, 45) 
                le.setAlignment(Qt.AlignCenter)
                le.setText(str(r * 3 + c + 1))
                self.grid_input.addWidget(le, r, c + 1, Qt.AlignCenter)
                
            arrow = QLabel("➔")
            arrow.setStyleSheet(f"color: {ORANGE}; font-size: 18px; font-weight: bold;")
            self.grid_input.addWidget(arrow, r, 4, Qt.AlignVCenter | Qt.AlignLeft)

        # 2. Matriz de Pesos B
        self.b_inputs = [[QLineEdit() for _ in range(3)] for _ in range(3)]
        for c in range(3):
            for r in range(3):
                le = self.b_inputs[r][c]
                le.setValidator(QIntValidator(-999, 999))
                le.setFixedSize(45, 40)
                le.setAlignment(Qt.AlignCenter)
                le.setText("1" if r == c else "0")
                self.grid_weight.addWidget(le, r, c, Qt.AlignCenter)
                
            arrow = QLabel("⬇")
            arrow.setStyleSheet(f"color: {MUSTARD}; font-size: 18px; font-weight: bold;")
            self.grid_weight.addWidget(arrow, 3, c, Qt.AlignTop | Qt.AlignHCenter)

        # 3. Systolic Array (PEs)
        self.pe_widgets = [[PEWidget(r, c) for c in range(3)] for r in range(3)]
        for r in range(3):
            for c in range(3):
                self.grid_core.addWidget(self.pe_widgets[r][c], r, c, Qt.AlignCenter)
                
        # 4. Output Memory (C)
        self.output_lbls = [[QLabel("?") for _ in range(3)] for _ in range(3)]
        for r in range(3):
            for c in range(3):
                lbl = self.output_lbls[r][c]
                lbl.setFixedSize(70, 50)
                lbl.setAlignment(Qt.AlignCenter)
                lbl.setStyleSheet(f"background-color: {GREEN_DIM}; color: {GREEN}; border: 1px solid {GREEN}; border-radius: 6px; font-weight: bold; font-size: 18px;")
                self.grid_output.addWidget(lbl, r, c)
                
        self._apply_matrix_styles(0)

    def get_raw_matrices(self):
        a_mat = []
        for r in range(3):
            row = []
            for c in range(3):
                val = self.a_inputs[r][c].text().strip()
                row.append(int(val) if val and val != '-' else 0)
            a_mat.append(row)
            
        b_mat = []
        for r in range(3):
            row = []
            for c in range(3):
                val = self.b_inputs[r][c].text().strip()
                row.append(int(val) if val and val != '-' else 0)
            b_mat.append(row)
            
        return a_mat, b_mat

    def force_update_output(self):
        if hasattr(self, 'last_model'):
            self.update_ui(self.last_model)

    def _apply_matrix_styles(self, current_cycle):
        for r in range(3):
            for c in range(3):
                target_cycle = r + c
                
                # Matriz A (Laranja)
                le_a = self.a_inputs[r][c]
                if current_cycle == target_cycle + 1: 
                    le_a.setStyleSheet(f"background-color: {ORANGE}; color: {BG_PANEL}; border: 2px solid {ORANGE}; border-radius: 6px; font-weight: bold; font-size: 16px;")
                elif current_cycle <= target_cycle:   
                    le_a.setStyleSheet(f"background-color: {ORANGE_DIM}; border: 1px solid {ORANGE}; color: {ORANGE}; border-radius: 6px; font-weight: bold; font-size: 16px;")
                else:                                 
                    le_a.setStyleSheet(f"background-color: transparent; border: 1px dashed {BORDER}; color: {TEXT_SECONDARY}; border-radius: 6px; font-weight: bold; font-size: 16px;")
                    
                # Matriz B (Mostarda)
                le_b = self.b_inputs[r][c]
                if current_cycle == target_cycle + 1: 
                    le_b.setStyleSheet(f"background-color: {MUSTARD}; color: {BG_PANEL}; border: 2px solid {MUSTARD}; border-radius: 6px; font-weight: bold; font-size: 16px;")
                elif current_cycle <= target_cycle:   
                    le_b.setStyleSheet(f"background-color: {MUSTARD_DIM}; border: 1px solid {MUSTARD}; color: {MUSTARD}; border-radius: 6px; font-weight: bold; font-size: 16px;")
                else:                                 
                    le_b.setStyleSheet(f"background-color: transparent; border: 1px dashed {BORDER}; color: {TEXT_SECONDARY}; border-radius: 6px; font-weight: bold; font-size: 16px;")

    def update_ui(self, model):
        self.last_model = model
        self.lbl_clock.setText(str(model.cycle))
        self._apply_matrix_styles(model.cycle)
        
        for r in range(3):
            for c in range(3):
                pe_state = model.pes[r][c]
                self.pe_widgets[r][c].update_state(pe_state['a'], pe_state['b'], pe_state['acc'], pe_state['done'])
                
                if pe_state['done']:
                    # ==========================================
                    # A LINHA QUE FALTAVA! (Puxar o valor do Acumulador)
                    val = pe_state['acc']
                    # ==========================================
                    
                    # --- PIPELINE DA PPU ---
                    if self.ppu_bias.active: 
                        val += 5
                    
                    if self.ppu_relu.active: 
                        val = max(0, val)
                    
                    if self.ppu_quant.active:
                        # 1. Escala: Reduz o acumulador de 32 bits (Divisão por 4)
                        val = val >> 2 
                        # 2. Saturação (Clipping) para limites de Inteiro de 8 bits com sinal
                        val = max(-128, min(127, val)) 
                        
                    self.output_lbls[r][c].setText(str(val))
                    self.output_lbls[r][c].setStyleSheet(f"background-color: {GREEN}; color: {BG_PANEL}; border: 2px solid {GREEN}; border-radius: 6px; font-weight: bold; font-size: 20px;")
                else:
                    self.output_lbls[r][c].setText("?")
                    self.output_lbls[r][c].setStyleSheet(f"background-color: {GREEN_DIM}; color: {GREEN}; border: 1px solid {GREEN}; border-radius: 6px; font-weight: bold; font-size: 18px;")