import flet as ft

from app.callback import callback_manager, EventName
from app.ui.widgets import ThemeToggleButton, ColorMenuButton
from app.ui.pages import page_manager, BasePage
from app.package.steam_session import note_js_utility
from app.core import Account


class MainPageContent(ft.Row):
    def __init__(self):
        super().__init__()

        callback_manager.register(EventName.ON_ACCOUNT_LOGGED_OUT, self.on_callback_logout)
        callback_manager.register(EventName.ON_ACCOUNT_LOGGED_IN, self.on_callback_authenticated)
        callback_manager.register(EventName.ON_ACCOUNT_LOGGED_ERROR, self.on_callback_authenticated_error)

        callback_manager.register(EventName.ON_QR_CODE_READY, self.on_callback_qr_code_ready)
        callback_manager.register(EventName.ON_QR_CODE_TIMEOUT, self.on_callback_qr_code_timeout)
        callback_manager.register(EventName.ON_REQUEST_CONFIRMATION_DEVICE, self.on_callback_request_confirmation_device)
        callback_manager.register(EventName.ON_REQUEST_CONFIRMATION_EMAIL, self.on_callback_request_confirmation_email)


        self.expand = True
        self.spacing = 0


        self._pages = self.get_pages_list()
        self.navigation_widget = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)
        self.navigation_widget.spacing = 0
        self.navigation_widget.alignment = ft.MainAxisAlignment.CENTER
        self.navigation_widget.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.navigation_widget.controls = self._pages


        self.logout_button = ft.IconButton(visible=False)
        self.logout_button.icon = ft.icons.LOGOUT
        self.logout_button.icon_color = ft.colors.RED
        self.logout_button.tooltip = "Logout"
        self.logout_button.on_click = self.on_press_logout


        self.design_editor = ft.Row(spacing=0)
        self.design_editor.alignment = ft.MainAxisAlignment.CENTER
        self.design_editor.vertical_alignment = ft.CrossAxisAlignment.CENTER
        self.design_editor.controls = [
            ThemeToggleButton(),
            ColorMenuButton()
        ]

        self.navigation_column = ft.Column(spacing=0)
        self.navigation_column.alignment = ft.MainAxisAlignment.CENTER
        self.navigation_column.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.navigation_column.controls = [
            self.navigation_widget,
            self.logout_button,
            self.design_editor
        ]

        self.content_page = ft.Column(controls=[], expand=True, spacing=1)

        self.controls = [self.navigation_column, ft.VerticalDivider(), self.content_page]

    def get_pages_list(self) -> list[BasePage]:
        pages = page_manager.get_pages()
        for page in pages:
            page.on_click = self.on_rail_change
        return pages

    def on_press_logout(self, *args):
        callback_manager.trigger(EventName.ON_ACCOUNT_LOGGED_OUT)

    def set_snack_bar(self, text: str):
        if self.page:
            text_snack_bar = ft.Text(text, expand=True, text_align=ft.TextAlign.CENTER)
            self.page.open(ft.SnackBar(text_snack_bar))
    def on_callback_logout(self):
        self.set_snack_bar("Logout success")
        set_page = next((page for page in self._pages if page.not_disabled or not page.disabled_is_logout), None)
        if set_page: self.set_page(set_page)
        self.logout_button.visible = False
        self.update()
    def on_callback_authenticated(self, account: Account):
        self.set_snack_bar(f"Success auth {account.account_name}")
        set_page = next((page for page in self._pages if page.not_disabled or not page.disabled_is_login), None)
        if set_page: self.set_page(set_page)
        self.logout_button.visible = True
        self.update()
    def on_callback_authenticated_error(self, error: str):
        self.set_snack_bar(f"Error auth {error}")
    def on_callback_qr_code_ready(self, qr_code: str):
        self.set_snack_bar("QR code ready")
    def on_callback_qr_code_timeout(self):
        self.set_snack_bar("QR code timeout")
    def on_callback_request_confirmation_device(self):
        self.set_snack_bar("Request confirmation on device")
    def on_callback_request_confirmation_email(self):
        self.set_snack_bar("Request confirmation on email")

    def set_page(self, page: BasePage):
        for p in self._pages:
            p.set_select_page(p == page)

        select_page = next((p for p in self._pages if p == page), None)
        if select_page:
            if select_page.page_content in self.content_page.controls: return
            select_page.set_select_page(True)
            self.content_page.controls = [select_page.page_content]
            if self.page: self.content_page.update()

    def on_rail_change(self, event: ft.ControlEvent = None, set_page: BasePage = None):
        if event is None and set_page is None:
            self.set_page(self._pages[0])
        elif event and event.control:
            self.set_page(event.control)
        elif set_page:
            self.set_page(set_page)


class MainPage:
    def __init__(self, title: str = None):
        self.title = title or "NoName Project"
        self.page = None
        self.page_content = MainPageContent()

    def build(self, page: ft.Page):
        self.page = page
        self.page.window.min_width = 1130
        self.page.window.min_height = 600
        self.page.padding = 2
        self.page.title = self.title
        self.page.spacing = 1
        self.page.controls = [
            self.page_content
        ]

        self.page.update()
        self.page_content.on_rail_change(None)

        if note_js_utility.start_install():
            self.page_content.set_snack_bar("NoteJS library success update or install")
        else:
            self.page_content.set_snack_bar("NoteJS library error update or install")
