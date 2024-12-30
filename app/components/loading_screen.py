from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel)
from qfluentwidgets import (IndeterminateProgressRing)


class LoadingScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LoadingScreen")
        # Make the widget cover its parent
        self.setFixedSize(parent.size())
        self.setupUi()
        # Hide by default
        self.hide()
        
    def setupUi(self):
        # Semi-transparent background
        self.setStyleSheet("""
            QWidget#LoadingScreen {
                background-color: rgba(0, 0, 0, 150);
            }
            QLabel {
                color: black;
                font-size: 16px;
                font-weight: 700;
                background: transparent;
            }
        """)
        
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)
        
        # Loading spinner
        self.spinner = IndeterminateProgressRing(self)
        self.spinner.setFixedSize(45, 45)
        self.layout.addWidget(self.spinner, alignment=Qt.AlignCenter)
        
        # Loading text
        self.textLabel = QLabel("Loading...", self)
        self.textLabel.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.textLabel, alignment=Qt.AlignCenter)
    
    def setLoadingText(self, text):
        self.textLabel.setText(text)
    
    def showEvent(self, event):
        super().showEvent(event)
        self.spinner.start()
        # Update size when shown
        if self.parent():
            self.setFixedSize(self.parent().size())
    
    def hideEvent(self, event):
        super().hideEvent(event)
        self.spinner.stop()
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Keep the loading screen the same size as its parent
        if self.parent():
            self.setFixedSize(self.parent().size())
