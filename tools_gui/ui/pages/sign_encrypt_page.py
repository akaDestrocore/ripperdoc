#!/usr/bin/env python

"""
File: sign_encrypt_page.py

Brief:
    Binary encryption and signing page for the GUI application.

Author:
    destrocore

Created: 2026-07-20
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QSizePolicy
from qfluentwidgets import (
    TitleLabel,
    StrongBodyLabel,
    LineEdit,
    PlainTextEdit,
    PrimaryPushButton,
    PushButton,
    InfoBar,
    InfoBarPosition,
)

from tools_gui.core import sign_encrypt
from tools_gui.core.sign_encrypt import SignEncryptError
from tools_gui.services import key_format_service as key_format

class SignEncryptPage(QWidget):
    def __init__(self, i18n, config, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("SignEncryptPage")
        self.i18n = i18n
        self.config = config

        self.build_ui()
        self.connect_signals()

    def build_ui(self) -> None:
        mainLayout = QHBoxLayout(self)
        mainLayout.addStretch()

        content = QWidget(self)
        content.setMaximumWidth(900)

        root = QVBoxLayout(content)
        root.setContentsMargins = (0, 0, 0, 0)
        root.setSpacing(24)

        mainLayout.addWidget(content)
        mainLayout.addStretch()

        # TITLE
        self.title_label = TitleLabel(self.i18n.t("sign_encrypt.title"), self)
        root.addWidget(self.title_label)

        root.addSpacing(30)

        # INPUT BINARY
        self.input_label = StrongBodyLabel(self.i18n.t("sign_encrypt.input_binary"), self)
        root.addWidget(self.input_label)

        inputRow = QHBoxLayout()

        self.input_edit = LineEdit(self)
        self.input_edit.setReadOnly(True)
        self.input_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.input_browse_button = PushButton(self.i18n.t("common.browse"), self)
        self.input_browse_button.setFixedWidth(100)

        inputRow.addWidget(self.input_edit, 1)
        inputRow.addWidget(self.input_browse_button)
        root.addLayout(inputRow)

        root.addSpacing(30)

        # PRIVATE KEY
        self.priv_key_label = StrongBodyLabel(self.i18n.t("sign_encrypt.private_key"), self)
        root.addWidget(self.priv_key_label)

        privRow = QHBoxLayout()

        self.priv_key_edit = PlainTextEdit(self)
        self.priv_key_edit.setMinimumHeight(40)
        self.priv_key_edit.setMinimumWidth(500)
        self.priv_key_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.priv_key_browse_button = PushButton(self.i18n.t("common.browse"), self)

        privRow.addWidget(self.priv_key_edit, stretch=1)
        privRow.addWidget(self.priv_key_browse_button, alignment=Qt.AlignTop)

        root.addLayout(privRow)

        # AES KEY
        self.aes_key_label = StrongBodyLabel(self.i18n.t("sign_encrypt.aes_key"), self)
        root.addWidget(self.aes_key_label)

        aesRow = QHBoxLayout()

        self.aes_key_edit = PlainTextEdit(self)
        self.aes_key_edit.setMinimumHeight(40)
        self.aes_key_edit.setMinimumWidth(500)
        self.priv_key_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.aes_key_browse_button = PushButton(self.i18n.t("common.browse"), self)

        aesRow.addWidget(self.aes_key_edit, stretch=1)
        aesRow.addWidget(self.aes_key_browse_button, alignment=Qt.AlignTop)

        root.addLayout(aesRow)

        # EXECUTE
        executeRow = QHBoxLayout()
        self.execute_button = PrimaryPushButton(self.i18n.t("sign_encrypt.execute"), self)
        executeRow.addWidget(self.execute_button, alignment=Qt.AlignmentFlag.AlignLeft)
        executeRow.addStretch()

        root.addLayout(executeRow)

        # LOG CONSOLE
        logRow = QHBoxLayout()
        self.log_label = StrongBodyLabel(self.i18n.t("sign_encrypt.log"), self)
        root.addWidget(self.log_label)
        self.log_console = PlainTextEdit(self)
        self.log_console.setReadOnly(True)
        logRow.addWidget(self.log_console, stretch=1)
        logRow.addStretch()

        root.addLayout(logRow)

        root.addStretch()


    def connect_signals(self) -> None:
        self.input_browse_button.clicked.connect(self.on_browse_input)
        self.priv_key_browse_button.clicked.connect(self.on_browse_priv_key)
        self.aes_key_browse_button.clicked.connect(self.on_browse_aes_key)
        self.execute_button.clicked.connect(self.on_execute)


    def on_browse_input(self) -> None:
        default_dir = self.config.last_used.get("input_dir", "")
        path, _ = QFileDialog.getOpenFileName(self, self.i18n.t("common.select_file"), 
                                              default_dir, "Binary (*.bin);;All Files (*)")

        if not path:
            return
        self.input_edit.setText(path)
        self.config.last_used["input_dir"] = str(Path(path).parent)


    def on_browse_priv_key(self) -> None:
        default_dir = self.config.last_used.get("priv_key_path", "")
        path, _ = QFileDialog.getOpenFileName(self, self.i18n.t("common.select_file"), 
                                                default_dir, "PEM (*.pem);;All Files (*)")
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            self.priv_key_edit.setPlainText(f.read())
        self.config.last_used["priv_key_path"] = path


    def on_browse_aes_key(self) -> None:
        default_dir = self.config.last_used.get("aes_key_path", "")
        path, _ = QFileDialog.getOpenFileName(
            self, self.i18n.t("common.select_file"), 
            default_dir, "AES Key (*.bin *.key);;All Files (*)")
        if not path:
            return
        with open(path, "rb") as f:
            raw = f.read()
        self.aes_key_edit.setPlainText(raw.hex())
        self.config.last_used["aes_key_path"] = path


    def on_execute(self) -> None:
        self.log_console.clear()

        input_path = self.input_edit.text().strip()
        if not input_path:
            self.report_error(self.i18n.t("sign_encrypt.no_input"))
            return

        try:
            with open(input_path, "rb") as f:
                raw = f.read()
        except OSError as exc:
            self.report_error(f"{exc}")
            return

        priv_pem = self.priv_key_edit.toPlainText().strip()
        aes_text = self.aes_key_edit.toPlainText().strip()

        if not priv_pem or not aes_text:
            self.report_error(self.i18n.t("sign_encrypt.missing_keys"))
            return

        try:
            aes_key_raw = key_format.decode(aes_text, key_format.FORMAT_HEX)
        except (key_format.KeyFormatError, ValueError) as exc:
            self.report_error(f"{exc}")
            return

        try:
            priv_key = sign_encrypt.load_private_key(priv_pem)
            aes_key = sign_encrypt.load_aes_key(aes_key_raw)
            result = sign_encrypt.process_bytes(raw, priv_key, aes_key)
        except SignEncryptError as exc:
            self.report_error(f"{exc}")
            return

        default_dir = self.config.last_used.get("output_dir", "")
        out_path, _ = QFileDialog.getSaveFileName(self, self.i18n.t("common.save_as"), default_dir, "Binary (*.bin)")

        if not out_path:
            return

        with open(out_path, "wb") as f:
            f.write(result.output_bytes)
        self.config.last_used["output_dir"] = str(Path(out_path).parent)

        self.log(f"image_type   : {result.image_type}")
        self.log(f"data_size       : {result.data_size}")
        self.log(f"nonce           : {result.nonce.hex()}")
        self.log(f"gcm_tag        : {result.tag.hex()}")
        self.log(f"sha256          : {result.sha256.hex()}")
        self.log(f"signature      : {result.signature.hex()}")
        self.log(f"written to    : {out_path}")

        InfoBar.success(title=self.i18n.t("common.success"), 
                        content=self.i18n.t("keygen.exported").format(path=out_path), 
                        position=InfoBarPosition.TOP, duration=2500, parent=self)


    def report_error(self, message: str) -> None:
        self.log(f"[ERROR] {message}")
        InfoBar.error(title=self.i18n.t("common.error"), content=message, 
                      position=InfoBarPosition.TOP, duration=3500, parent=self)

    def log(self, text: str) -> None:
        self.log_console.appendPlainText(text)

    def retranslate_ui(self) -> None:
            self.title_label.setText(self.i18n.t("sign_encrypt.title"))
            self.input_label.setText(self.i18n.t("sign_encrypt.input_binary"))
            self.priv_key_label.setText(self.i18n.t("sign_encrypt.private_key"))
            self.aes_key_label.setText(self.i18n.t("sign_encrypt.aes_key"))
            self.execute_button.setText(self.i18n.t("sign_encrypt.execute"))
            self.log_label.setText(self.i18n.t("sign_encrypt.log"))
            self.input_browse_button.setText(self.i18n.t("common.browse"))
            self.priv_key_browse_button.setText(self.i18n.t("common.browse"))
            self.aes_key_browse_button.setText(self.i18n.t("common.browse"))




