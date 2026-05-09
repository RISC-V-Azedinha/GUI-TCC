# ui/nn_widget.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QFrame, QGridLayout, QProgressBar, QGraphicsDropShadowEffect, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QTimer
from PyQt5.QtGui import QPainter, QPen, QImage, QColor, QPixmap, QFont
import qtawesome as qta
import time
import numpy as np
from PIL import Image

# Importando a Thread de Treinamento extraída
from core.nn_worker import HardwareTrainerThread

# ==========================================
# PALETA CYBERPUNK / NEON
# ==========================================
BG_MAIN = "#0A0A0F"
BG_PANEL = "#0A0A0F"
BG_ELEMENT = "#1A1D27"
BORDER = "#2A2F3A"
TEXT_PRIMARY = "#FFFFFF"
TEXT_SECONDARY = "#8B9BB4"

NEON_CYAN = "#3b82f6"
NEON_GREEN = "#5DB373"
NEON_PURPLE = "#B14AED"
NEON_RED = "#EF4444"
NEON_YELLOW = "#F59E0B"

def hex_to_rgba(hex_color, alpha=0.2):
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"

def add_neon_glow(widget, color_hex, blur_radius=30):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur_radius)
    shadow.setXOffset(0)
    shadow.setYOffset(0)
    shadow.setColor(QColor(color_hex))
    widget.setGraphicsEffect(shadow)

# ==========================================
# COMPONENTES VISUAIS DA UI
# ==========================================
class NPUCoreWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedSize(160, 160)
        self.setObjectName("NPUCore")
        self.set_idle()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)

        self.icon_lbl = QLabel()
        self.icon_lbl.setStyleSheet("background: transparent; border: none;")
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_lbl)

        texts = QVBoxLayout()
        texts.setSpacing(2)
        self.lbl_title = QLabel("NPU Core\n(4x4 Systolic)")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setStyleSheet(f"background: transparent; color: {NEON_PURPLE}; font-weight: bold; font-size: 12px;")
        texts.addWidget(self.lbl_title)

        self.lbl_status = QLabel("OFFLINE")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet(f"background: transparent; color: {TEXT_SECONDARY}; font-weight: 800; font-size: 11px; letter-spacing: 1px;")
        texts.addWidget(self.lbl_status)
        layout.addLayout(texts)

    def set_idle(self):
        self.setStyleSheet(f"#NPUCore {{ background-color: transparent; border: 2px dashed {BORDER}; border-radius: 16px; }}")
        if hasattr(self, 'icon_lbl'):
            self.icon_lbl.setPixmap(qta.icon('fa5s.microchip', color=TEXT_SECONDARY).pixmap(48, 48))
            self.lbl_title.setStyleSheet(f"background: transparent; color: {TEXT_SECONDARY}; font-weight: bold; font-size: 12px;")
            self.lbl_status.setText("OFFLINE")
            self.lbl_status.setStyleSheet(f"background: transparent; color: {TEXT_SECONDARY}; font-weight: 800; font-size: 11px; letter-spacing: 1px;")
        self.setGraphicsEffect(None)

    def set_ready(self):
        self.setStyleSheet(f"#NPUCore {{ background-color: {hex_to_rgba(NEON_PURPLE, 0.05)}; border: 2px dashed {NEON_PURPLE}; border-radius: 16px; }}")
        self.icon_lbl.setPixmap(qta.icon('fa5s.microchip', color=NEON_PURPLE).pixmap(48, 48))
        self.lbl_title.setStyleSheet(f"background: transparent; color: {NEON_PURPLE}; font-weight: bold; font-size: 12px;")
        self.lbl_status.setText("IDLE / READY")
        self.lbl_status.setStyleSheet(f"background: transparent; color: {NEON_PURPLE}; font-weight: 800; font-size: 11px; letter-spacing: 1px;")
        add_neon_glow(self, hex_to_rgba(NEON_PURPLE, 0.3), 20)

    def set_processing(self):
        self.setStyleSheet(f"#NPUCore {{ background-color: {hex_to_rgba(NEON_CYAN, 0.05)}; border: 2px dashed {NEON_CYAN}; border-radius: 16px; }}")
        self.icon_lbl.setPixmap(qta.icon('fa5s.microchip', color=NEON_CYAN).pixmap(48, 48))
        self.lbl_title.setStyleSheet(f"background: transparent; color: {NEON_CYAN}; font-weight: bold; font-size: 12px;")
        self.lbl_status.setText("PROCESSING...")
        self.lbl_status.setStyleSheet(f"background: transparent; color: {NEON_CYAN}; font-weight: 900; font-size: 11px; letter-spacing: 1px;")
        add_neon_glow(self, hex_to_rgba(NEON_CYAN, 0.6), 25)

