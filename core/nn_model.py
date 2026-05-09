# core/nn_model.py
import numpy as np
import torch
import torch.nn as nn

class MLP_Model(nn.Module):
    def __init__(self):
        super(MLP_Model, self).__init__()
        self.flatten = nn.Flatten()
        self.hidden_layer = nn.Linear(28 * 28, 128)
        self.relu = nn.ReLU()
        self.output_layer = nn.Linear(128, 10)

    def forward(self, x):
        x = self.flatten(x)
        x = self.hidden_layer(x)
        x = self.relu(x)
        return self.output_layer(x)

def quantize_tensor(tensor_float, target_dtype, max_val_int):
    max_abs = np.max(np.abs(tensor_float))
    scale = max_val_int / max_abs if max_abs > 0 else 1.0
    tensor_quant = np.round(tensor_float * scale)
    return np.clip(tensor_quant, -max_val_int, max_val_int).astype(target_dtype), scale

def empacotar_pesos_dma(W_int8):
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