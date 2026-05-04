# ui/os_console_widget.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QFrame, QTextEdit, QStackedWidget, QGridLayout)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
import qtawesome as qta
import time

# ==========================================
# PALETA OFICIAL DO PROJETO
# ==========================================
BG_PANEL = "#0B0D12"
BG_ELEMENT = "#12141A"
BORDER = "#2A2F3A"
TEXT_PRIMARY = "#E2E8F0"
TEXT_SECONDARY = "#8B9BB4"

TEAL = "#6CA1A2"
ORANGE = "#DC673E"
GREEN = "#5DB373"
MUSTARD = "#F2B845"
PURPLE = "#A855F7"
BLUE = "#3B82F6"
RED = "#EF4444"

def hex_to_rgba(hex_color, alpha=0.2):
    """Converte HEX para RGBA para garantir compatibilidade com o Qt Stylesheet"""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"

class OSConsoleWidget(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # ---------------------------------------------------------
        # PAINEL ESQUERDO: TERMINAL SERIAL
        # ---------------------------------------------------------
        terminal_panel = QFrame()
        terminal_panel.setStyleSheet(f"background-color: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 8px;")
        terminal_layout = QVBoxLayout(terminal_panel)
        terminal_layout.setContentsMargins(0, 0, 0, 0)
        terminal_layout.setSpacing(0)

        # Header do Terminal
        term_header = QFrame()
        term_header.setFixedHeight(40)
        term_header.setStyleSheet(f"background-color: {BG_ELEMENT}; border-bottom: 1px solid {BORDER}; border-radius: 8px 8px 0 0;")
        term_h_layout = QHBoxLayout(term_header)
        term_h_layout.setContentsMargins(15, 0, 15, 0)

        lbl_port_info = QLabel("/dev/ttyUSB0 - 115200 8N1")
        lbl_port_info.setStyleSheet(f"color: {TEXT_SECONDARY}; font-family: monospace; font-size: 11px; border: none;")
        term_h_layout.addWidget(lbl_port_info)
        term_h_layout.addStretch()

        self.lbl_status_dot = QLabel("●")
        self.lbl_status_dot.setStyleSheet(f"color: {RED}; border: none; font-size: 14px;") # Vermelho (Offline)
        self.lbl_status_text = QLabel("OFFLINE")
        self.lbl_status_text.setStyleSheet(f"color: {RED}; font-weight: bold; font-size: 11px; border: none;")
        
        term_h_layout.addWidget(self.lbl_status_dot)
        term_h_layout.addWidget(self.lbl_status_text)
        
        # Botão de Desconectar (Escondido inicialmente)
        self.btn_disconnect = QPushButton("✗")
        self.btn_disconnect.setStyleSheet(f"color: {RED}; background: transparent; border: none; font-weight: bold;")
        self.btn_disconnect.setCursor(Qt.PointingHandCursor)
        self.btn_disconnect.clicked.connect(self.disconnect_serial)
        self.btn_disconnect.hide()
        term_h_layout.addWidget(self.btn_disconnect)

        terminal_layout.addWidget(term_header)

        # Stack do Terminal (Página 0: Botão Conectar | Página 1: Texto)
        self.term_stack = QStackedWidget()
        
        # Página 0: Ecrã de Conexão
        page_connect = QWidget()
        page_connect.setStyleSheet("background-color: #000000; border-radius: 0 0 8px 8px;")
        conn_layout = QVBoxLayout(page_connect)
        conn_layout.setAlignment(Qt.AlignCenter)
        
        lbl_closed = QLabel("Serial Connection Closed")
        lbl_closed.setStyleSheet(f"color: {TEXT_SECONDARY}; font-family: monospace; border: none; margin-bottom: 10px;")
        lbl_closed.setAlignment(Qt.AlignCenter)
        
        green_hover = hex_to_rgba(GREEN, 0.1)
        green_pressed = hex_to_rgba(GREEN, 0.2)
        
        self.btn_connect = QPushButton("OPEN CONNECTION")
        self.btn_connect.setCursor(Qt.PointingHandCursor)
        self.btn_connect.setStyleSheet(f"""
            QPushButton {{
                border: 2px solid {GREEN};
                color: {GREEN};
                background-color: transparent;
                border-radius: 6px;
                padding: 12px 30px;
                font-weight: bold;
                font-family: monospace;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{ background-color: {green_hover}; }}
            QPushButton:pressed {{ background-color: {green_pressed}; }}
        """)
        self.btn_connect.clicked.connect(self.connect_serial)
        
        conn_layout.addWidget(lbl_closed)
        conn_layout.addWidget(self.btn_connect, alignment=Qt.AlignCenter)
        self.term_stack.addWidget(page_connect)

        # Página 1: Consola Real
        self.console_output = QTextEdit()
        self.console_output.document().setDocumentMargin(15)
        self.console_output.setReadOnly(True)
        self.console_output.setStyleSheet(f"""
            QTextEdit {{
                background-color: #000000;  /* <-- Mudei aqui para preto puro */
                color: {TEAL};
                font-family: 'Consolas', 'JetBrains Mono', monospace;
                font-size: 13px;
                border: none;
                border-radius: 0 0 8px 8px;
                padding: 15px;
            }}
        """)
        self.term_stack.addWidget(self.console_output)
        
        terminal_layout.addWidget(self.term_stack)
        main_layout.addWidget(terminal_panel, stretch=3)

        # ---------------------------------------------------------
        # PAINEL DIREITO: MACROS E CONFIGURAÇÃO
        # ---------------------------------------------------------
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setSpacing(20)

        # Secção: QUICK MACROS
        macros_panel = QFrame()
        macros_panel.setStyleSheet(f"background-color: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 8px;")
        m_layout = QVBoxLayout(macros_panel)
        m_layout.setContentsMargins(15, 15, 15, 15)
        
        lbl_m_title = QLabel("QUICK MACROS")
        lbl_m_title.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: bold; font-size: 11px; border: none; margin-bottom: 10px;")
        m_layout.addWidget(lbl_m_title)

        self.macro_buttons = []
        macros = [
            (" System Info", 'fa5s.microchip', self.macro_sysinfo),
            (" List Devices", 'fa5s.list', self.macro_list_dev),
            (" NPU Status", 'fa5s.brain', self.macro_npu_status),
            (" DMA Benchmark", 'fa5s.bolt', self.macro_dma),
            (" Reboot OS", 'fa5s.sync', self.macro_reboot)
        ]

        for text, icon, callback in macros:
            btn = QPushButton(text)
            btn.setIcon(qta.icon(icon, color=TEXT_SECONDARY))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {TEXT_SECONDARY};
                    border: 1px solid {BORDER};
                    border-radius: 6px;
                    padding: 10px;
                    text-align: left;
                    font-weight: bold;
                }}
                QPushButton:enabled:hover {{ 
                    background-color: {BG_ELEMENT}; 
                    color: {TEXT_PRIMARY}; 
                    border: 1px solid {TEXT_SECONDARY}; 
                }}
            """)
            btn.setEnabled(False)
            btn.clicked.connect(callback)
            self.macro_buttons.append(btn)
            m_layout.addWidget(btn)

        sidebar_layout.addWidget(macros_panel)

        # Secção: CONNECTION SETTINGS
        settings_panel = QFrame()
        settings_panel.setStyleSheet(f"background-color: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 8px;")
        s_layout = QVBoxLayout(settings_panel)
        s_layout.setContentsMargins(15, 15, 15, 15)
        
        lbl_s_title = QLabel("CONNECTION SETTINGS")
        lbl_s_title.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: bold; font-size: 11px; border: none; margin-bottom: 10px;")
        s_layout.addWidget(lbl_s_title)

        grid = QGridLayout()
        grid.setVerticalSpacing(10)

        settings = [
            ("Port", "/dev/ttyUSB0"),
            ("Baud", "115200"),
            ("Data", "8 bits"),
            ("Parity", "None"),
            ("Stop", "1 bit")
        ]
        
        for row, (k, v) in enumerate(settings):
            lbl_k = QLabel(k)
            lbl_k.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; border: none;")
            lbl_v = QLabel(v)
            lbl_v.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 12px; font-weight: bold; border: none;")
            lbl_v.setAlignment(Qt.AlignRight)
            grid.addWidget(lbl_k, row, 0)
            grid.addWidget(lbl_v, row, 1)
            
        s_layout.addLayout(grid)
        sidebar_layout.addWidget(settings_panel)

        sidebar_layout.addStretch()
        main_layout.addLayout(sidebar_layout, stretch=1)

        # Variáveis de Controlo Interno
        self.is_connected = False
        self.boot_timer = QTimer()
        self.boot_timer.timeout.connect(self._boot_sequence_step)
        self.boot_step = 0
        
        self.boot_messages = [
            f"<span style='color:{MUSTARD};'>[BOOT]</span> Inicializando RISC-V SoC...",
            f"<span style='color:{MUSTARD};'>[BOOT]</span> A carregar Kernel do ROM para RAM (0x80000000)...",
            f"<span style='color:{GREEN};'>[ OK ]</span> CPU Core RV32I verificado.",
            f"<span style='color:{GREEN};'>[ OK ]</span> Memória SRAM montada (256 KB).",
            f"<span style='color:{GREEN};'>[ OK ]</span> Módulo DMA mapeado em I/O.",
            f"<span style='color:{GREEN};'>[ OK ]</span> NPU Systolic Array pronta.",
            f"<br><span style='color:{BLUE};'>Bem-vindo ao AXON-OS v1.0</span>",
            "root@axon-os:~# "
        ]

    # ---------------------------------------------------------
    # LÓGICA DO TERMINAL (SIMULAÇÃO)
    # ---------------------------------------------------------
    def connect_serial(self):
        self.is_connected = True
        self.term_stack.setCurrentIndex(1)
        self.lbl_status_dot.setStyleSheet(f"color: {GREEN}; border: none; font-size: 14px;")
        self.lbl_status_text.setStyleSheet(f"color: {GREEN}; font-weight: bold; font-size: 11px; border: none;")
        self.lbl_status_text.setText("ONLINE")
        self.btn_disconnect.show()
        
        # Iniciar simulação de boot
        self.console_output.clear()
        self.boot_step = 0
        self.boot_timer.start(300) # Imprime uma linha a cada 300ms

    def disconnect_serial(self):
        self.is_connected = False
        self.term_stack.setCurrentIndex(0)
        self.lbl_status_dot.setStyleSheet(f"color: {RED}; border: none; font-size: 14px;")
        self.lbl_status_text.setStyleSheet(f"color: {RED}; font-weight: bold; font-size: 11px; border: none;")
        self.lbl_status_text.setText("OFFLINE")
        self.btn_disconnect.hide()
        
        for btn in self.macro_buttons:
            btn.setEnabled(False)

    def _boot_sequence_step(self):
        if self.boot_step < len(self.boot_messages):
            self.console_output.append(self.boot_messages[self.boot_step])
            self.boot_step += 1
        else:
            self.boot_timer.stop()
            # Ativa os botões de macro quando o boot termina
            for btn in self.macro_buttons:
                btn.setEnabled(True)

    def print_cmd(self, cmd, response):
        """Função auxiliar para imprimir um comando e a sua resposta falsa."""
        if not self.is_connected: return
        
        # Remove a última linha (que é o prompt)
        cursor = self.console_output.textCursor()
        cursor.movePosition(cursor.End)
        cursor.select(cursor.LineUnderCursor)
        cursor.removeSelectedText()
        
        # Imprime o comando digitado, a resposta, e o prompt novamente
        self.console_output.append(f"root@axon-os:~# <span style='color:{TEXT_PRIMARY};'>{cmd}</span>")
        self.console_output.append(response)
        self.console_output.append("root@axon-os:~# ")
        
        # Auto-scroll para o fim
        sb = self.console_output.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ---------------------------------------------------------
    # FUNÇÕES DAS MACROS
    # ---------------------------------------------------------
    def macro_sysinfo(self):
        resp = (
            f"<span style='color:{TEAL};'>"
            "Arquitetura: RV32I<br>"
            "Frequência de Clock: 100 MHz<br>"
            "Memória Total: 256 KB SRAM<br>"
            "Extensões Ativas: M, A, C (NPU)<br>"
            "Uptime: 2 minutos"
            "</span>"
        )
        self.print_cmd("cat /proc/cpuinfo", resp)

    def macro_list_dev(self):
        resp = (
            f"<span style='color:{TEAL};'>"
            "0x40000000 - UART0 (Serial Console)<br>"
            "0x40001000 - GPIO Controller<br>"
            "0x50000000 - DMA Engine<br>"
            "0x60000000 - Systolic NPU Co-Processor"
            "</span>"
        )
        self.print_cmd("lsdev", resp)

    def macro_npu_status(self):
        resp = (
            f"<span style='color:{TEAL};'>"
            f"NPU Power State: <span style='color:{GREEN};'>ON</span><br>"
            "Array Config: 3x3 Output Stationary<br>"
            "MAC Utilization: 0% (Idle)<br>"
            "PPU Pipeline: Active (ReLU + Bias)"
            "</span>"
        )
        self.print_cmd("npu_stat", resp)

    def macro_dma(self):
        resp = (
            f"<span style='color:{TEAL};'>"
            "A iniciar Transferência SRAM -> NPU...<br>"
            "Copiados 1024 bytes em 42 ciclos.<br>"
            "Bandwidth Estimada: 95.2 MB/s"
            "</span>"
        )
        self.print_cmd("dma_test --run", resp)

    def macro_reboot(self):
        self.print_cmd("reboot", f"<span style='color:{MUSTARD};'>O sistema está a ser reiniciado...</span>")
        # Desativa macros e roda o boot de novo após 1 segundo
        for btn in self.macro_buttons:
            btn.setEnabled(False)
        QTimer.singleShot(1000, self.connect_serial)