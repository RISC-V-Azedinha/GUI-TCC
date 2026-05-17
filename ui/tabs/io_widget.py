# ui/tabs/io_widget.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QFrame, QTableWidget, QTableWidgetItem,
                             QHeaderView, QAbstractItemView, QPlainTextEdit,
                             QProgressBar)
from PyQt5.QtCore import Qt, pyqtSignal, QRegExp
from PyQt5.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat
import qtawesome as qta

# Cores dinâmicas (Apenas para fins visuais estáticos agora)
PALETTE_HANDLE_OFF = "#475569"
PALETTE_LED_OFF_BG = "#2E1114"
PALETTE_LED_OFF_BORDER = "#4A1D24"

class CodeEditor(QPlainTextEdit):
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Tab:
            self.insertPlainText("    ")
            return
        super().keyPressEvent(event)

class CHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.rules = []
        
        keyword_fmt = QTextCharFormat()
        keyword_fmt.setForeground(QColor("#6CA1A2")) 
        keyword_fmt.setFontWeight(QFont.Bold)
        keywords = [r"\bvoid\b", r"\bint\b", r"\bvolatile\b", r"\bwhile\b", r"\bif\b", r"\belse\b", r"\bunsigned\b", r"\bchar\b"]
        for k in keywords:
            self.rules.append((QRegExp(k), keyword_fmt))
            
        macro_fmt = QTextCharFormat()
        macro_fmt.setForeground(QColor("#F2B845")) 
        self.rules.append((QRegExp(r"#define\b"), macro_fmt))
        
        number_fmt = QTextCharFormat()
        number_fmt.setForeground(QColor("#5DB373")) 
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

