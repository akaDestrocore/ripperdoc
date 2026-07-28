#!/usr/bin/env python

"""
File: merge.py

Brief:
    Merge multiple binaries into a single binary file. 
    Allows modifing some of binary header parameters.

Author:
    destrocore

Created: 2026-07-20
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFileDialog, QSpinBox, QSizePolicy
from qfluentwidgets import (
    TitleLabel,
    StrongBodyLabel,
    CaptionLabel,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    InfoBar,
    InfoBarPosition,
)

from tools_gui.core import merge
from tools_gui.core.patch_header import PatchHeaderError, read_image_type

DEFAULT_UPDATER_OFFSET      = 0x00004000
DEFAULT_APP_OFFSET          = 0x00040000
DEFAULT_UPDATER_BASE_ADDR   = 0x08004000
DEFAULT_APP_BASE_ADDR       = 0x08040000


class VersionFields(QWidget):

    def __init__(self, i18n, parent=None) -> None:
        super().__init__(parent)
        self.i18n = i18n

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(16)

        self.major_spin = self.make_spin(0xFF)
        self.minor_spin = self.make_spin(0xFF)
        self.patch_spin = self.make_spin(0xFF)

        # Full uint32 editor.
        self.security_edit = LineEdit(self)
        self.security_edit.setText("0")
        self.security_edit.setPlaceholderText("0 .. 0xFFFFFFFF")

        for caption_key, widget in (
            ("merge.version_major", self.major_spin),
            ("merge.version_minor", self.minor_spin),
            ("merge.version_patch", self.patch_spin),
            ("merge.security_version", self.security_edit),
        ):
            col = QVBoxLayout()
            col.addWidget(CaptionLabel(self.i18n.t(caption_key), self))
            col.addWidget(widget)
            row.addLayout(col)

        row.addStretch(1)


    def make_spin(self, max_value: int) -> QSpinBox:
        spin = QSpinBox(self)
        spin.setRange(0, max_value)
        return spin


    def values(self) -> tuple[tuple[int, int, int], int]:
        version = (
            self.major_spin.value(),
            self.minor_spin.value(),
            self.patch_spin.value(),
        )

        try:
            security_version = int(self.security_edit.text().strip(), 0)
        except ValueError as exc:
            raise ValueError("Invalid security version") from exc

        if not (0 <= security_version <= 0xFFFFFFFF):
            raise ValueError("Security version must be in range 0..0xFFFFFFFF")

        return version, security_version


class ImageSlot(QWidget):

    def __init__(self, i18n,
                label_text: str,
                checks_header: bool,
                parent=None) -> None:

        super().__init__(parent)

        self.i18n = i18n
        self.checks_header = checks_header

        self.raw: bytes | None = None
        self.detected_type: str | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        # Label
        self.label = StrongBodyLabel(label_text, self)
        root.addWidget(self.label)

        # Path row
        pathRow = QHBoxLayout()

        self.path_edit = LineEdit(self)
        self.path_edit.setReadOnly(True)
        self.path_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.browse_button = PushButton(self.i18n.t("common.browse"), self)
        self.browse_button.setFixedWidth(100)

        pathRow.addWidget(self.path_edit, 1)
        pathRow.addWidget(self.browse_button)

        root.addLayout(pathRow)

        # Status
        self.status_caption = CaptionLabel("", self)
        root.addWidget(self.status_caption)

        # Version editor
        self.version_fields: VersionFields | None = None

        if checks_header:
            self.version_fields = VersionFields(self.i18n, self)
            root.addWidget(self.version_fields)

        self.browse_button.clicked.connect(self.on_browse)


    def on_browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, self.i18n.t("common.select_file"), "", "Binary (*.bin);;All Files (*)")
        if not path:
            return

        with open(path, "rb") as f:
            self.raw = f.read()

        self.path_edit.setText(path)

        if not self.checks_header:
            self.detected_type = None
            self.status_caption.setText(f"{len(self.raw)} bytes")
            return

        try:
            self.detected_type = read_image_type(self.raw)
            self.status_caption.setText(f"{self.detected_type} — {len(self.raw)} bytes")
        except PatchHeaderError as exc:
            self.detected_type = None
            self.status_caption.setText(f"⊗ {exc}")



class MergePage(QWidget):

    def __init__(self, i18n, config, parent=None) -> None:
        super().__init__(parent)

        self.setObjectName("MergePage")

        self.i18n = i18n
        self.config = config

        self.build_ui()
        self.connect_signals()

    def build_ui(self) -> None:

        # Global layout
        mainLayout = QHBoxLayout(self)
        mainLayout.addStretch()

        content = QWidget(self)
        content.setMaximumWidth(950)

        root = QVBoxLayout(content)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(24)

        mainLayout.addWidget(content)
        mainLayout.addStretch()

        # TITLE
        self.title_label = TitleLabel(self.i18n.t("merge.title"),self)
        root.addWidget(self.title_label)

        root.addSpacing(30)

        # IMAGES
        self.boot_slot = ImageSlot(self.i18n, self.i18n.t("merge.bootloader"), checks_header=False, parent=self)

        self.updater_slot = ImageSlot(self.i18n, self.i18n.t("merge.updater"), checks_header=True, parent=self)

        self.app_slot = ImageSlot(self.i18n, self.i18n.t("merge.application"), checks_header=True, parent=self)

        root.addWidget(self.boot_slot)
        root.addWidget(self.updater_slot)
        root.addWidget(self.app_slot)

        # LAYOUT
        self.layout_label = StrongBodyLabel(self.i18n.t("merge.layout"), self)

        root.addWidget(self.layout_label)

        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(12)

        self.updater_offset_edit = self.make_hex_field(DEFAULT_UPDATER_OFFSET)

        self.app_offset_edit = self.make_hex_field(DEFAULT_APP_OFFSET)

        self.updater_base_edit = self.make_hex_field(DEFAULT_UPDATER_BASE_ADDR)

        self.app_base_edit = self.make_hex_field(DEFAULT_APP_BASE_ADDR)

        fields = (
            ("merge.updater_offset", self.updater_offset_edit, "merge.updater_base_addr", self.updater_base_edit),
            ("merge.app_offset", self.app_offset_edit, "merge.app_base_addr", self.app_base_edit),
        )

        for row, (leftLabel, leftEdit, rightLabel, rightEdit) in enumerate(fields):

            grid.addWidget(CaptionLabel(self.i18n.t(leftLabel), self), row, 0)

            grid.addWidget(leftEdit, row, 1)

            grid.addWidget(CaptionLabel(self.i18n.t(rightLabel), self), row, 2)

            grid.addWidget(rightEdit, row, 3)

        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

        root.addLayout(grid)

        # EXECUTE
        self.merge_button = PrimaryPushButton(self.i18n.t("merge.execute"), self)

        root.addWidget(self.merge_button, alignment=Qt.AlignLeft)

        root.addStretch()


    def make_hex_field(self, default_value: int) -> LineEdit:
        edit = LineEdit(self)
        edit.setText(f"0x{default_value:08X}")
        return edit


    def connect_signals(self) -> None:
        self.merge_button.clicked.connect(self.on_merge)


    def parse_hex_field(self, edit: LineEdit) -> int:
        return int(edit.text().strip(), 0)


    def on_merge(self) -> None:
        if self.boot_slot.raw is None or self.updater_slot.raw is None or self.app_slot.raw is None:
            self.report_error(self.i18n.t("merge.missing_slots"))
            return

        try:
            updater_offset = self.parse_hex_field(self.updater_offset_edit)
            app_offset = self.parse_hex_field(self.app_offset_edit)
            updater_base_addr = self.parse_hex_field(self.updater_base_edit)
            app_base_addr = self.parse_hex_field(self.app_base_edit)
        except ValueError:
            self.report_error(self.i18n.t("merge.bad_number"))
            return

        try:
            updater_version, updater_security_version = self.updater_slot.version_fields.values()
            app_version, app_security_version = self.app_slot.version_fields.values()
        except ValueError as exc:
            self.report_error(str(exc))
            return

        try:
            updater = merge.BinaryImage(
                offset=updater_offset,
                base_addr=updater_base_addr,
                version=updater_version,
                security_version=updater_security_version,
                raw=self.updater_slot.raw,
            )

            app = merge.BinaryImage(
                offset=app_offset,
                base_addr=app_base_addr,
                version=app_version,
                security_version=app_security_version,
                raw=self.app_slot.raw,
            )

            result = merge.patch_and_merge_bytes(
                self.boot_slot.raw,
                updater=updater,
                app=app,
            )
        except merge.MergeError as exc:
            self.report_error(f"{exc}")
            return

        default_dir = self.config.last_used.get("output_dir", "")
        out_path, _ = QFileDialog.getSaveFileName(
            self, self.i18n.t("common.save_as"), default_dir, "Binary (*.bin)"
        )
        if not out_path:
            return

        with open(out_path, "wb") as f:
            f.write(result.output_bytes)
        self.config.last_used["output_dir"] = str(Path(out_path).parent)

        InfoBar.success(title=self.i18n.t("common.success"),
                        content=self.i18n.t("keygen.exported").format(path=out_path),
                        position=InfoBarPosition.TOP,
                        duration=2500, parent=self)


    def report_error(self, message: str) -> None:
        InfoBar.error(
            title=self.i18n.t("common.error"),
            content=message,
            position=InfoBarPosition.TOP,
            duration=3500,
            parent=self,
        )


    def retranslate_ui(self) -> None:
        self.title_label.setText(self.i18n.t("merge.title"))
        self.boot_slot.label.setText(self.i18n.t("merge.bootloader"))
        self.updater_slot.label.setText(self.i18n.t("merge.updater"))
        self.app_slot.label.setText(self.i18n.t("merge.application"))
        for slot in (self.boot_slot, self.updater_slot, self.app_slot):
            slot.browse_button.setText(self.i18n.t("common.browse"))
        self.layout_label.setText(self.i18n.t("merge.layout"))
        self.merge_button.setText(self.i18n.t("merge.execute"))