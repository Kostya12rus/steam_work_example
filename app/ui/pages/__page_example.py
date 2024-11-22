import flet as ft
from app.ui.pages.base import BasePage, Title
from app.core import Account


class ExamplePageContent(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True

        self.title = Title('EXAMPLE PAGE')

        self.controls = [
            self.title,
        ]

class ExamplePage(BasePage):
    def __init__(self):
        super().__init__()
        self.name = 'example'
        self.label = 'Example'
        self.icon = ft.icons.PAYMENT
        self.selected_icon = ft.icons.PAYMENT_ROUNDED

        self.page_content = ExamplePageContent()

    def on_callback_qr_code_ready(self, image_str: str):
        ...
    def on_callback_qr_code_timeout(self):
        ...
    def on_callback_authenticated(self, account: Account):
        ...
    def on_callback_authenticated_error(self, error_str: str):
        ...
