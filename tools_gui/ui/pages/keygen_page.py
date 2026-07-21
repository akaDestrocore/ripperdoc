#!/usr/bin/env python3

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QApplication, QFileDialog
from qfluentwidgets import (
    TitleLabel,
    StrongBodyLabel,
    ComboBox,
    PrimaryPushButton,
    PlainTextEdit,
    PushButton,
    InfoBar,
    InfoBarPosition,
)

from tools_gui.core import keygen
from tools_gui.services import key_format_service as key_format

ALGORITHMS = ("AES",)
KEY_SIZES_BITS = (128, 192, 256)


class KeygenPage(QWidget):
    def __init__(self, config, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("KeygenPage")
        self.config = config
        self._raw_key: bytes | None = None
        self.raw_nonce: bytes | None = None
        self.build_ui()
        self.restore_last_settings()
        self.connect_signals()


    def build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

        self.title_label = TitleLabel("Keygen", self)
        root.addWidget(self.title_label)

        # ALGORITHM
        row = QHBoxLayout()
        row.setSpacing(24)

        algo_col = QVBoxLayout()
        self.algorithm_label = StrongBodyLabel("Algorithm", self)
        self.algorithm_combo = ComboBox(self)
        self.algorithm_combo.addItems(list(ALGORITHMS))
        algo_col.addWidget(self.algorithm_label)
        algo_col.addWidget(self.algorithm_combo)
        row.addLayout(algo_col)

        # KEY SIZE
        size_col = QVBoxLayout()
        self.key_size_label = StrongBodyLabel("Key size", self)
        self.key_size_combo = ComboBox(self)
        self.key_size_combo.addItems([str(bits) for bits in KEY_SIZES_BITS])
        size_col.addWidget(self.key_size_label)
        size_col.addWidget(self.key_size_combo)
        row.addLayout(size_col)

        # FORMAT
        format_col = QVBoxLayout()
        self.format_label = StrongBodyLabel("Format", self)
        self.format_combo = ComboBox(self)
        self.format_combo.addItems(list(key_format.SUPPORTED_FORMATS))
        format_col.addWidget(self.format_label)
        format_col.addWidget(self.format_combo)
        row.addLayout(format_col)

        row.addStretch(1)
        root.addLayout(row)

        # EXECUTE
        self.execute_button = PrimaryPushButton("Execute", self)
        root.addWidget(self.execute_button, alignment=Qt.AlignmentFlag.AlignLeft)

        # KEY
        self.key_label = StrongBodyLabel("Encrypt", self)
        root.addWidget(self.key_label)

        key_row = QHBoxLayout()
        self.key_edit = PlainTextEdit(self)
        self.key_edit.setFixedHeight(70)
        self.key_copy_button = PushButton("Copy", self)
        key_row.addWidget(self.key_edit, stretch=1)
        key_row.addWidget(self.key_copy_button, alignment=Qt.AlignmentFlag.AlignTop)
        root.addLayout(key_row)

        # NONCE
        self.nonce_label = StrongBodyLabel("Nonce", self)
        root.addWidget(self.nonce_label)

        nonce_row = QHBoxLayout()
        self.nonce_edit = PlainTextEdit(self)
        self.nonce_edit.setFixedHeight(70)
        self.nonce_copy_button = PushButton("Copy", self)
        nonce_row.addWidget(self.nonce_edit, stretch=1)
        nonce_row.addWidget(self.nonce_copy_button, alignment=Qt.AlignmentFlag.AlignTop)
        root.addLayout(nonce_row)

        # EXPORT
        export_row = QHBoxLayout()
        self.export_hex_button = PushButton("Export HEX", self)
        self.export_pem_button = PushButton("Export PEM", self)
        for btn in (
            self.export_hex_button,
            self.export_pem_button,
        ):
            export_row.addWidget(btn)
        export_row.addStretch(1)
        root.addLayout(export_row)

        root.addStretch(1)

    def restore_last_settings(self) -> None:
        keygen_cfg = self.config.keygen
        size_text = str(keygen_cfg.get("key_size", 256))
        if size_text in [str(b) for b in KEY_SIZES_BITS]:
            self.key_size_combo.setCurrentText(size_text)

        fmt = keygen_cfg.get("format", key_format.FORMAT_HEX)
        if fmt in key_format.SUPPORTED_FORMATS:
            self.format_combo.setCurrentText(fmt)

    def connect_signals(self) -> None:
        self.execute_button.clicked.connect(self.on_execute)
        self.format_combo.currentTextChanged.connect(self.on_format_changed)
        self.key_copy_button.clicked.connect(lambda: self.copy_to_clipboard(self.key_edit))
        self.nonce_copy_button.clicked.connect(lambda: self.copy_to_clipboard(self.nonce_edit))

        self.export_hex_button.clicked.connect(lambda: self.on_export(key_format.FORMAT_HEX))
        self.export_pem_button.clicked.connect(lambda: self.on_export(key_format.FORMAT_PEM))


    def on_execute(self) -> None:
        key_size_bits = int(self.key_size_combo.currentText())
        material = keygen.generate_aes_key(key_size_bits=key_size_bits)
        self.raw_key = material.key
        self.raw_nonce = material.nonce
        self.config.keygen["key_size"] = key_size_bits
        self.config.keygen["format"] = self.format_combo.currentText()
        self.render_current_format()

    def on_format_changed(self, new_format: str) -> None:
        self.try_absorb_edits(previous_format=self.config.keygen.get("format", key_format.FORMAT_HEX))
        self.config.keygen["format"] = new_format
        self.render_current_format()

    def try_absorb_edits(self, previous_format: str) -> None:
        key_text = self.key_edit.toPlainText()
        if key_text.strip():
            try:
                self._raw_key = key_format.decode(key_text, previous_format)
            except key_format.KeyFormatError:
                pass

        nonce_text = self.nonce_edit.toPlainText()
        if nonce_text.strip():
            try:
                self.raw_nonce = key_format.decode(nonce_text, previous_format)
            except key_format.KeyFormatError:
                pass

    def render_current_format(self) -> None:
        fmt = self.format_combo.currentText()
        if self._raw_key is not None:
            self.key_edit.setPlainText(key_format.encode(self._raw_key, fmt))
        if self.raw_nonce is not None:
            self.nonce_edit.setPlainText(key_format.encode(self.raw_nonce, fmt))

    def copy_to_clipboard(self, edit: PlainTextEdit) -> None:
        QApplication.clipboard().setText(edit.toPlainText())
        InfoBar.success(
            title="Success",
            content="Copied",
            position=InfoBarPosition.TOP,
            duration=1500,
            parent=self,
        )

    def on_export(self, export_format: str) -> None:
        self.try_absorb_edits(previous_format=self.format_combo.currentText())
        if self._raw_key is None:
            InfoBar.warning(
                title="Error",
                content="No key yet",
                position=InfoBarPosition.TOP,
                duration=2500,
                parent=self,
            )
            return

        default_dir = self.config.last_used.get("output_dir", "")
        path, _ = QFileDialog.getSaveFileName(self, "Save as", default_dir)
        if not path:
            return

        data = key_format.encode_bytes_for_export(self._raw_key, export_format)
        with open(path, "wb") as f:
            f.write(data)

        self.config.last_used["output_dir"] = str(__import__("pathlib").Path(path).parent)

        InfoBar.success(
            title="Success",
            content="Exported".format(path=path),
            position=InfoBarPosition.TOP,
            duration=2500,
            parent=self,
        )