import os

import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from qfluentwidgets import qconfig

from app.common.config import cfg


if "--debug" in sys.argv:
    cfg.appPath = "./"
    qconfig.load('./NobleBlocks Settings.json', cfg)
else:  
    cfg.appPath = os.path.dirname(sys.executable)
    qconfig.load('{}/NobleBlocks Settings.json'.format(os.path.dirname(sys.executable)), cfg)

    def exceptionHandler(type, value, traceback):  
        logger.exception(f"Unexpected error! {type}: {value}. Traceback: {traceback}")

    sys.excepthook = exceptionHandler

if cfg.get(cfg.dpiScale) == "Auto":
    pass
else:
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpiScale))

app = QApplication(sys.argv)

# Set application icon
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle (frozen)
    application_path = sys._MEIPASS
else:
    # If the application is run from a Python interpreter
    application_path = os.path.dirname(os.path.abspath(__file__))

icon_path = os.path.join(application_path, "images", "logo.ico")
app.setWindowIcon(QIcon(icon_path))

from PySide6.QtCore import QSharedMemory


sharedMemory = QSharedMemory()
sharedMemory.setKey("NobleBlocks")

if sharedMemory.attach(): 
    if sys.platform == "win32":
        import win32gui
        import win32con

        hWnd = win32gui.FindWindow(None, "NobleBlocks")
        win32gui.ShowWindow(hWnd, 1)

        win32gui.SendMessage(hWnd, win32con.WM_USER + 1, 0, 0)

        win32gui.SetForegroundWindow(hWnd)

    sys.exit(-1)

sharedMemory.create(1)

import warnings

import darkdetect

from loguru import logger
from qframelesswindow.utils import getSystemAccentColor
from qfluentwidgets import setTheme, Theme, setThemeColor
from app.view.main_window import MainWindow


warnings.warn = logger.warning

# Enable Theme
setTheme(Theme.DARK if darkdetect.isDark() else Theme.LIGHT, save=False)


if sys.platform == "win32" or "darwin":
    setThemeColor(getSystemAccentColor(), save=False)


w = MainWindow()

try:  
    if "--silence" in sys.argv:
        w.hide()
except:
    w.show()

sys.exit(app.exec())
