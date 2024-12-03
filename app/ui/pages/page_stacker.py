import time, datetime, threading
import flet as ft

from app.core import Account
from app.logger import logger
from app.ui.widgets import AppIDSelector
from app.ui.pages import BasePage, Title
from app.package.data_collectors import SteamAPIUtility, InventoryManager, InventoryItemRgDescriptions

class ItemRowContent(ft.Container):
    def __init__(self, item: InventoryItemRgDescriptions):
        # region ft.Container params
        super().__init__()
        self.ink = True
        self.padding = ft.padding.all(2)
        self.on_click = lambda *args: None
        self.alignment = ft.alignment.center_left
        self.border_radius = ft.border_radius.all(0)
        self.border = ft.border.only(bottom=ft.BorderSide(1))
        # endregion

        # region Class params
        self.item: InventoryItemRgDescriptions = item
        self.already_stacked = False
        # endregion

        # region Widgets
        self.url = self.item.get_market_url()

        self.item_image = ft.Image()
        self.item_image.width = 30
        self.item_image.height = 30
        self.item_image.src = self.item.get_icon_url(width=30, height=30)

        self.name_text = ft.Text()
        self.name_text.size = 15
        self.name_text.width = 250
        self.name_text.value = f"{self.item.name}"
        self.name_text.color = self.item.get_color()
        self.name_text.max_lines = 1
        self.name_text.selectable = True
        self.name_text.text_align = ft.TextAlign.LEFT
        self.name_text.overflow = ft.TextOverflow.ELLIPSIS

        self.amount_text = ft.Text()
        self.amount_text.size = 15
        self.amount_text.max_lines = 1
        self.amount_text.value = f"{self.item.get_amount()} pcs."
        self.amount_text.width = 100
        self.amount_text.text_align = ft.TextAlign.RIGHT
        self.amount_text.overflow = ft.TextOverflow.ELLIPSIS

        self.count_items_text = ft.Text()
        self.count_items_text.size = 15
        self.count_items_text.max_lines = 1
        self.count_items_text.value = f"{self.item.get_items_amount()} itm."
        self.count_items_text.width = 100
        self.count_items_text.text_align = ft.TextAlign.RIGHT
        self.count_items_text.overflow = ft.TextOverflow.ELLIPSIS

        self.limit_item_text = ft.Text()
        self.limit_item_text.size = 15
        self.limit_item_text.max_lines = 1
        self.limit_item_text.value = f"{self.item.end_ban_marketable()}" if self.item.end_ban_marketable() else ' '
        self.limit_item_text.color = ft.colors.RED
        self.limit_item_text.expand = True
        self.limit_item_text.text_align = ft.TextAlign.RIGHT
        self.limit_item_text.overflow = ft.TextOverflow.ELLIPSIS

        self.stack_button = ft.FilledTonalButton(height=25)
        self.stack_button.text = 'Stack'
        self.stack_button.icon = ft.icons.ADD
        self.stack_button.disabled = not self.is_stackable()
        self.stack_button.icon_color = ft.colors.GREEN if self.is_stackable() else ft.colors.RED
        self.stack_button.style = ft.ButtonStyle()
        self.stack_button.style.icon_size = 20
        self.stack_button.style.padding = ft.padding.all(5)
        self.stack_button.style.alignment = ft.alignment.center
        self.stack_button.style.shape = ft.RoundedRectangleBorder(radius=5)

        self.row = ft.Row()
        self.row.spacing = 2
        self.row.expand = True
        self.row.alignment = ft.MainAxisAlignment.START
        self.row.vertical_alignment = ft.CrossAxisAlignment.CENTER
        self.row.controls = [
            self.item_image,
            self.name_text,
            self.amount_text,
            self.count_items_text,
            self.limit_item_text,
            self.stack_button,
        ]

        self.content = self.row
        # endregion

    def get_amount(self) -> int:
        return self.item.get_amount()
    def get_count_items(self) -> int:
        return self.item.get_items_amount()
    def is_stackable(self) -> bool:
        return self.item.get_items_amount() > 1
    def get_sort_value(self) -> tuple[int, int]:
        return int(self.item.classid), int(self.item.instanceid)

