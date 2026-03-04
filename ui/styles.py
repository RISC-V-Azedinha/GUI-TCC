# ui/styles.py

STYLESHEET = """
QMainWindow, QWidget {
    background-color: #0f172a; 
    color: #cbd5e1; 
    font-family: 'Ubuntu', 'Segoe UI', -apple-system, sans-serif;
    font-size: 13px;
}

#Sidebar {
    background-color: #020617;
    border-right: 1px solid #1e293b;
}

#AppTitle {
    color: #f8fafc;
    font-size: 16px;
    font-weight: 800;
    letter-spacing: 1px;
    padding: 0px 20px; /* Removido padding vertical para alinhar perfeitamente */
    min-height: 70px;  /* Força exatamente a mesma altura do Header principal */
    max-height: 70px;
    border-bottom: 1px solid #1e293b;
    background: #020617;
}

#NavButton {
    background-color: transparent;
    color: #94a3b8;
    text-align: left;
    padding: 14px 20px;
    border: none;
    font-size: 14px;
    font-weight: 600;
    border-radius: 0px;
}

#NavButton:hover {
    background-color: #0f172a;
    color: #f8fafc;
}

#NavButton:checked {
    background-color: #1e3a8a;
    color: #60a5fa;
    border-left: 4px solid #3b82f6;
}

#NavButton:disabled { color: #334155; }

#Header {
    background-color: #0f172a;
    border-bottom: 1px solid #1e293b;
}

QPlainTextEdit, QTextEdit {
    background-color: #020617;
    color: #e2e8f0;
    font-family: 'Consolas', 'JetBrains Mono', 'Courier New', monospace;
    font-size: 14px;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 12px;
}

QTextEdit#TerminalOutput { 
    color: #a7f3d0;
    font-size: 13px;
    line-height: 1.5;
}

QTableWidget {
    background-color: #020617;
    color: #e2e8f0;
    border: 1px solid #1e293b;
    border-radius: 8px;
    gridline-color: #1e293b;
    font-family: 'Consolas', 'JetBrains Mono', monospace;
    font-size: 13px;
}
QHeaderView::section {
    background-color: #0f172a;
    color: #94a3b8;
    border: 1px solid #1e293b;
    padding: 6px;
    font-weight: 700;
}
QTableWidget::item:selected {
    background-color: #1e3a8a;
    color: #bfdbfe;
}

QPushButton.ActionBtn {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}
QPushButton.ActionBtn:hover { background-color: #334155; }
QPushButton.ActionBtn:disabled { color: #64748b; background-color: #0f172a; border-color: #1e293b; }

QPushButton.PrimaryBtn { background-color: #2563eb; color: white; border: none; }
QPushButton.PrimaryBtn:hover { background-color: #1d4ed8; }

QPushButton.SuccessBtn { background-color: #059669; color: white; border: none; }
QPushButton.SuccessBtn:hover { background-color: #047857; }

QPushButton.GhostBtn { background: transparent; color: #94a3b8; border: 1px solid #334155; border-radius: 6px; padding: 6px 12px; font-weight: 600; }
QPushButton.GhostBtn:hover { background: #1e293b; color: #f8fafc; }

QLabel.PipelineStage {
    background-color: #0f172a;
    color: #475569;
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 800;
    font-family: 'Consolas', monospace;
}
QLabel.PipelineStageActive {
    background-color: #1e3a8a;
    color: #60a5fa;
    border: 1px solid #3b82f6;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 800;
    font-family: 'Consolas', monospace;
}

QScrollBar:vertical {
    border: none;
    background: #020617;
    width: 12px;
    border-radius: 6px;
}
QScrollBar::handle:vertical {
    background: #334155;
    min-height: 20px;
    border-radius: 6px;
}
QScrollBar::handle:vertical:hover { background: #475569; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { border: none; background: none; }
"""