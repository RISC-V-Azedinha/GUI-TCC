STYLESHEET = """
/* Fundo geral e Tipografia */
QMainWindow, QWidget {
    background-color: #12141A; /* Chumbo profundo, reduz o cansaço visual */
    color: #E2E8F0; 
    font-family: 'Consolas', 'JetBrains Mono', 'Courier New', monospace;
    font-size: 13px;
}

/* ================== SIDEBAR ================== */
#Sidebar {
    background-color: #0B0D12;
    border-right: 1px solid #2A2F3A;
}

#AppTitle {
    color: #F2B845; /* Mostarda para dar destaque à marca */
    font-size: 16px;
    font-weight: 800;
    letter-spacing: 1px;
    padding: 0px 20px;
    min-height: 70px;
    max-height: 70px;
    border-bottom: 1px solid #2A2F3A;
    background: #0B0D12;
}

#NavButton {
    background-color: transparent;
    color: #8B9BB4;
    text-align: left;
    padding: 14px 20px;
    border: none;
    font-size: 14px;
    font-weight: bold;
    border-radius: 0px;
}

#NavButton:hover {
    background-color: #1A1D24;
    color: #F3F3F3;
}

#NavButton:checked {
    background-color: #1A1D24; 
    color: #6CA1A2; /* Teal - indica estado ativo */
    border-left: 3px solid #DC673E; /* Trilha Laranja simulando conexão */
}

#NavButton:disabled { color: #3A4150; }

/* ================== TOP HEADER ================== */
#Header {
    background-color: #12141A;
    border-bottom: 1px solid #2A2F3A;
}

/* ================== CAIXAS DE TEXTO E CONSOLE ================== */
QPlainTextEdit, QTextEdit {
    background-color: #0B0D12;
    color: #CBD5E1;
    font-family: 'Consolas', 'JetBrains Mono', monospace;
    font-size: 14px;
    border: 1px solid #2A2F3A;
    border-radius: 4px; /* Raio bem sutil, menos agressivo que 0px e 8px */
    padding: 10px;
}

QTextEdit#TerminalOutput { 
    color: #5DB373; /* Verde terminal clássico */
    font-size: 13px;
    line-height: 1.5;
}

/* ================== TABELAS (RegFile e RAM) ================== */
QTableWidget {
    background-color: #0B0D12;
    color: #E2E8F0;
    border: 1px solid #2A2F3A;
    border-radius: 4px;
    gridline-color: #1A1D24;
    font-family: 'Consolas', 'JetBrains Mono', monospace;
    font-size: 13px;
    selection-background-color: #1A1D24;
    selection-color: #F2B845;
}

QHeaderView::section {
    background-color: #12141A;
    color: #8B9BB4;
    border: none;
    border-bottom: 2px solid #6CA1A2; /* Trilha teal substituindo o roxo sólido */
    border-right: 1px solid #1A1D24;
    padding: 8px 6px;
    font-weight: bold;
}

QTableWidget::item:selected {
    background-color: #2A2F3A;
    border-left: 2px solid #DC673E;
}

/* ================== BOTÕES ================== */
QPushButton.ActionBtn {
    background-color: #1A1D24;
    color: #E2E8F0;
    border: 1px solid #2A2F3A;
    border-radius: 4px;
    padding: 6px 16px;
    font-weight: bold;
}
QPushButton.ActionBtn:hover { background-color: #2A2F3A; border-color: #6CA1A2; }
QPushButton.ActionBtn:pressed { background-color: #0B0D12; }
QPushButton.ActionBtn:disabled { color: #555555; border-color: #2A2F3A; }

/* Botões Principais de Ação */
QPushButton.PrimaryBtn { 
    background-color: #DC673E;
    color: #12141A; 
    border: none; 
    border-radius: 4px; 
    padding: 6px 16px;
    font-weight: bold;
    min-width: 100px; 
}
QPushButton.PrimaryBtn:hover { background-color: #E75122; }

QPushButton.SuccessBtn { 
    background-color: #5DB373; /* Verde para sucesso/upload */
    color: #12141A; 
    border: none; 
    border-radius: 4px;
    padding: 6px 16px;
    font-weight: bold;
}
QPushButton.SuccessBtn:hover { background-color: #4A9C5E; }

/* ================== BOTÕES GHOST (Save, Load, Config) ================== */
QPushButton.GhostBtn { 
    background: transparent; 
    color: #F3F3F3; 
    border: 1px solid transparent; /* Transparente para não dar 'pulo' na tela */
    border-radius: 4px; 
    padding: 6px 12px; 
    font-weight: bold; 
}

QPushButton.GhostBtn:hover { 
    background: #1A1D24; 
    color: #F2B845; 
}

QPushButton.GhostBtn:pressed {
    background: #2A2F3A;
    color: #DC673E; 
    border-color: #DC673E;
}

/* ================== PIPELINE STAGES ================== */
QLabel.PipelineStage {
    background-color: #0B0D12;
    color: #475569;
    border: 1px solid #1A1D24;
    border-radius: 4px;
    padding: 4px 10px;
    font-weight: bold;
    font-family: 'Consolas', monospace;
}
QLabel.PipelineStageActive {
    background-color: #1A1D24;
    color: #F2B845; /* Mostarda no estágio ativo */
    border: 1px solid #F2B845;
    border-radius: 4px;
    padding: 4px 10px;
    font-weight: bold;
    font-family: 'Consolas', monospace;
}

/* ================== SCROLLBARS ================== */
QScrollBar:vertical {
    border: none;
    background: #0B0D12;
    width: 10px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #2A2F3A; /* Discreto até o hover */
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover { background: #6CA1A2; } /* Brilha em Teal ao passar o mouse */
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { border: none; background: none; }
QScrollBar:horizontal {
    border: none;
    background: #0B0D12;
    height: 10px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background: #2A2F3A;
    min-width: 20px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal:hover { background: #6CA1A2; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { border: none; background: none; }
"""