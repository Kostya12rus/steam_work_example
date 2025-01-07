import re
import flet as ft

from app.core import AppDetails
from app.ui.pages.base import BasePage, Title
from app.callback import callback_manager, EventName


class AppIDContent(ft.Container):
    """
    Класс для отображения информации о приложении Steam в виде виджета.
    """
    def __init__(self, app_details: AppDetails):
        super().__init__()
        self.padding = 0
        self.border = ft.border.all(1)
        self.border_radius = ft.border_radius.all(5)
        self.alignment = ft.alignment.center

        self.app_details = app_details

        self.logo_image = self.create_logo_image(app_details.image)
        self.title_text = self.create_title_text(app_details.name)
        self.store_link_button = self.create_store_link_button(app_details.store_url)
        self.price_text = self.create_price_text(app_details.price_overview)
        self.delete_button = self.create_delete_button()
        self.details_column = self.create_details_column()

        self.content = self.create_main_row()

    def create_logo_image(self, image_url: str) -> ft.Column:
        """
        Создает виджет изображения для логотипа приложения.
        """
        logo = ft.Image(src=image_url)
        logo.fit = ft.ImageFit.CONTAIN
        logo.repeat = ft.ImageRepeat.NO_REPEAT
        logo.height = 70

        logo_column = ft.Column(spacing=0, expand=True)
        logo_column.alignment = ft.MainAxisAlignment.CENTER
        logo_column.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        logo_column.controls = [
            logo
        ]

        return logo_column

    def create_title_text(self, title: str) -> ft.Text:
        """
        Создает текстовый виджет для названия приложения.
        """
        text = ft.Text(title, expand=True, max_lines=1, size=20)
        text.text_align = ft.TextAlign.CENTER
        text.overflow = ft.TextOverflow.ELLIPSIS
        text.weight = ft.FontWeight.BOLD
        return text

    def create_store_link_button(self, store_url: str) -> ft.FilledTonalButton:
        """
        Создает кнопку с ссылкой на магазин Steam.
        """
        button = ft.FilledTonalButton(icon=ft.icons.LINK, url=store_url)
        button.text = "Open app Steam Store"
        return button

    def create_price_text(self, price: str) -> ft.Text:
        """
        Создает текстовый виджет для отображения цены.
        """
        price_text = ft.Text(expand=True, max_lines=1)
        price_text.value = f"Price: {price if price else 'Free'}"
        price_text.text_align = ft.TextAlign.CENTER
        price_text.overflow = ft.TextOverflow.ELLIPSIS
        return price_text

    def create_details_column(self) -> ft.Column:
        """
        Создает колонку с текстовыми элементами.
        """
        column = ft.Column(spacing=1, expand=True)
        column.alignment = ft.MainAxisAlignment.CENTER
        column.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        column.controls = [
            ft.Row(controls=[self.title_text]),
            ft.Row(controls=[self.store_link_button], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row(controls=[self.price_text]),
        ]
        return column

    def create_delete_button(self) -> ft.Column:
        """
        Создает виджет кнопки для удаления приложения.
        """
        button = ft.FilledTonalButton(icon=ft.icons.DELETE, icon_color=ft.colors.RED)
        button.text = 'Delete App'
        button.on_click = self.__on_click_delete_button

        button_column = ft.Column(spacing=0, expand=True)
        button_column.alignment = ft.MainAxisAlignment.CENTER
        button_column.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        button_column.controls = [
            button
        ]

        return button_column

    def create_main_row(self) -> ft.Row:
        """
        Создает основную строку с логотипом и колонкой.
        """

        row = ft.Row(spacing=5)
        row.alignment = ft.MainAxisAlignment.CENTER
        row.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        row.controls = [
            self.logo_image,
            self.details_column,
            self.delete_button,
        ]
        return row

    def __on_click_delete_button(self, e):
        self.app_details.delete()

        self.visible = False
        if self.page: self.update()

class AppIDsPageContent(ft.Column):
    def __init__(self):
        # Class variables
        if True:
            super().__init__()
            self.expand = True
            self.spacing = 0
            self.alignment = ft.MainAxisAlignment.START
            self.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        # Variables
        if True:
            self.account = None
            callback_manager.register(EventName.ON_APP_ID_REMOVED, self.__on_app_id_removed)
            callback_manager.register(EventName.ON_APP_ID_ADDED, self.__on_app_id_removed)

        # Title
        if True:
            self.title = Title('App IDs Settings')

        # Input App IDs
        if True:
            self.app_ids_input = ft.TextField(dense=True, height=30)
            self.app_ids_input.label = 'App ID | Steam App url'
            self.app_ids_input.border_color = ft.colors.GREY
            self.app_ids_input.content_padding = 10
            self.app_ids_input.max_lines = 1
            self.app_ids_input.multiline = False
            self.app_ids_input.expand = True

            self.button_add = ft.FilledTonalButton(height=30)
            self.button_add.text = 'Add App ID'
            self.button_add.icon = ft.icons.ADD
            self.button_add.on_click = self.__on_click_button_add

            self.app_ids_input_row = ft.Row(spacing=0)
            self.app_ids_input_row.controls = [
                self.app_ids_input,
                self.button_add
            ]

        if True:
            self.apps_id_column = ft.ListView()
            self.apps_id_column.spacing = 0
            self.apps_id_column.padding = ft.padding.only(right=10)
            self.apps_id_column.expand = True

        self.controls = [
            self.title,
            ft.Divider(),
            self.app_ids_input_row,
            self.apps_id_column
        ]

        self.__load_all_apps()

    def __load_all_apps(self):
        self.apps_id_column.controls = []
        for app_details in AppDetails.load_all():
            self.apps_id_column.controls.append(AppIDContent(app_details))
        if self.page: self.update()

    def __on_app_id_removed(self, app_details: AppDetails):
        self.__load_all_apps()

    def __on_click_button_add(self, e):
        app_id_input = self.app_ids_input.value
        app_re = re.findall(r'app/(\d+)/', app_id_input)
        app_id = app_re.pop() if app_re else app_id_input
        if not app_id.isnumeric(): return
        self.app_ids_input.value = ''
        if self.page: self.app_ids_input.update()
        app_details = AppDetails.create_from_appid(appid=app_id)
        if not app_details or not app_details.is_real_app(): return
        app_details.save()

class AppIDsPage(BasePage):
    load_position = 99
    def __init__(self):
        super().__init__()
        self.name = 'app_ids'
        self.label = 'App IDs'
        self.icon = ft.icons.LIBRARY_ADD_OUTLINED
        self.selected_icon = ft.icons.LIBRARY_ADD

        self.visible = False

        self.page_content = AppIDsPageContent()
