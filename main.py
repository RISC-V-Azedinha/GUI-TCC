# main.py
import os
import sys
import platform

# Folga para a moldura da janela (bordas e barra de título) ao decidir se a janela cabe na tela.
WINDOW_FRAME_W, WINDOW_FRAME_H = 16, 48


def fits_on_screen(ideal_w: int, ideal_h: int, avail_w: int, avail_h: int) -> bool:
    """A janela com os laboratórios inteiros (mais a moldura) cabe na área útil da tela?"""
    return ideal_w + WINDOW_FRAME_W <= avail_w and ideal_h + WINDOW_FRAME_H <= avail_h


def fit_minimum(min_w: int, min_h: int, avail_w: int, avail_h: int):
    """Tamanho mínimo da janela: o do layout, limitado ao que a tela comporta.

    Sem esse limite, em uma tela menor que o mínimo do layout o Windows abriria a janela maior
    do que o monitor, com as bordas direita e inferior fora da tela.
    """
    return (min(min_w, max(avail_w - WINDOW_FRAME_W, 640)),
            min(min_h, max(avail_h - WINDOW_FRAME_H, 480)))


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

    # Usa a escala do Windows sem arredondar (o Qt 5 transformaria 150% em 200%).
    #
    # A escala NUNCA é reduzida (QT_SCALE_FACTOR < 1). O Qt 5 encolhe a janela por esse fator, mas
    # desenha os widgets e as fontes no tamanho original: o conteúdo transborda e a interface sai
    # cortada (rótulos pela metade, botões sem texto, itens do menu que somem) — exatamente o que
    # acontecia em 1440x900. Tela pequena é resolvida pela rolagem dos laboratórios, não pela escala.
    os.environ['QT_SCALE_FACTOR_ROUNDING_POLICY'] = 'PassThrough'

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

    # Quem decide é a tela medida pelo próprio Qt (px lógicos, já com a escala do sistema em
    # vigor). Em tela grande a janela abre com os laboratórios inteiros. Em tela pequena ela abre
    # maximizada e o que não couber é alcançado pelas barras de rolagem dos laboratórios.
    available = app.primaryScreen().availableGeometry()
    ideal, minimum = main_window.sizeHint(), main_window.minimumSizeHint()
    main_window.setMinimumSize(*fit_minimum(minimum.width(), minimum.height(),
                                            available.width(), available.height()))

    if fits_on_screen(ideal.width(), ideal.height(), available.width(), available.height()):
        main_window.resize(ideal)
        main_window.show()
    else:
        main_window.showMaximized()

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
