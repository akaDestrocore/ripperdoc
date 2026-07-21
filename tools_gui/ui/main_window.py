#!/usr/bin/env python3

from PySide6.QtCore import Qt
from qframelesswindow import AcrylicWindow
from PySide6.QtWidgets import QWidget, QHBoxLayout, QStackedWidget, QVBoxLayout
from qfluentwidgets import NavigationInterface, NavigationItemPosition, FluentIcon 
from tools_gui.services import user_config
from tools_gui.services.i18n_service import I18nService
from tools_gui.ui.pages.keygen_page import KeygenPage
from tools_gui.ui.pages.settings_page import SettingsPage
from tools_gui.ui.widgets.status_bar import StatusBar

class MainWindow(AcrylicWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.windowEffect.setAcrylicEffect(self.winId(), gradientColor="22222244")
        # self.windowEffect.setAeroEffect(self.winId())
        self.titleBar.raise_()
        self.titleBar.minBtn.setStyleSheet("qproperty-normalColor: white; qproperty-hoverColor: lightgray;") 
        self.titleBar.maxBtn.setStyleSheet("qproperty-normalColor: white; qproperty-hoverColor: lightgray;") 
        self.titleBar.closeBtn.setStyleSheet("qproperty-normalColor: white; qproperty-hoverColor: red;")

        self.config = user_config.load_config()
        self.i18n = I18nService(language=self.config.language)
        self.pages: list = []
        self.nav_routes: dict[str, QWidget] = {}

        self.init_window()
        self.init_layout()
        self.init_pages()
        self.init_nav()
    

    def init_window(self) -> None:
        width = self.config.window.get("width", 1100)
        height = self.config.window.get("height", 720)
        self.resize(width, height)


    def init_layout(self) -> None:
        self.hBoxLayout = QHBoxLayout()
        self.hBoxLayout.setContentsMargins(0, self.titleBar.height(), 0, 0)
        self.hBoxLayout.setSpacing(0)

        self.navigationInterface = NavigationInterface(self, showMenuButton=True)
        self.stackedWidget = QStackedWidget(self)
        self.statusBar = StatusBar(self)

        rightLayout = QVBoxLayout()
        rightLayout.setContentsMargins(0, 0, 0, 0)
        rightLayout.setSpacing(0)
        rightLayout.addWidget(self.stackedWidget, stretch=1)
        rightLayout.addWidget(self.statusBar)

        self.hBoxLayout.addWidget(self.navigationInterface)
        self.hBoxLayout.addLayout(rightLayout, stretch=1)
        self.setLayout(self.hBoxLayout)

        self.navigationInterface.displayModeChanged.connect(
            self.titleBar.raise_
        )

    def init_pages(self) -> None:
        self.keygen_page = KeygenPage(self.i18n, self.config, parent=self)
        self.settings_page = SettingsPage(self.i18n, self.config, self, parent=self)

        self.settings_page.languageChanged.connect(self.on_language_changed)

        self.pages = [self.keygen_page, self.settings_page]
        for page in self.pages:
            self.stackedWidget.addWidget(page)


    def on_language_changed(self, language: str) -> None:
        self.i18n.set_language(language)
        self.config.language = language
        self.retranslate_ui()


    def retranslate_ui(self) -> None:
        self.setWindowTitle(self.i18n.t("app.title"))
        self.set_nav_item_text(self.keygen_page.objectName(), self.i18n.t("nav.keygen"))
        self.set_nav_item_text(self.settings_page.objectName(), self.i18n.t("nav.settings"))
        for page in self.pages:
            page.retranslate_ui()


    def init_nav(self) -> None:
        self.add_nav_item(self.keygen_page, FluentIcon.VPN, self.i18n.t("nav.keygen"))
        self.add_nav_item(
            self.settings_page,
            FluentIcon.SETTING,
            self.i18n.t("nav.settings"),
            position=NavigationItemPosition.BOTTOM,
        )

        self.stackedWidget.setCurrentWidget(self.keygen_page)
        self.navigationInterface.setCurrentItem(self.keygen_page.objectName())


    def add_nav_item(self, page: QWidget, icon: FluentIcon, text: str,
        position: NavigationItemPosition = NavigationItemPosition.TOP,) -> None:

        route_key = page.objectName()
        self.nav_routes[route_key] = page
        self.navigationInterface.addItem(
            routeKey=route_key,
            icon=icon,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(page),
            position=position,
        )

    def set_nav_item_text(self, route_key: str, text: str) -> None:
        nav_widget = self.navigationInterface.widget(route_key)
        if nav_widget is not None:
            nav_widget.setText(text)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.titleBar.resize(self.width(), self.titleBar.height())


    def closeEvent(self, event) -> None:
        self.config.window["width"] = self.width()
        self.config.window["height"] = self.height()
        user_config.save_config(self.config)
        super().closeEvent(event)