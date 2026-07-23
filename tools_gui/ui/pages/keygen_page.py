from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QSizePolicy
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

    def __init__(self, i18n, config, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("KeygenPage")
        self.i18n = i18n
        self.config = config

        self.raw_key: bytes | None = None
        self.raw_nonce: bytes | None = None

        self.build_ui()
        self.restore_last_settings()
        self.connect_signals()

    def build_ui(self) -> None:
        mainLayout = QHBoxLayout(self)

        # Global center align
        mainLayout.addStretch()

        content = QWidget(self)
        content.setMaximumWidth(900)

        root = QVBoxLayout(content)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(24)

        mainLayout.addWidget(content)
        mainLayout.addStretch()

        # TITLE
        self.title_label = TitleLabel(self.i18n.t("keygen.title"), self)
        root.addWidget(self.title_label)

        root.addSpacing(30)

        # OPTIONS
        optionsRow = QHBoxLayout()
        optionsRow.setSpacing(24)

        # ALGORITHM
        algoCol = QVBoxLayout()

        self.algorithm_label = StrongBodyLabel(self.i18n.t("keygen.algorithm"), self)
        self.algorithm_combo = ComboBox(self)
        self.algorithm_combo.addItems(list(ALGORITHMS))

        algoCol.addWidget(self.algorithm_label)
        algoCol.addWidget(self.algorithm_combo)

        optionsRow.addLayout(algoCol)

        # KEY SIZE
        sizeCol = QVBoxLayout()

        self.key_size_label = StrongBodyLabel(self.i18n.t("keygen.key_size"), self)
        self.key_size_combo = ComboBox(self)
        self.key_size_combo.addItems([str(bits) for bits in KEY_SIZES_BITS])

        sizeCol.addWidget(self.key_size_label)
        sizeCol.addWidget(self.key_size_combo)

        optionsRow.addLayout(sizeCol)

        # FORMAT
        formatCol = QVBoxLayout()

        self.format_label = StrongBodyLabel(self.i18n.t("keygen.format"), self)
        self.format_combo = ComboBox(self)
        self.format_combo.addItems(list(key_format.SUPPORTED_FORMATS))

        formatCol.addWidget(self.format_label)
        formatCol.addWidget(self.format_combo)

        optionsRow.addLayout(formatCol)
        optionsRow.addStretch()

        root.addLayout(optionsRow)

        root.addSpacing(30)

        # EXECUTE
        self.execute_button = PrimaryPushButton(self.i18n.t("keygen.execute"), self)
        root.addWidget(self.execute_button, alignment=Qt.AlignLeft)

        root.addSpacing(30)

        # KEY
        self.key_label = StrongBodyLabel(self.i18n.t("keygen.encryption_key"), self)
        root.addWidget(self.key_label)

        keyRow = QHBoxLayout()

        self.key_edit = PlainTextEdit(self)
        self.key_edit.setMinimumHeight(70)
        self.key_edit.setMinimumWidth(500)
        self.key_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.key_copy_button = PushButton(self.i18n.t("common.copy"), self)
        self.key_copy_button.setFixedWidth(90)

        keyRow.addWidget(self.key_edit, stretch=1)
        keyRow.addWidget(self.key_copy_button, alignment=Qt.AlignTop)

        root.addLayout(keyRow)

        # NONCE
        self.nonce_label = StrongBodyLabel(self.i18n.t("keygen.nonce"), self)
        root.addWidget(self.nonce_label)

        nonceRow = QHBoxLayout()

        self.nonce_edit = PlainTextEdit(self)
        self.nonce_edit.setMinimumHeight(70)
        self.nonce_edit.setMinimumWidth(500)
        self.nonce_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.nonce_copy_button = PushButton(self.i18n.t("common.copy"), self)
        self.nonce_copy_button.setFixedWidth(90)

        nonceRow.addWidget(self.nonce_edit, stretch=1)
        nonceRow.addWidget(self.nonce_copy_button, alignment=Qt.AlignTop)

        root.addLayout(nonceRow)

        # EXPORT
        exportRow = QHBoxLayout()

        self.export_hex_button = PrimaryPushButton(self.i18n.t("keygen.export_hex"), self)
        self.export_pem_button = PrimaryPushButton(self.i18n.t("keygen.export_pem"), self)

        exportRow.addWidget(self.export_hex_button)
        exportRow.addWidget(self.export_pem_button)
        exportRow.addStretch()

        root.addLayout(exportRow)

        root.addStretch()

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
                self.raw_key = key_format.decode(key_text, previous_format)
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

        if self.raw_key is not None:
            self.key_edit.setPlainText(key_format.encode(self.raw_key, fmt))
        if self.raw_nonce is not None:
            self.nonce_edit.setPlainText(key_format.encode(self.raw_nonce, fmt))

    def copy_to_clipboard(self, edit: PlainTextEdit) -> None:
        from PySide6.QtWidgets import QApplication

        QApplication.clipboard().setText(edit.toPlainText())
        InfoBar.success(
            title=self.i18n.t("common.success"),
            content=self.i18n.t("common.copied"),
            position=InfoBarPosition.TOP,
            duration=1500,
            parent=self,
        )

    def on_export(self, export_format: str) -> None:
        self.try_absorb_edits(previous_format=self.format_combo.currentText())

        if self.raw_key is None:
            InfoBar.warning(
                title=self.i18n.t("common.error"),
                content=self.i18n.t("keygen.no_key_yet"),
                position=InfoBarPosition.TOP,
                duration=2500,
                parent=self,
            )
            return

        default_dir = self.config.last_used.get("output_dir", "")
        path, _ = QFileDialog.getSaveFileName(self, self.i18n.t("common.save_as"), default_dir)
        if not path:
            return

        data = key_format.encode_bytes_for_export(self.raw_key, export_format)
        with open(path, "wb") as f:
            f.write(data)

        self.config.last_used["output_dir"] = str(__import__("pathlib").Path(path).parent)

        InfoBar.success(
            title=self.i18n.t("common.success"),
            content=self.i18n.t("keygen.exported").format(path=path),
            position=InfoBarPosition.TOP,
            duration=2500,
            parent=self,
        )

    def retranslate_ui(self) -> None:
        self.title_label.setText(self.i18n.t("keygen.title"))
        self.algorithm_label.setText(self.i18n.t("keygen.algorithm"))
        self.key_size_label.setText(self.i18n.t("keygen.key_size"))
        self.format_label.setText(self.i18n.t("keygen.format"))
        self.execute_button.setText(self.i18n.t("keygen.execute"))
        self.key_label.setText(self.i18n.t("keygen.encryption_key"))
        self.nonce_label.setText(self.i18n.t("keygen.nonce"))
        self.key_copy_button.setText(self.i18n.t("common.copy"))
        self.nonce_copy_button.setText(self.i18n.t("common.copy"))
        self.export_hex_button.setText(self.i18n.t("keygen.export_hex"))
        self.export_pem_button.setText(self.i18n.t("keygen.export_pem"))