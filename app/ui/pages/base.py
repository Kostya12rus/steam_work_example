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

class BasePage(ft.Container):
    def __init__(self):
        super().__init__()

        self.name: str | None = None
        self.label: str | None = None
        self.icon = ft.icons.HOURGLASS_EMPTY
        self.selected_icon = ft.icons.HOURGLASS_EMPTY_ROUNDED

        self.not_disabled = False
        self.disabled_is_login = False
        self.disabled_is_logout = False

        self.page_content: ft.Container | None = None

        callback_manager.register(EventName.ON_ACCOUNT_LOGGED_IN, self.__login_account)
        callback_manager.register(EventName.ON_ACCOUNT_LOGGED_OUT, self.__logout_account)

        callback_manager.register(EventName.ON_ACCOUNT_LOGGED_IN, self.on_callback_authenticated)
        callback_manager.register(EventName.ON_ACCOUNT_LOGGED_OUT, self.on_callback_logout)
        callback_manager.register(EventName.ON_ACCOUNT_LOGGED_ERROR, self.on_callback_authenticated_error)

        callback_manager.register(EventName.ON_QR_CODE_READY, self.on_callback_qr_code_ready)
        callback_manager.register(EventName.ON_QR_CODE_TIMEOUT, self.on_callback_qr_code_timeout)

        self._text_widget = None
        self._button_widget = None
        self.account: Account | None = None

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
            self._button_widget.color = ft.colors.GREY if is_disable else ft.colors.BLUE
            if self.page: self.page.update()
    def __login_account(self, account: Account):
        self.account = account
        sql_manager.account_save(account)

        is_disable = False if self.not_disabled else self.disabled_is_login
        if self.disabled != is_disable:
            self.disabled = is_disable
            self._button_widget.color = ft.colors.GREEN if self._button_widget.color == ft.colors.GREEN else ft.colors.GREY if is_disable else ft.colors.BLUE
            if self.page: self.page.update()

    def build(self):
        self.disabled = self.disabled_is_logout

        self._text_widget = ft.Text(f"{self.label}")
        self._text_widget.text_align = ft.TextAlign.CENTER
        self._text_widget.size = 14
        self._text_widget.max_lines = 2

        self._button_widget = ft.Icon()
        self._button_widget.name = self.icon
        self._button_widget.color = ft.colors.GREY if self.disabled else ft.colors.BLUE

        column_widget = ft.Column()
        column_widget.spacing = 0
        column_widget.alignment = ft.MainAxisAlignment.CENTER
        column_widget.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        column_widget.controls = [
            self._text_widget,
            self._button_widget
        ]

        self.content = ft.Container()
        self.content.width = 110
        self.content.padding = 0
        self.content.border = ft.border.all(1)
        self.content.border_radius = ft.border_radius.all(5)
        self.content.alignment = ft.alignment.center
        self.content.content = column_widget

        self.ink = True
        return self
    def set_select_page(self, is_select: bool):
        self._text_widget.weight = ft.FontWeight.BOLD if is_select else ft.FontWeight.NORMAL
        self._button_widget.color = ft.colors.GREEN if is_select else ft.colors.GREY if self.disabled else ft.colors.BLUE
        self._button_widget.name = self.selected_icon if is_select else self.icon
        if self.page: self.update()

    def will_unmount(self):
        ...
    def did_mount(self):
        ...
    def before_update(self) -> None:
        ...
