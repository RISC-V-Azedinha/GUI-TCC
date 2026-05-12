import os
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader

class Conv2D_Model(nn.Module):
    def __init__(self):
        super(Conv2D_Model, self).__init__()
        self.conv = nn.Conv2d(1, 4, kernel_size=3, stride=2, padding=0) 
        self.relu = nn.ReLU()
        self.flatten = nn.Flatten()
        self.fc = nn.Linear(13 * 13 * 4, 10)

    def forward(self, x):
        x = self.conv(x)  
        x = self.relu(x)
        x = x.permute(0, 2, 3, 1) # Formato da NPU (Channels-Last)
        x = self.flatten(x)
        return self.fc(x)

def empacotar_pesos_dma(W_int8):
    # (Mantenha o código original de empacotamento aqui)
    out_features, in_features = W_int8.shape
    packed_array = []
    for chunk_start in range(0, out_features, 4):
        chunk_size = min(4, out_features - chunk_start)
        for k in range(in_features):
            w0 = int(W_int8[chunk_start + 0, k]) & 0xFF if chunk_size > 0 else 0
            w1 = int(W_int8[chunk_start + 1, k]) & 0xFF if chunk_size > 1 else 0
            w2 = int(W_int8[chunk_start + 2, k]) & 0xFF if chunk_size > 2 else 0
            w3 = int(W_int8[chunk_start + 3, k]) & 0xFF if chunk_size > 3 else 0
            val = (w3 << 24) | (w2 << 16) | (w1 << 8) | w0
            packed_array.append(val)
    return packed_array

def carregar_ou_treinar(progress_cb=None):
    """Carrega o modelo .pth ou treina um novo, seguido pela calibração INT8."""
    model_path = "./artefacts/cnn_pretrained.pth"
    model = Conv2D_Model()
    
    # Precisamos do DataLoader pelo menos para a Calibração (evitar overflow)
    transform = transforms.Compose([
        transforms.RandomAffine(degrees=0, translate=(0.05, 0.05), shear=15),
        transforms.ToTensor()
    ])
    train_dataset = datasets.MNIST(root='./data', train=True, download=True, transform=transform)
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)

    # ==========================================
    # FASE 1: CARREGAR .PTH OU TREINAR
    # ==========================================
    if os.path.exists(model_path):
        if progress_cb: progress_cb(f"FASE 1: Carregando rede pré-treinada ({model_path})...")
        model.load_state_dict(torch.load(model_path, weights_only=True))
    else:
        if progress_cb: progress_cb("FASE 1: Rede não encontrada. Iniciando Treinamento...")
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=0.003)
        scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.5)

        epochs = 12 
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
            if progress_cb: 
                progress_cb(f"Treinamento: Época {epoch+1}/{epochs} | Loss: {running_loss/len(train_loader):.4f}")

        if progress_cb: progress_cb("Salvando novo modelo (conv2d_pretrained.pth)...")
        torch.save(model.state_dict(), model_path)

    # ==========================================
    # FASE 2: CALIBRAÇÃO INT8 (Rápido)
    # ==========================================
    if progress_cb: progress_cb("FASE 2: Calibração INT8 para o SoC RISC-V...")
    model.eval()
    
    max_y1 = 0.0
    max_y2 = 0.0
    with torch.no_grad():
        # Pega um batch para calibrar as escalas
        images, _ = next(iter(train_loader))
        y1 = model.relu(model.conv(images))
        logits = model(images)
        max_y1 = y1.max().item()          
        max_y2 = logits.abs().max().item() 

    w_conv_f = model.conv.weight.detach().numpy().reshape(4, 9)
    b_conv_f = model.conv.bias.detach().numpy()
    w_fc_f = model.fc.weight.detach().numpy()
    b_fc_f = model.fc.bias.detach().numpy()

    # Matemática de quantização
    scale_w1_max = 127.0 / np.max(np.abs(w_conv_f))
    scale_w1_safe = (120.0 * 256.0) / (max_y1 * 127.0) if max_y1 > 0 else scale_w1_max
    scale_w1 = min(scale_w1_max, scale_w1_safe)

    w_conv_i = np.round(w_conv_f * scale_w1).astype(np.int8)
    b_conv_i = np.round(b_conv_f * 127.0 * scale_w1).astype(np.int32)

    scale_y1 = (127.0 * scale_w1) / 256.0 

    scale_w2_max = 127.0 / np.max(np.abs(w_fc_f))
    scale_w2_safe = (120.0 * 256.0) / (max_y2 * scale_y1) if max_y2 > 0 else scale_w2_max
    scale_w2 = min(scale_w2_max, scale_w2_safe)

    w_fc_i = np.round(w_fc_f * scale_w2).astype(np.int8)
    b_fc_i = np.round(b_fc_f * scale_y1 * scale_w2).astype(np.int32)
    
    return w_conv_i, b_conv_i, w_fc_i, b_fc_i