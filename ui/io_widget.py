# ui/io_widget.py
import re
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QFrame, QTableWidget, QTableWidgetItem,
                             QHeaderView, QAbstractItemView, QPlainTextEdit, QGridLayout)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QRegExp
from PyQt5.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat
import qtawesome as qta

# Cores dinâmicas (Trazendo o aspecto de Hardware físico de volta)
PALETTE_HANDLE_OFF = "#475569"     # Slate Grey: Destaca a chave física contra o trilho escuro
PALETTE_HANDLE_ON = "#DC673E"      # Laranja Ativo
PALETTE_LED_OFF_BG = "#2E1114"     # Vermelho bem escuro (LED apagado)
PALETTE_LED_OFF_BORDER = "#4A1D24" # Borda do LED apagado
PALETTE_LED_ON_BG = "#DC673E"      
PALETTE_LED_ON_BORDER = "#F2B845"


# =====================================================================
# EDITOR COM SUPORTE A TAB = 4 ESPAÇOS
# =====================================================================
class CodeEditor(QPlainTextEdit):
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Tab:
            self.insertPlainText("    ")
            return
        super().keyPressEvent(event)

# =====================================================================
# C SYNTAX HIGHLIGHTER
# =====================================================================
class CHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.rules = []
        
        keyword_fmt = QTextCharFormat()
        keyword_fmt.setForeground(QColor("#6CA1A2")) # Teal
        keyword_fmt.setFontWeight(QFont.Bold)
        keywords = [r"\bvoid\b", r"\bint\b", r"\bvolatile\b", r"\bwhile\b", r"\bif\b", r"\belse\b"]
        for k in keywords:
            self.rules.append((QRegExp(k), keyword_fmt))
            
        macro_fmt = QTextCharFormat()
        macro_fmt.setForeground(QColor("#F2B845")) # Mostarda
        self.rules.append((QRegExp(r"#define\b"), macro_fmt))
        
        number_fmt = QTextCharFormat()
        number_fmt.setForeground(QColor("#5DB373")) # Verde
        self.rules.append((QRegExp(r"\b0x[0-9a-fA-F_]+\b"), number_fmt))
        self.rules.append((QRegExp(r"\b[0-9]+\b"), number_fmt))
        
        comment_fmt = QTextCharFormat()
        comment_fmt.setForeground(QColor("#8B9BB4"))
        comment_fmt.setFontItalic(True)
        self.rules.append((QRegExp(r"//[^\n]*"), comment_fmt))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, fmt)
                index = expression.indexIn(text, index + length)

# =====================================================================
# COMPONENTES DE HARDWARE VISUAL (SW e LED)
# =====================================================================
class SwitchWidget(QWidget):
    toggled = pyqtSignal(bool)
    
    def __init__(self, index):
        super().__init__()
        self.state = False
        self.index = index
        self.setFixedSize(24, 50)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.track = QFrame()
        self.track.setObjectName("IOSwitchTrack")
        t_layout = QVBoxLayout(self.track)
        t_layout.setContentsMargins(2, 2, 2, 2)
        
        self.handle = QFrame()
        self.handle.setFixedHeight(20)
        
        t_layout.addWidget(self.handle, alignment=Qt.AlignBottom)
        layout.addWidget(self.track)
        self._update_ui()
        
    def mousePressEvent(self, event):
        self.state = not self.state
        self._update_ui()
        self.toggled.emit(self.state)
        super().mousePressEvent(event)
        
    def _update_ui(self):
        t_layout = self.track.layout()
        t_layout.removeWidget(self.handle)
        if self.state:
            self.handle.setStyleSheet(f"background-color: {PALETTE_HANDLE_ON}; border-radius: 2px;")
            t_layout.addWidget(self.handle, alignment=Qt.AlignTop)
        else:
            self.handle.setStyleSheet(f"background-color: {PALETTE_HANDLE_OFF}; border-radius: 2px;")
            t_layout.addWidget(self.handle, alignment=Qt.AlignBottom)

class LEDWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedSize(16, 16)
        self.set_state(False)
        
    def set_state(self, is_on):
        if is_on:
            self.setStyleSheet(f"background-color: {PALETTE_LED_ON_BG}; border-radius: 8px; border: 1px solid {PALETTE_LED_ON_BORDER};")
        else:
            self.setStyleSheet(f"background-color: {PALETTE_LED_OFF_BG}; border-radius: 8px; border: 1px solid {PALETTE_LED_OFF_BORDER};")

# =====================================================================
# PAINEL PRINCIPAL DO LABORATÓRIO I/O
# =====================================================================
class IOWidget(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 30)
        main_layout.setSpacing(20)

        # Barra Superior
        top_bar = QHBoxLayout()
        lbl_mode = QLabel("🔌 Mode:  ")
        lbl_mode.setObjectName("IOModeLabel")
        
        self.btn_sim = QPushButton("SIM")
        self.btn_sim.setObjectName("IOSimModeBtn")
        
        self.btn_hw = QPushButton("HARDWARE")
        self.btn_hw.setObjectName("IOHwModeBtn")
        
        top_bar.addWidget(lbl_mode)
        top_bar.addWidget(self.btn_sim)
        top_bar.addWidget(self.btn_hw)
        top_bar.addStretch()
        main_layout.addLayout(top_bar)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(30)

        # -----------------------------------------------------
        # LADO ESQUERDO: EDITOR DE CÓDIGO
        # -----------------------------------------------------
        code_frame = QFrame()
        code_frame.setObjectName("IOCodePanel")
        code_layout = QVBoxLayout(code_frame)
        code_layout.setContentsMargins(15, 15, 15, 15)
        
        code_header_layout = QHBoxLayout()
        icon_code = QLabel()
        icon_code.setPixmap(qta.icon('fa5s.code', color='#F2B845').pixmap(16, 16))
        lbl_code = QLabel("DRIVER IMPLEMENTATION (C CODE)")
        lbl_code.setProperty("class", "IOSectionTitle")
        code_header_layout.addWidget(icon_code)
        code_header_layout.addWidget(lbl_code)
        code_header_layout.addStretch()
        code_layout.addLayout(code_header_layout)
        
        self.editor = CodeEditor()
        self.editor.document().setDocumentMargin(15)
        self.highlighter = CHighlighter(self.editor.document())
        default_code = """// Memory Map Definitions
#define SWITCHES_BASE 0x80001000 // 16-bit
#define LEDS_BASE     0x80001004 // 16-bit
#define HEX_BASE      0x80001008 // 32-bit (8 x 4-bit)

void main() {
    volatile int* sw_ptr = (int*)SWITCHES_BASE;
    volatile int* led_ptr = (int*)LEDS_BASE;
    
    while(1) {
        // Lemos os 16 Switches
        int sw_val = *sw_ptr;
        
        // Pega os 8 bits altos (SW15-SW8)
        int high_byte = (sw_val & 0xFF00) >> 8;
        
        // Pega os 8 bits baixos (SW7-SW0)
        int low_byte = sw_val & 0x00FF;
        
        // Escreve a soma nos LEDs
        *led_ptr = high_byte + low_byte;
    }
}"""
        self.editor.setPlainText(default_code)
        code_layout.addWidget(self.editor)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_run_sim = QPushButton(" Run Simulation")
        self.btn_run_sim.setIcon(qta.icon('fa5s.play', color='#12141A')) # Ícone escuro para contrastar com o fundo
        self.btn_run_sim.setProperty("class", "ActionBtn PrimaryBtn")
        self.btn_run_sim.clicked.connect(self.toggle_simulation)
        
        self.btn_upload = QPushButton(" Upload to FPGA")
        self.btn_upload.setIcon(qta.icon('fa5s.cloud-upload-alt', color='#E2E8F0'))
        self.btn_upload.setProperty("class", "ActionBtn")
        
        btn_layout.addWidget(self.btn_run_sim)
        btn_layout.addWidget(self.btn_upload)
        code_layout.addLayout(btn_layout)

        content_layout.addWidget(code_frame, stretch=1)

        # -----------------------------------------------------
        # LADO DIREITO: MAPA E FPGA
        # -----------------------------------------------------
        right_panel = QVBoxLayout()
        right_panel.setSpacing(20)

        # Mapa de Memória
        map_frame = QFrame()
        map_frame.setObjectName("IOMapPanel")
        map_layout = QVBoxLayout(map_frame)
        map_layout.setAlignment(Qt.AlignTop) 
        map_layout.setContentsMargins(15, 15, 15, 15)
        
        # --- NOVO CABEÇALHO COM ÍCONE COLORIDO ---
        map_header_layout = QHBoxLayout()
        icon_map = QLabel()
        icon_map.setPixmap(qta.icon('fa5s.microchip', color='#6CA1A2').pixmap(16, 16))
        lbl_map = QLabel("SOC MEMORY MAP")
        lbl_map.setProperty("class", "IOSectionTitle")
        map_header_layout.addWidget(icon_map)
        map_header_layout.addWidget(lbl_map)
        map_header_layout.addStretch()
        map_layout.addLayout(map_header_layout)
        # -----------------------------------------
        
        self.mem_table = QTableWidget(4, 3)
        self.mem_table.setObjectName("IOMemoryTable")
        
        # FORÇANDO O ESTILO MODERNO NA TABELA
        self.mem_table.setStyleSheet("""
            QTableWidget { border: none; background-color: transparent; }
            QHeaderView::section { background-color: transparent; color: #6CA1A2; border: none; border-bottom: 2px solid #6CA1A2; font-size: 12px; font-weight: bold; padding: 4px; }
            QTableWidget::item { border-bottom: 1px solid #1A1D24; }
        """)
        self.mem_table.setHorizontalHeaderLabels(["Address", "Name", "Type"])
        self.mem_table.verticalHeader().setVisible(False)
        self.mem_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.mem_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.mem_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.mem_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.mem_table.horizontalHeader().setFixedHeight(28)
        
        data = [
            ("0x8000_1000", "GPIO_SW_DATA", "RO"),
            ("0x8000_1004", "GPIO_LED_DATA", "R/W"),
            ("0x8000_1008", "GPIO_HEX_DATA", "R/W"),
            ("0x8000_2000", "UART_TX_DATA", "WO")
        ]
        
        for r, row_data in enumerate(data):
            for c, text in enumerate(row_data):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                # Aplicando cores da paleta oficial baseada na coluna
                item.setForeground(QColor("#E2E8F0" if c != 0 else "#6CA1A2"))
                self.mem_table.setItem(r, c, item)
                
        self.mem_table.setFixedHeight(140)
        map_layout.addWidget(self.mem_table)
        right_panel.addWidget(map_frame, stretch=0)

        # FPGA Board View
        fpga_panel = QFrame()
        fpga_panel.setObjectName("IOBoardPanel")
        f_layout = QVBoxLayout(fpga_panel)
        f_layout.setContentsMargins(20, 20, 20, 40)
        
        # --- NOVO CABEÇALHO COM ÍCONE COLORIDO ---
        fpga_header_layout = QHBoxLayout()
        icon_fpga = QLabel()
        icon_fpga.setPixmap(qta.icon('fa5s.plug', color='#5DB373').pixmap(16, 16))
        lbl_fpga = QLabel("FPGA BOARD VIEW")
        lbl_fpga.setProperty("class", "IOSectionTitle")
        fpga_header_layout.addWidget(icon_fpga)
        fpga_header_layout.addWidget(lbl_fpga)
        fpga_header_layout.addStretch()
        f_layout.addLayout(fpga_header_layout)
        # -----------------------------------------
        
        f_layout.addStretch()
        
        # 7-Segment Displays
        hex_layout = QHBoxLayout()
        hex_layout.setAlignment(Qt.AlignCenter)
        hex_layout.setSpacing(6)
        for _ in range(8):
            lbl_hex = QLabel("0")
            lbl_hex.setFixedSize(40, 55)
            lbl_hex.setAlignment(Qt.AlignCenter)
            lbl_hex.setProperty("class", "IOHexDisplay")
            hex_layout.addWidget(lbl_hex)
        f_layout.addLayout(hex_layout)
        f_layout.addSpacing(40)
        
        # LEDs Base
        led_container = QFrame()
        led_container.setObjectName("IOLedContainer")
        led_layout = QHBoxLayout(led_container)
        led_layout.setSpacing(8)
        led_layout.setAlignment(Qt.AlignCenter)
        
        self.leds = []
        for i in range(15, -1, -1):
            led = LEDWidget()
            self.leds.append(led)
            led_layout.addWidget(led)
            
        self.leds.reverse()
        f_layout.addWidget(led_container, alignment=Qt.AlignCenter)
        f_layout.addSpacing(30)
        
        # Switches Base
        sw_layout = QHBoxLayout()
        sw_layout.setSpacing(8)
        sw_layout.setAlignment(Qt.AlignCenter)
        
        self.switches = []
        for i in range(15, -1, -1):
            sw_container = QVBoxLayout()
            sw_container.setSpacing(5)
            sw = SwitchWidget(i)
            self.switches.append(sw)
            sw_lbl = QLabel(f"SW{i}")
            sw_lbl.setProperty("class", "IOSwitchLabel")
            sw_lbl.setAlignment(Qt.AlignCenter)
            sw_container.addWidget(sw, alignment=Qt.AlignCenter)
            sw_container.addWidget(sw_lbl, alignment=Qt.AlignCenter)
            sw_layout.addLayout(sw_container)
            
        self.switches.reverse()
        f_layout.addLayout(sw_layout)
        f_layout.addStretch()
        
        right_panel.addWidget(fpga_panel, stretch=1)
        content_layout.addLayout(right_panel, stretch=1)
        main_layout.addLayout(content_layout)

        self.sim_timer = QTimer()
        self.sim_timer.timeout.connect(self.simulation_step)
        self.is_simulating = False

    def toggle_simulation(self):
        if self.is_simulating:
            self.sim_timer.stop()
            self.btn_run_sim.setText(" Run Simulation")
            self.btn_run_sim.setIcon(qta.icon('fa5s.play', color='#12141A'))
            self.btn_run_sim.setProperty("class", "ActionBtn PrimaryBtn")
            self.btn_run_sim.setStyleSheet("") # Limpa o estilo de Stop
            self.is_simulating = False
        else:
            self.sim_timer.start(100)
            self.btn_run_sim.setText(" Stop Simulation")
            self.btn_run_sim.setIcon(qta.icon('fa5s.stop', color='#12141A'))
            # Sobrescreve visualmente para o estado de emergência/parada
            self.btn_run_sim.setStyleSheet("background-color: #DC673E; color: #12141A; border: none; font-weight: bold; border-radius: 4px; padding: 6px 16px;") 
            self.is_simulating = True

    def simulation_step(self):
        sw_value = 0
        for i, sw in enumerate(self.switches):
            if sw.state:
                sw_value |= (1 << i)
                
        code = self.editor.toPlainText()
        led_value = 0
        
        loop_match = re.search(r'while\s*\(\s*1\s*\)\s*\{([^}]*)\}', code, re.DOTALL)
        
        if loop_match:
            c_code = loop_match.group(1)
            lines = c_code.split('\n')
            py_code = []
            
            for line in lines:
                line = line.split('//')[0].strip()
                if not line: continue
                line = re.sub(r'^(?:volatile\s+)?(?:unsigned\s+)?(?:int|char|short|long|uint8_t|uint16_t|uint32_t)\s+', '', line)
                line = line.replace('*sw_ptr', 'sw_value')
                line = line.replace('*led_ptr', 'led_value')
                line = line.rstrip(';')
                py_code.append(line)
                
            local_vars = {'sw_value': sw_value, 'led_value': 0}
            
            try:
                exec('\n'.join(py_code), {}, local_vars)
                led_value = local_vars.get('led_value', 0)
            except Exception:
                pass
                
        for i, led in enumerate(self.leds):
            is_on = (led_value & (1 << i)) != 0
            led.set_state(is_on)