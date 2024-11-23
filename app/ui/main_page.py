import flet as ft

from app.callback import callback_manager, EventName
from app.ui.widgets import ThemeToggleButton, ColorMenuButton
from app.ui.pages import page_manager
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

        self._pages = page_manager.get_pages()

        self.expand = True
        self.spacing = 0

        self.logout_button = ft.IconButton(visible=False)
        self.logout_button.icon = ft.icons.LOGOUT
        self.logout_button.icon_color = ft.colors.RED
        self.logout_button.tooltip = "Logout"
        self.logout_button.on_click = self.on_press_logout

        self.navigation_rail = ft.NavigationRail(expand=True, selected_index=0)
        self.navigation_rail.label_type = ft.NavigationRailLabelType.ALL
        self.navigation_rail.destinations = self._pages
        self.navigation_rail.on_change = self.on_rail_change
        self.navigation_rail.trailing = self.logout_button

        self.design_editor_theme_toggle = ThemeToggleButton()
        self.design_editor_color_menu = ColorMenuButton()

        self.design_editor = ft.Row(spacing=0)
        self.design_editor.alignment = ft.MainAxisAlignment.CENTER
        self.design_editor.vertical_alignment = ft.CrossAxisAlignment.CENTER
        self.design_editor.controls = [
            self.design_editor_theme_toggle,
            self.design_editor_color_menu
        ]

        self.navigation_column = ft.Column()
        self.navigation_column.alignment = ft.MainAxisAlignment.CENTER
        self.navigation_column.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.navigation_column.controls = [
            self.navigation_rail,
            self.design_editor
        ]

        self.vertical_divider = ft.VerticalDivider()

        self.content_page = ft.Column(controls=[], expand=True, spacing=1)

        self.controls = [self.navigation_column, self.vertical_divider, self.content_page]

    def on_press_logout(self, *args):
        callback_manager.trigger(EventName.ON_ACCOUNT_LOGGED_OUT)

    def set_snack_bar(self, text: str):
        if self.page:
            text_snack_bar = ft.Text(text, expand=True, text_align=ft.TextAlign.CENTER)
            self.page.snack_bar = ft.SnackBar(text_snack_bar)
            self.page.snack_bar.open = True
            self.page.update()
    def on_callback_logout(self):
        self.set_snack_bar("Logout success")
        set_page = next((page for page in self._pages if page.not_disabled or not page.disabled_is_logout), None)
        if set_page: self.on_rail_change(set_page=set_page)
        self.logout_button.visible = False
        self.update()
    def on_callback_authenticated(self, account: Account):
        self.set_snack_bar(f"Success auth {account.account_name}")
        set_page = next((page for page in self._pages if page.not_disabled or not page.disabled_is_login), None)
        if set_page: self.on_rail_change(set_page=set_page)
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

    def on_rail_change(self, event: ft.ControlEvent = None, set_page: ft.NavigationRailDestination = None):
        if set_page:
            selected_index = self._pages.index(set_page)
            if selected_index != self.navigation_rail.selected_index:
                self.navigation_rail.selected_index = selected_index
                self.navigation_rail.update()
        now_page = self._pages[self.navigation_rail.selected_index]
        if not now_page: return
        if now_page.page_content in self.content_page.controls: return
        self.content_page.controls = [now_page.page_content]
        self.content_page.update()


class MainPage:
    def __init__(self, title: str = None):
        self.title = title or "Competitive Matches by Kostya12rus"
        self.page = None
        self.page_content = MainPageContent()

    def build(self, page: ft.Page):
        self.page = page
        self.page.window.min_width = 1130
        self.page.window.min_height = 600
        self.page.padding = 0
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
