# core/nn_worker.py
import os
from PyQt5.QtCore import QThread, pyqtSignal
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import numpy as np

from core.nn_model import MLP_Model, quantize_tensor
from core.npu_driver import NPUDriverEdge

class HardwareTrainerThread(QThread):
    progress = pyqtSignal(str)
    finished_success = pyqtSignal(object)
    finished_error = pyqtSignal(str)

    def __init__(self, port):
        super().__init__()
        self.port = port
        self.model_file = "artefacts/mlp_pretrained.pth"
        self.bin_file = "artefacts/mlp_server.bin"

    def run(self):
        try:
            # 1. Instanciar Driver
            self.progress.emit(f"STATUS: Conectando à FPGA ({self.port})...")
            driver = NPUDriverEdge(self.port, 921600)

            # 2. Upload do firmware em C (RISC-V)
            if not os.path.exists(self.bin_file):
                raise Exception(f"Arquivo '{self.bin_file}' não encontrado na raiz!")
            
            driver.boot_app_bin(self.bin_file, lambda msg: self.progress.emit(f"STATUS: {msg}"))

            # 3. Preparar a Rede Neural (Carregar ou Treinar)
            model = MLP_Model()
            
            if os.path.exists(self.model_file):
                self.progress.emit("STATUS: Carregando modelo pré-treinado do disco...")
                # weights_only=True é recomendado por segurança nas versões mais recentes do PyTorch
                model.load_state_dict(torch.load(self.model_file, map_location='cpu', weights_only=True))
                model.eval()
            else:
                self.progress.emit("STATUS: Modelo não encontrado. Iniciando treino local...")
                self._train_fallback(model)

            # 4. Quantização
            self.progress.emit("STATUS: Quantizando Modelo para INT8/INT32...")
            with torch.no_grad():
                w1_float, b1_float = model.hidden_layer.weight.numpy(), model.hidden_layer.bias.numpy()
                w2_float, b2_float = model.output_layer.weight.numpy(), model.output_layer.bias.numpy()

            w1_int8, scale_w1 = quantize_tensor(w1_float, np.int8, 127)
            w2_int8, scale_w2 = quantize_tensor(w2_float, np.int8, 127)
            b1_int32 = np.round(b1_float * scale_w1 * 255.0).astype(np.int32)
            b2_int32 = np.round(b2_float * scale_w2 * 127.0).astype(np.int32)

            # 5. Upload dos Pesos via DMA
            self.progress.emit("STATUS: Configurando NPU (DMA)...")
            driver.upload_modelo(w1_int8, b1_int32, w2_int8, b2_int32, lambda msg: self.progress.emit(f"STATUS: {msg}"))

            self.progress.emit("STATUS: SoC Configurado e Rede Pronta!")
            self.finished_success.emit(driver)

        except Exception as e:
            self.finished_error.emit(str(e))

    def _train_fallback(self, model):
        """ Se o arquivo não existir, treina rapidamente e salva """
        transform = transforms.Compose([transforms.ToTensor()])
        train_dataset = datasets.MNIST(root='./data', train=True, download=True, transform=transform)
        train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
        
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=0.002)
        scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)

        epochs = 15
        for epoch in range(epochs):
            model.train()
            running_loss = 0.0
            for images, labels in train_loader:
                optimizer.zero_grad()
                loss = criterion(model(images), labels)
                loss.backward()
                optimizer.step()
                running_loss += loss.item()
                
            scheduler.step()
            self.progress.emit(f"STATUS: Treinando PyTorch (Época {epoch+1}/{epochs}) - Loss: {running_loss/len(train_loader):.4f}")
            
        torch.save(model.state_dict(), self.model_file)