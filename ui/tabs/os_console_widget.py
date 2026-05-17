# ui/os_console_widget.py
import os
import serial
import struct
import time
import re
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QFrame, QTextEdit, QStackedWidget, QGridLayout, QApplication)
from PyQt5.QtGui import QTextOption, QColor, QFont, QTextCursor
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from core.connection_manager import ConnectionManager
import qtawesome as qta

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
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"


# ==========================================
# WIDGET CONSOLA INTERATIVA (True TTY)
# ==========================================
class TerminalConsole(QTextEdit):
    send_data = pyqtSignal(bytes)

    def __init__(self):
        super().__init__()
        self.setCursorWidth(8) 
        self.setLineWrapMode(QTextEdit.NoWrap) 
        self.document().setDocumentMargin(15)
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: #000000;
                color: {TEXT_PRIMARY};
                font-family: 'Consolas', 'JetBrains Mono', monospace;
                font-size: 14px;
                border: none;
            }}
        """)

    def keyPressEvent(self, event):
        if event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_C:
            super().keyPressEvent(event)
            return

        if event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_V:
            clipboard = QApplication.clipboard()
            if clipboard.text():
                self.send_data.emit(clipboard.text().encode('utf-8'))
            return

        if event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_L:
            self.clear()
            self.setTextColor(QColor(TEXT_PRIMARY))
            self.send_data.emit(b'\x0C') 
            return

        if event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_W:
            self.send_data.emit(b'\x17')
            return

        if event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_X:
            self.send_data.emit(b'\x18')
            return

        if event.modifiers() & (Qt.ControlModifier | Qt.AltModifier):
            return

        text = event.text()
        key = event.key()

        if key == Qt.Key_Return or key == Qt.Key_Enter:
            self.send_data.emit(b'\r')
        elif key == Qt.Key_Backspace:
            self.send_data.emit(b'\x08') 
        elif key == Qt.Key_Up:
            self.send_data.emit(b'\x1b[A')
        elif key == Qt.Key_Down:
            self.send_data.emit(b'\x1b[B')
        elif key == Qt.Key_Right:
            self.send_data.emit(b'\x1b[C')
        elif key == Qt.Key_Left:
            self.send_data.emit(b'\x1b[D')
        elif text:
            self.send_data.emit(text.encode('utf-8'))
            
        sb = self.verticalScrollBar()
        sb.setValue(sb.maximum())

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.moveCursor(QTextCursor.End)


# ==========================================
# WORKER SERIAL (Upload de Kernel + Monitor)
# ==========================================
class SerialMonitorWorker(QThread):
    log_msg = pyqtSignal(str, str)
    rx_data = pyqtSignal(str)
    os_status = pyqtSignal(str, str)
    finished = pyqtSignal()

    def __init__(self, port, baud, payload):
        super().__init__()
        self.port = port
        self.baud = baud
        self.payload = payload
        self.ser = None
        self.running = True
        self.to_send = b''
        self.rx_buffer = ""

    def send_data(self, data: bytes):
        self.to_send += data

    def run(self):
        try:
            self.log_msg.emit(f"Conectando em {self.port} ({self.baud} baud)...", "info")
            self.ser = serial.Serial(self.port, self.baud, rtscts=False, dsrdtr=False, timeout=0.05)
            
            self.ser.rts = False
            time.sleep(0.1)
            self.ser.write(b'\xCA\xFE\xBA\xBE')
            time.sleep(0.05)
            self.ser.write(b'\x09\x00\x00\x00\x00')
            time.sleep(0.01)
            self.ser.write(b'\x08')
            time.sleep(0.05)
            self.ser.rts = True

            self.log_msg.emit("Aguardando sinal do Bootloader da FPGA...", "info")
            buffer = ""
            start_wait = time.time()
            boot_found = False
            while time.time() - start_wait < 4.0 and self.running:
                if self.ser.in_waiting:
                    buffer += self.ser.read(self.ser.in_waiting).decode('utf-8', 'ignore')
                    if "BOOT" in buffer:
                        boot_found = True
                        break
            
            if not boot_found:
                self.log_msg.emit("Timeout aguardando 'BOOT'. Iniciando monitor passivo.", "error")
            else:
                # CORREÇÃO CRÍTICA: Limpa o lixo e o "\r\n" do "BOOT\r\n" antes de iniciar o Handshake
                time.sleep(0.05)
                self.ser.reset_input_buffer()
                
                self.ser.write(b'\xCA\xFE\xBA\xBE')
                ack = b''
                start_wait = time.time()
                while time.time() - start_wait < 2.0 and self.running:
                    if self.ser.in_waiting:
                        ack = self.ser.read(1)
                        if ack == b'!': break
                
                if ack == b'!':
                    size = len(self.payload)
                    self.log_msg.emit(f"Handshake OK! Transferindo kernel.bin ({size} bytes)...", "info")
                    self.ser.write(struct.pack('<I', size))
                    time.sleep(0.05)
                    
                    for i in range(0, size, 64):
                        if not self.running: break
                        self.ser.write(self.payload[i:i+64])
                        time.sleep(0.002)
                    
                    self.log_msg.emit("Upload finalizado! SO Inicializando...", "success")
                else:
                    self.log_msg.emit("Falha no Handshake. Inicialização abortada.", "error")
                    return

            # --- LOOP DO MONITOR ---
            while self.running:
                if self.ser.in_waiting:
                    raw = self.ser.read(self.ser.in_waiting)
                    text = raw.decode('utf-8', errors='replace') 
                    self.rx_buffer += text
                    
                    while '\x1b7' in self.rx_buffer and '\x1b8' in self.rx_buffer:
                        start = self.rx_buffer.find('\x1b7')
                        end = self.rx_buffer.find('\x1b8')
                        
                        if start < end:
                            block = self.rx_buffer[start+2:end]
                            self.rx_buffer = self.rx_buffer[:start] + self.rx_buffer[end+2:]
                            
                            if 'Uptime' in block: self.os_status.emit('uptime', block)
                            if '[LED:' in block: self.os_status.emit('led', block)
                        else:
                            self.rx_buffer = self.rx_buffer.replace('\x1b8', '', 1)

                    start_7 = self.rx_buffer.find('\x1b7')
                    if start_7 >= 0:
                        safe_text = self.rx_buffer[:start_7]
                        if safe_text:
                            self.rx_data.emit(safe_text)
                        self.rx_buffer = self.rx_buffer[start_7:]
                        if len(self.rx_buffer) > 512: 
                            self.rx_data.emit(self.rx_buffer)
                            self.rx_buffer = ""
                    else:
                        match = re.search(r'\x1b\[[0-9;?]*$|\x1b[()]$|\x1b$', self.rx_buffer)
                        if match:
                            cut = match.start()
                            safe_text = self.rx_buffer[:cut]
                            if safe_text:
                                self.rx_data.emit(safe_text)
                            self.rx_buffer = self.rx_buffer[cut:]
                            if len(self.rx_buffer) > 128:
                                self.rx_data.emit(self.rx_buffer)
                                self.rx_buffer = ""
                        else:
                            if self.rx_buffer:
                                self.rx_data.emit(self.rx_buffer)
                                self.rx_buffer = ""
                
                if self.to_send:
                    for byte in self.to_send:
                        self.ser.write(bytes([byte]))
                        time.sleep(0.002)
                    self.to_send = b''
                    
                time.sleep(0.01)

        except Exception as e:
            self.log_msg.emit(f"Erro Serial: {str(e)}", "error")
        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.finished.emit()

    def stop(self):
        self.running = False


# ==========================================
# WIDGET PRINCIPAL
# ==========================================
class OSConsoleWidget(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        self.conn_mgr = ConnectionManager()
        self.target_port = self.conn_mgr.get_port()
        self.target_baud = self.conn_mgr.get_baud()

        terminal_panel = QFrame()
        terminal_panel.setStyleSheet(f"background-color: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 8px;")
        terminal_layout = QVBoxLayout(terminal_panel)
        terminal_layout.setContentsMargins(0, 0, 0, 0)
        terminal_layout.setSpacing(0)

        term_header = QFrame()
        term_header.setFixedHeight(32)
        term_header.setStyleSheet(f"background-color: #050608; border-bottom: 1px solid {BORDER}; border-radius: 8px 8px 0 0;")
        term_h_layout = QHBoxLayout(term_header)
        term_h_layout.setContentsMargins(15, 0, 10, 0)
        term_h_layout.setSpacing(8)

        lbl_term_title = QLabel("TERMINAL")
        lbl_term_title.setStyleSheet(f"color: {TEXT_SECONDARY}; font-family: 'Consolas', 'JetBrains Mono', monospace; font-weight: bold; font-size: 11px; letter-spacing: 1px; border: none;")
        term_h_layout.addWidget(lbl_term_title)
        
        term_h_layout.addStretch()

        self.lbl_status_dot = QLabel("●")
        self.lbl_status_dot.setStyleSheet(f"color: {RED}; font-size: 12px; border: none; padding-bottom: 2px;") 

        self.lbl_status_text = QLabel("OFFLINE")
        self.lbl_status_text.setStyleSheet(f"color: {TEXT_SECONDARY}; font-family: 'Consolas', 'JetBrains Mono', monospace; font-weight: bold; font-size: 11px; border: none;")
        
        term_h_layout.addWidget(self.lbl_status_dot)
        term_h_layout.addWidget(self.lbl_status_text)
        
        spacer_label = QLabel(" ")
        spacer_label.setFixedWidth(5)
        spacer_label.setStyleSheet("border: none; background: transparent;")
        term_h_layout.addWidget(spacer_label)
        
        self.btn_disconnect = QPushButton()
        self.btn_disconnect.setIcon(qta.icon('fa5s.times', color=TEXT_SECONDARY))
        self.btn_disconnect.setCursor(Qt.PointingHandCursor)
        self.btn_disconnect.setFixedSize(24, 24)
        self.btn_disconnect.setToolTip("Disconnect")
        self.btn_disconnect.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {hex_to_rgba(RED, 0.2)};
            }}
        """)
        self.btn_disconnect.clicked.connect(self.disconnect_serial)
        self.btn_disconnect.hide()
        term_h_layout.addWidget(self.btn_disconnect)

        terminal_layout.addWidget(term_header)
        self.term_stack = QStackedWidget()
        
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

        page_console = QWidget()
        console_layout = QVBoxLayout(page_console)
        console_layout.setContentsMargins(0,0,0,0)
        console_layout.setSpacing(0)

        self.os_status_bar = QFrame()
        self.os_status_bar.setFixedHeight(34)
        self.os_status_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_ELEMENT}; 
                border-bottom: 1px solid {BORDER};
            }}
        """)
        status_layout = QHBoxLayout(self.os_status_bar)
        status_layout.setContentsMargins(15, 0, 15, 0)

        self.gui_lbl_uptime = QLabel("<span style='color: #8B9BB4;'>Uptime:</span> <span style='color: #6CA1A2; font-weight: bold;'>--:--</span>")
        self.gui_lbl_uptime.setStyleSheet(f"font-family: 'Consolas', 'JetBrains Mono', monospace; font-size: 13px; border: none; background: transparent;")

        self.gui_lbl_leds = QLabel(f"<span style='color: #8B9BB4;'>LED:</span> <span style='color: {BORDER}; font-size: 16px;'>●</span>")
        self.gui_lbl_leds.setStyleSheet(f"font-family: 'Consolas', 'JetBrains Mono', monospace; font-size: 13px; border: none; background: transparent;")

        status_layout.addWidget(self.gui_lbl_uptime)
        status_layout.addStretch()
        status_layout.addWidget(self.gui_lbl_leds)
        console_layout.addWidget(self.os_status_bar)

        self.console_output = TerminalConsole()
        console_layout.addWidget(self.console_output)

        self.term_stack.addWidget(page_console)
        terminal_layout.addWidget(self.term_stack)
        
        main_layout.addWidget(terminal_panel, stretch=3)

        sidebar_layout = QVBoxLayout()
        sidebar_layout.setSpacing(20)

        macros_panel = QFrame()
        macros_panel.setStyleSheet(f"background-color: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 8px;")
        m_layout = QVBoxLayout(macros_panel)
        m_layout.setContentsMargins(15, 15, 15, 15)
        
        lbl_m_title = QLabel("QUICK MACROS")
        lbl_m_title.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: bold; font-size: 11px; border: none; margin-bottom: 10px;")
        m_layout.addWidget(lbl_m_title)

        self.macro_buttons = []
        
        macros = [
            (" Help", 'fa5s.question-circle', "help"),
            (" Clear", 'fa5s.broom', "clear"),
            (" Process Status", 'fa5s.list', "ps"),
            (" Heap Usage", 'fa5s.memory', "heap"),
            (" Defrag Heap", 'fa5s.compress-arrows-alt', "defrag"),
            (" Trigger Panic", 'fa5s.bug', "panic"),
            (" Reboot OS", 'fa5s.sync', "reboot")
        ]

        for text, icon, cmd in macros:
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
            btn.clicked.connect(lambda _, c=cmd: self.send_macro(c))
            self.macro_buttons.append(btn)
            m_layout.addWidget(btn)

        sidebar_layout.addWidget(macros_panel)

        settings_panel = QFrame()
        settings_panel.setStyleSheet(f"background-color: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 8px;")
        s_layout = QVBoxLayout(settings_panel)
        s_layout.setContentsMargins(15, 15, 15, 15)
        
        lbl_s_title = QLabel("CONNECTION SETTINGS")
        lbl_s_title.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: bold; font-size: 11px; border: none; margin-bottom: 10px;")
        s_layout.addWidget(lbl_s_title)

        grid = QGridLayout()
        grid.setVerticalSpacing(10)

        self.lbl_set_port = QLabel(self.target_port)
        self.lbl_set_port.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 12px; font-weight: bold; border: none;")
        self.lbl_set_port.setAlignment(Qt.AlignRight)

        self.lbl_set_baud = QLabel(str(self.target_baud))
        self.lbl_set_baud.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 12px; font-weight: bold; border: none;")
        self.lbl_set_baud.setAlignment(Qt.AlignRight)

        lbl_k_port = QLabel("Port")
        lbl_k_port.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; border: none;")
        grid.addWidget(lbl_k_port, 0, 0)
        grid.addWidget(self.lbl_set_port, 0, 1)

        lbl_k_baud = QLabel("Baud")
        lbl_k_baud.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; border: none;")
        grid.addWidget(lbl_k_baud, 1, 0)
        grid.addWidget(self.lbl_set_baud, 1, 1)

        static_settings = [
            ("Data", "8 bits"),
            ("Parity", "None"),
            ("Stop", "1 bit")
        ]
        
        for row, (k, v) in enumerate(static_settings, start=2):
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

        # CORREÇÃO: Inscreve este widget no evento de atualização global do ConnectionManager
        self.conn_mgr.config_updated.connect(self.update_connection_params)
        self.worker = None

    # CORREÇÃO: Função dinâmica para atualizar as variáveis e o painel de texto ao mudar a configuração global
    def update_connection_params(self, port, baud):
        self.target_port = port
        self.target_baud = baud
        self.lbl_set_port.setText(port)
        self.lbl_set_baud.setText(str(baud))

    def connect_serial(self):
        # CORREÇÃO ADICIONAL: Garante que lê as configurações mais recentes imediatamente antes de abrir a porta
        self.target_port = self.conn_mgr.get_port()
        self.target_baud = self.conn_mgr.get_baud()
        self.update_connection_params(self.target_port, self.target_baud)

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        kernel_path = os.path.join(base_dir, "artefacts", "kernel.bin")
        
        payload = b''
        if os.path.exists(kernel_path):
            with open(kernel_path, 'rb') as f:
                payload = f.read()
        else:
            cursor = self.console_output.textCursor()
            fmt = cursor.charFormat()
            fmt.setForeground(QColor(RED))
            cursor.setCharFormat(fmt)
            cursor.insertText(f"[ERRO] kernel.bin não encontrado em: {kernel_path}\n")
            return

        self.console_output.clear()
        self.term_stack.setCurrentIndex(1)
        
        self.lbl_status_dot.setStyleSheet(f"color: {GREEN}; font-size: 12px; border: none; padding-bottom: 2px;")
        self.lbl_status_text.setText("CONNECTED")
        self.lbl_status_text.setStyleSheet(f"color: {GREEN}; font-family: 'Consolas', 'JetBrains Mono', monospace; font-weight: bold; font-size: 11px; border: none;")
        self.btn_disconnect.show()
        
        self.gui_lbl_uptime.setText(f"<span style='color: {TEXT_SECONDARY};'>Uptime:</span> <span style='color: {TEAL}; font-weight: bold;'>00:00</span>")
        self.gui_lbl_leds.setText(f"<span style='color: {TEXT_SECONDARY};'>LED:</span> <span style='color: {BORDER}; font-size: 16px;'>●</span>")

        for btn in self.macro_buttons:
            btn.setEnabled(True)

        self.worker = SerialMonitorWorker(port=self.target_port, baud=self.target_baud, payload=payload)
        self.worker.log_msg.connect(self.display_sys_log)
        self.worker.rx_data.connect(self.append_terminal_text)
        self.worker.os_status.connect(self.update_gui_status)
        self.worker.finished.connect(self.on_worker_finished)
        
        self.console_output.send_data.connect(self.worker.send_data)
        self.worker.start()
        
        self.console_output.setFocus()
        self.console_output.moveCursor(QTextCursor.End)

    def disconnect_serial(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait()
            self.worker = None

        self.term_stack.setCurrentIndex(0)
        
        self.lbl_status_dot.setStyleSheet(f"color: {RED}; font-size: 12px; border: none; padding-bottom: 2px;")
        self.lbl_status_text.setText("OFFLINE")
        self.lbl_status_text.setStyleSheet(f"color: {TEXT_SECONDARY}; font-family: 'Consolas', 'JetBrains Mono', monospace; font-weight: bold; font-size: 11px; border: none;")
        self.btn_disconnect.hide()
        
        for btn in self.macro_buttons:
            btn.setEnabled(False)

    def on_worker_finished(self):
        self.disconnect_serial()

    def send_macro(self, cmd):
        if self.worker and self.worker.running:
            self.worker.send_data(f"{cmd}\r\n".encode('utf-8'))
            self.console_output.setFocus()

    def display_sys_log(self, msg, msg_type):
        color = GREEN if msg_type == "success" else RED if msg_type == "error" else MUSTARD
        cursor = self.console_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = cursor.charFormat()
        fmt.setForeground(QColor(color))
        cursor.setCharFormat(fmt)
        cursor.insertText(f"[SISTEMA] {msg}\n")
        self.scroll_to_bottom()

    def update_gui_status(self, stat_type, raw_ansi):
        clean_text = re.sub(r'\x1b\[[0-9;?]*[A-Za-z]', '', raw_ansi)
        clean_text = re.sub(r'\x1b[()][A-Za-z0-9]', '', clean_text)
        clean_text = clean_text.replace('\r', '').replace('\n', '').replace('\x00', '').strip()
        
        if stat_type == 'uptime':
            time_str = clean_text.replace('Uptime: ', '').replace('Uptime:', '').strip()
            self.gui_lbl_uptime.setText(f"<span style='color: {TEXT_SECONDARY};'>Uptime:</span> <span style='color: {TEAL}; font-weight: bold;'>{time_str}</span>")
            
        elif stat_type == 'led':
            if '*' in clean_text:
                self.gui_lbl_leds.setText(f"<span style='color: {TEXT_SECONDARY};'>LED:</span> <span style='color: {GREEN}; font-size: 16px;'>●</span>")
            else:
                self.gui_lbl_leds.setText(f"<span style='color: {TEXT_SECONDARY};'>LED:</span> <span style='color: {BORDER}; font-size: 16px;'>●</span>")

    def append_terminal_text(self, text):
        cleared = False
        
        if '\x1b[2J' in text:
            self.console_output.clear()
            self.console_output.setTextColor(QColor(TEXT_PRIMARY))
            self.console_output.setFontWeight(QFont.Normal)
            text = text.split('\x1b[2J')[-1]
            cleared = True

        text = text.replace('\x1b[H', '').replace('\x1b[1;1H', '')
        text = text.replace('\x1b7', '').replace('\x1b8', '') 
        text = re.sub(r'\x1b\[[suK]', '', text)
        text = re.sub(r'\x1b\[[0-9;?]*[a-ln-zA-Z]', '', text)
        text = re.sub(r'\x1b[()][A-Za-z0-9]', '', text)

        if not text:
            return

        cursor = self.console_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        fmt = cursor.charFormat()
        if cleared:
            fmt.setForeground(QColor(TEXT_PRIMARY))
            fmt.setFontWeight(QFont.Normal)

        parts = re.split(r'(\x1b\[[\d;]*m)', text)

        for part in parts:
            if part.startswith('\x1b['):
                codes = part[2:-1].split(';')
                color = TEXT_PRIMARY
                weight = QFont.Normal

                for c in codes:
                    if c in ('0', ''): 
                        color = TEXT_PRIMARY
                        weight = QFont.Normal
                    elif c == '1': weight = QFont.Bold
                    elif c == '31': color = RED
                    elif c == '32': color = GREEN
                    elif c == '33': color = MUSTARD
                    elif c == '34': color = BLUE
                    elif c == '35': color = PURPLE
                    elif c == '36': color = TEAL
                    elif c == '37': color = TEXT_PRIMARY

                fmt.setForeground(QColor(color))
                fmt.setFontWeight(weight)
            else:
                if part:
                    cursor.setCharFormat(fmt)
                    clean_part = part.replace('\r\n', '\n').replace('\r', '')
                    
                    for char in clean_part:
                        if char in ('\b', '\x08', '\x7f'):
                            cursor.deletePreviousChar()
                        else:
                            cursor.insertText(char)

        self.console_output.setTextCursor(cursor)
        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        sb = self.console_output.verticalScrollBar()
        sb.setValue(sb.maximum())

    def hideEvent(self, event):
        self.disconnect_serial()
        super().hideEvent(event)

    def closeEvent(self, event):
        self.disconnect_serial()
        super().closeEvent(event)