# ui/tiling_widget.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QFrame, QGridLayout, QTextEdit)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
import qtawesome as qta
import random

# ==========================================
# PALETA OFICIAL DO PROJETO
# ==========================================
BG_PANEL = "#0B0D12"
BG_ELEMENT = "#12141A"
BORDER = "#2A2F3A"
TEXT_PRIMARY = "#E2E8F0"
TEXT_SECONDARY = "#8B9BB4"
TEXT_DIMMED = "#475569" # Cor para as células apagadas (fundo)

TEAL = "#6CA1A2"
ORANGE = "#DC673E"
GREEN = "#5DB373"
MUSTARD = "#F2B845"
PURPLE = "#A855F7"
BLUE = "#3b82f6"


def hex_to_rgba(hex_color, alpha=0.2):
    """Converte HEX para RGBA para garantir compatibilidade com o Qt Stylesheet"""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"


class BigMatrix(QFrame):
    """Representa uma Matriz 6x6 visualmente dividida em 4 quadrantes 3x3."""
    def __init__(self, title, color=TEXT_SECONDARY):
        super().__init__()
        self.color = color
        self.setStyleSheet(f"background-color: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 8px;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px; border: none;")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_title)
        
        layout.addSpacing(10)
        
        self.grid_frame = QFrame()
        self.grid_frame.setStyleSheet("border: none;")
        self.grid = QGridLayout(self.grid_frame)
        self.grid.setSpacing(4)
        
        self.cells = [[QLabel("0") for _ in range(6)] for _ in range(6)]
        
        for r in range(6):
            for c in range(6):
                lbl = self.cells[r][c]
                lbl.setFixedSize(28, 28)
                lbl.setAlignment(Qt.AlignCenter)
                # Separador visual a meio (para criar a ilusão de 4 tiles 3x3)
                margin_r = "4px" if c == 2 else "0px"
                margin_b = "4px" if r == 2 else "0px"
                # Adiciona borda transparente para não dar jitter de 1px quando selecionar
                lbl.setStyleSheet(f"background-color: {BG_ELEMENT}; color: {TEXT_DIMMED}; border: 1px solid transparent; border-radius: 4px; margin-right: {margin_r}; margin-bottom: {margin_b};")
                self.grid.addWidget(lbl, r, c)
                
        layout.addWidget(self.grid_frame, alignment=Qt.AlignCenter)

    def populate_random(self):
        for r in range(6):
            for c in range(6):
                val = random.randint(1, 5)
                self.cells[r][c].setText(str(val))
                self.cells[r][c].setProperty("val", val)

    def clear_data(self):
        for r in range(6):
            for c in range(6):
                self.cells[r][c].setText("0")
                self.cells[r][c].setProperty("val", 0)
                    
    def highlight_quadrant(self, q_r, q_c, active=True, highlight_color=TEAL):
        """Ilumina um quadrante 3x3 específico (q_r: 0 ou 1, q_c: 0 ou 1)."""
        start_r = q_r * 3
        start_c = q_c * 3
        
        # Primeiro, escurece tudo
        for r in range(6):
            for c in range(6):
                margin_r = "4px" if c == 2 else "0px"
                margin_b = "4px" if r == 2 else "0px"
                self.cells[r][c].setStyleSheet(f"background-color: {BG_ELEMENT}; color: {TEXT_DIMMED}; border: 1px solid transparent; border-radius: 4px; margin-right: {margin_r}; margin-bottom: {margin_b};")

        # Depois ilumina apenas o quadrante se ativo
        if active:
            bg_rgba = hex_to_rgba(highlight_color, 0.2) # 20% de opacidade para o fundo
            for r in range(start_r, start_r + 3):
                for c in range(start_c, start_c + 3):
                    margin_r = "4px" if c == 2 else "0px"
                    margin_b = "4px" if r == 2 else "0px"
                    self.cells[r][c].setStyleSheet(f"background-color: {bg_rgba}; color: {highlight_color}; border: 1px solid {highlight_color}; border-radius: 4px; font-weight: bold; margin-right: {margin_r}; margin-bottom: {margin_b};")


