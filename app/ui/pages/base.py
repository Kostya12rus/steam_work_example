import flet as ft
from app.database import sql_manager
from app.core import Account
from app.package.steam_session import steam_session_manager

class Title(ft.Row):
    def __init__(self, title_text: str, size: int = 20, color: ft.colors = ft.colors.BLUE, text_align: ft.TextAlign = ft.TextAlign.CENTER):
        super().__init__()
        self.spacing = 0
        self.run_spacing = 0
        self.alignment = ft.MainAxisAlignment.CENTER
        self.text_widget = ft.Text(value=title_text, size=size, color=color, text_align=text_align, weight=ft.FontWeight.BOLD)
        self.container = ft.Container(padding=0, expand=True, content=self.text_widget)
        self.controls = [self.container]

class BasePage(ft.NavigationRailDestination):
    def __init__(self):
        super().__init__()
        self.name = None
        self.page_content = None
        self.account: Account = None

        steam_session_manager.register_callback_authenticated(self.__new_account)

        steam_session_manager.register_callback_logout(self.on_callback_logout)
        steam_session_manager.register_callback_authenticated(self.on_callback_authenticated)
        steam_session_manager.register_callback_authenticated_error(self.on_callback_authenticated_error)
        steam_session_manager.register_callback_qr_code_ready(self.on_callback_qr_code_ready)
        steam_session_manager.register_callback_qr_code_timeout(self.on_callback_qr_code_timeout)

    def on_callback_logout(self):
        ...
    def on_callback_authenticated(self, account: Account):
        ...
    def on_callback_authenticated_error(self, error: str):
        ...
    def on_callback_qr_code_ready(self, qr_code: str):
        ...
    def on_callback_qr_code_timeout(self):
        ...
    def __new_account(self, account: Account):
        self.account = account
        sql_manager.account_save(account)

    def build(self):
        ...
    def will_unmount(self):
        ...
    def did_mount(self):
        ...
    def before_update(self) -> None:
        ...
