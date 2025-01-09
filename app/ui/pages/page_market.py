import flet as ft

from app.core import Account
from app.ui.pages import BasePage, Title
from app.ui.widgets import AppIDSelector
from app.package.data_collectors import SteamAPIUtility, MarketListenItem


class ItemRowContent(ft.Container):
    def __init__(self, item: MarketListenItem):
        # region ft.Container params
        super().__init__()
        self.ink = True
        self.padding = ft.padding.all(2)
        self.url = item.get_market_url()
        self.alignment = ft.alignment.center_left
        self.border_radius = ft.border_radius.all(0)
        self.border = ft.border.only(bottom=ft.BorderSide(1))
        # endregion

        # region Class params
        self.item: MarketListenItem = item
        # endregion

        # region Widgets
        self.item_image = ft.Image()
        self.item_image.width = 30
        self.item_image.height = 30
        self.item_image.src = item.get_icon_url()

        self.name_text = ft.Text()
        self.name_text.size = 15
        self.name_text.width = 250
        self.name_text.max_lines = 1
        self.name_text.expand = True
        self.name_text.value = item.name
        self.name_text.selectable = True
        self.name_text.color = item.get_color()
        self.name_text.text_align = ft.TextAlign.LEFT
        self.name_text.overflow = ft.TextOverflow.ELLIPSIS

        self.amount_text = ft.Text()
        self.amount_text.size = 15
        self.amount_text.width = 100
        self.amount_text.max_lines = 1
        self.amount_text.expand = True
        self.amount_text.text_align = ft.TextAlign.RIGHT
        self.amount_text.overflow = ft.TextOverflow.ELLIPSIS
        self.amount_text.value = f"{self.item.sell_listings} pcs."

        self.one_market_price_text = ft.Text()
        self.one_market_price_text.size = 15
        self.one_market_price_text.max_lines = 1
        self.one_market_price_text.expand = True
        self.one_market_price_text.text_align = ft.TextAlign.RIGHT
        self.one_market_price_text.value = item.multiply_price_by(1)

        self.row = ft.Row()
        self.row.spacing = 2
        self.row.expand = True
        self.row.alignment = ft.MainAxisAlignment.START
        self.row.vertical_alignment = ft.CrossAxisAlignment.CENTER
        self.row.controls = [
            self.item_image,
            self.name_text,
            self.amount_text,
            self.one_market_price_text,
        ]

        self.content = self.row
        # endregion

