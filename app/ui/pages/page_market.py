import flet as ft
from app.ui.pages import BasePage, Title
from app.core import Account


class MarketPageContent(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True

        self.title = Title('Page Market')

        text_coming_soon = ft.Text()
        text_coming_soon.size = 24
        text_coming_soon.expand = True
        text_coming_soon.value = 'Comming soon'
        text_coming_soon.color = ft.colors.BLUE
        text_coming_soon.text_align = ft.TextAlign.CENTER

        self.controls = [
            self.title,
            ft.Container(expand=True, content=text_coming_soon, alignment=ft.alignment.center)
        ]

class MarketPage(BasePage):
    load_position = 6
    def __init__(self):
        super().__init__()
        self.name = 'market'
        self.label = 'Market'
        self.icon = ft.icons.STORE_OUTLINED
        self.selected_icon = ft.icons.STORE

        self.disabled_is_logout = True

        self.visible = False

        self.page_content = MarketPageContent()

    def on_callback_authenticated(self, account: Account):
        ...
    def on_callback_logout(self):
        ...
