import time, threading

import flet as ft
from app.logger import logger
from app.core import Account
from app.ui.pages import BasePage, Title
from app.package.data_collectors import (
    SteamAPIUtility,
    MarketListingsListing,
    MarketListingsApp,
    MarketListingsAmount,
    MarketListingsPrice,
    MarketListingsItem,
    MarketMyHistoryManager,
    MarketMyHistoryParcedEvent,

    load_steam_mini_profile_info, SteamMiniProfileInfo
)

def create_text_widget():
    widget = ft.Text()
    widget.size = 15
    widget.max_lines = 1
    widget.expand = True
    widget.text_align = ft.TextAlign.CENTER
    widget.overflow = ft.TextOverflow.ELLIPSIS
    return widget

class HistoryItemContent(ft.Container):
    def __init__(self, item: MarketMyHistoryParcedEvent, prefix: str='', suffix: str=''):
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
        self.item = item
        item_name = item.get_item_name()
        item_color = item.get_item_color()
        item_icon_url = item.get_item_icon_url(width=30, height=30)
        item_market_url = item.get_item_market_url()

        app_icon_url = item.get_app_icon_url()

        buy_amount = item.get_buy_amount()
        left_amount = item.get_left_amount()
        start_amount = buy_amount + left_amount

        price_buy = item.get_price()
        price_buy_net = item.get_price(is_net_price=True)

        is_create = item.is_create()
        is_cancel = item.is_cancel()
        is_buy = item.is_buy()
        is_sell = item.is_sell()
        icon_event = None
        color_event = None
        if is_create:
            icon_event = ft.icons.ADD_TASK  # Создание
            color_event = "#4CAF50"  # Зеленый
        elif is_cancel:
            icon_event = ft.icons.CLOSE  # Отмена
            color_event = "#F44336"  # Красный
        elif is_buy:
            icon_event = ft.icons.SHOPPING_CART  # Покупка
            color_event = "#2196F3"  # Синий
        elif is_sell:
            icon_event = ft.icons.SELL  # Продажа
            color_event = "#FF9800"  # Оранжевый
        self.color_event = color_event
        # endregion

        # region Widgets
        self.url = item_market_url

        self.status_icon = ft.Icon()
        self.status_icon.name = icon_event
        self.status_icon.color = self.color_event
        self.status_icon.height = 30

        self.date_text = ft.Text()
        self.date_text.size = 10
        self.date_text.width = 75
        self.date_text.value = item.datetime_event.strftime('%Y.%m.%d\n%H:%M:%S')
        self.date_text.max_lines = 2
        self.date_text.text_align = ft.TextAlign.CENTER

        self.app_image = ft.Image()
        self.app_image.width = 30
        self.app_image.height = 30
        self.app_image.src = app_icon_url

        self.item_image = ft.Image()
        self.item_image.width = 30
        self.item_image.height = 30
        self.item_image.src = item_icon_url

        self.name_text = ft.Text()
        self.name_text.size = 15
        self.name_text.width = 250
        self.name_text.value = item_name
        self.name_text.color = item_color
        self.name_text.max_lines = 1
        self.name_text.selectable = True
        self.name_text.text_align = ft.TextAlign.LEFT
        self.name_text.overflow = ft.TextOverflow.ELLIPSIS

        self.amount_text = ft.Text()
        self.amount_text.size = 15
        self.amount_text.expand = True
        self.amount_text.value = f'{buy_amount} ({start_amount}->{left_amount})'
        self.amount_text.max_lines = 1
        self.amount_text.text_align = ft.TextAlign.LEFT

        self.price_text = ft.Text()
        self.price_text.size = 15
        self.price_text.expand = True
        self.price_text.value = f'{prefix}{price_buy}{suffix} ({prefix}{price_buy_net}{suffix})' if price_buy != price_buy_net else f'{prefix}{price_buy}{suffix}'
        self.price_text.max_lines = 1
        self.price_text.text_align = ft.TextAlign.LEFT

        self.user_avatar_image = ft.Image()
        self.user_avatar_image.width = 30
        self.user_avatar_image.height = 30
        self.user_avatar_image.src = ' '

        self.user_name_text = ft.Text()
        self.user_name_text.size = 15
        self.user_name_text.width = 100
        self.user_name_text.value = f'{self.item.steamid_actor}'
        self.user_name_text.max_lines = 1
        self.user_name_text.text_align = ft.TextAlign.LEFT
        self.user_name_text.overflow = ft.TextOverflow.ELLIPSIS

        self.user_container = ft.Container()
        self.user_container.height = 30
        self.user_container.padding = ft.padding.all(0)
        self.user_container.content = ft.Row(controls=[self.user_avatar_image, self.user_name_text])
        self.user_container.ink = True
        self.user_container.on_click = lambda e: ...
        self.user_container.on_hover = self.load_profile
        self.user_container.url = f'https://steamcommunity.com/profiles/{self.item.steamid_actor}'

        self.row = ft.Row()
        self.row.spacing = 2
        self.row.expand = True
        self.row.alignment = ft.MainAxisAlignment.START
        self.row.vertical_alignment = ft.CrossAxisAlignment.CENTER
        self.row.controls = [
            self.status_icon,
            self.date_text,
            self.app_image,
            self.item_image,
            self.name_text,
            self.amount_text,
            self.price_text,

            self.user_container
        ]

        self.content = self.row
        # endregion

    def build(self):
        # color_gradient = [
        #     self.color_event,
        #     "#FFFFFF" if self.page.theme_mode == ft.ThemeMode.LIGHT else "#212121"
        # ]
        # self.gradient = ft.LinearGradient(
        #     begin=ft.alignment.center_right,
        #     end=ft.alignment.center_left,
        #     colors=color_gradient,
        # )
        # threading.Thread(target=self.load_profile).start()
        return self

    def load_profile(self, *args):
        miniprofile = load_steam_mini_profile_info(self.item.steamid_actor)
        if not miniprofile: return
        self.user_name_text.value = miniprofile.name
        self.user_avatar_image.src = miniprofile.avatar_url
        self.user_container.url = f'https://steamcommunity.com/profiles/{miniprofile.steam_id.as_64}/'
        if self.user_container.page: self.user_container.page.update()
