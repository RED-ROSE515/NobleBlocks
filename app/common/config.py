# coding:utf-8
import sys

from PySide6.QtCore import QDir, QRect
from qfluentwidgets import (QConfig, ConfigItem, OptionsConfigItem, BoolValidator,
                            OptionsValidator, RangeConfigItem, RangeValidator,
                            FolderValidator, ConfigValidator, ConfigSerializer)

class GeometryValidator(ConfigValidator):  
    def validate(self, value: QRect) -> bool:
        if value == "Default":
            return True
        if type(value) == QRect:
            return True

    def correct(self, value) -> str:
        return value if self.validate(value) else "Default"

class GeometrySerializer(ConfigSerializer):  
    def serialize(self, value: QRect) -> str:
        if value == "Default":
            return value
        return f"{value.x()},{value.y()},{value.width()},{value.height()}"

    def deserialize(self, value: str) -> QRect:
        if value == "Default":
            return value
        x, y, w, h = map(int, value.split(","))
        return QRect(x, y, w, h)

class Config(QConfig):
    """ Config of application """
    # download
    downloadFolder = ConfigItem(
        "Download", "DownloadFolder", QDir.currentPath(), FolderValidator())

    maxBlockNum = RangeConfigItem("Download", "MaxBlockNum", 8, RangeValidator(1, 256))
    autoSpeedUp = ConfigItem("Download", "AutoSpeedUp", True, BoolValidator())

    # personalization
    if sys.platform == "win32":
        backgroundEffect = OptionsConfigItem("Personalization", "BackgroundEffect", "Mica", OptionsValidator(["Acrylic", "Mica", "MicaBlur", "MicaAlt", "Aero"]))
    dpiScale = OptionsConfigItem(
        "Personalization", "DpiScale", "Auto", OptionsValidator([1, 1.25, 1.5, 1.75, 2, "Auto"]), restart=True)

    # software
    checkUpdateAtStartUp = ConfigItem("Software", "CheckUpdateAtStartUp", True, BoolValidator())
    autoRun = ConfigItem("Software", "AutoRun", False, BoolValidator())
    geometry = ConfigItem("Software", "Geometry", "Default", GeometryValidator(), GeometrySerializer())  
    appPath = "./"


YEAR = 2018
DOWN_DIR = r"C:\Papers"
PAGE = 3

cfg = Config()
