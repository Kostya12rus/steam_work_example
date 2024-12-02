import flet as ft
from app.ui.pages import BasePage, Title
from app.core import Account


class StackerPageContent(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True

        self.title = Title('Page Stacker')

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

class StackerPage(BasePage):
    load_position = 4
    def __init__(self):
        super().__init__()
        self.name = 'stacker'
        self.label = 'Stacker'
        self.icon = ft.icons.LAYERS_OUTLINED
        self.selected_icon = ft.icons.LAYERS

        self.disabled_is_logout = True

        self.page_content = StackerPageContent()

    def on_callback_authenticated(self, account: Account):
        ...
    def on_callback_logout(self):
        ...
