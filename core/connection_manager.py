from PyQt5.QtCore import QObject, pyqtSignal

class ConnectionManager(QObject):
    """
    Singleton que gere globalmente as configurações da Porta Serial.
    Qualquer widget pode assinar o sinal 'config_updated' para atualizar a sua UI.
    """
    _instance = None
    
    # Sinal emitido sempre que as configurações mudam (envia porta e baudrate)
    config_updated = pyqtSignal(str, int)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConnectionManager, cls).__new__(cls)
            cls._instance.__init_singleton()
        return cls._instance

    def __init_singleton(self):
        super().__init__()
        # Configurações padrão seguras (podem ser lidas de um ficheiro JSON/INI no futuro)
        self._port = "/dev/ttyUSB1"
        self._baud = 921600

    def set_config(self, port: str, baud: int):
        self._port = port
        self._baud = baud
        # Notifica toda a aplicação que a porta mudou!
        self.config_updated.emit(self._port, self._baud)

    def get_port(self):
        return self._port

    def get_baud(self):
        return self._baud