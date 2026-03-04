# ui/dma_widget.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QFrame, QLineEdit, QComboBox, QGridLayout)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QIntValidator
import qtawesome as qta

class ToggleSwitch(QPushButton):
    """Um interruptor (switch) ao estilo iOS/Web para alternar a carga da CPU."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(40, 22)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(self._get_style(False))
        self.toggled.connect(lambda c: self.setStyleSheet(self._get_style(c)))

    def _get_style(self, checked):
        bg_color = "#10b981" if checked else "#334155" # Verde se ON, Slate se OFF
        align = "right" if checked else "left"
        return f"""
            QPushButton {{
                background-color: {bg_color};
                border-radius: 11px;
                border: 2px solid {bg_color};
                text-align: {align};
                padding: 0px 2px;
            }}
            QPushButton::indicator {{
                width: 18px; height: 18px;
                border-radius: 9px;
                background-color: white;
            }}
        """
        
    def paintEvent(self, event):
        # Desenhamos uma "bolinha" branca (falsa) via texto para ser mais simples sem QPainter
        self.setText("●" if not self.isChecked() else "   ●")
        super().paintEvent(event)

class BlockWidget(QFrame):
    """Bloco visual representando um componente do SoC (CPU, DMA, RAM)."""
    def __init__(self, title, icon_name, color="#94a3b8"):
        super().__init__()
        self.base_color = color
        self.icon_name = icon_name # Guarda o nome do ícone
        self.setStyleSheet(f"background-color: #0f172a; border: 2px solid {color}; border-radius: 8px;")
        self.setFixedSize(120, 90)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        self.icon_lbl = QLabel()
        self.icon_lbl.setPixmap(qta.icon(self.icon_name, color=color).pixmap(32, 32))
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setStyleSheet("border: none;")
        
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(f"color: {color}; font-weight: bold; border: none;")
        self.title_lbl.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.icon_lbl)
        layout.addWidget(self.title_lbl)

    def set_active(self, active, active_color="#10b981"):
        color = active_color if active else self.base_color
        bg = "#064e3b" if active and active_color=="#10b981" else "#0f172a"
        if active and active_color=="#f59e0b": bg = "#451a03" # Laranja escuro para CPU
        
        self.setStyleSheet(f"background-color: {bg}; border: 2px solid {color}; border-radius: 8px;")
        
        # Usa a string guardada em vez do cacheKey()
        self.icon_lbl.setPixmap(qta.icon(self.icon_name, color=color).pixmap(32, 32)) 
        self.title_lbl.setStyleSheet(f"color: {color}; font-weight: bold; border: none;")

class Wire(QFrame):
    """Linha visual do autocarro (bus)."""
    def __init__(self, vertical=False):
        super().__init__()
        self.vertical = vertical
        self.base_color = "#334155"
        self.set_active(False)
        
    def set_active(self, active, color="#10b981"):
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
        
        content_layout = QHBoxLayout()
        content_layout.setSpacing(25)

        # -----------------------------------------------------
        # 1. PAINEL ESQUERDO: DMA CONFIG & CONTROL
        # -----------------------------------------------------
        config_panel = QFrame()
        config_panel.setStyleSheet("background-color: #0b1120; border: 1px solid #1e293b; border-radius: 8px;")
        config_panel.setFixedWidth(280)
        c_layout = QVBoxLayout(config_panel)
        c_layout.setContentsMargins(20, 20, 20, 20)
        c_layout.setSpacing(15)
        
        lbl_ctitle = QLabel("DMA CONFIG & CONTROL")
        lbl_ctitle.setStyleSheet("color: #94a3b8; font-weight: bold; font-size: 11px; border: none; margin-bottom: 10px;")
        c_layout.addWidget(lbl_ctitle)
        
        # Inputs de Registo
        grid = QGridLayout()
        grid.setSpacing(10)
        
        self.inp_sar = QLineEdit("0x2000")
        self.inp_dar = QLineEdit("0x4000")
        self.inp_bcr = QLineEdit("8")
        self.inp_bcr.setValidator(QIntValidator(1, 1024))
        
        for inp in [self.inp_sar, self.inp_dar, self.inp_bcr]:
            inp.setStyleSheet("background-color: #020617; border: 1px solid #1e293b; border-radius: 4px; color: #60a5fa; padding: 6px; font-family: monospace; font-weight: bold; text-align: right;")
            inp.setAlignment(Qt.AlignRight)

        grid.addWidget(self._mk_lbl("SAR (Src)"), 0, 0)
        grid.addWidget(self.inp_sar, 0, 1)
        grid.addWidget(self._mk_lbl("DAR (Dst)"), 1, 0)
        grid.addWidget(self.inp_dar, 1, 1)
        grid.addWidget(self._mk_lbl("BCR (Count)"), 2, 0)
        grid.addWidget(self.inp_bcr, 2, 1)
        c_layout.addLayout(grid)
        
        # Arbitragem
        c_layout.addSpacing(10)
        c_layout.addWidget(self._mk_lbl("Bus Arbiter Policy"))
        self.combo_policy = QComboBox()
        self.combo_policy.addItems([
            "Burst Mode (DMA Halt CPU)",
            "Cycle Stealing (Transparent)",
            "Interleaved (1 CPU / 1 DMA)"
        ])
        self.combo_policy.setStyleSheet("""
            QComboBox { background-color: #020617; border: 1px solid #1e293b; border-radius: 4px; color: #f8fafc; padding: 8px; font-weight: bold; }
            QComboBox::drop-down { border: none; }
        """)
        c_layout.addWidget(self.combo_policy)
        
        # Carga da CPU
        c_layout.addSpacing(10)
        load_layout = QHBoxLayout()
        # Correção: Uso de <br> em vez de \n, e forcei o Formato RichText
        self.lbl_cpu_load = QLabel("CPU Load Sim<br><span style='color:#64748b; font-size:10px;'>CPU Idle</span>")
        self.lbl_cpu_load.setTextFormat(Qt.RichText) 
        self.lbl_cpu_load.setStyleSheet("border: none; font-weight: bold;")
        self.sw_load = ToggleSwitch()
        self.sw_load.toggled.connect(self._toggle_cpu_load)
        load_layout.addWidget(self.lbl_cpu_load)
        load_layout.addStretch()
        load_layout.addWidget(self.sw_load)
        c_layout.addLayout(load_layout)
        
        c_layout.addStretch()
        
        # Botões de Acção
        self.btn_run_cpu = QPushButton(" ▶ Run CPU Memcpy()")
        self.btn_run_cpu.setStyleSheet("background-color: transparent; border: 1px solid #3b82f6; color: #3b82f6; border-radius: 6px; padding: 12px; font-weight: bold;")
        self.btn_run_cpu.setCursor(Qt.PointingHandCursor)
        self.btn_run_cpu.clicked.connect(lambda: self.start_transfer('CPU'))
        
        self.btn_run_dma = QPushButton(" ⚡ Start DMA Transfer")
        self.btn_run_dma.setStyleSheet("background-color: #059669; border: none; color: white; border-radius: 6px; padding: 12px; font-weight: bold;")
        self.btn_run_dma.setCursor(Qt.PointingHandCursor)
        self.btn_run_dma.clicked.connect(lambda: self.start_transfer('DMA'))
        
        self.btn_reset = QPushButton(" 🔄 Reset System")
        self.btn_reset.setStyleSheet("background-color: transparent; border: 1px solid #ef4444; color: #ef4444; border-radius: 6px; padding: 10px; font-weight: bold;")
        self.btn_reset.setCursor(Qt.PointingHandCursor)
        self.btn_reset.clicked.connect(self.reset_ui)
        
        c_layout.addWidget(self.btn_run_cpu)
        c_layout.addWidget(self.btn_run_dma)
        c_layout.addSpacing(10)
        c_layout.addWidget(self.btn_reset)

        content_layout.addWidget(config_panel)

        # -----------------------------------------------------
        # 2. PAINEL CENTRAL: ARCHITECTURE (ANIMADO)
        # -----------------------------------------------------
        arch_panel = QFrame()
        arch_panel.setStyleSheet("background-color: #0b1120; border: 1px solid #1e293b; border-radius: 8px;")
        a_layout = QVBoxLayout(arch_panel)
        a_layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_atitle = QLabel("SYSTEM BUS ARCHITECTURE (ARBITRATION)")
        lbl_atitle.setStyleSheet("color: #94a3b8; font-weight: bold; font-size: 11px; border: none; margin-bottom: 20px;")
        a_layout.addWidget(lbl_atitle)
        
        # Grid do Diagrama Físico
        d_grid = QGridLayout()
        d_grid.setSpacing(0)
        
        # Blocos
        self.blk_cpu = BlockWidget("CPU", "fa5s.microchip", "#64748b")
        self.blk_arb = BlockWidget("ARBITER", "fa5s.exchange-alt", "#64748b")
        self.blk_dma = BlockWidget("DMA", "fa5s.exchange-alt", "#64748b")
        self.blk_mem = BlockWidget("System Memory", "fa5s.database", "#0891b2")
        self.blk_mem.setFixedSize(200, 100) # Memória é mais larga
        
        # Fios (Wires)
        self.w_cpu_arb = Wire(False)
        self.w_dma_arb = Wire(False)
        self.w_arb_bus = Wire(True)
        self.w_bus_mem = Wire(True)
        
        # System Bus
        self.bus_main = QFrame()
        self.bus_main.setFixedHeight(24)
        self.bus_main.setStyleSheet("background-color: #1e293b; border-radius: 4px;")
        bus_layout = QHBoxLayout(self.bus_main)
        bus_layout.setContentsMargins(10, 0, 10, 0)
        bus_lbl = QLabel("⇌ SYSTEM BUS (AHB/AXI) | DATA | ADDR | CTRL |")
        bus_lbl.setStyleSheet("color: #94a3b8; font-size: 9px; font-weight: bold; font-family: monospace; border: none;")
        bus_lbl.setAlignment(Qt.AlignCenter)
        bus_layout.addWidget(bus_lbl)
        
        # Posicionamento Mágico no Grid
        # Linha 0: CPU --- Arbiter --- DMA
        d_grid.addWidget(self.blk_cpu, 0, 0, Qt.AlignCenter)
        d_grid.addWidget(self.w_cpu_arb, 0, 1, Qt.AlignVCenter)
        d_grid.addWidget(self.blk_arb, 0, 2, Qt.AlignCenter)
        d_grid.addWidget(self.w_dma_arb, 0, 3, Qt.AlignVCenter)
        d_grid.addWidget(self.blk_dma, 0, 4, Qt.AlignCenter)
        
        # Linha 1: Arbiter desce para o Bus
        d_grid.addWidget(self.w_arb_bus, 1, 2, Qt.AlignHCenter)
        d_grid.setRowMinimumHeight(1, 40)
        
        # Linha 2: O Autocarro Principal
        d_grid.addWidget(self.bus_main, 2, 0, 1, 5)
        
        # Linha 3: Bus desce para Memória
        d_grid.addWidget(self.w_bus_mem, 3, 2, Qt.AlignHCenter)
        d_grid.setRowMinimumHeight(3, 40)
        
        # Linha 4: Memória
        d_grid.addWidget(self.blk_mem, 4, 0, 1, 5, Qt.AlignHCenter)

        a_layout.addStretch()
        a_layout.addLayout(d_grid)
        a_layout.addStretch()
        content_layout.addWidget(arch_panel, stretch=1)

        # -----------------------------------------------------
        # 3. PAINEL DIREITO: PERFORMANCE
        # -----------------------------------------------------
        perf_panel = QFrame()
        perf_panel.setStyleSheet("background-color: #0b1120; border: 1px solid #1e293b; border-radius: 8px;")
        perf_panel.setFixedWidth(280)
        p_layout = QVBoxLayout(perf_panel)
        p_layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_ptitle = QLabel("PERFORMANCE MONITOR")
        lbl_ptitle.setStyleSheet("color: #94a3b8; font-weight: bold; font-size: 11px; border: none; margin-bottom: 20px;")
        p_layout.addWidget(lbl_ptitle)
        
        # Cards de Métricas
        self.lbl_total_cyc = self._mk_metric_card(p_layout, "Total Cycles", "0")
        p_layout.addSpacing(15)
        self.lbl_stall_cyc = self._mk_metric_card(p_layout, "CPU Stall Cycles\nWait State", "0")
        
        p_layout.addStretch()
        
        policy_box = QFrame()
        policy_box.setStyleSheet("border: 1px dashed #334155; border-radius: 8px;")
        pb_layout = QVBoxLayout(policy_box)
        lbl_sel = QLabel("Selected Policy")
        lbl_sel.setStyleSheet("color: #64748b; font-size: 10px; font-weight: bold; border: none;")
        lbl_sel.setAlignment(Qt.AlignCenter)
        self.lbl_active_policy = QLabel("NONE")
        self.lbl_active_policy.setStyleSheet("color: #2dd4bf; font-weight: bold; font-size: 16px; border: none;")
        self.lbl_active_policy.setAlignment(Qt.AlignCenter)
        self.lbl_active_policy.setWordWrap(True)
        pb_layout.addWidget(lbl_sel)
        pb_layout.addWidget(self.lbl_active_policy)
        p_layout.addWidget(policy_box)
        
        content_layout.addWidget(perf_panel)
        main_layout.addLayout(content_layout)

        # --- Variáveis de Simulação ---
        self.timer = QTimer()
        self.timer.timeout.connect(self._step_sim)
        self.sim_active = False
        self.mode = None # 'CPU' ou 'DMA'
        self.target_words = 0
        self.current_words = 0
        self.cycles = 0
        self.stalls = 0
        self.cpu_heavy_load = False

    def _mk_lbl(self, text):
        l = QLabel(text)
        l.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold; border: none;")
        return l

    def _mk_metric_card(self, parent_layout, title, val):
        frame = QFrame()
        frame.setStyleSheet("background-color: #020617; border: 1px solid #1e293b; border-radius: 6px;")
        layout = QHBoxLayout(frame)
        
        l_title = QLabel(title)
        l_title.setStyleSheet("color: #64748b; font-size: 11px; font-weight: bold; border: none;")
        
        l_val = QLabel(val)
        l_val.setStyleSheet("color: #f8fafc; font-size: 24px; font-weight: bold; border: none;")
        l_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        layout.addWidget(l_title)
        layout.addWidget(l_val)
        parent_layout.addWidget(frame)
        return l_val

    def _toggle_cpu_load(self, checked):
        self.cpu_heavy_load = checked
        text = "CPU Heavy Task" if checked else "CPU Idle"
        color = "#f59e0b" if checked else "#64748b"
        # Correção: O <br> e o RichText forçam o Qt a não ignorar as tags HTML
        self.lbl_cpu_load.setText(f"CPU Load Sim<br><span style='color:{color}; font-size:10px;'>{text}</span>")

    def reset_ui(self):
        self.timer.stop()
        self.sim_active = False
        self.cycles = 0
        self.stalls = 0
        self.current_words = 0
        self.lbl_total_cyc.setText("0")
        self.lbl_stall_cyc.setText("0")
        self.lbl_active_policy.setText("NONE")
        
        self.btn_run_cpu.setEnabled(True)
        self.btn_run_dma.setEnabled(True)
        
        self._set_bus_active('NONE')

    def start_transfer(self, mode):
        self.reset_ui()
        try:
            self.target_words = int(self.inp_bcr.text())
        except:
            self.target_words = 8
            self.inp_bcr.setText("8")
            
        self.mode = mode
        self.sim_active = True
        self.btn_run_cpu.setEnabled(False)
        self.btn_run_dma.setEnabled(False)
        
        if mode == 'CPU':
            self.lbl_active_policy.setText("CPU Memcpy\n(No DMA)")
        else:
            self.lbl_active_policy.setText(self.combo_policy.currentText())
            
        self.timer.start(100) # 100ms por ciclo simulado

    def _step_sim(self):
        if self.current_words >= self.target_words:
            self.timer.stop()
            self._set_bus_active('NONE')
            self.btn_run_cpu.setEnabled(True)
            self.btn_run_dma.setEnabled(True)
            return

        self.cycles += 1
        policy = self.combo_policy.currentIndex() # 0: Burst, 1: Stealing, 2: Interleaved

        if self.mode == 'CPU':
            # CPU faz 1 read, 1 write (2 ciclos por word). CPU ocupada = stall do ponto de vista de I/O
            self.stalls += 1
            if self.cycles % 2 == 0:
                self.current_words += 1
            self._set_bus_active('CPU')
            
        elif self.mode == 'DMA':
            if policy == 0:
                # Burst: DMA monopoliza o bus. CPU sofre Stall contínuo se precisar do bus.
                self.current_words += 1
                if self.cpu_heavy_load: self.stalls += 1
                else: self.stalls += 1 # Em Burst, assumimos que a CPU paralisa completamente por norma
                self._set_bus_active('DMA')
                
            elif policy == 1:
                # Cycle Stealing (Transparent): DMA só transfere se a CPU não precisar do bus naquele ciclo
                if self.cpu_heavy_load:
                    # CPU precisa sempre do bus. DMA rouba 1, CPU tem 1. Lento.
                    if self.cycles % 2 == 0:
                        self.current_words += 1
                        self.stalls += 1 # CPU foi stallada neste ciclo
                        self._set_bus_active('DMA')
                    else:
                        self._set_bus_active('CPU')
                else:
                    # CPU Idle, DMA transfere à vontade sem causar Stalls
                    self.current_words += 1
                    self._set_bus_active('DMA')
                    
            elif policy == 2:
                # Interleaved: Força 1 ciclo CPU, 1 ciclo DMA estritamente.
                if self.cycles % 2 == 0:
                    self.current_words += 1
                    self._set_bus_active('DMA')
                else:
                    self._set_bus_active('CPU')
                    if self.cpu_heavy_load: self.stalls += 0 # Trabalhou normal, não é stall

        # Atualiza a interface numérico
        self.lbl_total_cyc.setText(str(self.cycles))
        self.lbl_stall_cyc.setText(str(self.stalls))

    def _set_bus_active(self, master):
        # Desliga tudo primeiro
        self.blk_cpu.set_active(False)
        self.blk_dma.set_active(False)
        self.blk_arb.set_active(False)
        self.blk_mem.set_active(False)
        self.w_cpu_arb.set_active(False)
        self.w_dma_arb.set_active(False)
        self.w_arb_bus.set_active(False)
        self.w_bus_mem.set_active(False)
        self.bus_main.setStyleSheet("background-color: #1e293b; border-radius: 4px;")

        if master == 'CPU':
            color = "#f59e0b" # Laranja
            self.blk_cpu.set_active(True, color)
            self.blk_arb.set_active(True, color)
            self.blk_mem.set_active(True, color)
            self.w_cpu_arb.set_active(True, color)
            self.w_arb_bus.set_active(True, color)
            self.w_bus_mem.set_active(True, color)
            self.bus_main.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
            
        elif master == 'DMA':
            color = "#10b981" # Verde
            self.blk_dma.set_active(True, color)
            self.blk_arb.set_active(True, color)
            self.blk_mem.set_active(True, color)
            self.w_dma_arb.set_active(True, color)
            self.w_arb_bus.set_active(True, color)
            self.w_bus_mem.set_active(True, color)
            self.bus_main.setStyleSheet(f"background-color: {color}; border-radius: 4px;")