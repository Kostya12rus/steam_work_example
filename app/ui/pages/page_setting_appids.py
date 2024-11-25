import re
import threading
import flet as ft

from app.ui.pages.base import BasePage, Title
from app.core import AppDetails
from app.database import sql_manager, config
from app.callback import callback_manager, EventName


class AppIDSelector(ft.FilledTonalButton):
    def __init__(self, use_config: bool = False, on_app_id_select: callable = None):
        super().__init__()
        # region Настройка кнопки
        self.text = 'Select App ID'
        self.icon = ft.icons.APPS
        self.on_click = self._on_button_click
        self.style = ft.ButtonStyle(padding=ft.padding.all(0))
        # endregion

        # region Локальные переменные
        self._app_details_list: list[AppDetails] = []
        self._app_controls_map: dict[str, ft.Control] = {}
        self.use_config: bool = use_config
        self.on_app_id_select: callable = on_app_id_select
        # endregion

        # region Кастомный выбор App ID
        self._custom_app_details: AppDetails | None = None

        self._custom_radio_button = ft.Radio()
        self._custom_radio_button.toggleable = True
        self._custom_radio_button.value = 'custom'
        self._custom_radio_button.disabled = True

        self._app_ids_input = ft.TextField()
        self._app_ids_input.height = 30
        self._app_ids_input.dense = True
        self._app_ids_input.expand = True
        self._app_ids_input.max_lines = 1
        self._app_ids_input.multiline = False
        self._app_ids_input.content_padding = 10
        self._app_ids_input.border_color = ft.colors.GREY
        self._app_ids_input.label = 'App ID | Steam App url'
        self._app_ids_input.on_change = self._on_change_app_ids_input

        button_style = ft.ButtonStyle()
        button_style.icon_size = 20
        button_style.padding = ft.padding.all(1)
        button_style.alignment = ft.alignment.center

        self._load_app_id_button = ft.IconButton()
        self._load_app_id_button.icon = ft.icons.CLOUD_DOWNLOAD
        self._load_app_id_button.style = button_style
        self._load_app_id_button.visible = False
        self._load_app_id_button.on_click = self._on_click_load_app_id_button

        self._custom_app_logo = ft.Image()
        self._custom_app_logo.src = " "
        self._custom_app_logo.height = 20
        self._custom_app_logo.visible = False
        self._custom_app_logo.fit = ft.ImageFit.CONTAIN
        self._custom_app_logo.repeat = ft.ImageRepeat.NO_REPEAT

        self._custom_app_name = ft.Text()
        self._custom_app_name.size = 20
        self._custom_app_name.expand = True
        self._custom_app_name.visible = False
        self._custom_app_name.max_lines = 1
        self._custom_app_name.text_align = ft.TextAlign.LEFT
        self._custom_app_name.overflow = ft.TextOverflow.ELLIPSIS

        self._save_app_id_button = ft.IconButton()
        self._save_app_id_button.icon = ft.icons.SAVE
        self._save_app_id_button.style = button_style
        self._save_app_id_button.visible = False
        self._save_app_id_button.on_click = self._on_click_save_app_id_button

        self._custom_radio_container = ft.Container()
        self._custom_radio_container.content = ft.Row(
            spacing=0,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self._custom_radio_button,
                self._app_ids_input,
                self._load_app_id_button,
                self._custom_app_logo,
                self._custom_app_name,
                self._save_app_id_button,
            ]
        )
        self._custom_radio_container.padding = 0
        self._custom_radio_container.height = 30
        self._custom_radio_container.alignment = ft.alignment.center_right
        self._custom_radio_container.on_click = lambda e: self.set_select_game('custom')
        self._custom_radio_container.ink = True
        # endregion

        # region Содержимое диалога
        self._dialog_content_column = ft.Column(spacing=0, controls=[self._custom_radio_container])
        self._dialog_radio_group = ft.RadioGroup(content=self._dialog_content_column)
        self._dialog_main_column = ft.Column(expand=True, controls=[self._dialog_radio_group])

        self._dialog_button_select = ft.FilledTonalButton(text='Select App ID', on_click=self._on_dialog_select_click)
        self._dialog_button_close = ft.FilledTonalButton(text='Close', on_click=self._on_dialog_close_click)

        self._dialog = ft.AlertDialog(
            scrollable=True,
            title=Title('Select App ID'),
            content=self._dialog_main_column,
            actions=[self._dialog_button_select, self._dialog_button_close]
        )
        # endregion

    def did_mount(self):
        self._update_app_ids()
    def _on_button_click(self, e):
        self._update_app_ids()
        self.page.open(self._dialog)
    def _on_dialog_close_click(self, e):
        self.page.close(self._dialog)

    def _get_config_name(self):
        if not self.page:
            return None
        parent_hierarchy = []
        parent = self.parent
        while parent:
            parent_hierarchy.insert(0, parent.__class__.__name__)
            parent = parent.parent
        if not parent_hierarchy:
            return None
        return f'{"_".join(parent_hierarchy)}_{self.__class__.__name__}'
    def _get_config_value(self):
        if not self.use_config: return None
        config_name = self._get_config_name()
        if not config_name: return None
        config.add_property(config_name, type_value=str, default_return="")
        return config.get_property(config_name)
    def _set_config_value(self, value):
        if not self.use_config: return
        config_name = self._get_config_name()
        if not config_name: return

        config.add_property(config_name, type_value=str, default_return="")
        config.set_property(config_name, value)

    def get_select_game(self, *args) -> str:
        if self._dialog_radio_group.value == 'custom':
            return self._on_change_app_ids_input(set_custom=False)
        elif self._dialog_radio_group.value:
            return str(self._dialog_radio_group.value)
        else:
            return ''
    def set_select_game(self, *args, app_id: str | int=''):
        if not app_id: app_id = ''
        app_id = str(app_id)

        if app_id in self._app_controls_map:
            self._dialog_radio_group.value = str(app_id)
        elif app_id == "custom":
            self._dialog_radio_group.value = 'custom'
        elif app_id:
            self._dialog_radio_group.value = 'custom'
            self._app_ids_input.value = str(app_id)
        else:
            self._dialog_radio_group.value = ''
        if self._dialog_radio_group.page: self._dialog_radio_group.update()

    def _create_app_control(self, app_details: AppDetails):
        if not app_details or not app_details.is_real_app(): return
        radio_button = ft.Radio()
        radio_button.toggleable = True
        radio_button.value = str(app_details.appid)
        radio_button.disabled = True

        app_logo = ft.Image()
        app_logo.height = 20
        app_logo.src = app_details.image
        app_logo.fit = ft.ImageFit.CONTAIN
        app_logo.repeat = ft.ImageRepeat.NO_REPEAT

        app_name_text = ft.Text()
        app_name_text.size = 20
        app_name_text.expand = True
        app_name_text.max_lines = 1
        app_name_text.value = app_details.name
        app_name_text.text_align = ft.TextAlign.LEFT
        app_name_text.overflow = ft.TextOverflow.ELLIPSIS

        app_row = ft.Row(
            spacing=0,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[radio_button, app_logo, app_name_text]
        )

        container = ft.Container()
        container.content = app_row
        container.padding = 0
        container.alignment = ft.alignment.center_right
        container.on_click = lambda e: self.set_select_game(app_id=app_details.appid)
        container.ink = True

        return container

    def _update_app_ids(self):
        self._app_details_list = sql_manager.appdetails_all_get()
        self._app_controls_map.update({
            str(app_details.appid): self._create_app_control(app_details)
            for app_details in self._app_details_list
            if app_details.is_real_app() and app_details.appid not in self._app_controls_map
        })
        for _app_id in self._app_controls_map.copy().keys():
            if not any(str(app_details.appid) == str(_app_id) for app_details in self._app_details_list):
                del self._app_controls_map[_app_id]

        self._dialog_content_column.controls = [self._custom_radio_container] + sorted(
            self._app_controls_map.values(),
            key=lambda control: next(
                int(app_id)
                for app_id, app_control in self._app_controls_map.items()
                if control == app_control
            )
        )
        config_app_id = self._get_config_value()
        self.set_select_game(app_id=config_app_id)
        self._update_main_button()

    def _update_main_button(self):
        selected_app_id = self.get_select_game()
        if not self.page: return
        self.icon = ft.icons.PLAYLIST_ADD_CHECK_CIRCLE if selected_app_id else ft.icons.APPS
        self.icon_color = ft.colors.GREEN if selected_app_id else None
        if self.page: self.update()

    def _on_dialog_select_click(self, e):
        self.page.close(self._dialog)
        self._set_config_value(self.get_select_game())

        self._update_main_button()
        self._execute_on_app_id_select()

    def _execute_on_app_id_select(self):
        if not self.on_app_id_select: return
        selected_app_id = self.get_select_game()
        threading.Thread(target=self.on_app_id_select, args=(selected_app_id,), daemon=True).start()

    def _on_change_app_ids_input(self, *args, set_custom=True):
        if set_custom: self.set_select_game(app_id='custom')

        app_id_input = self._app_ids_input.value
        app_re = re.findall(r'app/(\d+)/', app_id_input)
        input_app_id = app_re.pop() if app_re else app_id_input.strip()

        input_app_id_isnumeric = input_app_id.isnumeric()
        is_current_app_details = bool(self._custom_app_details and str(self._custom_app_details.appid) == str(input_app_id))

        self._load_app_id_button.visible = not is_current_app_details and input_app_id_isnumeric
        self._custom_app_logo.visible = is_current_app_details
        self._custom_app_name.visible = is_current_app_details
        self._save_app_id_button.visible = is_current_app_details
        if self._custom_radio_container.page: self._custom_radio_container.update()
        return input_app_id if input_app_id_isnumeric else ''
    def _on_click_load_app_id_button(self, e):
        input_app_id = self._on_change_app_ids_input()
        if not input_app_id: return
        self._custom_app_details = AppDetails.create_from_appid(input_app_id)
        if not self._custom_app_details or not self._custom_app_details.is_real_app(): return
        self._custom_app_logo.src = self._custom_app_details.image
        self._custom_app_name.value = self._custom_app_details.name
        self._on_change_app_ids_input()
    def _on_click_save_app_id_button(self, e):
        input_app_id = self._on_change_app_ids_input()
        if not input_app_id: return
        if not self._custom_app_details or not self._custom_app_details.is_real_app(): return
        if str(self._custom_app_details.appid) != str(input_app_id): return
        self._custom_app_details.save()
        self._update_app_ids()
        self.set_select_game(app_id=self._custom_app_details.appid)

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
        self.app_details.remove()

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
        for app_details in sql_manager.appdetails_all_get():
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
    def __init__(self):
        super().__init__()
        self.name = 'app_ids'
        self.label = 'App IDs'
        self.icon = ft.icons.APPS_OUTAGE
        self.selected_icon = ft.icons.APPS_OUTAGE_ROUNDED

        self.page_content = AppIDsPageContent()
