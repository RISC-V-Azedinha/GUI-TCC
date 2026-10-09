# ui/tabs/io_widget.py
import re
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QFrame, QTableWidget, QTableWidgetItem,
                             QHeaderView, QAbstractItemView, QPlainTextEdit,
                             QProgressBar)
from PyQt5.QtCore import Qt, pyqtSignal, QRegExp
from PyQt5.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat, QTextCursor
import qtawesome as qta

# Cores dinâmicas do tema
PALETTE_LED_OFF_BG = "#2E1114"
PALETTE_LED_OFF_BORDER = "#4A1D24"

# =====================================================================
# TERMINAL UART INTERATIVO (SEM ECO LOCAL)
# =====================================================================
class UARTTerminal(QPlainTextEdit):
    """Componente de terminal monospaçado que envia teclas direto para a serial."""
    send_char = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setReadOnly(True) # Evita que o usuário edite o histórico arbitrariamente
        self.setMaximumBlockCount(1000) # Limita o histórico para evitar consumo excessivo de memória
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #06080c; 
                color: #10b981; 
                font-family: 'Consolas', monospace; 
                font-size: 13px;
                border: 1px solid #1e293b;
                border-radius: 4px;
            }
        """)
        self.setPlaceholderText("=== TERMINAL UART ATIVO ===\nClique aqui e digite para interagir com a FPGA em tempo real...")

    def keyPressEvent(self, event):
        """Intercepta pressionamentos de tecla e envia os caracteres diretamente."""
        txt = event.text()
        if txt:
            # Emite o sinal para que o controlador transmita o caractere via cabo USB
            self.send_char.emit(txt)
        
        # CRÍTICO: Não chamamos super().keyPressEvent(event) aqui.
        # Isso impede o 'eco local', garantindo que o caractere só apareça no console 
        # se o firmware em C do RISC-V ler da FIFO e mandar de volta via UART!

# =====================================================================
# EDITOR DE CÓDIGO FONTE
# =====================================================================
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
        keywords = [r"\bvoid\b", r"\bint\b", r"\bvolatile\b", r"\bwhile\b", r"\bif\b", r"\belse\b", r"\bunsigned\b", r"\bchar\b", r"\buint32_t\b"]
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

# =====================================================================
# PAINEL PRINCIPAL DO LABORATÓRIO I/O
# =====================================================================
class IOWidget(QWidget):
    request_compile_and_upload = pyqtSignal(str) 
    request_uart_send = pyqtSignal(str) # Sinal para envio de caracteres UART

    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 30)
        main_layout.setSpacing(20)

        # Barra Superior
        top_bar = QHBoxLayout()
        lbl_mode = QLabel("Mode:  ")
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
        default_code = r"""#include <stdint.h>
#include "memory_map.h"
#include "hal/hal_gpio.h"   // GPIO: porta + pino, displays de 7 segmentos e LEDs RGB

// =========================================================
// UART (saída de texto no console abaixo)
// =========================================================
void uart_putc(char c) {
    while (MMIO32(UART_CTRL_REG_ADDR) & UART_STATUS_TX_BUSY);
    MMIO32(UART_DATA_REG_ADDR) = c;
}

void uart_puts(const char *s) {
    while (*s) uart_putc(*s++);
}

void delay(uint32_t n) {
    for (volatile uint32_t i = 0; i < n; i++);
}

