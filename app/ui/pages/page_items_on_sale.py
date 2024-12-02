import flet as ft
from app.ui.pages import BasePage, Title
from app.core import Account


class ItemsOnSalePageContent(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True

        self.title = Title('Page Items on Sale')

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

class ItemsOnSalePage(BasePage):
    load_position = 5
    def __init__(self):
        super().__init__()
        self.name = 'items_on_sale'
        self.label = 'Items on sale'
        self.icon = ft.icons.SELL_OUTLINED
        self.selected_icon = ft.icons.SELL

        self.disabled_is_logout = True

        self.page_content = ItemsOnSalePageContent()

    def on_callback_authenticated(self, account: Account):
        ...
    def on_callback_logout(self):
        ...
