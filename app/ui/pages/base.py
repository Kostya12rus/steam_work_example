import flet as ft
from app.database import sql_manager
from app.core import Account
from app.callback import callback_manager, EventName

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
        self.name: str | None = None
        self.page_content: ft.Container | None = None
        self.account: Account | None = None

        self.not_disabled = False
        self.disabled_is_login = False
        self.disabled_is_logout = False

        callback_manager.register(EventName.ON_ACCOUNT_LOGGED_IN, self.__login_account)
        callback_manager.register(EventName.ON_ACCOUNT_LOGGED_OUT, self.__logout_account)

        callback_manager.register(EventName.ON_ACCOUNT_LOGGED_IN, self.on_callback_authenticated)
        callback_manager.register(EventName.ON_ACCOUNT_LOGGED_OUT, self.on_callback_logout)
        callback_manager.register(EventName.ON_ACCOUNT_LOGGED_ERROR, self.on_callback_authenticated_error)

        callback_manager.register(EventName.ON_QR_CODE_READY, self.on_callback_qr_code_ready)
        callback_manager.register(EventName.ON_QR_CODE_TIMEOUT, self.on_callback_qr_code_timeout)

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

    def __logout_account(self):
        self.account = None

        is_disable = False if self.not_disabled else self.disabled_is_logout
        if self.disabled != is_disable:
            self.disabled = is_disable
            if self.page: self.page.update()
    def __login_account(self, account: Account):
        self.account = account
        sql_manager.account_save(account)

        is_disable = False if self.not_disabled else self.disabled_is_login
        if self.disabled != is_disable:
            self.disabled = is_disable
            if self.page: self.page.update()

    def build(self):
        ...
    def will_unmount(self):
        ...
    def did_mount(self):
        ...
    def before_update(self) -> None:
        ...
