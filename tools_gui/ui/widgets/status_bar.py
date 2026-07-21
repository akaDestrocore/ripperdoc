#!/usr/bin/env python3

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QWidget
from qfluentwidgets import CaptionLabel


class StatusBar(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("StatusBar")
        self.setFixedHeight(28)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)

        self.message_label = CaptionLabel("", self)
        layout.addWidget(self.message_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addStretch(1)

    def set_message(self, text: str) -> None:
        self.message_label.setText(text)

    def clear(self) -> None:
        self.message_label.setText("")