import flet as ft

from app.core import Account
from app.ui.pages import BasePage, Title


class GameAllItemsContent(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True

        self.title = Title('Page Game All Items')

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


class GameAllItemsPage(BasePage):
    load_position = 7

    def __init__(self):
        super().__init__()
        self.name = 'game_all_items'
        self.label = 'Game All Items'
        self.icon = ft.icons.INVENTORY_2_OUTLINED
        self.selected_icon = ft.icons.INVENTORY_2

        self.disabled_is_logout = True

        self.visible = False

        self.page_content = GameAllItemsContent()

    def on_callback_authenticated(self, account: Account):
        ...

    def on_callback_logout(self):
        ...
