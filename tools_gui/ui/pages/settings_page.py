from __future__ import annotations

import os
import subprocess
import sys

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget, QHBoxLayout, QSizePolicy
from qfluentwidgets import (
    ComboBox,
    HyperlinkButton,
    InfoBar,
    InfoBarPosition,
    MessageBox,
    PushButton,
    StrongBodyLabel,
    TitleLabel,
)

from tools_gui.services import user_config

LANGUAGE_CODES = ("en", "tr")
LANGUAGE_DISPLAY = {"en": "English", "tr": "Türkçe"}
THEMES = ("Acrylic",)


class SettingsPage(QWidget):

    languageChanged = Signal(str)

    def __init__(self, i18n, config, main_window, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("SettingsPage")

        self.i18n = i18n
        self.config = config
        self.main_window = main_window

        self.build_ui()
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
        self.title_label = TitleLabel(self.i18n.t("settings.title"), self)
        root.addWidget(self.title_label)

        # OPTIONS
        optionsRow = QHBoxLayout()
        optionsRow.setSpacing(24)

        mainCol = QVBoxLayout()

        self.language_label = StrongBodyLabel(self.i18n.t("settings.language"), self)

        self.language_combo = ComboBox(self)
        self.language_combo.addItems([LANGUAGE_DISPLAY[c] for c in LANGUAGE_CODES])
        self.language_combo.setCurrentText(LANGUAGE_DISPLAY[self.i18n.language])

        mainCol.addWidget(self.language_label)
        mainCol.addWidget(self.language_combo)

        # THEME OPTIONS
        self.theme_label = StrongBodyLabel(self.i18n.t("settings.theme"), self)
        mainCol.addWidget(self.theme_label)

        self.theme_combo = ComboBox(self)
        self.theme_combo.addItems(list(THEMES))
        self.theme_combo.setCurrentText(self.config.theme.capitalize())
        mainCol.addWidget(self.theme_combo)

        optionsRow.addLayout(mainCol)
        optionsRow.addStretch()
        root.addLayout(optionsRow)

        # BOTTOM
        bottomRow = QHBoxLayout()
        bottomRow.setSpacing(24)

        self.config_location_button = HyperlinkButton(url="", text=self.i18n.t("settings.config_location"), parent=self)
        mainCol.addWidget(self.config_location_button)

        self.reset_button = PushButton(self.i18n.t("settings.reset"), self)
        self.reset_button.setFixedWidth(200)
        mainCol.addWidget(self.reset_button, alignment=Qt.AlignCenter)

        bottomRow.addLayout(mainCol)
        bottomRow.addStretch()
        root.addLayout(bottomRow)

        root.addStretch(1)

    def connect_signals(self) -> None:
        self.language_combo.currentTextChanged.connect(self.on_language_combo_changed)
        self.theme_combo.currentTextChanged.connect(self.on_theme_combo_changed)
        self.config_location_button.clicked.connect(self.on_showconfig_location)
        self.reset_button.clicked.connect(self.on_reset_clicked)

    def on_language_combo_changed(self, display_text: str) -> None:
        for code, display in LANGUAGE_DISPLAY.items():
            if display == display_text:
                self.languageChanged.emit(code)
                return

    def on_theme_combo_changed(self, theme_text: str) -> None:
        self.config.theme = theme_text.lower()

    def on_showconfig_location(self) -> None:
        config_dir = user_config.get_config_dir()
        config_dir.mkdir(parents=True, exist_ok=True)

        if sys.platform.startswith("win"):
            os.startfile(str(config_dir))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(config_dir)])
        else:
            subprocess.Popen(["xdg-open", str(config_dir)])

    def on_reset_clicked(self) -> None:
        box = MessageBox(
            self.i18n.t("settings.reset_confirm_title"),
            self.i18n.t("settings.reset_confirm_body"),
            self.window(),
        )
        if not box.exec():
            return

        defaults = user_config.reset_config()
        self.config.language = defaults.language
        self.config.theme = defaults.theme
        self.config.window = defaults.window
        self.config.last_used = defaults.last_used
        self.config.keygen = defaults.keygen

        self.language_combo.setCurrentText(LANGUAGE_DISPLAY[defaults.language])
        self.theme_combo.setCurrentText(defaults.theme.capitalize())
        self.languageChanged.emit(defaults.language)

        InfoBar.success(
            title=self.i18n.t("common.success"),
            content=self.i18n.t("settings.reset"),
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self,
        )

    def retranslate_ui(self) -> None:
        self.title_label.setText(self.i18n.t("settings.title"))
        self.language_label.setText(self.i18n.t("settings.language"))
        self.theme_label.setText(self.i18n.t("settings.theme"))
        self.config_location_button.setText(self.i18n.t("settings.config_location"))
        self.reset_button.setText(self.i18n.t("settings.reset"))