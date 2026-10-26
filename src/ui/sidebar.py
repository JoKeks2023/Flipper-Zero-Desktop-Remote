from PySide6.QtCore import Signal
from PySide6.QtWidgets import QButtonGroup, QPushButton, QVBoxLayout, QWidget


class Sidebar(QWidget):
    """Native buttons expose every navigation destination to accessibility APIs."""
    currentRowChanged = Signal(int)

    def __init__(self):
        super().__init__()
        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(0, 8, 0, 0)
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.buttons = []
        self.index = -1

    def addItems(self, labels):
        for index, label in enumerate(labels):
            button = QPushButton(label)
            button.setCheckable(True)
            button.setMinimumHeight(38)
            button.toggled.connect(lambda checked, i=index: self.setCurrentRow(i) if checked else None)
            self.buttons.append(button)
            self.group.addButton(button, index)
            self.layout_.addWidget(button)
        self.layout_.addStretch()

    def setSpacing(self, value):
        self.layout_.setSpacing(value)

    def item(self, index):
        return self.buttons[index]

    def currentRow(self):
        return self.index

    def setCurrentRow(self, index):
        if index == self.index or not 0 <= index < len(self.buttons):
            return
        self.index = index
        self.buttons[index].setChecked(True)
        self.currentRowChanged.emit(index)
