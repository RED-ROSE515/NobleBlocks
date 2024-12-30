# coding:utf-8
import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, QResource
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QWidget, QFileDialog, QVBoxLayout, QApplication, QButtonGroup, QHBoxLayout, QSpacerItem, \
    QSizePolicy
from qfluentwidgets import FluentIcon as FIF, InfoBarPosition, ExpandGroupSettingCard, ConfigItem, \
    BodyLabel, RadioButton, ComboBox, LineEdit, ComboBoxSettingCard, FlyoutView, Flyout
from qfluentwidgets import InfoBar
from qfluentwidgets import (SettingCardGroup, SwitchSettingCard, PushSettingCard,
                            HyperlinkCard, PrimaryPushSettingCard, SmoothScrollArea,
                            setTheme, RangeSettingCard)

from ..common.config import cfg, FEEDBACK_URL, AUTHOR, VERSION, YEAR, AUTHOR_URL
from ..common.methods import getSystemProxy
from ..components.update_dialog import checkUpdate


class CustomProxySettingCard(ExpandGroupSettingCard):
    """ Custom proxyServer setting card """

    def __init__(self, configItem: ConfigItem, parent=None):
        """
        Parameters
        ----------
        configItem: ColorConfigItem
            options config item

        parent: QWidget
            parent window
        """
        icon = FIF.GLOBE
        title = "Proxy"
        content = "Set proxy server for connections"

        super().__init__(icon, title, content, parent=parent)

        self.configItem = configItem

        self.choiceLabel = BodyLabel(self)

        self.radioWidget = QWidget(self.view)
        self.radioLayout = QVBoxLayout(self.radioWidget)
        self.offRadioButton = RadioButton(
            "No Proxy", self.radioWidget)
        self.defaultRadioButton = RadioButton(
            "Auto-detect System Proxy", self.radioWidget)
        self.customRadioButton = RadioButton(
            "Use Custom Proxy", self.radioWidget)

        self.buttonGroup = QButtonGroup(self)

        self.customProxyWidget = QWidget(self.view)
        self.customProxyLayout = QHBoxLayout(self.customProxyWidget)
        self.customLabel = BodyLabel(
            "Edit Proxy Server: ", self.customProxyWidget)
        self.customProtocolComboBox = ComboBox(self.customProxyWidget)
        self.customProtocolComboBox.addItems(["socks5", "http", "https"])
        self.label_1 = BodyLabel("://", self.customProxyWidget)
        self.customIPLineEdit = LineEdit(self.customProxyWidget)
        self.customIPLineEdit.setPlaceholderText("Proxy IP Address")
        self.label_2 = BodyLabel(":", self.customProxyWidget)
        self.customPortLineEdit = LineEdit(self.customProxyWidget)
        self.customPortLineEdit.setPlaceholderText("Port")

        self.__initWidget()

        if self.configItem.value == "Auto":
            self.defaultRadioButton.setChecked(True)
            self.__onRadioButtonClicked(self.defaultRadioButton)
        elif self.configItem.value == "Off":
            self.offRadioButton.setChecked(True)
            self.__onRadioButtonClicked(self.offRadioButton)
        else:
            self.customRadioButton.setChecked(True)
            self.__onRadioButtonClicked(self.customRadioButton)
            self.customProtocolComboBox.setCurrentText(self.configItem.value[:self.configItem.value.find("://")])
            _ = self.configItem.value[self.configItem.value.find("://")+3:].split(":")
            self.customIPLineEdit.setText(_[0])
            self.customPortLineEdit.setText(_[1])

            self.choiceLabel.setText(self.buttonGroup.checkedButton().text())
            self.choiceLabel.adjustSize()

    def __initWidget(self):
        self.__initLayout()

        self.buttonGroup.buttonClicked.connect(self.__onRadioButtonClicked)

    def __initLayout(self):
        self.addWidget(self.choiceLabel)

        self.radioLayout.setSpacing(19)
        self.radioLayout.setAlignment(Qt.AlignTop)
        self.radioLayout.setContentsMargins(48, 18, 0, 18)

        self.buttonGroup.addButton(self.offRadioButton)
        self.buttonGroup.addButton(self.defaultRadioButton)
        self.buttonGroup.addButton(self.customRadioButton)

        self.radioLayout.addWidget(self.offRadioButton)
        self.radioLayout.addWidget(self.defaultRadioButton)
        self.radioLayout.addWidget(self.customRadioButton)
        self.radioLayout.setSizeConstraint(QVBoxLayout.SetMinimumSize)

        self.customProxyLayout.setContentsMargins(48, 18, 44, 18)
        self.customProxyLayout.addWidget(self.customLabel, 0, Qt.AlignLeft)
        self.customProxyLayout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.customProxyLayout.addWidget(self.customProtocolComboBox, 0, Qt.AlignLeft)
        self.customProxyLayout.addWidget(self.label_1, 0, Qt.AlignLeft)
        self.customProxyLayout.addWidget(self.customIPLineEdit, 0, Qt.AlignLeft)
        self.customProxyLayout.addWidget(self.label_2, 0, Qt.AlignLeft)
        self.customProxyLayout.addWidget(self.customPortLineEdit, 0, Qt.AlignLeft)
        self.customProxyLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.addGroupWidget(self.radioWidget)
        self.addGroupWidget(self.customProxyWidget)

    def __onRadioButtonClicked(self, button: RadioButton):
        """ radio button clicked slot """
        if button.text() == self.choiceLabel.text():
            return

        self.choiceLabel.setText(button.text())
        self.choiceLabel.adjustSize()

        if button is self.defaultRadioButton:  # Auto
            # Disable custom options
            self.customProxyWidget.setDisabled(True)

            _ = getSystemProxy()
            # Analyze SystemProxy, it can be None, "", or format like "http://127.0.0.1:1080"
            # If not empty, auto-fill custom options
            if _:
                protocol = _[:_.find("://")]
                self.customProtocolComboBox.setCurrentText(protocol)
                _ = _[_.find("://")+3:].split(":")
                self.customIPLineEdit.setText(_[0])
                self.customPortLineEdit.setText(_[1])
            else:
                self.customProtocolComboBox.setCurrentText("")
                self.customIPLineEdit.setText("No proxy detected")
                self.customPortLineEdit.setText("")

            cfg.set(self.configItem, "Auto")

        elif button is self.offRadioButton:  # Off
            # Disable custom options
            self.customProxyWidget.setDisabled(True)

            cfg.set(self.configItem, "Off")

        elif button is self.customRadioButton:
            # Enable custom options
            self.customProxyWidget.setDisabled(False)

    def leaveEvent(self, event): # Check if custom options are valid and save config when mouse leaves
        if self.customRadioButton.isChecked():
            protocol = self.customProtocolComboBox.currentText()
            ip = self.customIPLineEdit.text()
            port = self.customPortLineEdit.text()

            proxyServer = f"{protocol}://{ip}:{port}"
            if cfg.proxyServer.validator.PATTERN.match(proxyServer):
                cfg.set(self.configItem, proxyServer)
            else:
                self.defaultRadioButton.click()
                self.defaultRadioButton.setChecked(True)



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