class HistoryItemsDialog(ft.AlertDialog):
    def __init__(self):
        super().__init__()
        # region ft.AlertDialog params
        self.isolated = True
        self.expand = True
        # endregion

        # region Class params
        self._steam_api_utility: SteamAPIUtility | None = None
        # endregion Class params

        # region Title
        self.title_name_text = ft.Text()
        self.title_name_text.size = 29
        self.title_name_text.max_lines = 1
        self.title_name_text.value = 'History Market Sales'
        self.title_name_text.weight = ft.FontWeight.BOLD
        self.title_name_text.text_align = ft.TextAlign.CENTER
        self.title_name_text.overflow = ft.TextOverflow.ELLIPSIS

        self.title = self.title_name_text
        # endregion

        # region Items Column Content
        self._items_column = ft.ListView()
        self._items_column.spacing = 0
        self._items_column.expand = True
        self._items_column.padding = ft.padding.all(2)
        self._items_column.controls = []
        # endregion

        # region Main Content
        self.content = ft.Column()
        self.content.width = 1000
        self.content.expand = True
        self.content.alignment = ft.MainAxisAlignment.START
        self.content.vertical_alignment = ft.CrossAxisAlignment.START
        self.content.controls = [
            self._items_column,
        ]
        # endregion

    def init(self, items_event: MarketMyHistoryManager, prefix: str='', suffix: str=''):
        for event in items_event.parced_events:
            item_control = HistoryItemContent(event, prefix=prefix, suffix=suffix)
            self._items_column.controls.append(item_control)

        if self.page: self.update()


