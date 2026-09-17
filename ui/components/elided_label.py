# ui/components/elided_label.py
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QLabel


class ElidedLabel(QLabel):
    """Rótulo que aceita ficar mais estreito que o texto, encurtando-o com reticências.

    Um QLabel comum exige a largura do texto inteiro como mínimo. Em títulos longos (ex.: "Banco
    de Registradores (RegFile)") isso empurrava a largura mínima do laboratório para além da tela
    e a área dos laboratórios ganhava barras de rolagem. Aqui o tamanho *preferido* continua sendo
    o do texto completo — em tela grande nada muda; só quando falta espaço o texto é encurtado.
    """

    MIN_WIDTH = 70  # abaixo disso sobra só reticências, o que não ajudaria ninguém

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._full_text = text

    def setText(self, text: str) -> None:
        self._full_text = text
        super().setText(text)
        self._elide()

    def fullText(self) -> str:
        return self._full_text

    def _full_width(self) -> int:
        # As margens do QLabel (borda/padding do stylesheet) entram pelo sizeHint do texto atual.
        return QFontMetrics(self.font()).width(self._full_text) + (super().sizeHint().width()
                                                                   - QFontMetrics(self.font()).width(self.text()))

    def sizeHint(self) -> QSize:
        return QSize(self._full_width(), super().sizeHint().height())

    def minimumSizeHint(self) -> QSize:
        return QSize(min(self._full_width(), self.MIN_WIDTH), super().minimumSizeHint().height())

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._elide()

    def _elide(self) -> None:
        elided = QFontMetrics(self.font()).elidedText(self._full_text, Qt.ElideRight, self.width())
        if elided != self.text():
            super().setText(elided)
