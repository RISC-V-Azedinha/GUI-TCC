# main.py
import os
import sys
import platform

# Tamanho (px lógicos, com a moldura da janela) em que a janela mostra os laboratórios inteiros:
# largura do lab RV32I + barra lateral e altura do lab NPU + cabeçalho. Abaixo disso a área dos
# laboratórios ganha barras de rolagem (ver RiscVEduApp.setup_main_area), em vez de se desfigurar.
MIN_WINDOW_W, MIN_WINDOW_H = 1580, 980

# Limite de redução da escala: abaixo disso o texto fica pequeno demais para uma sala de aula.
# O que não couber depois desse limite passa a ser alcançado pelas barras de rolagem.
MIN_SCALE_RATIO = 0.7

# Espaço reservado para a moldura da janela (bordas e barra de título) ao encaixar o tamanho
# mínimo na área útil da tela.
WINDOW_FRAME_W, WINDOW_FRAME_H = 16, 48


def fit_minimum(ideal_w: int, ideal_h: int, avail_w: int, avail_h: int):
    """Tamanho mínimo da janela: o dos laboratórios inteiros, limitado ao que a tela comporta.

    Sem esse limite, uma tela menor que os laboratórios espremia os painéis abaixo do mínimo e a
    interface saía desfigurada. Com ele a janela cabe na tela e o resto é rolagem.
    """
    return (min(ideal_w, max(avail_w - WINDOW_FRAME_W, 640)),
            min(ideal_h, max(avail_h - WINDOW_FRAME_H, 480)))


def fit_scale(work_w: float, work_h: float, os_scale: float) -> float:
    """Maior escala (até a do sistema) com a qual a janela mínima cabe na área útil (px físicos)."""
    return min(os_scale, work_w / MIN_WINDOW_W, work_h / MIN_WINDOW_H)


def scale_ratio(work_w: float, work_h: float, os_scale: float):
    """Valor do QT_SCALE_FACTOR, ou None quando a janela já cabe ou a medição não é confiável.

    Só devolve um número > 0: o Qt 5 descarta em silêncio um QT_SCALE_FACTOR igual a zero (é o que
    acontecia quando o Windows não informava a área útil), e a janela abria maximizada na escala
    cheia — grande demais para a tela, com os painéis comprimidos e a interface desfigurada.
    """
    if not (work_w > 0 and work_h > 0 and 0.5 <= os_scale <= 5):
        return None
    ratio = fit_scale(work_w, work_h, os_scale) / os_scale
    return max(ratio, MIN_SCALE_RATIO) if ratio < 0.995 else None


def _windows_screen():
    """Área útil da tela principal em px físicos e escala do Windows, lidas antes do Qt existir."""
    import ctypes
    from ctypes import wintypes
    user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32

    # DESKTOPHORZRES (físico) / HORZRES (virtualizado enquanto o processo não é DPI-aware).
    # Drivers de vídeo genéricos e sessões remotas podem devolver 0: aí não há virtualização a medir.
    virtualization = 1.0
    hdc = user32.GetDC(0)
    if hdc:
        try:
            physical, logical = gdi32.GetDeviceCaps(hdc, 118), gdi32.GetDeviceCaps(hdc, 8)
        finally:
            user32.ReleaseDC(0, hdc)
        if physical > 0 and logical > 0:
            virtualization = physical / logical

    work = wintypes.RECT()
    if user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(work), 0):  # SPI_GETWORKAREA
        work_w, work_h = work.right - work.left, work.bottom - work.top
    else:  # sem área útil, usa a tela inteira (SM_CXSCREEN / SM_CYSCREEN)
        work_w, work_h = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

    try:
        os_scale = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
    except (OSError, AttributeError):
        os_scale = 0
    if not 0.5 <= os_scale <= 5:  # SCALE_INVALID (0) ou valor sem sentido: cai na virtualização
        os_scale = virtualization

    return work_w * virtualization, work_h * virtualization, os_scale


# =====================================================================
# TRUQUES AGRESSIVOS PARA MODO ESCURO E SCALING (LINUX & WINDOWS)
# =====================================================================
if platform.system() == "Linux":
    # Desativa o Wayland nativo para o Qt (que força barras brancas e causa erros)
    # e força o uso do servidor X11 (XWayland), que respeita o Dark Mode do sistema.
    os.environ['QT_QPA_PLATFORM'] = 'xcb'
    os.environ['QT_QPA_PLATFORMTHEME'] = 'gtk3'
    os.environ['GTK_THEME'] = 'Adwaita:dark'

    # FIX DO ZOOM: Desativa o auto-scaling agressivo do Linux e aplica um zoom
    # manual de 125% (1.25). Se achar que ainda está pequeno, mude para '1.5'.
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '0'
    os.environ['QT_SCALE_FACTOR'] = '1.50'

elif platform.system() == "Windows":
    sys.argv += ['-platform', 'windows:darkmode=1']

    # Usa a escala do Windows sem arredondar (o Qt 5 transformaria 150% em 200%) e, se a
    # janela mínima não couber na tela, reduz a escala só o necessário, mantendo a proporção.
    os.environ['QT_SCALE_FACTOR_ROUNDING_POLICY'] = 'PassThrough'
    try:
        _ratio = scale_ratio(*_windows_screen())
    except (OSError, AttributeError, ValueError, ZeroDivisionError):
        _ratio = None  # mantém a escala do sistema
    if _ratio:
        os.environ['QT_SCALE_FACTOR'] = f"{_ratio:.3f}"