class StackerPageContent(ft.Column):
    def __init__(self):
        # region ft.Column params
        super().__init__()
        self.spacing = 2
        self.expand = True
        # endregion

        # region Class params
        self._account: Account | None = None
        self.__items_content: dict[str, ItemRowContent] = {}
        self.__is_init_inventory = False
        self.__last_inventory: InventoryManager | None = None
        self.__last_update_inventory = datetime.datetime.now()
        self._steam_api_utility = SteamAPIUtility(self._account)
        self._lock_stack = threading.Lock()
        self._is_work = False
        self._on_update_is_work = False
        # endregion

        # region settings Title
        self._title = Title('Inventory Stacker')
        self._title.expand = True
        self._app_id_selector = AppIDSelector(height=25, padding=ft.padding.all(5))
        self._app_id_selector.use_config = True
        self._app_id_selector.on_app_id_select = self._on_select_app_id

        self._title_row = ft.Row()
        self._title_row.expand = True
        self._title_row.alignment = ft.MainAxisAlignment.CENTER
        self._title_row.controls = [
            self._title,
            self._app_id_selector
        ]
        # endregion

        # region Items Content
        self._items_column = ft.ListView()
        self._items_column.spacing = 0
        self._items_column.expand = True
        self._items_column.controls = []
        self._items_column.padding = ft.padding.all(2)
        # endregion

        # region Bottom Row
        style = ft.ButtonStyle()
        style.padding = ft.padding.all(0)
        style.alignment = ft.alignment.center
        style.icon_size = 20

        self._now_item_image = ft.Image()
        self._now_item_image.width = 30
        self._now_item_image.height = 30
        self._now_item_image.src = ' '

        self._now_item_text = ft.Text()
        self._now_item_text.size = 15
        self._now_item_text.width = 250
        self._now_item_text.max_lines = 1
        self._now_item_text.text_align = ft.TextAlign.LEFT
        self._now_item_text.overflow = ft.TextOverflow.ELLIPSIS

        self._time_left_text = ft.Text()
        self._time_left_text.size = 15
        self._time_left_text.width = 100
        self._time_left_text.text_align = ft.TextAlign.RIGHT
        self._time_left_text.overflow = ft.TextOverflow.ELLIPSIS

        self._now_item_progress = ft.ProgressBar(expand=True)
        self._now_item_progress.height = 10
        self._now_item_progress.value = 0.1
        self._now_item_progress.color = '#4CAF50'
        self._now_item_progress.bgcolor = '#E0E0E0'
        self._total_progress = ft.ProgressBar(expand=True)
        self._total_progress.height = 10
        self._total_progress.value = 0.5
        self._total_progress.color = '#2196F3'
        self._now_item_progress.bgcolor = '#B0BEC5'
        progress_column = ft.Column()
        progress_column.expand = True
        progress_column.spacing = 2
        progress_column.alignment = ft.MainAxisAlignment.CENTER
        progress_column.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        progress_column.controls = [
            self._now_item_progress,
            self._total_progress
        ]

        self._stacking_progress_row = ft.Row()
        self._stacking_progress_row.spacing = 2
        self._stacking_progress_row.visible = False
        self._stacking_progress_row.alignment = ft.MainAxisAlignment.START
        self._stacking_progress_row.vertical_alignment = ft.CrossAxisAlignment.CENTER
        self._stacking_progress_row.controls = [
            self._now_item_image,
            self._now_item_text,
            self._time_left_text,
            progress_column,
        ]

        self._is_update_after_stack = ft.Checkbox(label='Update after Stack', value=True, splash_radius=0)

        self._start_stacking_all_button = ft.FilledTonalButton()
        self._start_stacking_all_button.text = 'Stack All'
        self._start_stacking_all_button.icon = ft.icons.START
        self._start_stacking_all_button.icon_color = ft.colors.GREEN
        self._start_stacking_all_button.expand = True
        self._start_stacking_all_button.style = style
        self._start_stacking_all_button.on_click = self._on_click_start_stacking_all

        self._botton_row = ft.Row()
        self._botton_row.spacing = 2
        self._botton_row.height = 25
        self._botton_row.disabled = True
        self._botton_row.alignment = ft.MainAxisAlignment.START
        self._botton_row.vertical_alignment = ft.CrossAxisAlignment.CENTER
        self._botton_row.controls = [
            self._is_update_after_stack,
            self._start_stacking_all_button,
        ]
        # endregion

        # region Main Content
        container_items = ft.Container()
        container_items.expand = True
        container_items.border = ft.border.all(1)
        container_items.padding = ft.padding.all(0)
        container_items.content = self._items_column
        container_items.border_radius = ft.border_radius.all(5)
        # endregion

        self.controls = [
            ft.Row(controls=[self._title_row]),
            container_items,
            self._stacking_progress_row,
            self._botton_row,
        ]

    def _on_select_app_id(self, app_id: str):
        try:
            if not self._is_work:
                self._on_update_is_work = True
                return

            self._app_id_selector.update_button(disabled=True, icon=ft.icons.UPDATE, icon_color=ft.colors.BLUE, text='Loading...')
            self._items_column.controls = []
            if self._items_column.page: self._items_column.update()

            if not app_id: return
            self.__last_inventory = self._steam_api_utility.get_inventory_items(appid=app_id)
            inventory = self.__last_inventory.inventory if self.__last_inventory else []

            is_stackable = any(item.get_items_amount() > 1 for item in inventory)
            self._botton_row.disabled = not is_stackable
            self._start_stacking_all_button.icon_color = ft.colors.GREEN if is_stackable else ft.colors.RED
            if self._botton_row.page: self._botton_row.update()

            self._items_column.controls = [ItemRowContent(item) for item in inventory]
            for item_content in self._items_column.controls:
                item_content: ItemRowContent
                item_content.stack_button.on_click = lambda e, _item_content=item_content: self._on_click_start_stacking_item(item_content=_item_content)

            self._items_column.controls.sort(key=lambda x: x.get_sort_value())
            if self._items_column.page: self._items_column.update()
        finally:
            self._app_id_selector.update_button()

    def _stack_item(self, item_content: ItemRowContent, start_index: int, total_count: int):
        item_content.stack_button.disabled = True
        item_content.stack_button.icon_color = ft.colors.RED
        if item_content.stack_button.page: item_content.stack_button.update()

        total_item_count = item_content.get_count_items()
        time_wait = 0.05

        with self._lock_stack:
            self._stacking_progress_row.visible = True
            self._now_item_image.src = item_content.item.get_icon_url(width=29, height=29)
            self._now_item_text.value = item_content.item.name
            self._now_item_text.color = item_content.item.get_color()
            self._total_progress.value = start_index / total_count
            self._now_item_progress.value = 0
            self._time_left_text.value = f"~{(total_count-start_index)*time_wait} sec."
            if self._stacking_progress_row.page: self._stacking_progress_row.update()
            if item_content.already_stacked: return
            item_content.already_stacked = True
            if total_item_count <= 1: return

            logger.info(f"Start Stacking '{item_content.item.name}' {total_item_count} items")

            item_get_stack = item_content.item.items[0] if len(item_content.item.items) > 0 else None
            if not item_get_stack: return
            for num, item in enumerate(item_content.item.items, start=1):
                if not self._is_work:
                    logger.info(f"Stop Stacking (User close page) '{item_content.item.name}'")
                    return
                now_index = start_index+num
                self._now_item_progress.value = num / total_item_count
                self._total_progress.value = now_index / total_count
                time_left = (total_count - now_index) * time_wait
                self._time_left_text.value = f"~{time_left:.1f} sec."
                if self._stacking_progress_row.page: self._stacking_progress_row.update()
                if item_get_stack.assetid == item.assetid: continue

                threading.Thread(
                    target=self._steam_api_utility.combine_itemstacks,
                    kwargs={'fromitem': item, 'destitem': item_get_stack},
                    daemon=True
                ).start()

                time.sleep(time_wait)
            logger.info(f"Finish Stacking '{item_content.item.name}'")

    def _on_click_start_stacking_all(self, e):
        try:
            self._botton_row.disabled = True
            self._start_stacking_all_button.icon_color = ft.colors.RED
            if self._botton_row.page: self._botton_row.update()

            logger.info("Start Stacking All Items")

            items_content: list[ItemRowContent | ft.Control] = self._items_column.controls.copy()

            for item_content in items_content:
                item_content.stack_button.disabled = True
                item_content.stack_button.icon_color = ft.colors.RED
                if item_content.stack_button.page: item_content.stack_button.update()

            start_index = 0
            total_item_count = sum(ic.get_count_items() for ic in items_content if not ic.already_stacked)
            for item_content in items_content:
                if not self._is_work:
                    logger.info("Stop Stacking All Items (User close page)")
                    break
                if item_content.already_stacked: continue
                self._stack_item(item_content, start_index, total_item_count)
                item_count_items = item_content.get_count_items()
                start_index += item_count_items
        finally:
            logger.info("Finish Stacking All Items")
            if self._is_update_after_stack.value:
                self._stacking_progress_row.visible = True
                self._now_item_image.src = ' '
                self._now_item_text.value = 'Update after Stack'
                self._now_item_text.color = ft.colors.BLUE
                self._total_progress.value = None
                self._now_item_progress.value = None
                self._time_left_text.value = f"~5 sec."
                if self._stacking_progress_row.page: self._stacking_progress_row.update()
                time_sleep = 0.1
                count_update = int(5 / time_sleep)
                for i in range(count_update):
                    time_left = (count_update - i) * time_sleep
                    self._time_left_text.value = f"~{time_left:.1f} sec."
                    if self._stacking_progress_row.page: self._stacking_progress_row.update()
                    time.sleep(time_sleep)

            self._stacking_progress_row.visible = False
            if self._stacking_progress_row.page: self._stacking_progress_row.update()

        if self._is_update_after_stack.value:
            logger.info("Update after Stack")
            self._on_select_app_id(self._app_id_selector.get_config_value())

    def _on_click_start_stacking_item(self, item_content: ItemRowContent):
        if not item_content or not item_content.is_stackable(): return
        try:
            start_index = 0
            total_item_count = item_content.get_count_items()
            self._stack_item(item_content, start_index, total_item_count)
        finally:
            self._stacking_progress_row.visible = False
            if self._stacking_progress_row.page: self._stacking_progress_row.update()

    def on_update_account(self, account: Account = None):
        self._account = account
        self._steam_api_utility.account = account

    def did_mount(self):
        self._is_work = True
        if not self.__is_init_inventory or self._on_update_is_work:
            self.__is_init_inventory = True
            self._on_update_is_work = False
            self._on_select_app_id(self._app_id_selector.get_config_value())

    def will_unmount(self):
        self._is_work = False

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
        self.page_content.on_update_account(account)
    def on_callback_logout(self):
        self.page_content.on_update_account()
