# ui/components/connection_dialog.py
from PyQt5.QtWidgets import (QDialog, QFormLayout, QHBoxLayout, 
                             QPushButton, QLineEdit, QComboBox, QLabel)
from PyQt5.QtCore import Qt
from core.connection_manager import ConnectionManager

# ==========================================
# JANELA POP-UP DE CONFIGURAÇÃO (GLOBAL)
# ==========================================
class ConnectionConfigDialog(QDialog):
    """Janela Modal para alterar Porta e Baud Rate globalmente."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(" Connection Settings")
        
        # 1. Aumentámos a caixa para dar espaço aos elementos!
        self.setFixedSize(420, 240) 
        
        # Remove o botão de Ajuda (?) nativo do Windows
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.setStyleSheet("""
            QDialog { 
                background-color: #0B0D12; 
            }
            QLabel { 
                color: #8B9BB4; 
                font-weight: bold; 
                font-family: 'Consolas', 'Segoe UI', sans-serif; 
                font-size: 12px;
                letter-spacing: 1px;
            }
            QLineEdit, QComboBox {
                background-color: #12141A;
                color: #E2E8F0;
                border: 1px solid #2A2F3A;
                border-radius: 6px;
                padding: 8px 12px;
                font-family: 'Consolas', 'JetBrains Mono', monospace;
                font-size: 13px;
                min-height: 20px; /* 2. Proteção para nunca esmagar o texto */
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #6CA1A2;
                background-color: #1A1D24;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left: 1px solid #2A2F3A;
            }
            QComboBox QAbstractItemView {
                background-color: #12141A;
                color: #E2E8F0;
                border: 1px solid #2A2F3A;
                selection-background-color: #2A2F3A;
                selection-color: #6CA1A2;
                outline: none;
            }
            QPushButton {
                background-color: transparent;
                color: #E2E8F0;
                border: 1px solid #2A2F3A;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
                min-height: 20px;
            }
            QPushButton:hover { 
                background-color: #1A1D24; 
                border: 1px solid #8B9BB4; 
            }
        """)

        # Layout Principal
        layout = QFormLayout(self)
        layout.setContentsMargins(30, 30, 30, 25) # Mais espaço nas bordas
        layout.setSpacing(20) # Espaço entre as linhas
        
        # 3. Força os labels a ficarem alinhados à direita para um visual limpo
        layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter) 

        self.conn_mgr = ConnectionManager()

        self.port_input = QLineEdit(self.conn_mgr.get_port())
        
        self.baud_input = QComboBox()
        self.baud_input.setFocusPolicy(Qt.StrongFocus) 
        self.baud_input.addItems(["9600", "115200", "460800", "921600", "1000000"])
        self.baud_input.setCurrentText(str(self.conn_mgr.get_baud()))

        layout.addRow("🔌 PORTA SERIAL:", self.port_input)
        layout.addRow("⚡ BAUD RATE:", self.baud_input)

        # 4. Criamos uma linha de botões manualmente para garantir a estabilidade do CSS
        btn_layout = QHBoxLayout()
        btn_layout.addStretch() # Empurra os botões para a direita
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Apply")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(93, 179, 115, 0.15);
                color: #5DB373;
                border: 1px solid #5DB373;
            }
            QPushButton:hover {
                background-color: rgba(93, 179, 115, 0.3);
            }
        """)
        save_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)

        layout.addRow(btn_layout)

    def get_values(self):
        return self.port_input.text(), int(self.baud_input.currentText())