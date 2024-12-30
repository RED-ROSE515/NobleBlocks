from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, 
                               QListWidget, QTextEdit)
from qfluentwidgets import (FluentIcon as FIF, SmoothScrollArea, PrimaryPushButton,
                           SearchLineEdit, InfoBar, InfoBarPosition, TextEdit)
from app.common.paper_check import check_paper
from app.common.pdf_manager import select_pdf_folder, load_pdfs_to_list, filter_pdfs, open_pdf
from app.components.loading_screen import LoadingScreen
import os


class PaperCheckThread(QThread):
    finished = Signal(str)  # Signal to emit the result
    error = Signal(str)     # Signal to emit any errors
    progress = Signal(str)  # Signal to emit progress updates
    
    def __init__(self, pdf_path):
        super().__init__()
        self.pdf_path = pdf_path
        
    def run(self):
        try:
            self.progress.emit("Starting paper analysis...")
            result = check_paper(self.pdf_path)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class PaperCheckInterface(SmoothScrollArea):
    """ Paper Check Interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.current_folder = None
        self.check_thread = None
        self.loading_screen = None
        self.setupUi()

    def setupUi(self):
        self.setObjectName("PaperCheckInterface")
        self.scrollWidget = QWidget()
        self.expandLayout = QVBoxLayout(self.scrollWidget)

        # Top controls layout
        self.horizontalLayout = QHBoxLayout()
        
        # Folder selection button
        self.selectFolderButton = PrimaryPushButton(self)
        self.selectFolderButton.setIcon(FIF.FOLDER)
        self.selectFolderButton.setText("Select Folder")
        self.selectFolderButton.clicked.connect(self.selectFolder)
        self.horizontalLayout.addWidget(self.selectFolderButton)

        # Search box
        self.searchEdit = SearchLineEdit(self)
        self.searchEdit.setPlaceholderText("Search PDFs")
        self.searchEdit.textChanged.connect(self.filterPdfs)
        self.horizontalLayout.addWidget(self.searchEdit)

        self.expandLayout.addLayout(self.horizontalLayout)

        # Create horizontal layout for PDF list and text edit
        self.contentLayout = QHBoxLayout()

        # Left side - PDF list
        self.leftWidget = QWidget()
        self.leftLayout = QVBoxLayout(self.leftWidget)
        
        # Add Check PDF button
        self.checkButton = PrimaryPushButton()
        self.checkButton.setIcon(FIF.ASTERISK)
        self.checkButton.setText("Check PDF")
        self.checkButton.clicked.connect(self.checkSelectedPdf)
        self.checkButton.setEnabled(False)  # Disable initially
        self.leftLayout.addWidget(self.checkButton)
        
        self.pdfList = QListWidget()
        self.pdfList.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e6f3ff;
                color: black;
            }
        """)
        self.pdfList.itemDoubleClicked.connect(self.openPdf)
        self.pdfList.itemSelectionChanged.connect(self.onPdfSelectionChanged)
        self.leftLayout.addWidget(self.pdfList)
        self.contentLayout.addWidget(self.leftWidget)

        # Right side - Text Edit
        self.rightWidget = QWidget()
        self.rightLayout = QVBoxLayout(self.rightWidget)
        self.outputTextEdit = TextEdit()  # Using QFluentWidgets' TextEdit which supports markdown
        self.outputTextEdit.setReadOnly(True)
        self.outputTextEdit.setStyleSheet("""
            TextEdit {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
            }
        """)
        self.outputTextEdit.setPlaceholderText("Output will be displayed here...")
        self.rightLayout.addWidget(self.outputTextEdit)
        self.contentLayout.addWidget(self.rightWidget)

        # Set the content layout to expand
        self.expandLayout.addLayout(self.contentLayout)

        # Set up the scroll area
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        # Initialize loading screen
        self.loading_screen = LoadingScreen(self)
        self.loading_screen.setLoadingText("Analyzing paper...")

    def selectFolder(self):
        """Open folder selection dialog and load PDFs"""
        folder = select_pdf_folder(self)
        if folder:
            self.current_folder = folder
            self.loadPdfs(folder)

    def loadPdfs(self, folder_path):
        """Load all PDFs from the selected folder"""
        load_pdfs_to_list(folder_path, self.pdfList, self)

    def filterPdfs(self, text):
        """Filter PDFs based on search text"""
        filter_pdfs(self.pdfList, text)

    def openPdf(self, item):
        """Open the selected PDF file"""
        if self.current_folder:
            pdf_path = os.path.join(self.current_folder, item.text())
            open_pdf(pdf_path, self)

    def onPdfSelectionChanged(self):
        """Enable/disable check button based on selection"""
        self.checkButton.setEnabled(bool(self.pdfList.selectedItems()))

    def checkSelectedPdf(self):
        """Check the selected PDF for errors"""
        selected_items = self.pdfList.selectedItems()
        if not selected_items or not self.current_folder:
            return

        pdf_path = os.path.join(self.current_folder, selected_items[0].text())
        self.outputTextEdit.clear()
        self.outputTextEdit.setMarkdown("*Analyzing PDF... Please wait...*")
        
        # Start loading animations
        self.loading_screen.show()
        
        # Create and start the analysis thread
        self.check_thread = PaperCheckThread(pdf_path)
        self.check_thread.finished.connect(self.onAnalysisComplete)
        self.check_thread.error.connect(self.onAnalysisError)
        self.check_thread.progress.connect(self.onAnalysisProgress)
        self.check_thread.start()
    
    def onAnalysisProgress(self, message):
        """Handle progress updates"""
        self.loading_screen.setLoadingText(message)
        self.outputTextEdit.append(message)
    
    def onAnalysisComplete(self, result):
        """Handle successful analysis completion"""
        # Hide loading screen
        self.loading_screen.hide()
        
        self.outputTextEdit.append("\nAnalysis Complete!\n")
        self.outputTextEdit.append("Summary of Findings:")
        self.outputTextEdit.append(result)
        self.outputTextEdit.setMarkdown(self.outputTextEdit.toPlainText())
        
        # Stop loading animation
        self.checkButton.setEnabled(True)
        self.pdfList.setEnabled(True)
        
        # Clean up thread
        self.check_thread = None
    
    def onAnalysisError(self, error_msg):
        """Handle analysis error"""
        # Hide loading screen
        self.loading_screen.hide()
        
        self.outputTextEdit.append(f"\nError during analysis: {error_msg}")
            
        InfoBar.error(
            title='Error',
            content=f'Failed to analyze PDF: {error_msg}',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            parent=self
        )
        
        # Stop loading animation
        self.checkButton.setEnabled(True)
        self.pdfList.setEnabled(True)
        
        # Clean up thread
        self.check_thread = None
