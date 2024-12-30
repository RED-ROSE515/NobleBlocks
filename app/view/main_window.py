# coding: utf-8
import ctypes
import sys
from ctypes import byref, c_int

import darkdetect
from PySide6.QtCore import QSize, QThread, Signal, QTimer, QPropertyAnimation
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QGraphicsOpacityEffect
from loguru import logger
from qfluentwidgets import FluentIcon as FIF, setTheme, Theme
from qfluentwidgets import NavigationItemPosition, MSFluentWindow, SplashScreen

from .setting_interface import SettingInterface
from .paper_interface import PaperInterface
from ..common.config import cfg


class CustomSplashScreen(SplashScreen):

    def finish(self):
        """ fade out splash screen """
        opacityEffect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(opacityEffect)
        opacityAni = QPropertyAnimation(opacityEffect, b'opacity', self)
        opacityAni.setStartValue(1)
        opacityAni.setEndValue(0)
        opacityAni.setDuration(200)
        opacityAni.finished.connect(self.deleteLater)
        opacityAni.start()


class ThemeChangedListener(QThread):
    themeChanged = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        darkdetect.listener(self.themeChanged.emit)


class MainWindow(MSFluentWindow):

    def __init__(self):
        super().__init__()
        self.initWindow()

        # create sub interface
        self.settingInterface = SettingInterface(self)
        self.paperInterface = PaperInterface(self)

        # add items to navigation interface
        self.initNavigation()

        # set background effect
        self.applyBackgroundEffectByCfg()

        # create theme change listener
        self.themeChangedListener = ThemeChangedListener(self)
        self.themeChangedListener.themeChanged.connect(self.toggleTheme)
        self.themeChangedListener.start()

        self.splashScreen.finish()

    def initNavigation(self):
        # add navigation items
        self.addSubInterface(self.paperInterface, FIF.DOWNLOAD, "Paper Fetch")
        self.addSubInterface(self.settingInterface, FIF.SETTING, "Settings", position=NavigationItemPosition.BOTTOM)
        

    def initWindow(self):

        if cfg.geometry.value == "Default":
            self.resize(960, 780)
            desktop = QApplication.screens()[0].availableGeometry()
            w, h = desktop.width(), desktop.height()
            self.move(w//2 - self.width()//2, h//2 - self.height()//2)
        else:
            try:
                self.setGeometry(cfg.get(cfg.geometry))
            except Exception as e:
                logger.error(f"Failed to restore geometry: {e}")
                cfg.set(cfg.geometry, "Default")

                self.resize(960, 780)
                desktop = QApplication.screens()[0].availableGeometry()
                w, h = desktop.width(), desktop.height()
                self.move(w//2 - self.width()//2, h//2 - self.height()//2)

        self.setWindowIcon(QIcon(':/image/logo.png'))
        self.setWindowTitle('NobleBlocks')

        # create splash screen
        self.splashScreen = CustomSplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()

        self.show()

        QApplication.processEvents()

    def toggleTheme(self, callback: str):
        if callback == 'Dark':  # PySide6
            setTheme(Theme.DARK, save=False)
            if cfg.backgroundEffect.value in ['Mica', 'MicaBlur', 'MicaAlt']:
                QTimer.singleShot(100, self.applyBackgroundEffectByCfg)
                QTimer.singleShot(200, self.applyBackgroundEffectByCfg)
                QTimer.singleShot(300, self.applyBackgroundEffectByCfg)

        elif callback == 'Light':
            setTheme(Theme.LIGHT, save=False)

        self.applyBackgroundEffectByCfg()

    def applyBackgroundEffectByCfg(self):  
        if sys.platform == 'win32':
            self.windowEffect.removeBackgroundEffect(self.winId())

            if cfg.backgroundEffect.value == 'Acrylic':
                self.windowEffect.setAcrylicEffect(self.winId(), "00000030" if darkdetect.isDark() else "F2F2F230")
            elif cfg.backgroundEffect.value == 'Mica':
                self.windowEffect.setMicaEffect(self.winId(), darkdetect.isDark())
            elif cfg.backgroundEffect.value == 'MicaBlur':
                self.windowEffect.setMicaEffect(self.winId(), darkdetect.isDark())
                self.windowEffect.DwmSetWindowAttribute(self.winId(), 38, byref(c_int(3)), 4)
            elif cfg.backgroundEffect.value == 'MicaAlt':
                self.windowEffect.setMicaEffect(self.winId(), darkdetect.isDark(), True)
            elif cfg.backgroundEffect.value == 'Aero':
                self.windowEffect.setAeroEffect(self.winId())

    def closeEvent(self, event):
        # Intercept close event, hide window instead of exiting
        event.ignore()
        # Save window position
        cfg.set(cfg.geometry, self.geometry())

        self.hide()

    def nativeEvent(self, eventType, message):
        # Handle window reopen events
        if eventType == "windows_generic_MSG":
            msg = ctypes.wintypes.MSG.from_address(message.__int__())

            # WIN_USER = 1024
            if msg.message == 1024 + 1:
                self.show()
                return True, 0

        return super().nativeEvent(eventType, message)
