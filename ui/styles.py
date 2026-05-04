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
    padding: 0 px;
}

QTextEdit#TerminalOutput { 
    color: #5DB373; /* Verde terminal clássico */
    font-size: 13px;
    line-height: 1.5;
}

/* ================== SPLITTER ================== */

/* Espaçamento entre o Editor e as Tabelas */
QSplitter::handle:horizontal {
    background-color: transparent; /* Mantém o fundo limpo */
    width: 60px; /* Define o tamanho do 'gap' (ajuste conforme preferir) */
}

/* ================== TABELAS (RegFile e RAM) ================== */
QTableWidget {
    background-color: transparent; /* Deixa a tabela mesclar com o fundo do painel/janela */
    color: #E2E8F0;
    border: none; /* Remove a caixa externa grossa */
    gridline-color: transparent; /* Oculta a grade padrão do Qt (linhas verticais) */
    font-family: 'Consolas', 'JetBrains Mono', monospace;
    font-size: 13px;
    selection-background-color: #1A1D24;
    selection-color: #F2B845;
}

/* Cria o efeito de "linha de caderno" apenas na horizontal */
QTableWidget::item {
    border-bottom: 1px solid #1A1D24; 
}

/* Remove a borda esquerda para as células da primeira coluna, dando um ar mais solto */
QTableWidget::item:first-child {
    border-left: none;
}

/* O Cabeçalho com o Efeito Teal */
QHeaderView::section {
    background-color: transparent; /* Tira o bloco de cor do cabeçalho */
    color: #6CA1A2; /* Texto do cabeçalho em Teal igual ao print */
    border: none;
    border-bottom: 2px solid #6CA1A2; /* A trilha de destaque embaixo */
    border-right: none; /* Remove a linha vertical que separava os cabeçalhos */
    padding: 8px 6px;
    font-weight: bold;
}

/* Célula vazia no canto superior esquerdo (se existir) */
QTableCornerButton::section {
    background-color: transparent;
    border: none;
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
    border-left: 1px solid #2A2F3A;
    width: 13px; /* Deixei um pouco mais largo para destacar o formato retangular */
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #F2B845; /* Mostarda (Laranja Amarelado) */
    min-height: 20px;
    border-radius: 0px; /* Zera o arredondamento, deixando perfeitamente retangular */
}
QScrollBar::handle:vertical:hover { 
    background: #DC673E; /* Muda para o Laranja do botão Run ao passar o mouse */
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { 
    border: none; 
    background: none; 
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: #0B0D12;
    height: 12px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background: #F2B845;
    min-width: 20px;
    border-radius: 0px;
}
QScrollBar::handle:horizontal:hover { 
    background: #DC673E; 
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { 
    border: none; 
    background: none; 
    width: 0px;
}

/* ================== IO WIDGET ================== */
#IOCodePanel, #IOMapPanel, #IOBoardPanel {
    background-color: #0B0D12;
    border: 1px solid #2A2F3A;
    border-radius: 8px;
}

QLabel[class="IOSectionTitle"] {
    background-color: transparent;
    color: #8B9BB4;
    font-weight: bold;
    font-size: 12px;
    border: none;
    margin-bottom: 5px;
}

/* Modos de Operação (SIM/HARDWARE) */
QLabel#IOModeLabel {
    background-color: transparent;
    color: #8B9BB4;
    font-weight: bold;
    font-size: 14px;
}

QPushButton#IOSimModeBtn {
    background-color: #6CA1A2; /* Teal da paleta */
    color: #12141A;
    font-weight: bold;
    border-radius: 4px;
    padding: 4px 12px;
}

QPushButton#IOHwModeBtn {
    background-color: transparent;
    color: #8B9BB4;
    font-weight: bold;
    border-radius: 4px;
    padding: 4px 12px;
}

/* Tabela de Memória do IO */
QTableWidget#IOMemoryTable {
    border: none; 
    background-color: transparent;
}
QTableWidget#IOMemoryTable::item {
    border-bottom: 1px solid #2A2F3A;
}

/* Componentes Visuais da FPGA */
QLabel.IOHexDisplay {
    background-color: #12141A;
    border: 2px solid #2A2F3A;
    border-radius: 6px;
    color: #DC673E; /* Laranja da paleta em vez de vermelho puro */
    font-family: 'Consolas', monospace;
    font-size: 26px;
    font-weight: bold;
}

#IOLedContainer {
    background-color: #12141A;
    border: 1px solid #2A2F3A; /* Borda devolve o aspecto de "caixa" do componente */
    border-radius: 16px;
    padding: 10px;
}

#IOSwitchTrack {
    background-color: #06070A; /* Quase preto: cria o efeito de uma cavidade afundada na placa */
    border: 1px solid #2A2F3A;
    border-radius: 4px;
}

QLabel.IOSwitchLabel {
    color: #8B9BB4;
    font-size: 8px;
    font-weight: bold;
    border: none;
}

"""