# Executável sem console (PyInstaller windowed): sys.stdout/sys.stderr são None, e bibliotecas
# que escrevem progresso (ex.: o download do MNIST no Lab 7) falhariam com "'NoneType' ... 'write'".
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

# --selftest: usado pelo CI da release. Abre a janela principal, fecha em seguida e grava
# o resultado em selftest.log (o executável não tem console para exibir erros).
SELFTEST = "--selftest" in sys.argv


def main():
    # O torch precisa ser carregado ANTES do PyQt5: no Windows, o Qt traz um runtime
    # Visual C++ antigo (msvcp140 14.26) e, se ele for carregado primeiro, as DLLs do
    # torch (compiladas com MSVC >= 14.40) falham ao inicializar ("WinError 1114").
    import torch  # noqa: F401

    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QTimer, Qt
    from ui.styles import STYLESHEET

    from core.emulator import RISCV_Emulator
    from core.npu import NPUModel
    from ui.main_window import RiscVEduApp
    from controllers.main_controller import MainController
    from controllers.npu_controller import NPUController
    from core.toolchain import add_bundled_to_path, find_toolchain

    # Disponibiliza o GCC RISC-V distribuído com a aplicação (Lab 2) para os subprocessos
    add_bundled_to_path()

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # FIX DA LINHA: Limpeza rigorosa das bordas e alturas para garantir
    # que o menu da esquerda e o cabeçalho casam pixel a pixel.
    PATCH_CSS = """
    #AppTitle {
        min-height: 70px;
        max-height: 70px;
        border: none;
        border-bottom: 1px solid #1e293b;
        margin: 0px;
        padding: 0px 20px;
    }
    #Header {
        min-height: 70px;
        max-height: 70px;
        border: none;
        border-bottom: 1px solid #1e293b;
        margin: 0px;
        padding: 0px;
    }
    """
    app.setStyleSheet(STYLESHEET + PATCH_CSS)

    main_window = RiscVEduApp()

    rv32i_model = RISCV_Emulator()
    rv32i_controller = MainController(rv32i_model, main_window.rv32i_view)
    main_window.stacked_widget.currentChanged.connect(rv32i_controller.on_tab_changed)

    rv32i_controller.io_view = main_window.io_view
    main_window.io_view.request_compile_and_upload.connect(rv32i_controller.handle_io_compile_upload)
    main_window.io_view.request_uart_send.connect(rv32i_controller.handle_io_uart_transmit)

    npu_model = NPUModel()
    npu_controller = NPUController(npu_model, main_window.npu_view)

    app.aboutToQuit.connect(rv32i_controller.cleanup_hardware)

    # Quem decide é a tela medida pelo próprio Qt (px lógicos, já com a escala em vigor), e não a
    # estimativa feita antes do Qt existir. Em tela grande nada muda: a janela abre (e não encolhe
    # além) do tamanho dos laboratórios inteiros. Em tela pequena o mínimo cede até caber na área
    # útil, a janela abre maximizada e o que sobrar é alcançado pelas barras de rolagem.
    available = app.primaryScreen().availableGeometry()
    ideal = main_window.sizeHint()
    main_window.setMinimumSize(*fit_minimum(ideal.width(), ideal.height(),
                                            available.width(), available.height()))

    if available.width() < MIN_WINDOW_W or available.height() < MIN_WINDOW_H:
        main_window.showMaximized()
    else:
        main_window.resize(ideal)
        main_window.show()

    if SELFTEST:
        toolchain = find_toolchain()
        _selftest_log(f"torch {torch.__version__}: tensor {torch.ones(2).sum().item()}")
        _selftest_log(f"toolchain: {toolchain[0] if toolchain else 'NAO ENCONTRADO'}")
        _selftest_log(f"janela principal: {main_window.windowTitle()}")

        def _report_geometry():
            avail = app.primaryScreen().availableGeometry()
            frame = main_window.frameGeometry()
            minimum = main_window.minimumSizeHint()
            _selftest_log(f"escala: {main_window.devicePixelRatioF():.3f} (QT_SCALE_FACTOR={os.environ.get('QT_SCALE_FACTOR', '-')}) | "
                          f"área útil: {avail.width()}x{avail.height()} | janela: {frame.width()}x{frame.height()} | "
                          f"mínimo do layout: {minimum.width()}x{minimum.height()} | cabe na tela: {avail.contains(frame)}")

        QTimer.singleShot(1000, _report_geometry)
        QTimer.singleShot(1500, app.quit)

    sys.exit(app.exec_())


def _selftest_log(line: str) -> None:
    base = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base, "selftest.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")


if __name__ == "__main__":
    if not SELFTEST:
        main()
    else:
        try:
            main()
        except SystemExit as exit_:
            _selftest_log("OK" if not exit_.code else f"FALHA: código de saída {exit_.code}")
            raise
        except BaseException:
            import traceback
            _selftest_log("FALHA:\n" + traceback.format_exc())
            os._exit(1)
