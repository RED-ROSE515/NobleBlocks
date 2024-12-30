import os

import sys

from PySide6.QtWidgets import QApplication
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


import time
import warnings

import darkdetect

from PySide6.QtGui import QColor

from loguru import logger
from qframelesswindow.utils import getSystemAccentColor

from qfluentwidgets import setTheme, Theme, setThemeColor


import Res_rc

from app.common.methods import loadPlugins
from app.view.main_window import MainWindow


warnings.warn = logger.warning

# Enable Theme
setTheme(Theme.DARK if darkdetect.isDark() else Theme.LIGHT, save=False)


if sys.platform == "win32" or "darwin":
    setThemeColor(getSystemAccentColor(), save=False)
if sys.platform == "linux":

    if 'KDE_SESSION_UID' in os.environ: # KDE Plasma

        import configparser
        config = configparser.ConfigParser()

        config.read(f"/home/{os.getlogin()}/.config/kdeglobals")

        # 获取 DecorationFocus 的值
        if 'Colors:Window' in config:
            color = list(map(int, config.get('Colors:Window', 'DecorationFocus').split(",")))
            setThemeColor(QColor(*color))


w = MainWindow()


pluginsPath=os.path.join(cfg.appPath, "plugins")
loadPlugins(w, pluginsPath)

try:  
    if "--silence" in sys.argv:
        w.hide()
except:
    w.show()

sys.exit(app.exec())
