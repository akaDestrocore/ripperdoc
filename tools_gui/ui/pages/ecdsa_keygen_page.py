#!/usr/bin/env python

"""
File: ecdsa_keygen_page.py

Brief:
    Page to generate ECDSA keypair

Author:
    destrocore

Created: 2026-07-20
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QSizePolicy, QApplication
from qfluentwidgets import (
    TitleLabel,
    StrongBodyLabel,
    PrimaryPushButton,
    PlainTextEdit,
    PushButton,
    InfoBar,
    InfoBarPosition,
    CaptionLabel
)

from tools_gui.core import keygen

class EcdsaKeygenPage(QWidget):

    def __init__(self, i18n, config, parent=None):
        super().__init__(parent)
        self.setObjectName("EcdsaKeygenPage")
        self.i18n = i18n
        self.config = config
        self.keypair: keygen.EcdsaKeypair | None = None

        self.build_ui()
        self.connect_signals()

    def build_ui(self) -> None:
        mainLayout = QHBoxLayout(self)
        mainLayout.addStretch()

        content = QWidget(self)
        content.setMaximumWidth(900)

        root = QVBoxLayout(content)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(24)

        mainLayout.addWidget(content)
        mainLayout.addStretch()

        # TITLE
        self.title_label = TitleLabel(self.i18n.t("ecdsa.title"), self)
        root.addWidget(self.title_label)

        root.addSpacing(20)

        # EXECUTE
        self.execute_button = PrimaryPushButton(self.i18n.t("ecdsa.execute"), self)
        root.addWidget(self.execute_button, alignment=Qt.AlignLeft)

        root.addSpacing(30)

        # PRIVATE PEM
        self.private_key_label = StrongBodyLabel(self.i18n.t("ecdsa.private_key"), self)
        root.addWidget(self.private_key_label)

        privRow = QHBoxLayout()

        self.private_key_edit = PlainTextEdit(self)
        self.private_key_edit.setReadOnly(True)
        self.private_key_edit.setMinimumHeight(120)
        self.private_key_edit.setMinimumWidth(500)
        self.private_key_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        privButtonsCol = QVBoxLayout()
        self.private_copy_button = PushButton(self.i18n.t("common.copy"), self)
        self.private_export_button = PushButton(self.i18n.t("ecdsa.export_private_pem"), self)
        privButtonsCol.addWidget(self.private_copy_button)
        privButtonsCol.addWidget(self.private_export_button)
        privButtonsCol.addStretch()

        privRow.addWidget(self.private_key_edit, stretch=1)
        privRow.addLayout(privButtonsCol)

        root.addLayout(privRow)

        self.private_warning_label = CaptionLabel(self.i18n.t("ecdsa.private_key_warning"), self)
        root.addWidget(self.private_warning_label)

        root.addSpacing(20)

        # PUBLIC KEY
        self.public_key_label = StrongBodyLabel(self.i18n.t("ecdsa.public_key"), self)
        root.addWidget(self.public_key_label)

        pubRow = QHBoxLayout()

        self.public_key_edit = PlainTextEdit(self)
        self.public_key_edit.setReadOnly(True)
        self.public_key_edit.setMinimumHeight(100)
        self.public_key_edit.setMinimumWidth(500)
        self.public_key_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        pubButtonsCol = QVBoxLayout()
        self.public_copy_button = PushButton(self.i18n.t("common.copy"), self)
        self.public_export_pem_button = PushButton(self.i18n.t("ecdsa.export_public_pem"), self)
        self.public_export_bin_button = PushButton(self.i18n.t("ecdsa.export_public_bin"), self)
        self.public_export_header_button = PushButton(self.i18n.t("ecdsa.export_c_header"), self)
        pubButtonsCol.addWidget(self.public_copy_button)
        pubButtonsCol.addWidget(self.public_export_pem_button)
        pubButtonsCol.addWidget(self.public_export_bin_button)
        pubButtonsCol.addWidget(self.public_export_header_button)
        pubButtonsCol.addStretch()

        pubRow.addWidget(self.public_key_edit, stretch=1)
        pubRow.addLayout(pubButtonsCol)

        root.addLayout(pubRow)

        root.addStretch()


    def connect_signals(self) -> None:
        self.execute_button.clicked.connect(self.on_execute)

        self.private_copy_button.clicked.connect(lambda: self.copy_to_clipboard(self.private_key_edit))
        self.public_copy_button.clicked.connect(lambda: self.copy_to_clipboard(self.public_key_edit))

        self.private_export_button.clicked.connect(self.on_export_private_pem)
        self.public_export_pem_button.clicked.connect(self.on_export_public_pem)
        self.public_export_bin_button.clicked.connect(self.on_export_public_bin)
        self.public_export_header_button.clicked.connect(self.on_export_c_header)


    def on_execute(self) -> None:
        self.keypair = keygen.generate_ecdsa_keypair()
        self.private_key_edit.setPlainText(self.keypair.private_pem)
        self.public_key_edit.setPlainText(self.keypair.public_pem)


    def copy_to_clipboard(self, edit: PlainTextEdit) -> None:
        from PySide6.QtWidgets import QApplication

        QApplication.clipboard().setText(edit.toPlainText())
        InfoBar.success(title=self.i18n.t("common.success"),
                        content=self.i18n.t("common.copied"),
                        position=InfoBarPosition.TOP,
                        duration=1500, parent=self)


    def save_export(self, data: bytes, name_filter: str) -> None:
        default_dir = self.config.last_used.get("output_dir", "")
        path, _ = QFileDialog.getSaveFileName(self, self.i18n.t("common.save_as"), default_dir, name_filter)
        if not path:
            return

        with open(path, "wb") as f:
            f.write(data)

        self.config.last_used["output_dir"] = str(Path(path).parent)

        InfoBar.success(title=self.i18n.t("common.success"),
                        content=self.i18n.t("keygen.exported").format(path=path),
                        position=InfoBarPosition.TOP, duration=2500, parent=self)


    def require_keypair(self) -> bool:
        if self.keypair is None:
            InfoBar.warning(title=self.i18n.t("common.error"),
                            content=self.i18n.t("ecdsa.no_key_yet"),
                            position=InfoBarPosition.TOP,
                            duration=2500, parent=self)
            return False
        
        return True


    def on_export_private_pem(self) -> None:
        if not self.require_keypair():
            return
        self.save_export(self.keypair.private_pem.encode("ascii"), "PEM (*.pem);;All Files (*)")


    def on_export_public_pem(self) -> None:
        if not self.require_keypair():
            return
        self.save_export(self.keypair.public_pem.encode("ascii"), "PEM (*.pem);;All Files (*)")


    def on_export_public_bin(self) -> None:
        if not self.require_keypair():
            return
        self.save_export(self.keypair.public_bin, "Binary (*.bin);;All Files (*)")


    def on_export_c_header(self) -> None:
        if not self.require_keypair():
            return
        self.save_export(self.keypair.public_header_c.encode("ascii"), "C Header (*.h);;All Files (*)")


    def retranslate_ui(self) -> None:
        self.title_label.setText(self.i18n.t("ecdsa.title"))
        self.execute_button.setText(self.i18n.t("ecdsa.execute"))
        self.private_key_label.setText(self.i18n.t("ecdsa.private_key"))
        self.private_warning_label.setText(self.i18n.t("ecdsa.private_key_warning"))
        self.public_key_label.setText(self.i18n.t("ecdsa.public_key"))
        self.private_copy_button.setText(self.i18n.t("common.copy"))
        self.public_copy_button.setText(self.i18n.t("common.copy"))
        self.private_export_button.setText(self.i18n.t("ecdsa.export_private_pem"))
        self.public_export_pem_button.setText(self.i18n.t("ecdsa.export_public_pem"))
        self.public_export_bin_button.setText(self.i18n.t("ecdsa.export_public_bin"))
        self.public_export_header_button.setText(self.i18n.t("ecdsa.export_c_header"))