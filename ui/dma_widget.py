# ui/dma_widget.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QFrame, QLineEdit, QComboBox, QGridLayout, 
                             QSlider, QTextEdit)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIntValidator, QPainter, QColor, QPen
import qtawesome as qta
import random

# ==========================================
# PALETA OFICIAL DO PROJETO
# ==========================================
BG_PANEL = "#0B0D12"
BG_ELEMENT = "#12141A"
BG_BLOCK = "#1A1D24"
BORDER = "#2A2F3A"
TEXT_PRIMARY = "#E2E8F0"
TEXT_SECONDARY = "#8B9BB4"
TEAL = "#6CA1A2"
ORANGE = "#DC673E"
GREEN = "#5DB373"
MUSTARD = "#F2B845"
RED = "#EF4444"

SLIDER_STYLE = f"""
    QSlider::groove:horizontal {{
        border-radius: 4px;
        height: 6px;
        background: {BORDER};
    }}
    QSlider::sub-page:horizontal {{
        background: {TEAL};
        border-radius: 4px;
    }}
    QSlider::handle:horizontal {{
        background: {TEXT_PRIMARY};
        width: 14px;
        height: 14px;
        margin: -4px 0;
        border-radius: 7px;
    }}
    QSlider::handle:horizontal:hover {{
        background: {MUSTARD};
    }}
"""

class MemoryMapWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(100)
        self.progress_pct = 0.0
        self.cpu_active = False

    def update_map(self, progress_pct, cpu_active):
        self.progress_pct = progress_pct
        self.cpu_active = cpu_active
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        painter.fillRect(self.rect(), QColor(BG_ELEMENT))
        
        cols, rows = 20, 5
        cell_w = self.width() / cols
        cell_h = self.height() / rows
        
        total_cells = cols * rows
        cells_filled = int(self.progress_pct * total_cells)
        
        for i in range(total_cells):
            x = (i % cols) * cell_w
            y = (i // cols) * cell_h
            
            rect = (int(x) + 1, int(y) + 1, int(cell_w) - 2, int(cell_h) - 2)
            color = QColor(BG_BLOCK)
            
            if i < cells_filled:
                color = QColor(GREEN)
                
            if self.cpu_active and i >= cells_filled and random.random() < 0.05:
                color = QColor(ORANGE)

            painter.setBrush(color)
            painter.setPen(QPen(QColor(BORDER), 1))
            painter.drawRoundedRect(*rect, 2, 2)

class BlockWidget(QFrame):
    def __init__(self, title, icon_name, color=TEXT_SECONDARY):
        super().__init__()
        self.base_color = color
        self.icon_name = icon_name
        self.setStyleSheet(f"background-color: {BG_BLOCK}; border: 2px solid {color}; border-radius: 8px;")
        self.setFixedSize(120, 90)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        self.ctrl_lbl = QLabel("")
        self.ctrl_lbl.setStyleSheet(f"color: {MUSTARD}; font-size: 10px; font-weight: bold; border: none;")
        self.ctrl_lbl.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.ctrl_lbl.setFixedHeight(12)
        
        self.icon_lbl = QLabel()
        self.icon_lbl.setPixmap(qta.icon(self.icon_name, color=color).pixmap(32, 32))
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setStyleSheet("border: none;")
        
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(f"color: {color}; font-weight: bold; border: none;")
        self.title_lbl.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.ctrl_lbl)
        layout.addWidget(self.icon_lbl)
        layout.addWidget(self.title_lbl)

    def set_active(self, active, active_color=GREEN):
        color = active_color if active else self.base_color
        bg = "#1B2A24" if active and active_color==GREEN else BG_BLOCK
        if active and active_color==ORANGE: bg = "#2D1C17" 
        
        self.setStyleSheet(f"background-color: {bg}; border: 2px solid {color}; border-radius: 8px;")
        self.icon_lbl.setPixmap(qta.icon(self.icon_name, color=color).pixmap(32, 32))
        self.title_lbl.setStyleSheet(f"color: {color}; font-weight: bold; border: none;")

    def set_control_signal(self, text):
        self.ctrl_lbl.setText(text)

class Wire(QFrame):
    def __init__(self, vertical=False):
        super().__init__()
        self.vertical = vertical
        self.base_color = BORDER
        self.set_active(False)
        
    def set_active(self, active, color=GREEN):
        c = color if active else self.base_color
        if self.vertical:
            self.setFixedWidth(4)
            self.setStyleSheet(f"background-color: {c}; border-radius: 2px;")
        else:
            self.setFixedHeight(4)
            self.setStyleSheet(f"background-color: {c}; border-radius: 2px;")