class IOWidget(QWidget):
    # AGORA O SINAL ENVIA O CÓDIGO FONTE (STRING)
    request_compile_and_upload = pyqtSignal(str) 

    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 30)
        main_layout.setSpacing(20)

        # Barra Superior Simplificada
        top_bar = QHBoxLayout()
        lbl_mode = QLabel("🔌 Mode:  ")
        lbl_mode.setObjectName("IOModeLabel")
        
        self.btn_hw = QPushButton("HARDWARE (GCC TOOLCHAIN)")
        self.btn_hw.setObjectName("IOHwModeBtn")
        self.btn_hw.setStyleSheet("color: #DC673E; font-weight: bold; border-bottom: 2px solid #DC673E;")
        
        top_bar.addWidget(lbl_mode)
        top_bar.addWidget(self.btn_hw)
        top_bar.addStretch()
        main_layout.addLayout(top_bar)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(30)

        # --- LADO ESQUERDO: EDITOR C ---
        code_frame = QFrame()
        code_frame.setObjectName("IOCodePanel")
        code_layout = QVBoxLayout(code_frame)
        code_layout.setContentsMargins(15, 15, 15, 15)
        
        code_header_layout = QHBoxLayout()
        icon_code = QLabel()
        icon_code.setPixmap(qta.icon('fa5s.code', color='#F2B845').pixmap(16, 16))
        lbl_code = QLabel("FIRMWARE EM C")
        lbl_code.setProperty("class", "IOSectionTitle")
        code_header_layout.addWidget(icon_code)
        code_header_layout.addWidget(lbl_code)
        code_header_layout.addStretch()
        code_layout.addLayout(code_header_layout)
        
        self.editor = CodeEditor()
        self.editor.document().setDocumentMargin(15)
        self.highlighter = CHighlighter(self.editor.document())
        default_code = """// Memory Map Definitions
#define LEDS_BASE     0x20000000 // 16-bit (R/W)
#define SWITCHES_BASE 0x20000004 // 16-bit (RO)

void main() {
    volatile int* led_ptr = (int*)LEDS_BASE;
    volatile int* sw_ptr = (int*)SWITCHES_BASE;
    
    while(1) {
        // Lê os switches
        int sw_val = *sw_ptr;
        
        int high_byte = (sw_val & 0xFF00) >> 8;
        int low_byte = sw_val & 0x00FF;
        
        // Escreve nos LEDs
        *led_ptr = high_byte + low_byte;
    }
}"""
        self.editor.setPlainText(default_code)
        code_layout.addWidget(self.editor)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.progressBar.setFixedHeight(34)
        self.progressBar.setFixedWidth(200)
        self.progressBar.hide() 
        self.progressBar.setStyleSheet("""
            QProgressBar { border: 1px solid #2A2F3A; border-radius: 4px; text-align: center; color: white; background-color: #0B0D12;}
            QProgressBar::chunk { background-color: #5DB373; border-radius: 3px; }
        """)

        self.btn_upload = QPushButton(" Compile & Flash FPGA")
        self.btn_upload.setIcon(qta.icon('fa5s.cogs', color='#E2E8F0'))
        self.btn_upload.setProperty("class", "ActionBtn SuccessBtn")
        self.btn_upload.clicked.connect(self.trigger_compile_and_upload)
        
        btn_layout.addWidget(self.progressBar)
        btn_layout.addWidget(self.btn_upload)
        code_layout.addLayout(btn_layout)

        content_layout.addWidget(code_frame, stretch=1)

        # --- LADO DIREITO: MAPA VISUAL ---
        right_panel = QVBoxLayout()
        right_panel.setSpacing(20)

        map_frame = QFrame()
        map_frame.setObjectName("IOMapPanel")
        map_layout = QVBoxLayout(map_frame)
        map_layout.setAlignment(Qt.AlignTop) 
        map_layout.setContentsMargins(15, 15, 15, 15)
        
        map_header_layout = QHBoxLayout()
        icon_map = QLabel()
        icon_map.setPixmap(qta.icon('fa5s.microchip', color='#6CA1A2').pixmap(16, 16))
        lbl_map = QLabel("SOC MEMORY MAP")
        lbl_map.setProperty("class", "IOSectionTitle")
        map_header_layout.addWidget(icon_map)
        map_header_layout.addWidget(lbl_map)
        map_header_layout.addStretch()
        map_layout.addLayout(map_header_layout)
        
        self.mem_table = QTableWidget(4, 3)
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
            ("0x2000_0000", "GPIO_LED_DATA", "R/W"),
            ("0x2000_0004", "GPIO_SW_DATA", "RO"),
            ("0x2000_0008", "GPIO_HEX_DATA", "R/W"),
            ("0x1000_0000", "UART_TX_DATA", "WO")
        ]
        
        for r, row_data in enumerate(data):
            for c, text in enumerate(row_data):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                item.setForeground(QColor("#E2E8F0" if c != 0 else "#6CA1A2"))
                self.mem_table.setItem(r, c, item)
                
        self.mem_table.setFixedHeight(140)
        map_layout.addWidget(self.mem_table)
        right_panel.addWidget(map_frame, stretch=0)

        # Referência Estática da Placa
        fpga_panel = QFrame()
        fpga_panel.setObjectName("IOBoardPanel")
        f_layout = QVBoxLayout(fpga_panel)
        f_layout.setContentsMargins(20, 20, 20, 40)
        
        fpga_header_layout = QHBoxLayout()
        icon_fpga = QLabel()
        icon_fpga.setPixmap(qta.icon('fa5s.plug', color='#5DB373').pixmap(16, 16))
        lbl_fpga = QLabel("HARDWARE REFERENCE (STATIC)")
        lbl_fpga.setProperty("class", "IOSectionTitle")
        fpga_header_layout.addWidget(icon_fpga)
        fpga_header_layout.addWidget(lbl_fpga)
        fpga_header_layout.addStretch()
        f_layout.addLayout(fpga_header_layout)
        
        f_layout.addStretch()
        
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
        
        led_container = QFrame()
        led_container.setObjectName("IOLedContainer")
        led_layout = QHBoxLayout(led_container)
        led_layout.setSpacing(8)
        led_layout.setAlignment(Qt.AlignCenter)
        
        for i in range(16):
            led = QFrame()
            led.setFixedSize(16, 16)
            led.setStyleSheet(f"background-color: {PALETTE_LED_OFF_BG}; border-radius: 8px; border: 1px solid {PALETTE_LED_OFF_BORDER};")
            led_layout.addWidget(led)
            
        f_layout.addWidget(led_container, alignment=Qt.AlignCenter)
        f_layout.addSpacing(30)
        
        sw_layout = QHBoxLayout()
        sw_layout.setSpacing(8)
        sw_layout.setAlignment(Qt.AlignCenter)
        
        for i in range(15, -1, -1):
            sw_container = QVBoxLayout()
            sw_container.setSpacing(5)
            
            sw_track = QFrame()
            sw_track.setObjectName("IOSwitchTrack")
            sw_track.setFixedSize(24, 50)
            t_layout = QVBoxLayout(sw_track)
            t_layout.setContentsMargins(2, 2, 2, 2)
            sw_handle = QFrame()
            sw_handle.setFixedHeight(20)
            sw_handle.setStyleSheet(f"background-color: {PALETTE_HANDLE_OFF}; border-radius: 2px;")
            t_layout.addWidget(sw_handle, alignment=Qt.AlignBottom)
            
            sw_lbl = QLabel(f"SW{i}")
            sw_lbl.setProperty("class", "IOSwitchLabel")
            sw_lbl.setAlignment(Qt.AlignCenter)
            sw_container.addWidget(sw_track, alignment=Qt.AlignCenter)
            sw_container.addWidget(sw_lbl, alignment=Qt.AlignCenter)
            sw_layout.addLayout(sw_container)
            
        f_layout.addLayout(sw_layout)
        f_layout.addStretch()
        
        right_panel.addWidget(fpga_panel, stretch=1)
        content_layout.addLayout(right_panel, stretch=1)
        main_layout.addLayout(content_layout)

        # Console de saída do GCC
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setFixedHeight(140)
        self.console.setStyleSheet("background-color: #0B0D12; color: #E2E8F0; font-family: 'Consolas', monospace;")
        main_layout.addWidget(self.console)

    def trigger_compile_and_upload(self):
        c_code = self.editor.toPlainText()
        self.progressBar.setValue(0)
        self.progressBar.show()
        self.btn_upload.setEnabled(False)
        self.btn_upload.setText(" Compiling...")
        
        self.console.clear()
        self.log(">> Iniciando processo de compilação C via Makefile...", "#38bdf8")
        
        # Dispara o sinal enviando o texto fonte
        self.request_compile_and_upload.emit(c_code)

    def log(self, msg: str, color: str = "#cbd5e1"):
        self.console.appendHtml(f"<span style='color:{color};'>{msg}</span>")
        sb = self.console.verticalScrollBar()
        sb.setValue(sb.maximum())