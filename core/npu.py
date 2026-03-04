# core/npu.py

class NPUModel:
    """Modelo matemático de um Systolic Array 3x3 (Output-Stationary)."""
    def __init__(self):
        self.reset()

    def reset(self, a_matrix=None, b_matrix=None):
        self.pes = [[{'acc':0, 'a':0, 'b':0, 'done':False} for _ in range(3)] for _ in range(3)]
        
        # Valores padrão caso venha vazio
        if a_matrix is None:
            a_matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        if b_matrix is None:
            b_matrix = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
            
        # Aplica o Skew Espacial Horizontal (Adiciona 0s na esquerda da matriz A)
        self.a_queues = []
        for r in range(3):
            self.a_queues.append([0]*r + a_matrix[r])
            
        # Aplica o Skew Espacial Vertical (Adiciona 0s no topo da matriz B)
        self.b_queues = []
        for c in range(3):
            col = [b_matrix[r][c] for r in range(3)]
            self.b_queues.append([0]*c + col)
            
        self.cycle = 0
        self.max_cycles = 8 # Tempo total para preencher um grid 3x3
        self.done = False

    def step(self):
        if self.cycle > self.max_cycles:
            self.done = True
            return

        next_a = [[0]*3 for _ in range(3)]
        next_b = [[0]*3 for _ in range(3)]

        for r in range(3):
            for c in range(3):
                # Puxa A (da fila se for borda esquerda, ou do vizinho)
                if c == 0:
                    next_a[r][c] = self.a_queues[r].pop(0) if self.a_queues[r] else 0
                else:
                    next_a[r][c] = self.pes[r][c-1]['a']

                # Puxa B (da fila se for borda superior, ou do vizinho)
                if r == 0:
                    next_b[r][c] = self.b_queues[c].pop(0) if self.b_queues[c] else 0
                else:
                    next_b[r][c] = self.pes[r-1][c]['b']

        for r in range(3):
            for c in range(3):
                self.pes[r][c]['a'] = next_a[r][c]
                self.pes[r][c]['b'] = next_b[r][c]
                
                # Só calcula MAC se a "onda" de dados já tiver chegado neste PE
                start_cycle = r + c
                if self.cycle >= start_cycle and self.cycle <= start_cycle + 2:
                    self.pes[r][c]['acc'] += next_a[r][c] * next_b[r][c]
                
                if self.cycle >= start_cycle + 2:
                    self.pes[r][c]['done'] = True

        self.cycle += 1