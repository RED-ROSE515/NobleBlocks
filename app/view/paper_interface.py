from PySide6.QtCore import Qt, QProcess
from PySide6.QtWidgets import (QWidget, QFrame, QHBoxLayout, QVBoxLayout, 
                              QSpacerItem, QSizePolicy, QTextEdit)
from qfluentwidgets import (FluentIcon as FIF, SmoothScrollArea, TitleLabel, 
                           PrimaryPushButton, PushButton, SearchLineEdit)
from ..components.del_dialog import DelDialog
from ..common.config import PAGE, DOWN_DIR, YEAR

class PaperInterface(SmoothScrollArea):
    """ Paper interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setObjectName("TaskInterface")
        self.status = 'paused'
        self.process = QProcess()
        # Set process channel mode to merge stdout and stderr
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.handle_output)
        self.process.readyReadStandardError.connect(self.handle_error)
        # Add finished signal handler
        self.process.finished.connect(self.handle_finished)
        
        self.setupUi()

        self.allStartButton.clicked.connect(self.allStartTasks)
        self.allPauseButton.clicked.connect(self.allPauseTasks)
        self.allDeleteButton.clicked.connect(self.allDeleteTasks)

        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        self.setStyleSheet("""QScrollArea, .QWidget {
                                border: none;
                                background-color: transparent;
                            }""")

    def setupUi(self):
        self.setMinimumWidth(816)
        self.setFrameShape(QFrame.NoFrame)
        self.scrollWidget = QWidget()
        self.scrollWidget.setObjectName("scrollWidget")
        self.scrollWidget.setMinimumWidth(816)
        self.expandLayout = QVBoxLayout(self.scrollWidget)
        self.expandLayout.setObjectName("expandLayout")
        self.expandLayout.setAlignment(Qt.AlignTop)
        self.expandLayout.setContentsMargins(11, 11, 11, 0)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setContentsMargins(2,2,2,2)

        self.searchEdit = SearchLineEdit(self)
        self.searchEdit.setObjectName(u"searchEdit")
        self.horizontalLayout.addWidget(self.searchEdit)
        
        self.allStartButton = PrimaryPushButton(self)
        self.allStartButton.setObjectName(u"allStartButton")
        self.allStartButton.setIcon(FIF.PLAY)
        self.horizontalLayout.addWidget(self.allStartButton)

        self.allPauseButton = PushButton(self)
        self.allPauseButton.setObjectName(u"allPauseButton")
        self.allPauseButton.setIcon(FIF.PAUSE)
        self.horizontalLayout.addWidget(self.allPauseButton)

        self.allDeleteButton = PushButton(self)
        self.allDeleteButton.setObjectName(u"allDeleteButton")
        self.allDeleteButton.setIcon(FIF.DELETE)
        self.horizontalLayout.addWidget(self.allDeleteButton)

        self.horizontalLayout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.allStartButton.setText("Start")
        self.allPauseButton.setText("Pause")
        self.allDeleteButton.setText("Delete")

        self.expandLayout.addLayout(self.horizontalLayout)

        self.title = TitleLabel("Download Scientific Papers and ManuScripts", self.scrollWidget)
        self.title.setObjectName("title")
        self.title.setAlignment(Qt.AlignCenter)
        self.expandLayout.addWidget(self.title)
        self.scrollWidget.setMinimumWidth(816)

        # Add text view for output
        self.outputText = QTextEdit(self.scrollWidget)
        self.outputText.setReadOnly(True)
        self.outputText.setMinimumHeight(300)
        self.outputText.setStyleSheet("""
            QTextEdit {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        self.expandLayout.addWidget(self.outputText)

        # Modify search edit
        self.searchEdit.setPlaceholderText("Enter search query for papers")
        self.searchEdit.setMinimumWidth(300)

    def handle_output(self):
        """Handle process standard output"""
        data = self.process.readAllStandardOutput()
        text = bytes(data).decode('utf-8', errors='replace')
        if text:
            self.outputText.append(text.strip())
            # Scroll to bottom
            self.outputText.verticalScrollBar().setValue(
                self.outputText.verticalScrollBar().maximum()
            )

    def handle_error(self):
        """Handle process standard error"""
        data = self.process.readAllStandardError()
        text = bytes(data).decode('utf-8', errors='replace')
        if text:
            self.outputText.append(f"Error: {text.strip()}")
            # Scroll to bottom
            self.outputText.verticalScrollBar().setValue(
                self.outputText.verticalScrollBar().maximum()
            )

    def handle_finished(self, exit_code, exit_status):
        """Handle process completion"""
        if exit_code == 0:
            self.outputText.append("\nProcess completed successfully!")
        else:
            self.outputText.append(f"\nProcess failed with exit code: {exit_code}")

    def allStartTasks(self):
        query = self.searchEdit.text()
        if not query:
            self.outputText.append("Please enter a search query first!")
            return
       
        # Show the command being executed
        program = "py"  
        arguments = [
            "-m", 
            "PyPaperBot",
            f"--query={query}",  # Removed extra quotes
            f"--scholar-pages={PAGE}",
            f"--min-year={YEAR}",
            f"--dwn-dir={DOWN_DIR}",
            "--scihub-mirror=https://sci-hub.do"
        ]
        
        # Display the command that's being run
        command = f"{program} {' '.join(arguments)}"
        self.outputText.append(f"Executing command:\n{command}\n")
        
        # Set working directory and start the process
        self.process.setWorkingDirectory(DOWN_DIR)
        self.process.start(program, arguments)

    def allPauseTasks(self):
        if self.process.state() == QProcess.Running:
            self.process.terminate()
            self.outputText.append("Process terminated")

    def allDeleteTasks(self):
        dialog = DelDialog(self.window())
        if dialog.exec():
            completely = dialog.checkBox.isChecked()
            if completely:
                self.outputText.clear()
                if self.process.state() == QProcess.Running:
                    self.process.terminate()

        dialog.deleteLater()