class ItemRowContent(ft.Container):
    def __init__(self, item: MarketListingsListing):
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
        self.item: MarketListingsListing = item
        self.item_class: MarketListingsItem = item.get_item_class()
        self.app_class: MarketListingsApp = item.get_app_class()
        self.amount_class: MarketListingsAmount = item.get_amount_class()
        self.price_class: MarketListingsPrice = item.get_price_class()
        self.already_cansel = False
        # endregion

        # region Widgets
        self.url = self.item_class.get_market_url()

        self.app_image = ft.Image()
        self.app_image.width = 30
        self.app_image.height = 30
        self.app_image.src = self.app_class.get_icon_url()

        self.item_image = ft.Image()
        self.item_image.width = 30
        self.item_image.height = 30
        self.item_image.src = self.item_class.get_icon_url(width=30, height=30)

        self.name_text = ft.Text()
        self.name_text.size = 15
        self.name_text.width = 250
        self.name_text.value = f"{self.item_class.name}"
        self.name_text.color = self.item_class.get_color()
        self.name_text.max_lines = 1
        self.name_text.selectable = True
        self.name_text.text_align = ft.TextAlign.LEFT
        self.name_text.overflow = ft.TextOverflow.ELLIPSIS

        amount = self.amount_class.get_amount()
        amount_start = self.amount_class.get_amount_start()
        self.amount_text = create_text_widget()
        self.amount_text.value = f"{self.amount_class.get_amount()} <- {self.amount_class.get_amount_start()}" if amount != amount_start else f"{self.amount_class.get_amount()}"

        self.price_per_unut_text = create_text_widget()
        self.price_per_unut_text.value = f"{self.price_class.get_price_per_unut()}({self.price_class.get_price_per_unut_net()})"
        self.now_price_text = create_text_widget()
        self.now_price_text.value = f"{self.price_class.get_now_price()}({self.price_class.get_now_price_net()})"

        self.cansel_button = ft.FilledTonalButton(height=25)
        self.cansel_button.text = 'Cansel'
        self.cansel_button.icon = ft.icons.CANCEL
        self.cansel_button.icon_color = ft.colors.GREEN
        self.cansel_button.style = ft.ButtonStyle()
        self.cansel_button.style.icon_size = 20
        self.cansel_button.style.padding = ft.padding.all(5)
        self.cansel_button.style.alignment = ft.alignment.center
        self.cansel_button.style.shape = ft.RoundedRectangleBorder(radius=5)

        self.row = ft.Row()
        self.row.spacing = 2
        self.row.expand = True
        self.row.alignment = ft.MainAxisAlignment.START
        self.row.vertical_alignment = ft.CrossAxisAlignment.CENTER
        self.row.controls = [
            self.app_image,
            self.item_image,
            self.name_text,

            self.amount_text,

            self.price_per_unut_text,
            self.now_price_text,

            self.cansel_button,
        ]

        self.content = self.row
        # endregion

    def get_sort_value(self):
        return self.app_class.appid, self.price_class.get_price_per_unut_net(), self.item.time_created