class DrawingBoard(QWidget):
    drawing_started = pyqtSignal()
    drawing_updated = pyqtSignal(QImage)
    drawing_finished = pyqtSignal(QImage)

    def __init__(self, size=420):
        super().__init__()
        self.setFixedSize(size, size)
        self.setCursor(Qt.CrossCursor)
        self.image = QImage(self.size(), QImage.Format_ARGB32)
        self.image.fill(Qt.transparent)
        self.drawing = False
        self.last_point = QPoint()

        self.sample_timer = QTimer()
        self.sample_timer.timeout.connect(self.emit_update)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.last_point = event.pos()
            self.drawing_started.emit()
            self.sample_timer.start(150)

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.LeftButton) and self.drawing:
            painter = QPainter(self.image)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setPen(QPen(QColor(NEON_CYAN), 32, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawLine(self.last_point, event.pos())
            self.last_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False
            self.sample_timer.stop()
            self.drawing_finished.emit(self.image)

    def emit_update(self):
        if self.drawing:
            self.drawing_updated.emit(self.image)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        # Se estiver desabilitado, desenha um fundo mais escuro
        bg_color = BG_ELEMENT if self.isEnabled() else BG_MAIN
        painter.fillRect(self.rect(), QColor(bg_color))
        
        painter.setPen(QPen(QColor(BORDER), 1, Qt.SolidLine))
        step = 35
        for x in range(0, self.width(), step): painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), step): painter.drawLine(0, y, self.width(), y)
        
        painter.setPen(QPen(QColor(BORDER), 2, Qt.SolidLine))
        painter.drawRect(0, 0, self.width()-1, self.height()-1)
        painter.drawImage(self.rect(), self.image, self.image.rect())

    def clear_board(self):
        self.image.fill(Qt.transparent)
        self.update()


class NNWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.driver = None 
        
        font = QFont("Segoe UI", 10)
        font.setStyleHint(QFont.SansSerif)
        self.setFont(font)
        self.setStyleSheet(f"background-color: {BG_MAIN};")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 20)
        main_layout.setSpacing(25)

        # =========================================================
        # CABEÇALHO COM CONTROLES DA FPGA E LOADING
        # =========================================================
        header = QHBoxLayout()
        title_icon = QLabel()
        title_icon.setPixmap(qta.icon('fa5s.network-wired', color=NEON_PURPLE).pixmap(28, 28))
        title_icon.setStyleSheet("background: transparent; border: none;")
        header.addWidget(title_icon)
        
        title_texts = QVBoxLayout()
        title_texts.setSpacing(2)
        lbl_title = QLabel("Neural Network Inference (MNIST)")
        lbl_title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {TEXT_PRIMARY}; background: transparent;")
        lbl_sub = QLabel("Treino Local (PyTorch) + Aceleração em Hardware (SoC RISC-V)")
        lbl_sub.setStyleSheet(f"font-size: 13px; color: {TEXT_SECONDARY}; font-weight: 500; background: transparent;")
        title_texts.addWidget(lbl_title)
        title_texts.addWidget(lbl_sub)
        header.addLayout(title_texts)
        header.addStretch()

        # BARRA DE LOADING
        self.loading_bar = QProgressBar()
        self.loading_bar.setRange(0, 0) # Indeterminado para animação contínua
        self.loading_bar.setFixedWidth(150)
        self.loading_bar.setFixedHeight(8)
        self.loading_bar.setTextVisible(False)
        self.loading_bar.setStyleSheet(f"""
            QProgressBar {{ border: none; border-radius: 4px; background-color: {BG_ELEMENT}; }} 
            QProgressBar::chunk {{ background-color: {NEON_YELLOW}; border-radius: 4px; }}
        """)
        self.loading_bar.setVisible(False)
        header.addWidget(self.loading_bar)

        # INPUT E BOTÃO DE HARDWARE
        self.inp_port = QLineEdit("/dev/ttyUSB1")
        self.inp_port.setFixedWidth(130)
        self.inp_port.setStyleSheet(f"background-color: {BG_ELEMENT}; border: 1px solid {BORDER}; border-radius: 4px; color: {NEON_CYAN}; padding: 6px; font-family: monospace; font-weight: bold;")
        header.addWidget(self.inp_port)

        self.btn_hw = QPushButton(" Programar FPGA") 
        self.btn_hw.setIcon(qta.icon('fa5s.microchip', color=BG_ELEMENT))
        self.btn_hw.setStyleSheet(f"background-color: {NEON_GREEN}; color: {BG_ELEMENT}; border-radius: 6px; padding: 8px 16px; font-weight: bold;")
        self.btn_hw.setCursor(Qt.PointingHandCursor)
        self.btn_hw.clicked.connect(self.start_training)
        header.addWidget(self.btn_hw)
        
        main_layout.addLayout(header)

        # =========================================================
        # ÁREA CENTRAL
        # =========================================================
        workspace = QHBoxLayout()
        workspace.setSpacing(40)

        # --- PAINEL ESQUERDO ---
        self.left_panel = QFrame()
        self.left_panel.setObjectName("PanelEsquerdo")
        self.left_panel.setStyleSheet(f"#PanelEsquerdo {{ background-color: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 12px; }}")
        add_neon_glow(self.left_panel, hex_to_rgba(NEON_CYAN, 0.1), 40)
        
        l_layout = QVBoxLayout(self.left_panel)
        l_layout.setAlignment(Qt.AlignCenter)
        l_layout.setSpacing(20)
        l_layout.setContentsMargins(30, 30, 30, 30)

        draw_header_layout = QHBoxLayout()
        draw_header_layout.setAlignment(Qt.AlignCenter)
        draw_header_layout.setSpacing(8)
        
        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon('fa5s.pen', color=TEXT_SECONDARY).pixmap(14, 14))
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        
        lbl_draw = QLabel("ENTRADA DE DESENHO (0-9)")
        lbl_draw.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; font-weight: 700; letter-spacing: 1px; background: transparent;")
        
        draw_header_layout.addWidget(icon_lbl)
        draw_header_layout.addWidget(lbl_draw)
        l_layout.addLayout(draw_header_layout)

        self.board = DrawingBoard(size=420)
        self.board.drawing_started.connect(self.on_draw_start)
        self.board.drawing_updated.connect(self.on_draw_update)
        self.board.drawing_finished.connect(self.on_draw_finish)
        l_layout.addWidget(self.board, alignment=Qt.AlignCenter)

        self.btn_clear = QPushButton(" LIMPAR LOUSA")
        self.btn_clear.setIcon(qta.icon('fa5s.eraser', color=NEON_PURPLE))
        self.btn_clear.setFixedSize(420, 48)
        self.btn_clear.setStyleSheet(f"""
            QPushButton {{ background-color: {hex_to_rgba(NEON_PURPLE, 0.1)}; color: {NEON_PURPLE}; border: 1px solid {hex_to_rgba(NEON_PURPLE, 0.3)}; border-radius: 6px; font-size: 13px; font-weight: bold; letter-spacing: 1px; }}
            QPushButton:hover {{ background-color: {hex_to_rgba(NEON_PURPLE, 0.2)}; border: 1px solid {NEON_PURPLE}; }}
            QPushButton:disabled {{ background-color: {BG_ELEMENT}; color: {BORDER}; border: 1px solid {BORDER}; }}
        """)
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.clicked.connect(self.clear_ui)
        l_layout.addWidget(self.btn_clear, alignment=Qt.AlignCenter)

        workspace.addWidget(self.left_panel, stretch=1)

        # --- PAINEL DIREITO ---
        self.right_panel = QFrame()
        self.right_panel.setObjectName("PanelDireito")
        self.right_panel.setStyleSheet(f"#PanelDireito {{ background-color: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 12px; }}")
        add_neon_glow(self.right_panel, hex_to_rgba(NEON_CYAN, 0.1), 40)
        
        r_layout = QVBoxLayout(self.right_panel)
        r_layout.setContentsMargins(40, 30, 40, 30)
        r_layout.setSpacing(25)

        top_r_layout = QHBoxLayout()
        top_r_layout.setSpacing(30)
        top_r_layout.setAlignment(Qt.AlignCenter)

        npu_view_container = QVBoxLayout()
        npu_view_container.setAlignment(Qt.AlignCenter)
        lbl_npu_in = QLabel("VISÃO DA NPU (28x28)")
        lbl_npu_in.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; font-weight: 700; letter-spacing: 1px; background: transparent;")
        lbl_npu_in.setAlignment(Qt.AlignCenter)
        npu_view_container.addWidget(lbl_npu_in)

        self.lbl_npu_preview = QLabel()
        self.lbl_npu_preview.setFixedSize(140, 140) 
        self.lbl_npu_preview.setObjectName("PreviewNPU")
        self.lbl_npu_preview.setStyleSheet(f"#PreviewNPU {{ background-color: {BG_ELEMENT}; border: 1px solid {BORDER}; border-radius: 8px; }}")
        self.lbl_npu_preview.setAlignment(Qt.AlignCenter)
        npu_view_container.addWidget(self.lbl_npu_preview)
        
        top_r_layout.addLayout(npu_view_container)

        arrow_lbl = QLabel()
        arrow_lbl.setPixmap(qta.icon('fa5s.arrow-right', color=BORDER).pixmap(24, 24))
        arrow_lbl.setStyleSheet("background: transparent; border: none;")
        top_r_layout.addWidget(arrow_lbl)

        self.npu_core = NPUCoreWidget()
        top_r_layout.addWidget(self.npu_core)
        r_layout.addLayout(top_r_layout)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"border: none; background-color: {BORDER}; max-height: 1px;")
        r_layout.addWidget(line)

        bottom_h_layout = QHBoxLayout()
        bottom_h_layout.setSpacing(40)

        # Círculo de Previsão
        pred_layout = QVBoxLayout()
        pred_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter) 
        lbl_pred_title = QLabel("PREVISÃO")
        lbl_pred_title.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; font-weight: 700; background: transparent;")
        lbl_pred_title.setAlignment(Qt.AlignCenter)
        pred_layout.addWidget(lbl_pred_title)
        pred_layout.addSpacing(15)

        self.pred_circle = QFrame()
        self.pred_circle.setFixedSize(140, 140)
        self.pred_circle.setStyleSheet(f"background-color: {hex_to_rgba(BORDER, 0.2)}; border: 3px solid {BORDER}; border-radius: 70px;")
        circle_layout = QVBoxLayout(self.pred_circle)
        self.lbl_prediction = QLabel("?")
        self.lbl_prediction.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 72px; font-weight: 900; background: transparent; border: none;")
        self.lbl_prediction.setAlignment(Qt.AlignCenter)
        circle_layout.addWidget(self.lbl_prediction)
        
        pred_layout.addWidget(self.pred_circle, alignment=Qt.AlignCenter)
        bottom_h_layout.addLayout(pred_layout)

        # Barras de Confiança
        bars_layout = QVBoxLayout()
        bars_layout.setAlignment(Qt.AlignTop) 
        lbl_conf_title = QLabel("CONFIANÇA")
        lbl_conf_title.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; font-weight: 700; background: transparent;")
        lbl_conf_title.setAlignment(Qt.AlignCenter)
        bars_layout.addWidget(lbl_conf_title)
        bars_layout.addSpacing(15)

        conf_container = QWidget()
        conf_container.setStyleSheet("background: transparent;")
        conf_grid = QGridLayout(conf_container)
        conf_grid.setContentsMargins(0, 0, 0, 0)
        conf_grid.setVerticalSpacing(8)
        conf_grid.setHorizontalSpacing(10)
        
        self.conf_bars = []
        for i in range(10):
            lbl_digit = QLabel(str(i))
            lbl_digit.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: 800; font-size: 14px; background: transparent;")
            lbl_digit.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            bar = QProgressBar()
            bar.setRange(0, 1000)
            bar.setValue(0)
            bar.setTextVisible(False)
            bar.setFixedHeight(8)
            bar.setStyleSheet(f"QProgressBar {{ border: none; border-radius: 4px; background-color: {BG_ELEMENT}; }} QProgressBar::chunk {{ background-color: {BORDER}; border-radius: 4px; }}")
            
            lbl_pct = QLabel("0.0%")
            lbl_pct.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: bold; font-size: 11px; background: transparent;")
            lbl_pct.setFixedWidth(40)
            lbl_pct.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            conf_grid.addWidget(lbl_digit, i, 0)
            conf_grid.addWidget(bar, i, 1)
            conf_grid.addWidget(lbl_pct, i, 2)
            self.conf_bars.append((lbl_digit, bar, lbl_pct))

        bars_layout.addWidget(conf_container)
        bottom_h_layout.addLayout(bars_layout)
        
        r_layout.addLayout(bottom_h_layout)
        workspace.addWidget(self.right_panel, stretch=1)
        main_layout.addLayout(workspace)

        # BARRA DE STATUS MELHORADA
        status_bar = QHBoxLayout()
        self.lbl_status = QLabel("Aguardando configuração. Pressione 'Programar FPGA' para enviar o SW e os pesos da NPU.")
        self.lbl_status.setObjectName("StatusBarText")
        self.lbl_status.setStyleSheet(f"""
            #StatusBarText {{
                color: {NEON_YELLOW}; 
                font-size: 14px; 
                font-weight: bold; 
                letter-spacing: 1px; 
                background: {BG_ELEMENT};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 10px;
            }}
        """)
        status_bar.addWidget(self.lbl_status, alignment=Qt.AlignCenter)
        main_layout.addLayout(status_bar)

        # TRAVAR INTERFACE INICIALMENTE
        self.lock_interface()

    # -------------------------------------------------------------
    # GERENCIAMENTO DE ESTADO DA INTERFACE
    # -------------------------------------------------------------
    def lock_interface(self):
        """Desabilita a interação até a FPGA ser configurada."""
        self.board.setEnabled(False)
        self.btn_clear.setEnabled(False)
        self.left_panel.setStyleSheet(f"#PanelEsquerdo {{ background-color: {BG_MAIN}; border: 1px solid {BORDER}; border-radius: 12px; }}")
        self.left_panel.setGraphicsEffect(None)
        
        self.right_panel.setStyleSheet(f"#PanelDireito {{ background-color: {BG_MAIN}; border: 1px solid {BORDER}; border-radius: 12px; }}")
        self.right_panel.setGraphicsEffect(None)

    def unlock_interface(self):
        """Libera a interface para desenho e inferência real."""
        self.board.setEnabled(True)
        self.btn_clear.setEnabled(True)
        
        self.left_panel.setStyleSheet(f"#PanelEsquerdo {{ background-color: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 12px; }}")
        add_neon_glow(self.left_panel, hex_to_rgba(NEON_CYAN, 0.1), 40)
        
        self.right_panel.setStyleSheet(f"#PanelDireito {{ background-color: {BG_PANEL}; border: 1px solid {BORDER}; border-radius: 12px; }}")
        add_neon_glow(self.right_panel, hex_to_rgba(NEON_CYAN, 0.1), 40)
        
        self.npu_core.set_ready()

    # -------------------------------------------------------------
    # CONTROLE DA FPGA / TREINAMENTO
    # -------------------------------------------------------------
    def start_training(self):
        self.btn_hw.setEnabled(False)
        self.btn_hw.setText(" Transferindo Dados...")
        self.loading_bar.setVisible(True)
        
        # Feedback mais descritivo para o fluxo de hardware
        self.lbl_status.setStyleSheet(f"color: {NEON_YELLOW}; font-size: 14px; font-weight: bold; background: {BG_ELEMENT}; border: 1px solid {BORDER}; border-radius: 6px; padding: 10px;")
        self.lbl_status.setText("Enviando Software e Pesos para os registradores (Arquitetura Output Stationary)... ⏳")
        
        port = self.inp_port.text().strip()
        self.worker = HardwareTrainerThread(port)
        # Opcional: conectar mensagens da thread para a label
        self.worker.progress.connect(lambda msg: self.lbl_status.setText(f"Processando: {msg} ⏳"))
        self.worker.finished_success.connect(self.on_training_success)
        self.worker.finished_error.connect(self.on_training_error)
        self.worker.start()

    def on_training_success(self, driver):
        self.driver = driver
        self.loading_bar.setVisible(False)
        self.btn_hw.setEnabled(True)
        self.btn_hw.setText(" SoC Conectado!")
        self.btn_hw.setStyleSheet(f"background-color: {NEON_GREEN}; color: {BG_ELEMENT}; border-radius: 6px; padding: 8px 16px; font-weight: bold;")
        
        self.lbl_status.setStyleSheet(f"color: {NEON_GREEN}; font-size: 14px; font-weight: bold; background: {BG_ELEMENT}; border: 1px solid {NEON_GREEN}; border-radius: 6px; padding: 10px;")
        self.lbl_status.setText("FPGA Programada com Sucesso! NPU populada e pronta para inferência. ✅")
        
        self.unlock_interface()

    def on_training_error(self, err_msg):
        self.loading_bar.setVisible(False)
        self.btn_hw.setEnabled(True)
        self.btn_hw.setText(" Programar FPGA")
        
        self.lbl_status.setStyleSheet(f"color: {NEON_RED}; font-size: 14px; font-weight: bold; background: {BG_ELEMENT}; border: 1px solid {NEON_RED}; border-radius: 6px; padding: 10px;")
        self.lbl_status.setText(f"Erro de Comunicação: {err_msg} ❌")

    # -------------------------------------------------------------
    # EVENTOS DE TEMPO REAL
    # -------------------------------------------------------------
    def on_draw_start(self):
        if not self.driver:
            return
        self.npu_core.set_processing()
        self.lbl_status.setText("Capturando imagem e transferindo via barramento do SoC...")
        self.lbl_status.setStyleSheet(f"color: {NEON_CYAN}; font-size: 14px; font-weight: bold; background: {BG_ELEMENT}; border: 1px solid {NEON_CYAN}; border-radius: 6px; padding: 10px;")

    def on_draw_update(self, image):
        if self.driver:
            self._execute_pipeline(image)

    def on_draw_finish(self, image):
        if self.driver:
            self._execute_pipeline(image)
            self.npu_core.set_ready()

    def _execute_pipeline(self, image):
        base = QImage(self.board.width(), self.board.height(), QImage.Format_RGB32)
        base.fill(Qt.black)
        painter = QPainter(base)
        painter.drawImage(0, 0, image)
        painter.end()

        small_img = base.scaled(28, 28, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        preview_img = small_img.scaled(140, 140, Qt.IgnoreAspectRatio, Qt.FastTransformation)
        self.lbl_npu_preview.setPixmap(QPixmap.fromImage(preview_img))
        
        ptr = image.bits()
        ptr.setsize(image.byteCount())
        arr = np.array(ptr).reshape(image.height(), image.width(), 4)
        alpha = arr[:, :, 3]
        
        pil_img = Image.fromarray(alpha, mode='L')
        bbox = pil_img.getbbox()
        
        if not bbox:
            self.clear_ui()
            return

        img_cropped = pil_img.crop(bbox)
        width, height = img_cropped.size
        ratio = 20.0 / max(width, height)
        new_width, new_height = int(width * ratio), int(height * ratio)

        img_resized = img_cropped.resize((new_width, new_height), Image.Resampling.LANCZOS)
        img_28x28 = Image.new("L", (28, 28), color=0)
        img_28x28.paste(img_resized, ((28 - new_width) // 2, (28 - new_height) // 2))
        img_npu = np.clip(np.array(img_28x28).flatten() // 2, 0, 127).astype(np.int8)

        if self.driver:
            try:
                start_t = time.time()
                logits = self.driver.inferir(img_npu)
                latencia = (time.time() - start_t) * 1000
                
                logits_np = np.array(logits, dtype=np.float64)

                # T é a Temperatura. Valores maiores "espalham" mais a incerteza.
                # Comece testando com 100.0, 500.0 ou 1000.0 dependendo do tamanho bruto 
                # dos inteiros que saem dos acumuladores da sua NPU.
                T = 15.0
                logits_scaled = logits_np / T

                # Softmax com os logits escalonados
                exp_logits = np.exp(logits_scaled - np.max(logits_scaled))
                probs = (exp_logits / exp_logits.sum()) * 100.0
                top_digit = int(np.argmax(logits_np))
                
                self._update_results(top_digit, probs)
                self.lbl_status.setText(f"Inferência Executada no Hardware | PREDIÇÃO: {top_digit} | LATÊNCIA: {latencia:.1f} ms")
            except Exception as e:
                self.lbl_status.setText(f"Erro ao processar inferência na FPGA: {str(e)} ❌")
                self.lbl_status.setStyleSheet(f"color: {NEON_RED}; font-size: 14px; font-weight: bold; background: {BG_ELEMENT}; border: 1px solid {NEON_RED}; border-radius: 6px; padding: 10px;")

    def _update_results(self, top_digit, confs):
        self.lbl_prediction.setText(str(top_digit))
        self.lbl_prediction.setStyleSheet(f"color: {NEON_CYAN}; font-size: 72px; font-weight: 900; background: transparent; border: none;")
        self.pred_circle.setStyleSheet(f"background-color: {hex_to_rgba(NEON_CYAN, 0.1)}; border: 3px solid {NEON_CYAN}; border-radius: 70px;")
        add_neon_glow(self.pred_circle, hex_to_rgba(NEON_CYAN, 0.5), 20)
        
        for i in range(10):
            lbl_digit, bar, lbl_pct = self.conf_bars[i]
            val = confs[i]
            bar.setValue(int(val * 10))
            lbl_pct.setText(f"{val:.1f}%")
            
            if i == top_digit:
                lbl_digit.setStyleSheet(f"color: {NEON_CYAN}; font-weight: 900; font-size: 15px; background: transparent;")
                lbl_pct.setStyleSheet(f"color: {NEON_CYAN}; font-weight: bold; font-size: 11px; background: transparent;")
                bar.setStyleSheet(f"QProgressBar {{ border: none; border-radius: 4px; background-color: {BG_ELEMENT}; }} QProgressBar::chunk {{ background-color: {NEON_CYAN}; border-radius: 4px; }}")
            else:
                lbl_digit.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: 800; font-size: 14px; background: transparent;")
                lbl_pct.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: bold; font-size: 11px; background: transparent;")
                cor_barra = NEON_PURPLE if val > 2.0 else BORDER
                bar.setStyleSheet(f"QProgressBar {{ border: none; border-radius: 4px; background-color: {BG_ELEMENT}; }} QProgressBar::chunk {{ background-color: {cor_barra}; border-radius: 4px; }}")

    def clear_ui(self):
        self.board.clear_board()
        self.lbl_npu_preview.clear()
        
        if self.driver:
            self.npu_core.set_ready()
            self.lbl_status.setText("Aguardando desenho...")
            self.lbl_status.setStyleSheet(f"color: {NEON_GREEN}; font-size: 14px; font-weight: bold; background: {BG_ELEMENT}; border: 1px solid {NEON_GREEN}; border-radius: 6px; padding: 10px;")
        
        self.lbl_prediction.setText("?")
        self.lbl_prediction.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 72px; font-weight: 900; background: transparent; border: none;")
        self.pred_circle.setStyleSheet(f"background-color: {hex_to_rgba(BORDER, 0.2)}; border: 3px solid {BORDER}; border-radius: 70px;")
        self.pred_circle.setGraphicsEffect(None)
        
        for lbl_digit, bar, lbl_pct in self.conf_bars:
            lbl_digit.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: 800; font-size: 14px; background: transparent;")
            lbl_pct.setText("0.0%")
            lbl_pct.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: bold; font-size: 11px; background: transparent;")
            bar.setValue(0)
            bar.setStyleSheet(f"QProgressBar {{ border: none; border-radius: 4px; background-color: {BG_ELEMENT}; }} QProgressBar::chunk {{ background-color: {BORDER}; border-radius: 4px; }}")