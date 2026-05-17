# ui/highlighter.py
from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt5.QtCore import QRegExp

class RISCVHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []

        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor("#60a5fa"))
        keywordFormat.setFontWeight(QFont.Bold)

        registerFormat = QTextCharFormat()
        registerFormat.setForeground(QColor("#f472b6"))

        numberFormat = QTextCharFormat()
        numberFormat.setForeground(QColor("#a7f3d0"))

        labelFormat = QTextCharFormat()
        labelFormat.setForeground(QColor("#fde047"))
        labelFormat.setFontWeight(QFont.Bold)

        directiveFormat = QTextCharFormat()
        directiveFormat.setForeground(QColor("#c084fc"))

        commentFormat = QTextCharFormat()
        commentFormat.setForeground(QColor("#64748b"))
        commentFormat.setFontItalic(True)

        keywords = ["\\badd\\b", "\\baddi\\b", "\\bsw\\b", "\\blw\\b", 
                    "\\bj\\b", "\\bbeq\\b", "\\bli\\b", "\\bmv\\b", "\\bwfi\\b"]
        for pattern in keywords:
            self.highlightingRules.append((QRegExp(pattern), keywordFormat))

        self.highlightingRules.append((QRegExp("\\.[a-zA-Z0-9_]+"), directiveFormat))
        self.highlightingRules.append((QRegExp("\\b[a-zA-Z0-9_]+:"), labelFormat))

        regs = ["\\bx[0-9]+\\b", "\\bt[0-6]\\b", "\\ba[0-7]\\b", "\\bs[0-9]+\\b", 
                "\\bzero\\b", "\\bra\\b", "\\bsp\\b", "\\bgp\\b", "\\btp\\b"]
        for pattern in regs:
            self.highlightingRules.append((QRegExp(pattern), registerFormat))

        self.highlightingRules.append((QRegExp("\\b-?[0-9]+\\b"), numberFormat))
        self.highlightingRules.append((QRegExp("\\b0x[0-9a-fA-F]+\\b"), numberFormat))
        self.highlightingRules.append((QRegExp("#[^\n]*"), commentFormat))

    def highlightBlock(self, text: str):
        for pattern, format in self.highlightingRules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)