class DMAWidget(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 30)
        main_layout.setSpacing(20)
        
        # CABEÇALHO
        header = QHBoxLayout()
        title_icon = QLabel()
        title_icon.setPixmap(qta.icon('fa5s.microchip', color=MUSTARD).pixmap(24, 24))
        header.addWidget(title_icon)
        
        title_texts = QVBoxLayout()
        lbl_title = QLabel("Direct Memory Access (DMA)")
        lbl_title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {TEXT_PRIMARY};")
        lbl_sub = QLabel("Arbitragem de Barramento: Burst, Cycle Stealing e Concorrência")
        lbl_sub.setStyleSheet(f"font-size: 11px; color: {TEXT_SECONDARY};")
        title_texts.addWidget(lbl_title)
        title_texts.addWidget(lbl_sub)
        header.addLayout(title_texts)
        header.addStretch()
        main_layout.addLayout(header)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(25)

        # -----------------------------------------------------
        # 1. PAINEL ESQUERDO: CONFIGURAÇÕES
        # -----------------------------------------------------
        config_panel = QFrame()
        config_panel.setStyleSheet(f"background-color: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 8px;")
        config_panel.setFixedWidth(320)
        c_layout = QVBoxLayout(config_panel)
        c_layout.setContentsMargins(20, 20, 20, 20)
        c_layout.setSpacing(15)
        
        c_layout.addWidget(self._mk_lbl("DMA REGISTERS", MUSTARD))
        
        grid = QGridLayout()
        grid.setSpacing(8)
        self.inp_bcr = QLineEdit("100")
        self.inp_bcr.setValidator(QIntValidator(1, 10000))
        self.inp_bcr.setStyleSheet(f"background-color: {BG_ELEMENT}; border: 1px solid {BORDER}; border-radius: 4px; color: {TEAL}; padding: 6px; font-family: monospace; font-weight: bold; text-align: right;")
        grid.addWidget(self._mk_lbl("Word Count (BCR):"), 0, 0)
        grid.addWidget(self.inp_bcr, 0, 1)
        c_layout.addLayout(grid)

        c_layout.addSpacing(10)
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"border: none; background-color: {BORDER}; max-height: 1px;")
        c_layout.addWidget(line)
        c_layout.addSpacing(10)

        c_layout.addWidget(self._mk_lbl("ARBITRATION ALGORITHM", MUSTARD))
        
        # Algoritmos Simplificados
        self.combo_policy = QComboBox()
        self.combo_policy.addItems([
            "[0] Burst Mode (DMA Locks Bus)",
            "[1] Cycle Stealing (Forced Alternate)",
            "[2] Round-Robin (Fair 50/50)",
            "[3] Weighted Priority (Use Slider)"
        ])
        self.combo_policy.setStyleSheet(f"""
            QComboBox {{ background-color: {BG_ELEMENT}; border: 1px solid {BORDER}; border-radius: 4px; color: {TEXT_PRIMARY}; padding: 8px; font-weight: bold; font-size: 11px;}}
            QComboBox::drop-down {{ border: none; }}
        """)
        self.combo_policy.currentIndexChanged.connect(self._on_policy_change)
        c_layout.addWidget(self.combo_policy)

        # Slider: Prioridade 0-10
        self.lbl_prio_val = self._mk_lbl("DMA Priority Weight: 7")
        c_layout.addWidget(self.lbl_prio_val)
        
        self.slider_prio = QSlider(Qt.Horizontal)
        self.slider_prio.setRange(0, 10)
        self.slider_prio.setValue(7)
        self.slider_prio.setPageStep(1)
        self.slider_prio.setEnabled(False) # Só ativa no index 3
        self.slider_prio.setStyleSheet(SLIDER_STYLE)
        self.slider_prio.setCursor(Qt.PointingHandCursor)
        self.slider_prio.valueChanged.connect(lambda v: self.lbl_prio_val.setText(f"DMA Priority Weight: {v}"))
        c_layout.addWidget(self.slider_prio)

        c_layout.addSpacing(10)

        # Slider: Carga da CPU
        c_layout.addWidget(self._mk_lbl("CPU TRAFFIC GENERATOR (Live)", MUSTARD))
        self.lbl_cpu_load = self._mk_lbl("CPU Bus Req Probability: 60%")
        c_layout.addWidget(self.lbl_cpu_load)
        
        self.slider_cpu_load = QSlider(Qt.Horizontal)
        self.slider_cpu_load.setRange(0, 100)
        self.slider_cpu_load.setValue(60)
        self.slider_cpu_load.setStyleSheet(SLIDER_STYLE)
        self.slider_cpu_load.setCursor(Qt.PointingHandCursor)
        self.slider_cpu_load.valueChanged.connect(lambda v: self.lbl_cpu_load.setText(f"CPU Bus Req Probability: {v}%"))
        c_layout.addWidget(self.slider_cpu_load)

        c_layout.addSpacing(10)

        # NOVO: Descrição Dinâmica
        self.lbl_policy_desc = QLabel()
        self.lbl_policy_desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px; font-style: italic; border: none; background-color: {BG_ELEMENT}; padding: 8px; border-radius: 4px;")
        self.lbl_policy_desc.setWordWrap(True)
        self.lbl_policy_desc.setMinimumHeight(65)
        self.lbl_policy_desc.setAlignment(Qt.AlignTop)
        c_layout.addWidget(self.lbl_policy_desc)

        c_layout.addStretch()
        
        # Botões Start/Pause/Reset
        b_layout = QHBoxLayout()
        
        self.btn_toggle = QPushButton(" START")
        self.btn_toggle.setIcon(qta.icon('fa5s.play', color=BG_ELEMENT))
        self.btn_toggle.setStyleSheet(f"background-color: {GREEN}; border: none; color: {BG_ELEMENT}; border-radius: 6px; padding: 12px; font-weight: bold;")
        self.btn_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_toggle.clicked.connect(self.toggle_simulation)
        
        self.btn_reset = QPushButton(" RESET")
        self.btn_reset.setIcon(qta.icon('fa5s.redo', color=RED))
        self.btn_reset.setStyleSheet(f"background-color: transparent; border: 1px solid {RED}; color: {RED}; border-radius: 6px; padding: 12px; font-weight: bold;")
        self.btn_reset.setCursor(Qt.PointingHandCursor)
        self.btn_reset.clicked.connect(self.reset_ui)
        
        b_layout.addWidget(self.btn_toggle, stretch=2)
        b_layout.addWidget(self.btn_reset, stretch=1)
        c_layout.addLayout(b_layout)
        
        content_layout.addWidget(config_panel)

        # Inicializa a descrição
        self._update_policy_desc(0)

        # -----------------------------------------------------
        # 2. PAINEL CENTRAL: ARQUITETURA E RAM
        # -----------------------------------------------------
        arch_panel = QFrame()
        arch_panel.setStyleSheet(f"background-color: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 8px;")
        a_layout = QVBoxLayout(arch_panel)
        a_layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_atitle = QLabel("SYSTEM ARCHITECTURE")
        lbl_atitle.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: bold; font-size: 11px; border: none; margin-bottom: 10px;")
        a_layout.addWidget(lbl_atitle)
        
        d_grid = QGridLayout()
        d_grid.setSpacing(0)
        
        self.blk_cpu = BlockWidget("CPU Core", "fa5s.microchip", TEXT_SECONDARY)
        self.blk_arb = BlockWidget("BUS ARBITER", "fa5s.random", TEXT_SECONDARY)
        self.blk_dma = BlockWidget("DMA Controller", "fa5s.bolt", TEXT_SECONDARY)
        
        self.w_cpu_arb = Wire(False)
        self.w_dma_arb = Wire(False)
        self.w_arb_bus = Wire(True)
        self.w_bus_mem = Wire(True)
        
        self.bus_main = QFrame()
        self.bus_main.setFixedHeight(18)
        self.bus_main.setStyleSheet(f"background-color: {BORDER}; border-radius: 4px;")
        bus_layout = QHBoxLayout(self.bus_main)
        bus_layout.setContentsMargins(10, 0, 10, 0)
        bus_lbl = QLabel("SHARED SYSTEM BUS")
        bus_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 9px; font-weight: bold; font-family: monospace; border: none;")
        bus_lbl.setAlignment(Qt.AlignCenter)
        bus_layout.addWidget(bus_lbl)
        
        d_grid.addWidget(self.blk_cpu, 0, 0, Qt.AlignCenter)
        d_grid.addWidget(self.w_cpu_arb, 0, 1, Qt.AlignVCenter)
        d_grid.addWidget(self.blk_arb, 0, 2, Qt.AlignCenter)
        d_grid.addWidget(self.w_dma_arb, 0, 3, Qt.AlignVCenter)
        d_grid.addWidget(self.blk_dma, 0, 4, Qt.AlignCenter)
        
        d_grid.addWidget(self.w_arb_bus, 1, 2, Qt.AlignHCenter)
        d_grid.setRowMinimumHeight(1, 20)
        
        d_grid.addWidget(self.bus_main, 2, 0, 1, 5)
        
        d_grid.addWidget(self.w_bus_mem, 3, 2, Qt.AlignHCenter)
        d_grid.setRowMinimumHeight(3, 20)

        a_layout.addLayout(d_grid)
        
        # --- MAPA DE MEMÓRIA (VISUAL) ---
        a_layout.addSpacing(10)
        lbl_mem = QLabel("PHYSICAL MEMORY (RAM MAP)")
        lbl_mem.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: bold; font-size: 11px; border: none;")
        lbl_mem.setAlignment(Qt.AlignCenter)
        a_layout.addWidget(lbl_mem)
        
        self.mem_map = MemoryMapWidget()
        a_layout.addWidget(self.mem_map, stretch=1)

        content_layout.addWidget(arch_panel, stretch=1)

        # -----------------------------------------------------
        # 3. PAINEL DIREITO: MONITOR & LOG
        # -----------------------------------------------------
        perf_panel = QFrame()
        perf_panel.setStyleSheet(f"background-color: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 8px;")
        perf_panel.setFixedWidth(290)
        p_layout = QVBoxLayout(perf_panel)
        p_layout.setContentsMargins(20, 20, 20, 20)
        
        p_layout.addWidget(self._mk_lbl("PERFORMANCE METRICS", MUSTARD))
        
        self.lbl_total_cyc = self._mk_metric_card(p_layout, "Total Clocks", "0")
        self.lbl_cpu_stalls = self._mk_metric_card(p_layout, "CPU Stalls", "0", ORANGE)
        self.lbl_dma_stalls = self._mk_metric_card(p_layout, "DMA Stalls", "0", GREEN)
        
        p_layout.addSpacing(15)
        p_layout.addWidget(self._mk_lbl("ARBITRATION EVENT LOG", MUSTARD))
        
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setStyleSheet(f"background-color: {BG_ELEMENT}; border: 1px solid {BORDER}; border-radius: 6px; color: {TEXT_PRIMARY}; font-family: monospace; font-size: 10px; padding: 5px;")
        p_layout.addWidget(self.log_box)

        content_layout.addWidget(perf_panel)
        main_layout.addLayout(content_layout)

        # --- Variáveis de Simulação (Máquina de Estados) ---
        self.timer = QTimer()
        self.timer.timeout.connect(self._step_sim)
        self.sim_state = 'IDLE' # IDLE, RUNNING, PAUSED
        
        self.target_words = 0
        self.current_words = 0
        self.cycles = 0
        self.cpu_stalls = 0
        self.dma_stalls = 0
        self.rr_last_served = 'CPU'
        self.last_cycle_winner = 'NONE'

    def _mk_lbl(self, text, color=TEXT_SECONDARY):
        l = QLabel(text)
        l.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold; border: none;")
        return l

    def _mk_metric_card(self, parent_layout, title, val, val_color=TEXT_PRIMARY):
        frame = QFrame()
        frame.setStyleSheet(f"background-color: {BG_BLOCK}; border: 1px solid {BORDER}; border-radius: 6px;")
        layout = QHBoxLayout(frame)
        
        l_title = QLabel(title)
        l_title.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px; font-weight: bold; border: none;")
        
        l_val = QLabel(val)
        l_val.setStyleSheet(f"color: {val_color}; font-size: 20px; font-weight: bold; border: none;")
        l_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        layout.addWidget(l_title)
        layout.addWidget(l_val)
        parent_layout.addWidget(frame)
        return l_val

    def _on_policy_change(self, index):
        self.slider_prio.setEnabled(index == 3) # Ativa slider no index 3 (Weighted)
        self._update_policy_desc(index)

    def _update_policy_desc(self, index):
        desc = {
            0: "O DMA toma o controle absoluto do barramento e não o libera até terminar a transferência. A CPU sofre Stall em todos os ciclos de conflito.",
            1: "O DMA rouba um ciclo por vez e é forçado a devolver o barramento à CPU no ciclo seguinte (alternância obrigatória).",
            2: "Em caso de colisão de requisições, o árbitro alterna o acesso de forma justa e igualitária (1 para 1).",
            3: "Permite criar pesos. Peso 10: DMA se comporta como Burst. Peso 0: CPU dita as regras. Use a barra acima para testar colisões dinâmicas."
        }
        self.lbl_policy_desc.setText(desc.get(index, ""))

    def log(self, msg, color=TEXT_PRIMARY):
        self.log_box.append(f"<span style='color:{color};'>[{self.cycles:04d}] {msg}</span>")
        self.log_box.verticalScrollBar().setValue(self.log_box.verticalScrollBar().maximum())

    # --- CONTROLE DA SIMULAÇÃO ---
    def toggle_simulation(self):
        if self.sim_state == 'IDLE' or self.sim_state == 'PAUSED':
            if self.sim_state == 'IDLE':
                try:
                    self.target_words = int(self.inp_bcr.text())
                except:
                    self.target_words = 100
                    self.inp_bcr.setText("100")
                self.log("Simulation Started.", MUSTARD)
            else:
                self.log("Simulation Resumed.", MUSTARD)
                
            self.sim_state = 'RUNNING'
            self.timer.start(150)
            
            self.btn_toggle.setText(" PAUSE")
            self.btn_toggle.setIcon(qta.icon('fa5s.pause', color=BG_ELEMENT))
            self.btn_toggle.setStyleSheet(f"background-color: {MUSTARD}; border: none; color: {BG_ELEMENT}; border-radius: 6px; padding: 12px; font-weight: bold;")
            
        elif self.sim_state == 'RUNNING':
            self.sim_state = 'PAUSED'
            self.timer.stop()
            self.log("Simulation Paused.", ORANGE)
            
            self.btn_toggle.setText(" RESUME")
            self.btn_toggle.setIcon(qta.icon('fa5s.play', color=BG_ELEMENT))
            self.btn_toggle.setStyleSheet(f"background-color: {GREEN}; border: none; color: {BG_ELEMENT}; border-radius: 6px; padding: 12px; font-weight: bold;")

    def reset_ui(self):
        self.timer.stop()
        self.sim_state = 'IDLE'
        self.cycles = 0
        self.cpu_stalls = 0
        self.dma_stalls = 0
        self.current_words = 0
        self.last_cycle_winner = 'NONE'
        
        self.btn_toggle.setText(" START")
        self.btn_toggle.setIcon(qta.icon('fa5s.play', color=BG_ELEMENT))
        self.btn_toggle.setStyleSheet(f"background-color: {GREEN}; border: none; color: {BG_ELEMENT}; border-radius: 6px; padding: 12px; font-weight: bold;")
        
        self.mem_map.update_map(0.0, False)
        
        self.lbl_total_cyc.setText("0")
        self.lbl_cpu_stalls.setText("0")
        self.lbl_dma_stalls.setText("0")
        self.log_box.clear()
        
        self.blk_cpu.set_control_signal("")
        self.blk_dma.set_control_signal("")
        self._set_bus_active('NONE')

    def _step_sim(self):
        self.cycles += 1
        
        # 1. Requisições
        cpu_wants_bus = random.randint(1, 100) <= self.slider_cpu_load.value()
        dma_wants_bus = self.current_words < self.target_words

        self.blk_cpu.set_control_signal("REQ" if cpu_wants_bus else "")
        self.blk_dma.set_control_signal("REQ" if dma_wants_bus else "")

        bus_granted_to = 'NONE'
        policy_idx = self.combo_policy.currentIndex()

        # 2. Resolução de Conflitos
        if cpu_wants_bus and dma_wants_bus:
            if policy_idx == 0:   # Burst Mode
                bus_granted_to = 'DMA'
                self.cpu_stalls += 1
                self.log("Colisão -> DMA segura o bus (Burst)", GREEN)
            
            elif policy_idx == 1: # Cycle Stealing
                if self.last_cycle_winner == 'DMA':
                    bus_granted_to = 'CPU'
                    self.dma_stalls += 1
                    self.log("Colisão -> DMA devolve o bus (Cycle Stealing)", ORANGE)
                else:
                    bus_granted_to = 'DMA'
                    self.cpu_stalls += 1
                    self.log("Colisão -> DMA rouba o bus (Cycle Stealing)", GREEN)

            elif policy_idx == 2: # Round-Robin Alternado
                bus_granted_to = 'DMA' if self.rr_last_served == 'CPU' else 'CPU'
                if bus_granted_to == 'DMA': self.cpu_stalls += 1
                else: self.dma_stalls += 1
                self.rr_last_served = bus_granted_to
                color = GREEN if bus_granted_to == 'DMA' else ORANGE
                self.log(f"Colisão -> {bus_granted_to} ganha (Round-Robin)", color)
            
            elif policy_idx == 3: # Weighted Slider (0 a 10)
                dma_win_chance = self.slider_prio.value() * 10 
                if random.randint(1, 100) <= dma_win_chance:
                    bus_granted_to = 'DMA'
                    self.cpu_stalls += 1
                    self.log(f"Colisão -> DMA ganha (Peso {self.slider_prio.value()})", GREEN)
                else:
                    bus_granted_to = 'CPU'
                    self.dma_stalls += 1
                    self.log(f"Colisão -> CPU ganha (Peso {self.slider_prio.value()})", ORANGE)
        else:
            if cpu_wants_bus:
                bus_granted_to = 'CPU'
                self.log("Acesso Limpo - CPU", TEXT_SECONDARY)
            elif dma_wants_bus:
                bus_granted_to = 'DMA'
                self.log("Acesso Limpo - DMA", TEXT_SECONDARY)
            else:
                self.log("Barramento Ocioso", BORDER)

        self.last_cycle_winner = bus_granted_to

        # 3. Executar a Ação
        if bus_granted_to == 'DMA':
            self.current_words += 1
            self.blk_dma.set_control_signal("REQ + GRANT")
        elif bus_granted_to == 'CPU':
            self.blk_cpu.set_control_signal("REQ + GRANT")

        # 4. Atualizar View
        self._set_bus_active(bus_granted_to)
        
        prog = self.current_words / self.target_words if self.target_words > 0 else 0
        self.mem_map.update_map(prog, cpu_active=(bus_granted_to == 'CPU'))

        self.lbl_total_cyc.setText(str(self.cycles))
        self.lbl_cpu_stalls.setText(str(self.cpu_stalls))
        self.lbl_dma_stalls.setText(str(self.dma_stalls))

        # 5. Fim da Transferência
        if self.current_words >= self.target_words and not dma_wants_bus:
            if self.current_words == self.target_words:
                self.log("DMA TRANSFER COMPLETE! Interrupção Gerada (IRQ).", MUSTARD)
                self.current_words += 1 
            
            self.timer.stop()
            self.sim_state = 'IDLE'
            self._set_bus_active('NONE')
            self.blk_cpu.set_control_signal("")
            self.blk_dma.set_control_signal("")
            
            self.btn_toggle.setText(" RESTART")
            self.btn_toggle.setIcon(qta.icon('fa5s.play', color=BG_ELEMENT))
            self.btn_toggle.setStyleSheet(f"background-color: {TEAL}; border: none; color: {BG_ELEMENT}; border-radius: 6px; padding: 12px; font-weight: bold;")

    def _set_bus_active(self, master):
        self.blk_cpu.set_active(False)
        self.blk_dma.set_active(False)
        self.blk_arb.set_active(False)
        self.w_cpu_arb.set_active(False)
        self.w_dma_arb.set_active(False)
        self.w_arb_bus.set_active(False)
        self.w_bus_mem.set_active(False)
        self.bus_main.setStyleSheet(f"background-color: {BORDER}; border-radius: 4px;")

        if master == 'CPU':
            self.blk_cpu.set_active(True, ORANGE)
            self.blk_arb.set_active(True, ORANGE)
            self.w_cpu_arb.set_active(True, ORANGE)
            self.w_arb_bus.set_active(True, ORANGE)
            self.w_bus_mem.set_active(True, ORANGE)
            self.bus_main.setStyleSheet(f"background-color: {ORANGE}; border-radius: 4px;")
            
        elif master == 'DMA':
            self.blk_dma.set_active(True, GREEN)
            self.blk_arb.set_active(True, GREEN)
            self.w_dma_arb.set_active(True, GREEN)
            self.w_arb_bus.set_active(True, GREEN)
            self.w_bus_mem.set_active(True, GREEN)
            self.bus_main.setStyleSheet(f"background-color: {GREEN}; border-radius: 4px;")