class MarketPageContent(ft.Column):
    def __init__(self):
        # region ft.Column params
        super().__init__()
        self.spacing = 2
        self.expand = True
        # endregion

        # region Class params
        self._account: Account | None = None
        self.__items_content: list[ItemRowContent] = []
        self.__is_init = False
        self._steam_api_utility = SteamAPIUtility(self._account)
        # endregion

        # region settings Title
        self.title = Title('Page Market')
        self.title.expand = True
        self.app_id_selector = AppIDSelector(height=25, padding=ft.padding.all(5))
        self.app_id_selector.use_config = True
        self.app_id_selector.on_app_id_select = self._on_select_app_id

        self.title_row = ft.Row()
        self.title_row.expand = True
        self.title_row.alignment = ft.MainAxisAlignment.CENTER
        self.title_row.controls = [
            self.title,
            self.app_id_selector,
        ]
        # endregion

        # region Sort Buttons
        style = ft.ButtonStyle()
        style.padding = ft.padding.all(0)
        style.alignment = ft.alignment.center
        style.icon_size = 20

        self.sort_item_image = ft.Image(width=30, src=' ')

        self.sort_name_input = ft.TextField()
        self.sort_name_input.width = 250
        self.sort_name_input.dense = True
        self.sort_name_input.max_lines = 1
        self.sort_name_input.expand = True
        self.sort_name_input.multiline = False
        self.sort_name_input.label = 'Item Name Sort'
        self.sort_name_input.border_color = ft.colors.GREY
        self.sort_name_input.content_padding = ft.padding.all(0)
        self.sort_name_input.on_change = self._on_change_sort_name

        self.sort_amount_button = ft.FilledTonalButton()
        self.sort_amount_button.text = 'Quantity'
        self.sort_amount_button.icon = ft.icons.ARROW_UPWARD
        self.sort_amount_button.icon_color = ft.colors.GREEN
        self.sort_amount_button.width = 110
        self.sort_amount_button.style = style
        self.sort_amount_button.expand = True
        self.sort_amount_button.on_click = self._on_click_sort

        self.sort_one_market_price_button = ft.FilledTonalButton()
        self.sort_one_market_price_button.text = 'Unit Price'
        self.sort_one_market_price_button.expand = True
        self.sort_one_market_price_button.style = style
        self.sort_one_market_price_button.on_click = self._on_click_sort

        self.sort_row = ft.Row()
        self.sort_row.spacing = 2
        self.sort_row.height = 25
        self.sort_row.alignment = ft.MainAxisAlignment.START
        self.sort_row.vertical_alignment = ft.CrossAxisAlignment.CENTER
        self.sort_row.controls = [
            self.sort_item_image,
            self.sort_name_input,
            self.sort_amount_button,
            self.sort_one_market_price_button
        ]
        # endregion

        # region Items Content
        self._items_column = ft.ListView()
        self._items_column.spacing = 0
        self._items_column.expand = True
        self._items_column.controls = []
        self._items_column.padding = ft.padding.all(2)
        # endregion

        # region Main Content
        items_column = ft.Column()
        items_column.expand = True
        items_column.spacing = 0
        items_column.controls = [
            self.sort_row,
            self._items_column,
        ]

        container_items = ft.Container()
        container_items.expand = True
        container_items.border = ft.border.all(1)
        container_items.padding = ft.padding.all(0)
        container_items.content = items_column
        container_items.border_radius = ft.border_radius.all(5)
        # endregion

        # region settings ft.Column controls
        self.controls = [
            ft.Row(controls=[self.title_row]),
            container_items,
        ]
        # endregion

    def _on_click_sort(self, e: ft.ControlEvent):
        button: ft.FilledTonalButton = e.control
        if not button or not isinstance(button, ft.FilledTonalButton): return

        if button.icon == ft.icons.ARROW_DOWNWARD:
            button.icon = None
            button.icon_color = None
        elif button.icon == ft.icons.ARROW_UPWARD:
            button.icon = ft.icons.ARROW_DOWNWARD
            button.icon_color = ft.colors.RED
        else:
            button.icon = ft.icons.ARROW_UPWARD
            button.icon_color = ft.colors.GREEN

        for b in self.sort_row.controls:
            if b != button:
                b.icon = None
                b.icon_color = None

        self.__sort_items()
        if self.page: self.update()

    def _on_change_sort_name(self, e: ft.ControlEvent):
        self.__sort_items()
        if self.page: self.update()

    def __sort_items(self):
        def _get_sort_value(button: ft.FilledTonalButton) -> int:
            if button.icon == ft.icons.ARROW_DOWNWARD: return 1
            elif button.icon == ft.icons.ARROW_UPWARD: return -1
            else: return 0

        self.__sort_by_name()

        sort_amount = _get_sort_value(self.sort_amount_button)
        sort_one_market_price = _get_sort_value(self.sort_one_market_price_button)

        sorting_criteria = [
            (sort_amount, lambda x: x.item.sell_listings),
            (sort_one_market_price, lambda x: x.item.sell_price),
        ]

        active_criteria = [(order, key) for order, key in sorting_criteria if order != 0]

        for order, key in reversed(active_criteria):
            self._items_column.controls.sort(key=key, reverse=(order == -1))

    def __sort_by_name(self):
        find_name = self.sort_name_input.value.lower() if self.sort_name_input.value else None

        self._items_column.controls = []
        for item_content in self.__items_content:
            if not find_name:
                self._items_column.controls.append(item_content)
                continue

            names_to_check = [item_content.item.name, item_content.item.hash_name, item_content.item.get_market_hash_name()]
            if any(find_name in name.lower() for name in names_to_check):
                self._items_column.controls.append(item_content)

    def _on_select_app_id(self, app_id: str):
        try:
            self.app_id_selector.update_button(disabled=True, icon=ft.icons.UPDATE, icon_color=ft.colors.BLUE, text='Loading...')
            self._items_column.controls = []
            if self._items_column.page: self._items_column.update()

            if not app_id: return
            market_items: list[MarketListenItem] = self._steam_api_utility.get_market_listings(appid=app_id)
            real_market_items = [item for item in market_items if not item.is_empty() and not item.is_bug_item() and item.is_for_current_game(app_id)]

            self.__items_content = [ItemRowContent(item) for item in real_market_items]

            self._items_column.controls = self.__items_content
            self.__sort_items()
            if self._items_column.page: self._items_column.update()
        finally:
            self.app_id_selector.update_button()

    def on_update_account(self, account: Account = None):
        self._account = account
        self._steam_api_utility.account = account

        self._items_column.controls = []
        self.__items_content = []
        if self._items_column.page: self._items_column.update()
        self.__is_init = False

    def did_mount(self):
        if not self.__is_init:
            self.__is_init = True
            self._on_select_app_id(self.app_id_selector.get_config_value())

class MarketPage(BasePage):
    load_position = 6
    def __init__(self):
        super().__init__()
        self.name = 'market'
        self.label = 'Market'
        self.icon = ft.icons.STORE_OUTLINED
        self.selected_icon = ft.icons.STORE

        self.disabled_is_logout = True

        self.page_content = MarketPageContent()

    def on_callback_authenticated(self, account: Account):
        self.page_content.on_update_account(account)
    def on_callback_logout(self):
        self.page_content.on_update_account()
