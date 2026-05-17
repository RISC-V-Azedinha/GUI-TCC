# main.py
import os
import sys
import platform

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

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, Qt
import qtawesome as qta
from ui.styles import STYLESHEET

from core.emulator import RISCV_Emulator
from core.npu import NPUModel
from ui.main_window import RiscVEduApp
from controllers.main_controller import MainController
from controllers.npu_controller import NPUController

def main():
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
    
    npu_model = NPUModel()
    npu_controller = NPUController(npu_model, main_window.npu_view)
    
    app.aboutToQuit.connect(rv32i_controller.cleanup_hardware)
    
    main_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()