// =========================================================
// MAIN: Fibonacci nos LEDs (binário) e no display (decimal)
// =========================================================
//  SW0  = pausa         BTNU = reinicia a sequência
//  LD16 = cor muda a cada termo; JA pino 0 (pino 1 do conector)
//  pisca a cada termo, para ver com um osciloscópio
void main() {
    uint32_t t1 = 0, t2 = 1, n = 1;

    hal_gpio_set_dir(GPIO_JA, 0, GPIO_OUTPUT);       // como num microcontrolador:
                                                     // porta, pino e direção
    uart_puts("\n\r FIBONACCI: LEDs, display e LED RGB\n\r");

    while (1) {
        if (hal_gpio_read(GPIO_SW, 0)) continue;     // SW0 ligada: pausa

        if (hal_gpio_read(GPIO_BTN, GPIO_BTN_UP) || n > 45) {
            t1 = 0; t2 = 1; n = 1;                   // BTNU ou estouro: reinicia
            uart_puts(" reinicio\n\r");
        }

        hal_leds_write(t2 & 0xFFFF);                 // LEDs: termo em binário
        hal_seg7_write_dec(t2);                      // display: termo em decimal
        hal_rgb_set(RGB_LD16, (n & 1) ? 255 : 0, (n & 2) ? 255 : 0, (n & 4) ? 255 : 0);
        hal_gpio_toggle(GPIO_JA, 0);                 // pino do Pmod JA

        uint32_t next = t1 + t2;
        t1 = t2; t2 = next; n++;
        delay(800000);
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

        content_layout.addWidget(code_frame, stretch=2)

        # --- LADO DIREITO: MAPA VISUAL E CONSOLE UART ---
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
            ("0x2000_0000", "PMOD JA..JD", "R/W"),
            ("0x2000_0100", "LED / SW / BTN", "R/W"),
            ("0x2000_0200", "7-SEG / RGB", "R/W"),
            ("0x1000_0000", "UART_DATA", "R/W")
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

        # --- CONSOLE UART INTERATIVO ---
        self.uart_frame = QFrame()
        self.uart_frame.setObjectName("IOBoardPanel") 
        u_layout = QVBoxLayout(self.uart_frame)
        u_layout.setContentsMargins(15, 15, 15, 15)
        
        uart_header_layout = QHBoxLayout()
        icon_uart = QLabel()
        icon_uart.setPixmap(qta.icon('fa5s.terminal', color='#10b981').pixmap(16, 16))
        lbl_uart = QLabel("INTERACTIVE UART CONSOLE")
        lbl_uart.setProperty("class", "IOSectionTitle")
        uart_header_layout.addWidget(icon_uart)
        uart_header_layout.addWidget(lbl_uart)
        uart_header_layout.addStretch()
        u_layout.addLayout(uart_header_layout)
        
        # Instanciação do Terminal customizado
        self.uart_terminal = UARTTerminal()
        self.uart_terminal.send_char.connect(self.request_uart_send.emit)
        u_layout.addWidget(self.uart_terminal)
        
        right_panel.addWidget(self.uart_frame, stretch=1)
        content_layout.addLayout(right_panel, stretch=1)
        main_layout.addLayout(content_layout)

        # Console inferior exclusivo para logs do GCC
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setFixedHeight(100)
        self.console.setMaximumBlockCount(500)
        self.console.setStyleSheet("background-color: #0B0D12; color: #E2E8F0; font-family: 'Consolas', monospace;")
        main_layout.addWidget(self.console)

    def trigger_compile_and_upload(self):
        c_code = self.editor.toPlainText()
        self.progressBar.setValue(0)
        self.progressBar.show()
        self.btn_upload.setEnabled(False)
        self.btn_upload.setText(" Compiling...")
        
        self.console.clear()
        self.log(">> Salvando e invocando Toolchain RISC-V local...", "#38bdf8")
        self.request_compile_and_upload.emit(c_code)

    def append_uart_output(self, text: str):
        """Atualiza a tela do terminal serial avançando o cursor automaticamente."""
        
        # Filtra o Carriage Return (\r) para o PyQt não bugar a formatação visual
        clean_text = text.replace('\r', '')
        
        self.uart_terminal.moveCursor(QTextCursor.End)
        self.uart_terminal.insertPlainText(clean_text)
        self.uart_terminal.moveCursor(QTextCursor.End)

    def log(self, msg: str, color: str = "#cbd5e1"):
        self.console.appendHtml(f"<span style='color:{color};'>{msg}</span>")
        sb = self.console.verticalScrollBar()
        sb.setValue(sb.maximum())