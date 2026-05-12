from PyQt5.QtCore import QThread, pyqtSignal
from core.nn_model import carregar_ou_treinar  # <--- Nome atualizado aqui
from core.npu_driver import NPUDriverEdge
import os

class HardwareTrainerThread(QThread):
    progress = pyqtSignal(str)
    finished_success = pyqtSignal(object)
    finished_error = pyqtSignal(str)

    def __init__(self, port, baud=921600):
        super().__init__()
        self.port = port
        self.baud = baud

    def run(self):
        try:
            # 1. Carrega o .pth (ou treina) e faz a calibração Int8
            w_conv, b_conv, w_fc, b_fc = carregar_ou_treinar(
                progress_cb=lambda msg: self.progress.emit(msg)
            )

            self.progress.emit("Conectando à porta Serial da FPGA...")
            driver = NPUDriverEdge(self.port, self.baud)
            
            # 2. Boot do firmware (Opcional, se existir cnn_server.bin)
            bin_path = "./artefacts/cnn_server.bin"
            if os.path.exists(bin_path):
                self.progress.emit("Fazendo upload do firmware (cnn_server.bin)...")
                driver.boot_app_bin(bin_path, progress_cb=lambda msg: self.progress.emit(msg))

            # 3. Transferência do Modelo via DMA
            self.progress.emit("Transferindo parâmetros da rede Conv2D para NPU via DMA...")
            driver.upload_modelo(w_conv, b_conv, w_fc, b_fc, 
                                 progress_cb=lambda msg: self.progress.emit(msg))

            self.finished_success.emit(driver)

        except Exception as e:
            self.finished_error.emit(str(e))