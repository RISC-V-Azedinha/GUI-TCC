# core/toolchain.py
import glob
import os
import shutil
import subprocess

from core.paths import artifact_path, project_root

# Evita que cada chamada ao GCC abra uma janela de console no executável Windows
NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

# Prefixos aceitos: o do toolchain distribuído (xPack) e o dos pacotes do Linux
PREFIXES = ("riscv-none-elf-", "riscv64-unknown-elf-")


def bundled_bin_dir() -> str:
    """Pasta bin/ do toolchain distribuído junto com a aplicação (tools/fetch_toolchain.py)."""
    return os.path.join(project_root(), "toolchain", "bin")


def add_bundled_to_path() -> None:
    """Coloca o toolchain distribuído no início do PATH do processo (não altera o PATH do sistema)."""
    bin_dir = bundled_bin_dir()
    path = os.environ.get("PATH", "")
    if os.path.isdir(bin_dir) and bin_dir not in path.split(os.pathsep):
        os.environ["PATH"] = bin_dir + os.pathsep + path


def find_toolchain():
    """
    Localiza o GCC RISC-V, priorizando o distribuído com a aplicação.
    Retorna (gcc, objcopy, flags_extras) ou None se nenhum toolchain for encontrado.
    """
    candidates = [os.path.join(bundled_bin_dir(), f"{p}gcc") for p in PREFIXES]
    candidates += [f"{p}gcc" for p in PREFIXES]

    for gcc in candidates:
        gcc_path = shutil.which(gcc)
        if not gcc_path:
            continue
        objcopy_path = shutil.which(gcc_path[:gcc_path.rfind("gcc")] + "objcopy" + os.path.splitext(gcc_path)[1])
        if not objcopy_path:
            continue
        return gcc_path, objcopy_path, _libc_flags(gcc_path)
    return None


def gcc_command(gcc: str, libc_flags: list, elf_path: str, c_file: str) -> list:
    """Linha de comando que compila e liga o firmware do Lab 2 (start.s + BSP + código do aluno).

    O BSP (artifacts/bsp) traz o mapa de memória, a HAL de GPIO (hal/hal_gpio.h) e a divisão em
    software (math_ops.c), já que o RV32I não tem instrução de divisão.
    """
    bsp_dir = artifact_path("bsp")
    return [
        gcc,
        "-march=rv32i", "-mabi=ilp32", "-nostdlib", "-nostartfiles", "-g", *libc_flags,
        f"-I{bsp_dir}",
        "-T", artifact_path("link.ld"),
        "-o", elf_path,
        artifact_path("start.s"),
        *glob.glob(os.path.join(bsp_dir, "**", "*.c"), recursive=True),
        c_file,
    ]


def _libc_flags(gcc_path: str) -> list:
    """Usa os headers da picolibc quando o toolchain a oferece (pacotes do Linux); senão, os da newlib."""
    try:
        out = subprocess.run([gcc_path, "-print-file-name=picolibc.specs"], capture_output=True,
                             text=True, timeout=10, creationflags=NO_WINDOW).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return []
    return ["--specs=picolibc.specs"] if os.path.isabs(out) and os.path.exists(out) else []
