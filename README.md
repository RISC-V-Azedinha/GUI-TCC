# GUI-TCC — Plataforma Didática RISC-V

Aplicação desktop (PyQt5) para ensino de Arquitetura de Computadores e Sistemas Embarcados, combinando **simulação de software** e **execução em hardware real** (FPGA) sobre um SoC RISC-V.

Cada aba da interface é um experimento independente, cobrindo desde o datapath de um processador multiciclo até a inferência de uma rede neural acelerada por uma NPU dedicada:

| Aba | Módulo | Foco |
|---|---|---|
| **RV32I** | `ui/tabs/rv32i_widget.py` | Datapath multiciclo (IF/ID/EX/MEM/WB), registradores, breakpoints |
| **I/O** | `ui/tabs/io_widget.py` | GPIO/UART mapeados em memória, compilação C → FPGA |
| **DMA** | `ui/tabs/dma_widget.py` | Arbitragem de barramento, Burst/Cycle Stealing/Round-Robin/Weighted |
| **OS Console** | `ui/tabs/os_console_widget.py` | Multitarefa preemptiva (CLINT/PLIC), heap e desfragmentação |
| **NPU** | `ui/tabs/npu_widget.py` | Systolic Array 3x3, pipeline de pós-processamento (PPU) |
| **Tiling** | `ui/tabs/tiling_widget.py` | Multiplicação de matrizes em blocos sobre hardware pequeno |
| **Neural Network** | `ui/tabs/nn_widget.py` | Inferência MNIST na NPU (PyTorch + hardware) |

## Estrutura do projeto

```
GUI-TCC/
├── main.py              # Ponto de entrada da aplicação
├── ui/                   # Widgets e estilos da interface (PyQt5)
│   └── tabs/             # Um widget por experimento/aba
├── core/                 # Modelos e lógica de simulação (emulador, NPU, drivers seriais)
├── controllers/          # Camada de controle (MVC) entre UI e core
├── artifacts/            # Binários e firmware (kernel, bootloader, pesos treinados)
├── build/                # Artefatos de build gerados para a FPGA
├── docs/                 # Roteiro de experimentos (LaTeX) — ver seção abaixo
└── GUI-TCC.spec          # Receita do PyInstaller para o executável Windows
```

## Download (Windows)

A versão pronta para Windows está na página de [Releases](https://github.com/RISC-V-Azedinha/GUI-TCC/releases): baixe o `GUI-TCC-windows-x64.zip`, extraia e execute `GUI-TCC.exe` (não é preciso instalar Python).

> ⚠️ O firmware da aba de redes neurais (`artifacts/cnn_server.bin`) usa os descritores de camada e os demais recursos da NPU do SoC RISC-V **v1.2.0 ou posterior**. Grave na FPGA o bitstream dessa versão ([releases do RISC-V](https://github.com/RISC-V-Azedinha/RISC-V/releases)); com um bitstream anterior, a inferência não responde.

O executável já inclui o GCC RISC-V (xPack `riscv-none-elf-gcc`) usado pela aba **I/O**; ele é adicionado ao `PATH` da aplicação automaticamente, sem instalação extra.

Rodando pelo código-fonte, a aba **I/O** usa o toolchain do sistema (`riscv64-unknown-elf-gcc`, ex.: pacotes `gcc-riscv64-unknown-elf` e `picolibc-riscv64-unknown-elf` no Ubuntu) ou uma cópia local baixada com:

```bash
python3 tools/fetch_toolchain.py
```

## Como rodar a aplicação

1. Crie o ambiente virtual:
```bash
python3 -m venv .venv
```

2. Ative o ambiente:
```bash
source .venv/bin/activate
```

3. Instale as dependências:
```bash
pip3 install -r requirements.txt
```

4. Execute o script de entrada:
```bash
python3 main.py
```

> Para usar as abas que dependem de hardware real (Upload FPGA, Sync Hardware, OS Console, NN Inference), é necessário ter a placa FPGA conectada via USB/serial.

## Roteiro de Experimentos

O roteiro das aulas práticas está em [`docs/roteiro_experimentos.tex`](docs/roteiro_experimentos.tex). A cada push em `main` que altere `docs/`, o GitHub Actions compila o PDF e o publica no GitHub Pages: [Roteiro (PDF)](https://risc-v-azedinha.github.io/GUI-TCC/roteiro_experimentos.pdf).

Para compilar localmente no VS Code, use a extensão **LaTeX Workshop** (configurada em `.vscode/settings.json`). Pela linha de comando:

```bash
cd docs && latexmk -xelatex -outdir=../build/latex roteiro_experimentos.tex
```

Os arquivos intermediários e o PDF ficam em `build/latex/`, que é ignorado pelo git.

## Publicando uma release

Envie uma tag de versão; o workflow `.github/workflows/release.yml` gera o executável Windows com PyInstaller e cria a release com o `.zip`:

```bash
git tag v1.0.0
git push origin v1.0.0
```