class ItemsOnSalePageContent(ft.Column):
    def __init__(self):
        # region ft.Column params
        super().__init__()
        self.spacing = 2
        self.expand = True
        # endregion

        # region Class params
        self._account: Account | None = None
        self._steam_api_utility = SteamAPIUtility(self._account)
        self._is_init = False
        self._is_work = False
        self._on_update_is_work = False
        self._lock_cansel = threading.Lock()
        # endregion

        # region settings Title
        self._title = Title('My items on Sale')
        self._title.expand = True

        self._update_button = ft.FilledTonalButton()
        self._update_button.text = 'Update'
        self._update_button.height = 25
        self._update_button.icon = ft.icons.UPDATE
        self._update_button.on_click = self._on_click_update_button
        self._update_button.style = ft.ButtonStyle()
        self._update_button.style.padding = ft.padding.all(5)
        self._update_button.style.alignment = ft.alignment.center
        self._update_button.style.icon_size = 20

        self._title_row = ft.Row()
        self._title_row.expand = True
        self._title_row.alignment = ft.MainAxisAlignment.CENTER
        self._title_row.controls = [
            self._title,
            self._update_button
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
        button_style = ft.ButtonStyle()
        button_style.padding = ft.padding.all(0)
        button_style.alignment = ft.alignment.center
        button_style.icon_size = 20

        self._start_load_price_button = ft.FilledTonalButton()
        self._start_load_price_button.text = 'Load Market Price'
        self._start_load_price_button.icon = ft.icons.SYNC
        self._start_load_price_button.icon_color = ft.colors.RED
        self._start_load_price_button.expand = True
        self._start_load_price_button.visible = False #TODO Дописать функционал
        self._start_load_price_button.style = button_style
        self._start_load_price_button.on_click = self._on_click_start_load_price_button

        self._start_show_history_button = ft.FilledTonalButton()
        self._start_show_history_button.text = 'Show My history'
        self._start_show_history_button.icon = ft.icons.HISTORY_EDU
        self._start_show_history_button.icon_color = ft.colors.GREEN
        self._start_show_history_button.expand = True
        self._start_show_history_button.style = button_style
        self._start_show_history_button.on_click = self._on_click_start_show_history

        self._start_cansel_all_button = ft.FilledTonalButton()
        self._start_cansel_all_button.text = 'Cansel All'
        self._start_cansel_all_button.icon = ft.icons.CLOSE
        self._start_cansel_all_button.icon_color = ft.colors.RED
        self._start_cansel_all_button.expand = True
        self._start_cansel_all_button.style = button_style
        self._start_cansel_all_button.on_click = self._on_click_start_cansel_all_button

        self._botton_row = ft.Row()
        self._botton_row.spacing = 2
        self._botton_row.height = 25
        self._botton_row.alignment = ft.MainAxisAlignment.START
        self._botton_row.vertical_alignment = ft.CrossAxisAlignment.CENTER
        self._botton_row.controls = [
            self._start_load_price_button,
            self._start_show_history_button,
            self._start_cansel_all_button,
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
            self._botton_row,
        ]

    def _bottom_button_disable(self, is_disabled: bool = True):
        self._start_cansel_all_button.icon_color = ft.colors.RED if is_disabled else ft.colors.GREEN
        self._start_cansel_all_button.disabled = is_disabled
        self._start_load_price_button.icon_color = ft.colors.RED if is_disabled else ft.colors.GREEN
        self._start_load_price_button.disabled = is_disabled
        if self._botton_row.page: self._botton_row.update()

    def _on_click_update_button(self, *args):
        try:
            self._items_column.controls = []
            if self._items_column.page: self._items_column.update()

            if not self._is_work:
                self._on_update_is_work = True
                return

            self._bottom_button_disable()

            self._update_button.text = 'Loading...'
            self._update_button.icon_color = ft.colors.BLUE
            self._update_button.icon = ft.icons.UPDATE
            self._update_button.disabled = True
            if self._update_button.page: self._update_button.update()

            market_my_listings = self._steam_api_utility.fetch_my_listings()
            self._items_column.controls = [ItemRowContent(item) for item in market_my_listings.listings]
            for item_content in self._items_column.controls:
                item_content: ItemRowContent
                item_content.cansel_button.on_click = lambda e, _item_content=item_content: self._on_click_start_cansel_button(item_content=_item_content)

            self._items_column.controls.sort(key=lambda x: x.get_sort_value(), reverse=True)
            if self._items_column.page: self._items_column.update()
        finally:
            self._bottom_button_disable(is_disabled=(len(self._items_column.controls) <= 0))

            self._update_button.text = 'Update'
            self._update_button.icon_color = None
            self._update_button.icon = ft.icons.UPDATE
            self._update_button.disabled = False
            if self._update_button.page: self._update_button.update()

    def _on_click_start_cansel_button(self, *args, item_content: ItemRowContent):
        if not item_content or item_content.already_cansel: return
        item_content.already_cansel = True

        item_content.cansel_button.disabled = True
        item_content.cansel_button.icon_color = ft.colors.RED
        if item_content.cansel_button.page: item_content.cansel_button.update()

        with self._lock_cansel:
            if not self._is_work: return
            logger.info(f'Start cansel Sell: {item_content.item_class.name} {item_content.amount_class.get_total()} {item_content.price_class.get_total()}')
            status = self._steam_api_utility.remove_my_listing(item_content.item)
            logger.info(f'Finish cansel Sell: {item_content.item_class.name} {status=}')
            if status: return

        item_content.cansel_button.disabled = False
        item_content.cansel_button.icon_color = ft.colors.GREEN
        if item_content.cansel_button.page: item_content.cansel_button.update()

    def _on_click_start_cansel_all_button(self, *args):
        self._bottom_button_disable(is_disabled=True)

        for item_content in self._items_column.controls:
            item_content: ItemRowContent
            if not self._is_work: continue
            self._on_click_start_cansel_button(item_content=item_content)
            time.sleep(0.3)

        if not self._is_work:
            self._on_update_is_work = True

    def _on_click_start_load_price_button(self, *args):
        print(f"_on_click_start_load_price_button: {args}")

    def _on_click_start_show_history(self, *args):
        history = self._steam_api_utility.fetch_market_myhistory()
        if not history or not history.success: return

        dialog = HistoryItemsDialog()
        dialog.init(history)
        if self.page: self.page.open(dialog)

    def on_update_account(self, account: Account = None):
        self._account = account
        self._steam_api_utility.account = account

        self._items_column.controls = []
        if self._items_column.page: self._items_column.update()
        self._is_init = False

        if not account:
            self._on_update_is_work = True

    def did_mount(self):
        self._is_work = True
        if not self._is_init or self._on_update_is_work:
            self._is_init = True
            self._on_update_is_work = False
            self._on_click_update_button()

    def will_unmount(self):
        self._is_work = False


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
        self.page_content.on_update_account(account)
    def on_callback_logout(self):
        self.page_content.on_update_account()
