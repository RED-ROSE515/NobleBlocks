import os
from PySide6.QtWidgets import QFileDialog, QListWidgetItem
from PySide6.QtCore import Qt
from qfluentwidgets import FluentIcon as FIF, InfoBar, InfoBarPosition
from qfluentwidgets.common.icon import Icon


def select_pdf_folder(parent, default_path="C:\\Papers"):
    """Open folder selection dialog and return selected folder path"""
    if not os.path.exists(default_path):
        default_path = "C:\\"
        
    folder = QFileDialog.getExistingDirectory(
        parent,
        "Select Folder",
        default_path,
        QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
    )
    return folder if folder else None


def load_pdfs_to_list(folder_path, list_widget, parent=None):
    """Load all PDFs from the selected folder into the list widget"""
    list_widget.clear()
    try:
        pdf_files = [f for f in os.listdir(folder_path) 
                    if f.lower().endswith('.pdf')]
        
        for pdf in sorted(pdf_files):
            item = QListWidgetItem(pdf)
            item.setIcon(Icon(FIF.DOCUMENT))
            list_widget.addItem(item)

        if parent:
            InfoBar.success(
                title='Success',
                content=f'Found {len(pdf_files)} PDF files',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=parent
            )
            
        return len(pdf_files)
    except Exception as e:
        if parent:
            InfoBar.error(
                title='Error',
                content=f'Failed to load PDFs: {str(e)}',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                parent=parent
            )
        return 0


def filter_pdfs(list_widget, search_text):
    """Filter PDFs in the list widget based on search text"""
    for i in range(list_widget.count()):
        item = list_widget.item(i)
        item.setHidden(search_text.lower() not in item.text().lower())


def open_pdf(pdf_path, parent=None):
    """Open the PDF file using the system default application"""
    try:
        os.startfile(pdf_path) if os.name == 'nt' else \
        os.system(f'xdg-open "{pdf_path}"')
    except Exception as e:
        if parent:
            InfoBar.error(
                title='Error',
                content=f'Failed to open PDF: {str(e)}',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                parent=parent
            ) 