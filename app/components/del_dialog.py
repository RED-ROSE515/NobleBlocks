from qfluentwidgets import MessageBox


class DelDialog(MessageBox):
    def __init__(self, parent=None):
        super().__init__(
            title="Delete Downloaded PDFs",
            content="Are you sure you want to delete the downloaded PDFs?",
            parent=parent
        )
        self.setClosableOnMaskClicked(True)