class TilingWidget(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 30)
        main_layout.setSpacing(20)

        # CABEÇALHO
        header = QHBoxLayout()
        title_icon = QLabel()
        title_icon.setPixmap(qta.icon('fa5s.layer-group', color=TEAL).pixmap(24, 24))
        header.addWidget(title_icon)
        
        title_texts = QVBoxLayout()
        lbl_title = QLabel("NPU Tiling & Scaling")
        lbl_title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {TEXT_PRIMARY};")
        lbl_sub = QLabel("Block Matrix Multiplication – 6x6 Matrix on a 3x3 Hardware Array")
        lbl_sub.setStyleSheet(f"font-size: 11px; color: {TEXT_SECONDARY};")
        title_texts.addWidget(lbl_title)
        title_texts.addWidget(lbl_sub)
        header.addLayout(title_texts)
        header.addStretch()
        
        self.btn_reset = QPushButton(" Reset Data")
        self.btn_reset.setIcon(qta.icon('fa5s.sync-alt', color=TEXT_PRIMARY))
        self.btn_reset.setProperty("class", "ActionBtn")
        self.btn_reset.clicked.connect(self.reset_system)
        
        self.btn_step = QPushButton(" Step Tile")
        self.btn_step.setIcon(qta.icon('fa5s.step-forward', color=BG_ELEMENT))
        self.btn_step.setStyleSheet(f"background-color: {ORANGE}; color: {BG_ELEMENT}; border-radius: 6px; padding: 8px 16px; font-weight: bold;")
        self.btn_step.clicked.connect(self.step_tiling)
        
        self.btn_run = QPushButton(" Auto Run")
        self.btn_run.setIcon(qta.icon('fa5s.play', color='white'))
        self.btn_run.setStyleSheet(f"background-color: {BLUE}; color: white; border-radius: 6px; padding: 8px 16px; font-weight: bold;")
        self.btn_run.clicked.connect(self.toggle_run)
        
        header.addWidget(self.btn_reset)
        header.addWidget(self.btn_step)
        header.addWidget(self.btn_run)
        main_layout.addLayout(header)
        
        # ÁREA CENTRAL (As 3 Matrizes e a NPU)
        workspace = QHBoxLayout()
        workspace.setAlignment(Qt.AlignCenter)
        
        # Matriz A (Esquerda)
        self.mat_a = BigMatrix("MATRIX A (INPUT) - 6x6", ORANGE)
        workspace.addWidget(self.mat_a, alignment=Qt.AlignCenter)
        
        # Matriz B (Meio Esquerda)
        self.mat_b = BigMatrix("MATRIX B (WEIGHTS) - 6x6", MUSTARD)
        workspace.addWidget(self.mat_b, alignment=Qt.AlignCenter)
        
        # NPU Core (Centro)
        npu_core = QFrame()
        npu_core.setStyleSheet(f"background-color: {BG_ELEMENT}; border: 2px dashed {BORDER}; border-radius: 12px;")
        npu_core.setFixedSize(160, 200)
        npu_layout = QVBoxLayout(npu_core)
        npu_layout.setAlignment(Qt.AlignCenter)
        
        npu_icon = QLabel()
        npu_icon.setPixmap(qta.icon('fa5s.microchip', color=PURPLE).pixmap(48, 48))
        npu_icon.setAlignment(Qt.AlignCenter)
        npu_layout.addWidget(npu_icon)
        
        self.npu_status = QLabel("NPU Core\n(3x3 Systolic)")
        self.npu_status.setStyleSheet(f"color: {PURPLE}; font-weight: bold; text-align: center; border: none;")
        self.npu_status.setAlignment(Qt.AlignCenter)
        npu_layout.addWidget(self.npu_status)
        
        self.lbl_operation = QLabel("IDLE")
        self.lbl_operation.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 10px; border: none; margin-top: 10px;")
        self.lbl_operation.setAlignment(Qt.AlignCenter)
        npu_layout.addWidget(self.lbl_operation)
        
        workspace.addWidget(npu_core, alignment=Qt.AlignCenter)
        
        # Matriz C (Direita)
        self.mat_c = BigMatrix("MATRIX C (OUTPUT) - 6x6", GREEN)
        workspace.addWidget(self.mat_c, alignment=Qt.AlignCenter)
        
        main_layout.addLayout(workspace, stretch=1)
        
        # PAINEL DE LOG DE EXECUÇÃO
        log_panel = QFrame()
        log_panel.setStyleSheet(f"background-color: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 8px;")
        log_panel.setFixedHeight(180)
        l_layout = QVBoxLayout(log_panel)
        
        lbl_log = QLabel("TILING STATE MACHINE LOG")
        lbl_log.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: bold; font-size: 11px; border: none;")
        l_layout.addWidget(lbl_log)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(f"background-color: transparent; color: {TEXT_PRIMARY}; font-family: 'Consolas'; font-size: 13px; border: none;")
        l_layout.addWidget(self.log_text, stretch=1)
        
        main_layout.addWidget(log_panel)

        # MÁQUINA DE ESTADOS DA MULTIPLICAÇÃO EM BLOCOS
        self.fsm_steps = [
            {"a": (0,0), "b": (0,0), "c": (0,0), "accumulate": False, "desc": "C_11 (P1) = A_11 * B_11"},
            {"a": (0,1), "b": (1,0), "c": (0,0), "accumulate": True,  "desc": "C_11 (P2) = C_11 + (A_12 * B_21)  [C_11 DONE]"},
            
            {"a": (0,0), "b": (0,1), "c": (0,1), "accumulate": False, "desc": "C_12 (P1) = A_11 * B_12"},
            {"a": (0,1), "b": (1,1), "c": (0,1), "accumulate": True,  "desc": "C_12 (P2) = C_12 + (A_12 * B_22)  [C_12 DONE]"},
            
            {"a": (1,0), "b": (0,0), "c": (1,0), "accumulate": False, "desc": "C_21 (P1) = A_21 * B_11"},
            {"a": (1,1), "b": (1,0), "c": (1,0), "accumulate": True,  "desc": "C_21 (P2) = C_21 + (A_22 * B_21)  [C_21 DONE]"},
            
            {"a": (1,0), "b": (0,1), "c": (1,1), "accumulate": False, "desc": "C_22 (P1) = A_21 * B_12"},
            {"a": (1,1), "b": (1,1), "c": (1,1), "accumulate": True,  "desc": "C_22 (P2) = C_22 + (A_22 * B_22)  [C_22 DONE]"},
        ]
        
        self.current_step = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.step_tiling)
        
        self.reset_system()

    def reset_system(self):
        self.timer.stop()
        self.btn_run.setText(" Auto Run")
        self.btn_run.setIcon(qta.icon('fa5s.play', color='white'))
        self.current_step = 0
        
        self.mat_a.populate_random()
        self.mat_b.populate_random()
        self.mat_c.clear_data()
        
        self.mat_a.highlight_quadrant(0, 0, False)
        self.mat_b.highlight_quadrant(0, 0, False)
        self.mat_c.highlight_quadrant(0, 0, False)
        
        self.lbl_operation.setText("IDLE")
        
        self.log_text.clear()
        self.log_text.append(">> Sistema Resetado. Matrizes carregadas na DRAM principal.")
        self.log_text.append(">> A aguardar instrução do Escalonador (Scheduler) para iniciar o Tiling...")

    def toggle_run(self):
        if self.timer.isActive():
            self.timer.stop()
            self.btn_run.setText(" Auto Run")
            self.btn_run.setIcon(qta.icon('fa5s.play', color='white'))
        else:
            if self.current_step >= len(self.fsm_steps):
                self.reset_system()
            self.timer.start(1200)
            self.btn_run.setText(" Pause")
            self.btn_run.setIcon(qta.icon('fa5s.pause', color='white'))

    def step_tiling(self):
        if self.current_step >= len(self.fsm_steps):
            self.timer.stop()
            self.btn_run.setText(" Auto Run")
            self.btn_run.setIcon(qta.icon('fa5s.play', color='white'))
            
            self.log_text.append(f"<br><span style='color:{GREEN};'>[SUCESSO] Multiplicação 6x6 concluída usando hardware 3x3!</span>")
            
            self.mat_a.highlight_quadrant(0, 0, False)
            self.mat_b.highlight_quadrant(0, 0, False)
            self.mat_c.highlight_quadrant(0, 0, False)
            self.lbl_operation.setText("FINISHED")
            return

        step_data = self.fsm_steps[self.current_step]
        
        # 1. Iluminar os Quadrantes Corretos com as cores da Paleta
        self.mat_a.highlight_quadrant(step_data["a"][0], step_data["a"][1], True, ORANGE)
        self.mat_b.highlight_quadrant(step_data["b"][0], step_data["b"][1], True, MUSTARD)
        self.mat_c.highlight_quadrant(step_data["c"][0], step_data["c"][1], True, GREEN)
        
        # 2. Atualizar NPU Status
        op_type = "MULTIPLY + ACCUMULATE" if step_data["accumulate"] else "MULTIPLY"
        self.lbl_operation.setText(f"LOADING TILES...\n{op_type}\n[{step_data['a']}] x [{step_data['b']}]")
        
        # 3. Matemática Aproximada para animação
        c_r, c_c = step_data["c"]
        for r in range(3):
            for c in range(3):
                cell_c = self.mat_c.cells[c_r * 3 + r][c_c * 3 + c]
                current_val = int(cell_c.text())
                added_val = random.randint(10, 50)
                if step_data["accumulate"]:
                    cell_c.setText(str(current_val + added_val))
                else:
                    cell_c.setText(str(added_val))

        # 4. Atualizar Log com as cores oficiais
        log_msg = f">> Passo {self.current_step + 1}/8: Carregou Tile A({step_data['a'][0]},{step_data['a'][1]}) e Tile B({step_data['b'][0]},{step_data['b'][1]}). "
        log_msg += f"NPU a executar: <span style='color:{PURPLE};'>{step_data['desc']}</span>"
        
        if step_data["accumulate"]:
            log_msg += f" <span style='color:{GREEN};'>(Quadrante Escrito na Memória)</span>"
            
        self.log_text.append(log_msg)
        
        self.current_step += 1