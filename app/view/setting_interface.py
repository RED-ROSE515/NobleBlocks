# coding:utf-8
import sys

from PySide6.QtCore import Qt

from PySide6.QtWidgets import QWidget,  QVBoxLayout
from qfluentwidgets import FluentIcon as FIF, ComboBoxSettingCard
from qfluentwidgets import InfoBar
from qfluentwidgets import (SettingCardGroup,  SmoothScrollArea,
                            setTheme)

from ..common.config import cfg

class SettingInterface(SmoothScrollArea):
    """ Setting interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.expandLayout = QVBoxLayout(self.scrollWidget)

        # personalization
        self.personalGroup = SettingCardGroup(
            "Personalization", self.scrollWidget)

        if sys.platform == "win32":
            self.backgroundEffectCard = ComboBoxSettingCard(
                cfg.backgroundEffect,
                FIF.BRUSH,
                "Window Background Effect",
                "Set window background transparency effect and material",
                texts=["Acrylic", "Mica", "MicaBlur", "MicaAlt", "Aero"],
                parent=self.personalGroup
            )

        self.zoomCard = ComboBoxSettingCard(
            cfg.dpiScale,
            FIF.ZOOM,
            "Interface Scaling",
            "Change the scaling of application interface",
            texts=[
                "100%", "125%", "150%", "175%", "200%",
                "Auto"
            ],
            parent=self.personalGroup
        )

        # application

        self.__initWidget()

        # Apply QSS
        self.setStyleSheet("""QScrollArea, .QWidget {
                                border: none;
                                background-color: transparent;
                            }""")

    def __initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName('settingInterface')

        # initialize style sheet
        self.scrollWidget.setObjectName('scrollWidget')

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        if sys.platform == "win32":
            self.personalGroup.addSettingCard(self.backgroundEffectCard)
        self.personalGroup.addSettingCard(self.zoomCard)


        # add setting card group to layout
        self.expandLayout.setSpacing(20)
        self.expandLayout.setContentsMargins(36, 30, 36, 30)
        self.expandLayout.addWidget(self.personalGroup)

    def __showRestartTooltip(self):
        """ show restart tooltip """
        InfoBar.success(
            "Configured",
            "Changes will take effect after restart",
            duration=1500,
            parent=self
        )

    def __onBackgroundEffectCardChanged(self, option):
        """ background effect card changed slot """
        self.window().applyBackgroundEffectByCfg()


    def __connectSignalToSlot(self):
        """ connect signal to slot """
        cfg.appRestartSig.connect(self.__showRestartTooltip)
        cfg.themeChanged.connect(setTheme)

        # personalization
        if sys.platform == "win32":
            self.backgroundEffectCard.comboBox.currentIndexChanged.connect(self.__onBackgroundEffectCardChanged)


