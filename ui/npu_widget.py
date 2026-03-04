# ui/npu_widget.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFrame, QGridLayout, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIntValidator
import qtawesome as qta

class PPUToggle(QFrame):
    """Componente visual interativo para ativar/desativar as etapas do PPU."""
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
        self.dot.setStyleSheet("border: none;")
        
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
        color = "#2dd4bf" if self.active else "#475569"
        border = f"1px solid {color}" if self.active else "1px dashed #334155"
        self.setStyleSheet(f"background-color: #020617; border: {border}; border-radius: 6px;")
        self.lbl.setStyleSheet(f"color: {color}; border: none; font-weight: bold;")
        self.dot.setStyleSheet(f"color: {color}; border: none;")

class PEWidget(QFrame):
    """Representação de um Processing Element (MAC)."""
    def __init__(self, r, c):
        super().__init__()
        self.r = r
        self.c = c
        self.setObjectName("PEBox")
        self.setStyleSheet("""
            #PEBox { border: 2px solid #a855f7; border-radius: 8px; background-color: #020617; }
            #PEBoxDone { border: 2px solid #10b981; border-radius: 8px; background-color: #020617; }
        """)
        self.setFixedSize(110, 110)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        h_layout = QHBoxLayout()
        lbl_name = QLabel(f"PE_{r}{c}")
        lbl_name.setStyleSheet("color: #94a3b8; font-size: 11px; border: none;")
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: #a855f7; font-size: 11px; font-weight: bold; border: none;")
        h_layout.addWidget(lbl_name)
        h_layout.addStretch()
        h_layout.addWidget(self.lbl_status)
        layout.addLayout(h_layout)
        
        self.lbl_mac = QLabel("---")
        self.lbl_mac.setStyleSheet("color: #e2e8f0; font-size: 13px; border: none;")
        self.lbl_mac.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_mac)
        
        self.lbl_acc = QLabel("0")
        self.lbl_acc.setStyleSheet("color: #f8fafc; font-size: 26px; font-weight: bold; border: none;")
        self.lbl_acc.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_acc)
        
        self.progress = QFrame()
        self.progress.setFixedHeight(4)
        self.progress.setStyleSheet("background-color: #334155; border-radius: 2px;")
        layout.addWidget(self.progress)

    def update_state(self, a, b, acc, done):
        self.lbl_mac.setText(f"{a}*{b}" if not done else "---")
        self.lbl_acc.setText(str(acc))
        if done:
            self.lbl_status.setText("DONE")
            self.lbl_acc.setStyleSheet("color: #10b981; font-size: 26px; font-weight: bold; border: none;")
            self.progress.setStyleSheet("background-color: #10b981; border-radius: 2px;")
            self.setObjectName("PEBoxDone")
        else:
            self.lbl_status.setText("")
            self.lbl_acc.setStyleSheet("color: #f8fafc; font-size: 26px; font-weight: bold; border: none;")
            self.progress.setStyleSheet("background-color: #a855f7; border-radius: 2px;")
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
        title_icon.setPixmap(qta.icon('fa5s.brain', color='#a855f7').pixmap(24, 24))
        header.addWidget(title_icon)
        
        title_texts = QVBoxLayout()
        lbl_title = QLabel("NPU Micro-Architecture")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #f8fafc;")
        lbl_sub = QLabel("Systolic Array 3x3 • Output Stationary • PPU Pipeline")
        lbl_sub.setStyleSheet("font-size: 11px; color: #94a3b8;")
        title_texts.addWidget(lbl_title)
        title_texts.addWidget(lbl_sub)
        header.addLayout(title_texts)
        header.addStretch()
        
        # Relógio Global
        lbl_clock_title = QLabel("Global Clock")
        lbl_clock_title.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.lbl_clock = QLabel("0")
        self.lbl_clock.setStyleSheet("color: #2dd4bf; font-size: 24px; font-weight: bold;")
        
        clock_layout = QVBoxLayout()
        clock_layout.addWidget(lbl_clock_title)
        clock_layout.addWidget(self.lbl_clock)
        clock_layout.setAlignment(Qt.AlignRight)
        header.addLayout(clock_layout)
        header.addSpacing(20)
        
        # Botões de Ação
        self.btn_reset = QPushButton(" Reset")
        self.btn_reset.setIcon(qta.icon('fa5s.sync-alt', color='#f8fafc'))
        self.btn_reset.setProperty("class", "ActionBtn")
        self.btn_reset.clicked.connect(self.request_reset.emit)
        
        self.btn_step = QPushButton(" Step Clock")
        self.btn_step.setIcon(qta.icon('fa5s.step-forward', color='#f8fafc'))
        self.btn_step.setStyleSheet("background-color: #d97706; color: white; border-radius: 6px; padding: 8px 16px; font-weight: bold;")
        self.btn_step.clicked.connect(self.request_step.emit)

        self.btn_run = QPushButton(" Auto Run")
        self.btn_run.setIcon(qta.icon('fa5s.play', color='white'))
        self.btn_run.setProperty("class", "ActionBtn PrimaryBtn")
        self.btn_run.clicked.connect(self.request_run.emit)
        
        header.addWidget(self.btn_reset)
        header.addWidget(self.btn_step)
        header.addWidget(self.btn_run)
        main_layout.addLayout(header)
        main_layout.addSpacing(20)
        
        # GRID PRINCIPAL E ALINHAMENTO
        panels_grid = QGridLayout()
        panels_grid.setSpacing(40)
        
        # Painéis
        frame_input, self.panel_input = self._create_panel("INPUT MEMORY (A)")
        frame_weight, self.panel_weight = self._create_panel("WEIGHT MEMORY (B)")
        frame_core, self.panel_core = self._create_panel("SYSTOLIC ARRAY (CORE)")
        
        # Layouts internos dos painéis
        self.grid_input = QGridLayout(self.panel_input)
        self.grid_weight = QGridLayout(self.panel_weight)
        self.grid_core = QGridLayout(self.panel_core)
        
        # Posicionamento no Grid Mestre
        panels_grid.addWidget(frame_input, 1, 0, Qt.AlignTop | Qt.AlignRight)
        panels_grid.addWidget(frame_weight, 0, 1, Qt.AlignBottom | Qt.AlignHCenter)
        panels_grid.addWidget(frame_core, 1, 1, Qt.AlignTop | Qt.AlignHCenter)
        
        # Painel Direito (Output e PPU)
        col_right = QVBoxLayout()
        frame_output, self.panel_output = self._create_panel("OUTPUT MEMORY (C)")
        frame_output.setFixedWidth(280)  # Força um tamanho compacto horizontalmente
        self.grid_output = QGridLayout(self.panel_output)
        
        frame_ppu, self.panel_ppu = self._create_panel("PPU PIPELINE")
        frame_ppu.setFixedWidth(280)     # Força um tamanho compacto horizontalmente
        ppu_layout = QVBoxLayout(self.panel_ppu)
        
        # PPU Interativo
        self.ppu_bias = PPUToggle("Add Bias (+5)", active=False)
        self.ppu_relu = PPUToggle("ReLU Activation", active=True)
        self.ppu_quant = PPUToggle("Quantization (Int8)", active=False)
        
        self.ppu_bias.toggled.connect(self.force_update_output)
        self.ppu_relu.toggled.connect(self.force_update_output)
        self.ppu_quant.toggled.connect(self.force_update_output)
        
        ppu_layout.addWidget(self.ppu_bias)
        ppu_layout.addWidget(self.ppu_relu)
        ppu_layout.addWidget(self.ppu_quant)
        
        col_right.addWidget(frame_output)
        col_right.addWidget(frame_ppu)
        col_right.addStretch()
        
        # Forçamos a coluna direita a iniciar na LINHA 1 do Grid (mesma linha do Core e Input)
        panels_grid.addLayout(col_right, 1, 2, Qt.AlignTop | Qt.AlignLeft)
        
        # Um Wrapper para impedir que o Qt estique todo o bloco e centralizá-lo horizontalmente
        wrapper = QHBoxLayout()
        wrapper.addStretch()
        wrapper.addLayout(panels_grid)
        wrapper.addStretch()
        
        # Adiciona um stretch vertical antes e depois do wrapper para centralizar perfeitamente
        main_layout.addStretch()
        main_layout.addLayout(wrapper)
        main_layout.addStretch()
        
        self.setup_grids()
        
    def _create_panel(self, title):
        frame = QFrame()
        frame.setStyleSheet("background-color: #0b1120; border: 1px solid #1e293b; border-radius: 8px;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 15, 15, 15)
        
        lbl = QLabel(title)
        lbl.setStyleSheet("color: #94a3b8; font-weight: bold; font-size: 12px; border: none; margin-bottom: 5px;")
        layout.addWidget(lbl)
        
        content = QWidget()
        content.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(content)
        return frame, content

    def setup_grids(self):
        # 0. Sincronização Perfeita de Espaçamento e Tamanhos (Pixel-Perfect Alignment)
        self.grid_weight.setHorizontalSpacing(20)
        self.grid_core.setHorizontalSpacing(20)
        for c in range(3):
            self.grid_weight.setColumnMinimumWidth(c, 110)
            self.grid_core.setColumnMinimumWidth(c, 110)
            
        self.grid_input.setVerticalSpacing(20)
        self.grid_core.setVerticalSpacing(20)
        for r in range(3):
            self.grid_input.setRowMinimumHeight(r, 110)
            self.grid_core.setRowMinimumHeight(r, 110)

        # 1. Matriz de Entrada A (Formato quadrado perfeito)
        self.a_inputs = [[QLineEdit() for _ in range(3)] for _ in range(3)]
        for r in range(3):
            lbl_row = QLabel(f"R{r}")
            lbl_row.setStyleSheet("color: #64748b; font-size: 10px; font-weight: bold;")
            self.grid_input.addWidget(lbl_row, r, 0, Qt.AlignVCenter | Qt.AlignRight)
            
            for c in range(3):
                le = self.a_inputs[r][c]
                le.setValidator(QIntValidator(-999, 999))
                le.setFixedSize(40, 40)
                le.setAlignment(Qt.AlignCenter)
                le.setText(str(r * 3 + c + 1)) 
                
                # Sem deslocamento físico! Todos alinhados colado na esquerda (coluna c+1)
                self.grid_input.addWidget(le, r, c + 1, Qt.AlignCenter)
            
            # As setas ficam sempre na coluna 4 (à direita da matriz)
            arrow = QLabel("➔")
            arrow.setStyleSheet("color: #d97706; font-size: 16px;")
            self.grid_input.addWidget(arrow, r, 4, Qt.AlignVCenter | Qt.AlignLeft)

        # 2. Matriz de Pesos B (Formato quadrado perfeito)
        self.b_inputs = [[QLineEdit() for _ in range(3)] for _ in range(3)]
        for c in range(3):
            for r in range(3):
                le = self.b_inputs[r][c]
                le.setValidator(QIntValidator(-999, 999))
                le.setFixedSize(44, 30)
                le.setAlignment(Qt.AlignCenter)
                le.setText("1" if r == c else "0")
                
                # Sem deslocamento físico! Todos alinhados colado ao topo (linha r)
                self.grid_weight.addWidget(le, r, c, Qt.AlignCenter)
                
            # As setas ficam sempre na linha 3 (abaixo da matriz)
            arrow = QLabel("⬇")
            arrow.setStyleSheet("color: #0891b2; font-size: 16px;")
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
                lbl.setFixedSize(65, 40)
                lbl.setAlignment(Qt.AlignCenter)
                lbl.setStyleSheet("background-color: #0f172a; color: #475569; border-radius: 4px; font-weight: bold; font-size: 18px;")
                self.grid_output.addWidget(lbl, r, c)
                
        # Atualiza as cores iniciais estáticas
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
        """Aplica o highlight dinâmico criando um rastro luminoso nos dados sendo processados."""
        for r in range(3):
            for c in range(3):
                # O ciclo em que o dado [r][c] entra na matriz e é calculado (consumido)
                target_cycle = r + c
                
                # Matriz A (Laranja/Amarelo)
                le_a = self.a_inputs[r][c]
                if current_cycle == target_cycle + 1: # Sendo Consumido AGORA
                    le_a.setStyleSheet("background-color: #f59e0b; color: #020617; border: 2px solid #fcd34d; border-radius: 4px; font-weight: bold;")
                elif current_cycle <= target_cycle:   # Aguardando na fila
                    le_a.setStyleSheet("background-color: #020617; border: 1px solid #d97706; color: #fcd34d; border-radius: 4px; font-weight: bold;")
                else:                                 # Já foi consumido
                    le_a.setStyleSheet("background-color: transparent; border: 1px dashed #1e293b; color: #334155; border-radius: 4px; font-weight: bold;")
                
                # Matriz B (Ciano/Azul)
                le_b = self.b_inputs[r][c]
                if current_cycle == target_cycle + 1: # Sendo Consumido AGORA
                    le_b.setStyleSheet("background-color: #06b6d4; color: #020617; border: 2px solid #67e8f9; border-radius: 4px; font-weight: bold;")
                elif current_cycle <= target_cycle:   # Aguardando na fila
                    le_b.setStyleSheet("background-color: #020617; border: 1px solid #0891b2; color: #67e8f9; border-radius: 4px; font-weight: bold;")
                else:                                 # Já foi consumido
                    le_b.setStyleSheet("background-color: transparent; border: 1px dashed #1e293b; color: #334155; border-radius: 4px; font-weight: bold;")

    def update_ui(self, model):
        self.last_model = model
        self.lbl_clock.setText(str(model.cycle))
        
        # Atualiza as cores brilhantes das matrizes
        self._apply_matrix_styles(model.cycle)
        
        # Atualiza Core e Output Memory
        for r in range(3):
            for c in range(3):
                pe_state = model.pes[r][c]
                self.pe_widgets[r][c].update_state(pe_state['a'], pe_state['b'], pe_state['acc'], pe_state['done'])
                
                if pe_state['done']:
                    val = pe_state['acc']
                    
                    if self.ppu_bias.active:
                        val += 5
                    if self.ppu_relu.active:
                        val = max(0, val)
                    if self.ppu_quant.active:
                        val = max(-128, min(127, val)) 
                        
                    self.output_lbls[r][c].setText(str(val))
                    self.output_lbls[r][c].setStyleSheet("background-color: #10b981; color: #020617; border-radius: 4px; font-weight: bold; font-size: 18px;")
                else:
                    self.output_lbls[r][c].setText("?")
                    self.output_lbls[r][c].setStyleSheet("background-color: #0f172a; color: #475569; border-radius: 4px; font-weight: bold; font-size: 18px;")