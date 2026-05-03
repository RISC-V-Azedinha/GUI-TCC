# core/emulator.py
import re
from typing import Tuple, Dict, List
import struct

class RISCV_Emulator:
    """
    Model (MVC): Responsável puramente pela lógica de negócio e simulação do hardware.
    Não possui conhecimento da interface gráfica (PyQt).
    """
    def __init__(self) -> None:
        self.regs: List[int] = [0] * 32
        self.memory: Dict[int, int] = {}
        self.pc: int = 0
        self.stage: int = 0
        
        self.IR: str = ""
        self.op: str = ""
        self.rd: int = 0
        self.rs1: int = 0
        self.rs2: int = 0
        self.imm: int = 0
        self.A: int = 0
        self.B: int = 0
        self.ALUOut: int = 0
        self.MDR: int = 0
        
        self.labels: Dict[str, int] = {}
        self.instructions: List[str] = []
        self.line_map: Dict[int, int] = {} 
        self.halted: bool = False
        
        self.abi: Dict[str, int] = {
            'zero':0, 'ra':1, 'sp':2, 'gp':3, 'tp':4, 't0':5, 't1':6, 't2':7,
            's0':8, 'fp':8, 's1':9, 'a0':10, 'a1':11, 'a2':12, 'a3':13, 'a4':14,
            'a5':15, 'a6':16, 'a7':17, 's2':18, 's3':19, 's4':20, 's5':21,
            's6':22, 's7':23, 's8':24, 's9':25, 's10':26, 's11':27, 't3':28,
            't4':29, 't5':30, 't6':31
        }

    def get_reg_idx(self, name: str) -> int:
        name = name.strip().replace(',', '')
        if name in self.abi: return self.abi[name]
        if name.startswith('x') and name[1:].isdigit(): return int(name[1:])
        return 0

    def parse_mem_op(self, op_str: str) -> Tuple[int, int]:
        match = re.match(r"(-?\d+)\((.*?)\)", op_str)
        if match:
            return int(match.group(1)), self.get_reg_idx(match.group(2))
        return 0, 0

    def parse_code(self, text: str) -> None:
        self.__init__() # Reset do estado interno
        
        lines = text.split('\n')
        for line_idx, line in enumerate(lines):
            raw = line.split('#')[0].strip()
            if not raw or raw.startswith('.'): continue
            
            if ':' in raw:
                parts = raw.split(':')
                label = parts[0].strip()
                self.labels[label] = len(self.instructions)
                inst = parts[1].strip()
                if inst:
                    self.line_map[len(self.instructions)] = line_idx
                    self.instructions.append(inst)
            else:
                self.line_map[len(self.instructions)] = line_idx
                self.instructions.append(raw)

    def get_current_line(self) -> int:
        """Retorna a linha no editor correspondente ao PC atual."""
        return self.line_map.get(self.pc, -1)

    def clock_tick(self) -> Tuple[bool, str, int]:
        """Avança a máquina de estados (FSM) em um ciclo de relógio."""
        if self.halted: return False, "", -1

        current_stage = self.stage
        msg = ""

        if self.stage == 0: # IF
            if self.pc >= len(self.instructions):
                self.halted = True
                return False, "Fim da execução (EOF).", current_stage
            self.IR = self.instructions[self.pc]
            msg = f"[ IF  ] Buscou instrução em PC={self.pc}: '{self.IR}'"
            self.stage = 1
            
        elif self.stage == 1: # ID
            msg = self.stage_decode()
            self.stage = 2
            
        elif self.stage == 2: # EX
            msg = self.stage_execute()
            if self.op in ['lw', 'sw']:
                self.stage = 3 
            elif self.op in ['li', 'mv', 'add', 'addi']:
                self.stage = 4 
            elif self.op in ['j', 'beq']:
                self.stage = 0 
            elif self.op == 'wfi':
                self.stage = 4 
            else:
                self.stage = 0
            
        elif self.stage == 3: # MEM
            msg = self.stage_memory()
            if self.op == 'lw':
                self.stage = 4 
            else:
                self.stage = 0 
            
        elif self.stage == 4: # WB
            msg = self.stage_writeback()
            self.stage = 0 

        return True, msg, current_stage

    def stage_decode(self) -> str:
        parts = self.IR.replace(',', ' ').split()
        self.op = parts[0]
        self.rd = self.rs1 = self.rs2 = self.imm = self.A = self.B = 0
        
        try:
            if self.op == 'li':
                self.rd = self.get_reg_idx(parts[1])
                self.imm = int(parts[2])
                return f"[ ID  ] Decodificado 'li': Alvo x{self.rd}, Imediato={self.imm}"
            elif self.op == 'mv':
                self.rd = self.get_reg_idx(parts[1])
                self.rs1 = self.get_reg_idx(parts[2])
                self.A = self.regs[self.rs1]
                return f"[ ID  ] Decodificado 'mv': Lê x{self.rs1} (Valor={self.A})"
            elif self.op == 'add':
                self.rd = self.get_reg_idx(parts[1])
                self.rs1 = self.get_reg_idx(parts[2])
                self.rs2 = self.get_reg_idx(parts[3])
                self.A, self.B = self.regs[self.rs1], self.regs[self.rs2]
                return f"[ ID  ] Decodificado 'add': Lê x{self.rs1}({self.A}) e x{self.rs2}({self.B})"
            elif self.op == 'addi':
                self.rd = self.get_reg_idx(parts[1])
                self.rs1 = self.get_reg_idx(parts[2])
                self.imm = int(parts[3])
                self.A = self.regs[self.rs1]
                return f"[ ID  ] Decodificado 'addi': Lê x{self.rs1}({self.A}), Imm={self.imm}"
            elif self.op == 'lw':
                self.rd = self.get_reg_idx(parts[1])
                self.imm, self.rs1 = self.parse_mem_op(parts[2])
                self.A = self.regs[self.rs1]
                return f"[ ID  ] Decodificado 'lw': Base x{self.rs1}({self.A}), Offset={self.imm}"
            elif self.op == 'sw':
                self.rs2 = self.get_reg_idx(parts[1])
                self.imm, self.rs1 = self.parse_mem_op(parts[2])
                self.A, self.B = self.regs[self.rs1], self.regs[self.rs2]
                return f"[ ID  ] Decodificado 'sw': Salvar x{self.rs2}({self.B}) em Base x{self.rs1}({self.A})+{self.imm}"
            elif self.op == 'j':
                self.imm = self.labels.get(parts[1], self.pc + 1)
                return f"[ ID  ] Decodificado 'j': Alvo '{parts[1]}' resolvido para PC={self.imm}"
            elif self.op == 'beq':
                self.rs1, self.rs2 = self.get_reg_idx(parts[1]), self.get_reg_idx(parts[2])
                self.A, self.B = self.regs[self.rs1], self.regs[self.rs2]
                self.imm = self.labels.get(parts[3], self.pc + 1)
                return f"[ ID  ] Decodificado 'beq': Lê x{self.rs1}({self.A}) e x{self.rs2}({self.B})"
            elif self.op == 'wfi':
                return "[ ID  ] Decodificado 'wfi': Aguardar Interrupção (Halt)"
            else:
                return f"[ ID  ] Opcode ignorado/desconhecido: {self.op}"
        except Exception:
            return "[ ID  ] Erro ao decodificar operandos."

    def stage_execute(self) -> str:
        if self.op in ['li', 'mv']:
            self.ALUOut = self.imm if self.op == 'li' else self.A
            return f"[ EX  ] ULA Pass-through: Resultado = {self.ALUOut}"
        elif self.op == 'add':
            self.ALUOut = self.A + self.B
            return f"[ EX  ] ULA: {self.A} + {self.B} = {self.ALUOut}"
        elif self.op == 'addi':
            self.ALUOut = self.A + self.imm
            return f"[ EX  ] ULA: {self.A} + {self.imm} = {self.ALUOut}"
        elif self.op in ['lw', 'sw']:
            self.ALUOut = (self.A + self.imm) & ~3
            return f"[ EX  ] Calcula Endereço: {self.A} + {self.imm} -> {self.ALUOut}"
        elif self.op == 'j':
            self.pc = self.imm
            return f"[ EX  ] Resolve Jump: Novo PC = {self.pc}"
        elif self.op == 'beq':
            self.pc = self.imm if self.A == self.B else self.pc + 1
            return f"[ EX  ] Resolve Branch: {self.A} == {self.B} -> PC={self.pc}"
        else:
            return "[ EX  ] Nenhum cálculo necessário (NOP)."

    def stage_memory(self) -> str:
        if self.op == 'lw':
            # Se o endereço for lido antes de ser escrito, registramos ele na RAM com valor 0
            if self.ALUOut not in self.memory:
                self.memory[self.ALUOut] = 0
            
            self.MDR = self.memory[self.ALUOut]
            return f"[ MEM ] Leu Memória: Mem[{self.ALUOut}] = {self.MDR}"
            
        elif self.op == 'sw':
            self.memory[self.ALUOut] = self.B
            self.pc += 1
            return f"[ MEM ] Escreveu Memória: Mem[{self.ALUOut}] <- {self.B}. PC Avançou"
        else:
            return "[ MEM ] Sem acesso à memória neste ciclo."

    def stage_writeback(self) -> str:
        if self.op in ['li', 'mv', 'add', 'addi']:
            if self.rd != 0: self.regs[self.rd] = self.ALUOut
            self.pc += 1
            return f"[ WB  ] Registrador x{self.rd} atualizado para {self.ALUOut}. PC Avança."
        elif self.op == 'lw':
            if self.rd != 0: self.regs[self.rd] = self.MDR
            self.pc += 1
            return f"[ WB  ] Registrador x{self.rd} atualizado para {self.MDR}. PC Avança."
        elif self.op == 'wfi':
            self.halted = True
            return "[ WB  ] Halt acionado. Clock Paralisado."
        else:
            self.pc += 1
            return "[ WB  ] Ciclo concluído. PC Avança."


    def generate_binary_payload(instructions):
    # instruções: lista de inteiros de 32 bits (ex: [0x00000013, 0x00100093])
    # '<I' garante o formato Little Endian (padrão RISC-V)
        return b''.join(struct.pack('<I', instr) for instr in instructions)
    

    def get_binary_image(self, instructions_list):
        """
        Converte uma lista de instruções (ints, strings hex/bin, ou objetos) 
        em um payload binário Little Endian.
        """
        import struct
        payload = b''
        
        for instr in instructions_list:
            try:
                val = 0
                
                # 1. Se já for um número inteiro
                if isinstance(instr, int):
                    val = instr
                    
                # 2. Se for um texto (String Hex, Binária ou Decimal)
                elif isinstance(instr, str):
                    instr_clean = instr.strip().lower()
                    if instr_clean.startswith('0x'):
                        val = int(instr_clean, 16)
                    elif instr_clean.startswith('0b'):
                        val = int(instr_clean, 2)
                    elif len(instr_clean) == 32 and all(c in '01' for c in instr_clean):
                        val = int(instr_clean, 2) # Binário puro de 32 bits sem '0b'
                    else:
                        val = int(instr_clean) # Tenta decimal
                        
                # 3. Se for um Objeto criado por você (ex: instâncias de uma classe Instruction)
                elif hasattr(instr, 'machine_code'):
                    val = int(instr.machine_code)
                elif hasattr(instr, 'value'):
                    val = int(instr.value)
                    
                else:
                    # Tenta converter a força bruta
                    val = int(instr)

                # Aplica a máscara 0xFFFFFFFF para garantir que cabe em 32-bits unsigned
                payload += struct.pack('<I', val & 0xFFFFFFFF)
                
            except Exception as e:
                print(f"Erro ao converter instrução '{instr}' (tipo {type(instr)}): {e}")
                return b'' # Retorna vazio para a GUI avisar do erro
                
        return payload