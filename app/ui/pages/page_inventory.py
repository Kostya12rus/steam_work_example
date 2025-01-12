import re, time, datetime
import flet as ft

from app.core import Account
from app.logger import logger
from app.database import config
from app.ui.widgets import AppIDSelector
from app.ui.pages import BasePage, Title
from app.package.data_collectors import SteamAPIUtility, InventoryManager, InventoryItemRgDescriptions, MarketListenItem, ItemOrdersHistogram


def create_input_widget():
    input_widget = ft.TextField()
    input_widget.height = 30
    input_widget.dense = True
    input_widget.expand = True
    input_widget.max_lines = 1
    input_widget.text_size = 14
    input_widget.content_padding = 10
    input_widget.border_color = ft.colors.BLUE
    input_widget.text_align = ft.TextAlign.RIGHT
    input_widget.text_vertical_align = ft.VerticalAlignment.CENTER
    return input_widget
def create_button_widget():
    button = ft.FilledTonalButton()
    button.height = 30
    button.style = ft.ButtonStyle()
    button.style.icon_size = 20
    button.style.padding = ft.padding.all(5)
    button.style.alignment = ft.alignment.center
    button.style.shape = ft.RoundedRectangleBorder()
    button.style.shape.radius = 5
    button.style.text_style = ft.TextStyle()
    button.style.text_style.size = 14
    return button
def parce_value(value: str):
    unified_value = value.replace(',', '.')
    match = re.search(r'\d+(\.\d{0,3})?', unified_value)
    if match:
        try:
            return float(match.group())
        except:
            pass
    else:
        return ''

class IntervalEnum(ft.dropdown.Option):
    def __init__(self, text: str = '1 sec', timedelta: datetime.timedelta = datetime.timedelta(seconds=1)):
        super().__init__()
        self.text = text
        self.key = text
        self.timedelta = timedelta
class IntervalInventoryUpdate(ft.Dropdown):
    def __init__(self, on_select_interval: callable = None):
        super().__init__()
        self.options = [
            IntervalEnum(text='Not Update', timedelta=datetime.timedelta(weeks=100)),
            IntervalEnum(text='30 sec',     timedelta=datetime.timedelta(seconds=30)),
            IntervalEnum(text='1 min',      timedelta=datetime.timedelta(minutes=1)),
            IntervalEnum(text='2 min',      timedelta=datetime.timedelta(minutes=2)),
            IntervalEnum(text='5 min',      timedelta=datetime.timedelta(minutes=5)),
            IntervalEnum(text='10 min',     timedelta=datetime.timedelta(minutes=10)),
        ]
        self.padding = ft.padding.all(2)
        self.alignment = ft.alignment.center
        self.content_padding = ft.padding.all(2)
        self.height = 30
        self.width = 100
        self.dense = True
        self.text_size = 14

        self.on_select_interval = on_select_interval
        self.on_change = self.__on_change
        self.__load_from_config()
    def __on_change(self, *args):
        if not self.on_select_interval: return
        selected_option: IntervalEnum = next((option for option in self.options if option.key == self.value), None)
        if not selected_option: return
        config.interval_update_inventory = selected_option.key
        self.on_select_interval(selected_option.timedelta)
    def __load_from_config(self):
        config_value = config.interval_update_inventory
        selected_option: IntervalEnum = next((option for option in self.options if option.key == config_value), None)
        self.value = config_value if selected_option else 'Not Update'
    def get_selected_interval(self) -> datetime.timedelta:
        selected_option: IntervalEnum = next((option for option in self.options if option.key == self.value), None)
        return selected_option.timedelta

class SellAllItemContent(ft.Container):
    def __init__(self):
        # region ft.Container params
        super().__init__()
        self.padding = ft.padding.all(2)
        self.alignment = ft.alignment.center_left
        # endregion

        # region Class params
        self._items_content: list['ItemRowContent'] = []
        self._histogram: ItemOrdersHistogram | None = None
        self._on_change_callback: callable = None

        self._price_sell_percent: float = 1.0
        self._is_minimum_auto_buy: bool = True
        self._minimum_price: float = 0.03
        self._price_dont_sell: float = 0.00

        self._count_sell: int = 0
        self._price_get: float = 0
        self._price_sell: float = 0

        self._user_price_get: float | None = None
        self._user_price_sell: float | None = None

        self._histogram_price_buy: float = 0
        self._histogram_price_sell: float = 0

        self._price_prefix: str = ""
        self._price_suffix: str = ""
        # endregion

        # region Image Item
        self.item_image = ft.Image()
        self.item_image.width = 30
        self.item_image.height = 30
        self.item_image.src = ' '
        # endregion

        # region Name
        self.name_text = ft.Text()
        self.name_text.size = 15
        self.name_text.width = 200
        self.name_text.max_lines = 1
        self.name_text.selectable = True
        self.name_text.text_align = ft.TextAlign.LEFT
        self.name_text.overflow = ft.TextOverflow.ELLIPSIS
        # endregion

        # region Price
        self.price_sell_input = create_input_widget()
        self.price_sell_input.label = 'Sell Price'
        self.price_sell_input.on_change = self.__on_change_sell_price

        self.price_get_input = create_input_widget()
        self.price_get_input.label = 'Net Price'
        self.price_get_input.on_change = self.__on_change_get_price
        # endregion

        # region Count
        self.count_item_sell_input = create_input_widget()
        self.count_item_sell_input.value = '1'
        self.count_item_sell_input.suffix_text = f" | 1"
        self.count_item_sell_input.label = 'Quantity'
        self.count_item_sell_input.on_change = self.__on_change_count
        self.count_item_sell_input.input_filter = ft.NumbersOnlyInputFilter()
        # endregion

        # region Min Sell Price
        self.min_sell_price_text = ft.Text()
        self.min_sell_price_text.size = 15
        self.min_sell_price_text.value = f""
        self.min_sell_price_text.width = 150
        self.min_sell_price_text.max_lines = 1
        self.min_sell_price_text.text_align = ft.TextAlign.RIGHT
        # endregion

        # region Auto Buy Price
        self.auto_buy_price_text = ft.Text()
        self.auto_buy_price_text.size = 15
        self.auto_buy_price_text.value = f""
        self.auto_buy_price_text.width = 150
        self.auto_buy_price_text.max_lines = 1
        self.auto_buy_price_text.text_align = ft.TextAlign.RIGHT
        # endregion

        # region Main Content
        self.row = ft.Row()
        self.row.spacing = 2
        self.row.expand = True
        self.row.alignment = ft.MainAxisAlignment.START
        self.row.vertical_alignment = ft.CrossAxisAlignment.CENTER
        self.row.controls = [
            self.item_image,
            self.name_text,
            self.price_sell_input,
            self.price_get_input,
            self.count_item_sell_input,
            self.min_sell_price_text,
            self.auto_buy_price_text,
        ]

        self.content = self.row
        # endregion

    def init_items(self, items_content: list['ItemRowContent']):
        self._items_content = items_content

        self.item_image.src = next((item.item.get_icon_url() for item in items_content if item.item), " ")
        self.name_text.value = next((item.item.name for item in items_content if item.item), None)
        self.name_text.color = next((item.item.get_color() for item in items_content if item.item), None)

        if not self._count_sell: self.set_sell_amount(self.get_sum_amount())

        if self.page: self.update()

    def init_histogram(self, histogram: ItemOrdersHistogram):
        if not histogram or not histogram.is_successful(): return False
        for item in self._items_content: item.update_histogram(histogram)
        self._histogram = histogram

        self._price_prefix = histogram.price_prefix
        self._price_suffix = histogram.price_suffix

        self.price_sell_input.prefix_text = histogram.price_prefix
        self.price_sell_input.suffix_text = f"{histogram.price_suffix} | шт."
        self.price_get_input.prefix_text = histogram.price_prefix
        self.price_get_input.suffix_text = f"{histogram.price_suffix} | шт."

        self._histogram_price_sell = histogram.get_lowest_sell_order()
        self._histogram_price_buy = histogram.get_highest_buy_order()

        self.min_sell_price_text.value = histogram.get_lowest_sell_order_str()
        self.auto_buy_price_text.value = histogram.get_highest_buy_order_str()

        self.set_price(price_sell=self._histogram_price_sell)

        if self.page: self.update()

    def start_sell(self, steam_api_utility: SteamAPIUtility):
        if not steam_api_utility: return
        count_item_sell = self.get_count_sell()
        if not count_item_sell: return

        price_sell = self.get_price_sell()
        if not price_sell: return
        price_dont_sell = self._price_dont_sell
        if price_sell <= price_dont_sell: return

        _price_get = self.get_price_get()
        price_get = int(float(_price_get if _price_get else 0) * 100)
        if not price_get: return

        for item_content in self._items_content:
            item: InventoryItemRgDescriptions = item_content.item
            if not item.is_marketable(): continue
            if item.get_amount() <= 0: continue

            items_list = item.get_amount_items(count_item_sell)
            selling_amount = items_list.get_amount()
            count_item_sell -= selling_amount

            for select_item in items_list.items:
                if select_item.amount <= 0: continue
                status = steam_api_utility.sell_item(select_item, amount=select_item.amount, price=price_get)
                logger.info(f"Sell initiated: name='{item.name}', "
                            f"amount={select_item.amount}, "
                            f"price_sell={self._price_prefix}{price_sell}{self._price_suffix} | шт., "
                            f"net_price={self._price_prefix}{_price_get}{self._price_suffix} | шт., "
                            f"steam_price={price_get} | шт., "
                            f"assetid={select_item.assetid}")
                if not status or not status.get('success', False): select_item.amount = 0
                logger.info(f"Sell finished: {status=}")

            succell_amount = items_list.get_amount()
            count_item_sell += selling_amount - succell_amount
            item.remove_items(items_list)
            item_content.update_widget()

        self.set_sell_amount(amount=count_item_sell)

    def __on_change_sell_price(self, *args):
        value = parce_value(self.price_sell_input.value)
        value = value if value else 0
        self.set_user_price(price_sell=value)
    def __on_change_get_price(self, *args):
        value = parce_value(self.price_get_input.value)
        value = value if value else 0
        self.set_user_price(price_get=value)
    def __on_change_count(self, *args):
        value = self.count_item_sell_input.value
        value = int(value) if value else 0
        self.set_sell_amount(amount=value)
    def __on_change_content(self, *args):
        if not self._on_change_callback: return
        if self.page: self.page.run_thread(self._on_change_callback)

    def set_on_change_callback(self, callback: callable = None):
        if not callback: return
        self._on_change_callback = callback
    def set_user_price(self, price_sell: float = None, price_get: float = None):
        self._user_price_get = None
        self._user_price_sell = None

        if price_sell == 0 or price_get == 0:
            self._user_price_get = 0
            self._user_price_sell = 0
            self.update_price_content(price_sell=0, price_get=0)
            return

        if price_sell:
            self._user_price_sell = price_sell
            self._user_price_get = self._calculate_price_sell(price_sell)
            self.price_get_input.value = f'{round(self._user_price_get, 2):.2f}'
            if self.price_get_input.page: self.price_get_input.update()
        if price_get:
            self._user_price_sell = self._calculate_price_buy(price_get)
            self._user_price_get = price_get
            self.price_sell_input.value = f'{round(self._user_price_sell, 2):.2f}'
            if self.price_sell_input.page: self.price_sell_input.update()
        self.__on_change_content()
    def set_sell_amount(self, amount: int = None):
        amount = amount if amount and amount > 0 else 0
        total_amount = self.get_sum_amount()
        if amount > total_amount: amount = total_amount

        self._count_sell = amount
        self.count_item_sell_input.value = self._count_sell if isinstance(self._count_sell, int) else 0
        self.count_item_sell_input.suffix_text = f" | {total_amount}"
        if self.count_item_sell_input.page: self.count_item_sell_input.update()
        self.__on_change_content()
    def set_price(self, price_sell: float = None, price_get: float = None):
        if price_sell is None and price_get is None:
            self._price_get = None
            self._price_sell = None
            return
        if price_sell == 0 or price_get == 0:
            self._price_get = 0
            self._price_sell = 0
            if self._user_price_get is None or self._user_price_sell is None:
                self.update_price_content(price_sell=0, price_get=0)
            return

        if price_sell:
            price_sell *= self._price_sell_percent
            if self._is_minimum_auto_buy and self._histogram_price_buy:
                max_price_sell = max(price_sell, self._histogram_price_buy)
                if max_price_sell != price_sell:
                    price_sell = max_price_sell
            if price_sell < self._minimum_price:
                price_sell = self._minimum_price
            self._price_sell = price_sell
            self._price_get = self._calculate_price_sell(price_sell)
            if self._price_sell <= self._price_dont_sell:
                self._price_get = 0
                self._price_sell = 0

        if price_get:
            self._price_sell = self._calculate_price_buy(price_get)
            self._price_get = price_get
            if self._is_minimum_auto_buy and self._histogram_price_buy:
                max_price_sell = max(self._price_sell, self._histogram_price_buy)
                if max_price_sell != self._price_sell:
                    self.set_price(price_sell=max_price_sell)
                    return
            if self._price_sell < self._minimum_price:
                self.set_price(price_sell=self._minimum_price)
                return
            if self._price_sell <= self._price_dont_sell:
                self._price_get = 0
                self._price_sell = 0

        if self._user_price_get is not None or self._user_price_sell is not None: return
        self.update_price_content(price_sell=self._price_sell, price_get=self._price_get)

    def update_price_content(self, price_sell: float = None, price_get: float = None):
        price_sell = price_sell if price_sell else 0
        price_get = price_get if price_get else 0

        self.price_get_input.value = f'{round(price_get, 2):.2f}'
        if self.price_get_input.page: self.price_get_input.update()
        self.price_sell_input.value = f'{round(price_sell, 2):.2f}'
        if self.price_sell_input.page: self.price_sell_input.update()

        self.__on_change_content()

    def set_percent(self, percent: float = None):
        if not percent: return
        self._price_sell_percent = percent
        if not self._histogram_price_sell: return
        self.set_price(price_sell=self._histogram_price_sell)
    def set_price_to_auto_buy(self, set_minimun_price: bool = False):
        if not self._histogram: return
        self._price_sell_percent = 1
        highest_buy_order = self._histogram.get_highest_buy_order()
        if set_minimun_price:
            if highest_buy_order < self._minimum_price:
                highest_buy_order = self._minimum_price
        self.set_price(price_sell=highest_buy_order)
    def set_is_minimum_auto_buy(self, is_minimum_auto_buy: bool = True):
        self._is_minimum_auto_buy = is_minimum_auto_buy if is_minimum_auto_buy is not None else True
        if not self._is_minimum_auto_buy: return
        if self._user_price_get is not None or self._user_price_sell is not None: return
        price_now = self.get_price_sell()
        if price_now >= self._histogram_price_buy: return
        self.set_price(price_sell=self._histogram_price_buy)
    def set_minimum_price(self, minimum_price: float = None):
        self._minimum_price = minimum_price if minimum_price is not None else 0.03
        if self._user_price_get is not None or self._user_price_sell is not None: return
        price_now = self.get_price_sell()
        if price_now >= self._minimum_price: return
        self.set_price(price_sell=self._minimum_price)
    def set_price_dont_sell(self, price_dont_sell: float = None):
        self._price_dont_sell = price_dont_sell if price_dont_sell is not None else 0
        price_now = self.get_price_sell()
        if price_now >= self._price_dont_sell: return
        self.set_price(price_sell=0)

    @staticmethod
    def _calculate_price_buy(price_get: float = None):
        """
        Посчитать сколько заплатить покупатель
        :param price_get:
        :return:
        """
        if price_get is None: return None
        if price_get < 0.01: return 0
        min_commission = 0.02

        price_sell = price_get / 100 * 115
        if price_sell - price_get < min_commission:
            price_sell = price_get + min_commission
        if price_sell < 0.03:
            price_sell = 0.03
        return price_sell
    @staticmethod
    def _calculate_price_sell(price_sell: float = None):
        """
        Посчитать сколько получит продавец
        :param price_sell:
        :return:
        """
        if price_sell is None: return None
        if price_sell < 0.03: return 0
        min_commission = 0.02

        price_get = price_sell / 115 * 100
        if price_sell - price_get < min_commission:
            price_get = price_sell - min_commission
        if price_get < 0.01:
            price_get = 0.01
        return price_get


    def get_price_sell(self) -> float:
        if not self._count_sell: return 0
        if self._user_price_sell is not None: return round(self._user_price_sell, 2)
        return round(self._price_sell, 2) if self._price_sell else 0
    def get_price_get(self) -> float:
        if not self._count_sell: return 0.0
        if self._user_price_get is not None: return round(self._user_price_get, 2)
        return round(self._price_get, 2) if self._price_get else 0
    def get_count_sell(self) -> int:
        count_sell = int(self._count_sell) if self._count_sell else 0
        if not count_sell or not self.get_price_sell() or not self.get_price_get(): return 0
        return count_sell
    def get_all_price_sell(self) -> float:
        return self.get_price_sell() * self.get_count_sell()
    def get_all_price_get(self) -> float:
        return self.get_price_get() * self.get_count_sell()

    def get_prefix_text(self) -> str:
        return self._price_prefix
    def get_suffix_text(self) -> str:
        return self._price_suffix

    def get_sum_amount(self):
        return sum(item.item.get_amount() for item in self._items_content if item.item and item.item.is_marketable())
    def get_appid(self):
        return next((item.item.appid for item in self._items_content if item.item), None)
    def get_market_hash_name(self):
        return next((item.item.market_hash_name for item in self._items_content if item.item), None)
class SellAllItemsDialog(ft.AlertDialog):
    def __init__(self):
        super().__init__()
        # region ft.AlertDialog params
        self.isolated = True
        self.expand = True
        # endregion

        # region Class params
        self._steam_api_utility: SteamAPIUtility | None = None
        self._items_content: list['ItemRowContent'] | None = None
        # endregion Class params

        # region Title
        self.title_name_text = ft.Text()
        self.title_name_text.size = 29
        self.title_name_text.max_lines = 1
        self.title_name_text.value = 'Sell All Items'
        self.title_name_text.weight = ft.FontWeight.BOLD
        self.title_name_text.text_align = ft.TextAlign.CENTER
        self.title_name_text.overflow = ft.TextOverflow.ELLIPSIS

        self.title = self.title_name_text
        # endregion

        # region Items Column Content
        self._items_column = ft.ListView()
        self._items_column.spacing = 2
        self._items_column.expand = True
        self._items_column.padding = ft.padding.all(2)
        self._items_column.controls = []
        # endregion

        # region Top Bar Content
        percent_button_row = ft.Row()
        percent_button_row.expand = True
        percent_button_row.alignment = ft.MainAxisAlignment.CENTER
        percent_button_row.vertical_alignment = ft.CrossAxisAlignment.CENTER

        button = ft.Radio(value=f"-101", label=f'Min Price')
        button.splash_radius = 0
        percent_button_row.controls.append(button)
        button = ft.Radio(value=f"-100", label=f'AutoBuy')
        button.splash_radius = 0
        percent_button_row.controls.append(button)
        for percent in [-20, -15, -10, -5, -1, -0.1, 0, 0.1, 1, 5, 10, 15, 20]:
            button = ft.Radio(value=f"{1 + (percent / 100)}", label=f'{percent}%')
            button.splash_radius = 0
            percent_button_row.controls.append(button)
        self._percent_radio_group = ft.RadioGroup(content=percent_button_row, value="1.0")
        self._percent_radio_group.on_change = self._on_change_percent_radio_group

        self._is_minimun_auto_buy = ft.Checkbox(label='Auto-buy at min price', value=True)
        self._is_minimun_auto_buy.on_change = self._on_change_minimun_auto_buy

        self._minimun_price = create_input_widget()
        self._minimun_price.label = 'Min sell price threshold'
        self._minimun_price.value = '0.03'
        self._minimun_price.suffix_text = f" | шт."
        self._minimun_price.on_change = self._on_change_minimun_price

        self._minimun_price_dont_sell = create_input_widget()
        self._minimun_price_dont_sell.label = 'Do not sell below this price'
        self._minimun_price_dont_sell.value = '0.00'
        self._minimun_price_dont_sell.suffix_text = f" | шт."
        self._minimun_price_dont_sell.on_change = self._on_change_minimun_price_dont_sell


        row_sell_settings = ft.Row()
        row_sell_settings.expand = True
        row_sell_settings.alignment = ft.MainAxisAlignment.CENTER
        row_sell_settings.vertical_alignment = ft.CrossAxisAlignment.CENTER
        row_sell_settings.controls = [
            self._is_minimun_auto_buy,
            self._minimun_price,
            self._minimun_price_dont_sell,
        ]


        self._top_bar = ft.Column()
        self._top_bar.alignment = ft.MainAxisAlignment.START
        self._top_bar.horizontal_alignment = ft.MainAxisAlignment.CENTER
        self._top_bar.controls = [
            self._percent_radio_group,
            row_sell_settings,
        ]
        # endregion

        # region Bottom Bar Content
        self._button_start_sell = create_button_widget()
        self._button_start_sell.text = 'Start Sell'
        self._button_start_sell.expand = True
        self._button_start_sell.icon = ft.icons.SELL
        self._button_start_sell.icon_color = ft.colors.GREEN
        self._button_start_sell.on_click = self._on_click_start_sell

        self.actions_alignment = ft.MainAxisAlignment.CENTER,
        self.actions = [
            ft.Row(expand=True, controls=[self._button_start_sell])
        ]
        # endregion

        # region Main Content
        self.content = ft.Column()
        self.content.expand = True
        self.content.alignment = ft.MainAxisAlignment.START
        self.content.vertical_alignment = ft.CrossAxisAlignment.START
        self.content.controls = [
            self._top_bar,
            self._items_column,
        ]
        # endregion

    def init(self, steam_api_utility: SteamAPIUtility, items_content: list['ItemRowContent']):
        self._steam_api_utility = steam_api_utility
        self._items_content = items_content

        market_hash_names = set(item.item.market_hash_name for item in items_content if item.item and item.item.is_marketable())
        ready_items = [item for item in items_content if item.item and item.item.is_marketable()]
        for market_hash_name in market_hash_names:
            items = [item for item in ready_items if item.item.market_hash_name == market_hash_name]
            if not items: continue

            item_control = SellAllItemContent()
            item_control.init_items(items)
            item_control.set_on_change_callback(self._on_change_content)
            self._items_column.controls.append(item_control)
        self._items_column.controls.sort(key=lambda x: x.get_sum_amount(), reverse=True)

        self.title_name_text.value = f'Sell {self._get_sum_amount()} Items'

        if self.page: self.update()

    def _get_sum_amount(self):
        return sum(item.item.get_amount() for item in self._items_content if item.item and item.item.is_marketable())

    def start_update_histogram(self):
        try:
            self._button_start_sell.disabled = True
            if self._button_start_sell.page: self._button_start_sell.update()

            for item_control in self._items_column.controls:
                item_control: SellAllItemContent
                if not self.open: continue
                item_amount = item_control.get_sum_amount()
                if not item_amount: continue
                appid = item_control.get_appid()
                market_hash_name = item_control.get_market_hash_name()
                histogram = self._steam_api_utility.fetch_market_itemordershistogram(appid=appid, market_hash_name=market_hash_name)
                item_control.init_histogram(histogram)
        finally:
            self._button_start_sell.disabled = False
            if self._button_start_sell.page: self._button_start_sell.update()

    def _on_click_start_sell(self, *args):
        if self.disabled: return
        self.disabled = True
        if self.page: self.page.update()

        try:
            for item_control in self._items_column.controls:
                item_control: SellAllItemContent
                item_control.start_sell(self._steam_api_utility)
        finally:
            self.disabled = False
            if self.page: self.page.update()

    def _on_change_percent_radio_group(self, *args):
        value = parce_value(self._percent_radio_group.value)
        if value == 100 or value == 101:
            for item_control in self._items_column.controls:
                item_control: SellAllItemContent
                item_control.set_price_to_auto_buy(set_minimun_price=value == 101)
            return
        value = value if value else 1.0
        for item_control in self._items_column.controls:
            item_control: SellAllItemContent
            item_control.set_percent(percent=value)
    def _on_change_minimun_auto_buy(self, *args):
        value = self._is_minimun_auto_buy.value
        for item_control in self._items_column.controls:
            item_control: SellAllItemContent
            item_control.set_is_minimum_auto_buy(is_minimum_auto_buy=value)
    def _on_change_minimun_price(self, *args):
        value = parce_value(self._minimun_price.value)
        value = value if value else 0.03
        for item_control in self._items_column.controls:
            item_control: SellAllItemContent
            item_control.set_minimum_price(minimum_price=value)
    def _on_change_minimun_price_dont_sell(self, *args):
        value = parce_value(self._minimun_price_dont_sell.value)
        value = value if value else 0.00
        for item_control in self._items_column.controls:
            item_control: SellAllItemContent
            item_control.set_price_dont_sell(price_dont_sell=value)

    def _on_change_content(self, *args):
        items_content: list['SellAllItemContent' | 'ft.Control'] = self._items_column.controls
        total_price_get = f'{round(sum(item.get_all_price_get() for item in items_content), 2):.2f}'
        total_price_sell = f'{round(sum(item.get_all_price_sell() for item in items_content), 2):.2f}'
        total_count_sell = sum(item.get_count_sell() for item in items_content)

        self._button_start_sell.disabled = bool(not total_count_sell)

        prefix = next((item.get_prefix_text() for item in items_content if item.get_prefix_text()), "")
        suffix = next((item.get_suffix_text() for item in items_content if item.get_suffix_text()), "")

        price_text = f"{prefix}{total_price_sell}{suffix}({prefix}{total_price_get}{suffix})"
        self._button_start_sell.text = f"Start Sell {total_count_sell} Items {price_text}"

        self._minimun_price.prefix_text = prefix
        self._minimun_price.suffix_text = f"{suffix} | шт."

        self._minimun_price_dont_sell.prefix_text = prefix
        self._minimun_price_dont_sell.suffix_text = f"{suffix} | шт."

        if self._button_start_sell.page: self._button_start_sell.update()

    def did_mount(self):
        self.start_update_histogram()


class SellItemDialog(ft.AlertDialog):
    def __init__(self):
        super().__init__()
        # region ft.AlertDialog params
        self.isolated = True
        self.expand = True
        # endregion

        # region Class params
        self._last_updated = datetime.datetime.min
        self._steam_api_utility: SteamAPIUtility | None = None
        self._items_content: list['ItemRowContent'] | None = None
        self._histogram: ItemOrdersHistogram | None = None

        self._count_sell: int = 1
        self._price_get: float | None = None
        self._price_sell: float | None = None
        # endregion Class params

        # region Title
        self.title_image = ft.Image()
        self.title_image.width = 30
        self.title_image.height = 30
        self.title_image.src = ' '

        self.title_count_text = ft.Text()
        self.title_count_text.size = 29
        self.title_count_text.max_lines = 1
        self.title_count_text.selectable = True
        self.title_count_text.text_align = ft.TextAlign.CENTER
        self.title_count_text.overflow = ft.TextOverflow.ELLIPSIS

        self.title_name_text = ft.Text()
        self.title_name_text.size = 29
        self.title_name_text.max_lines = 1
        self.title_name_text.selectable = True
        self.title_name_text.weight = ft.FontWeight.BOLD
        self.title_name_text.text_align = ft.TextAlign.CENTER
        self.title_name_text.overflow = ft.TextOverflow.ELLIPSIS

        self.title_update_text = ft.Text()
        self.title_update_text.max_lines = 1
        self.title_update_text.selectable = True
        self.title_update_text.text_align = ft.TextAlign.CENTER
        self.title_update_text.overflow = ft.TextOverflow.ELLIPSIS

        self.title = ft.Row()
        self.title.expand = True
        self.title.alignment = ft.MainAxisAlignment.CENTER
        self.title.controls = [
            self.title_image,
            self.title_count_text,
            self.title_name_text,
            self.title_update_text
        ]
        # endregion

        # region Item Info Content
        price_button_row = ft.Row()
        for percent in [-20, -10, -5, -1, 1, 5, 10, 20]:
            button = create_button_widget()
            button.expand = True
            button.text = f'{percent}%'
            button.on_click = lambda e, _percent=percent: self._set_price_get_percent(1 + (_percent / 100))
            price_button_row.controls.append(button)

        self.price_sell_input = create_input_widget()
        self.price_sell_input.label = 'Sell Price'
        self.price_sell_input.suffix_text = f" | шт."
        self.price_sell_input.on_change = self.__on_change_sell_price
        self.price_get_input = create_input_widget()
        self.price_get_input.label = 'Net Price'
        self.price_get_input.suffix_text = f" | шт."
        self.price_get_input.on_change = self.__on_change_get_price
        price_input_row = ft.Row()
        price_input_row.controls = [
            self.price_sell_input,
            self.price_get_input
        ]

        self.count_item_sell_input = create_input_widget()
        self.count_item_sell_input.label = 'Quantity'
        self.count_item_sell_input.value = '1'
        self.count_item_sell_input.input_filter = ft.NumbersOnlyInputFilter()
        self.count_item_sell_input.suffix_text = f" | 1"
        self.count_item_sell_input.on_change = self.__on_change_count

        self.count_item_sell_one = create_button_widget()
        self.count_item_sell_one.text = '1 шт.'
        self.count_item_sell_one.on_click = lambda e: self._set_sell_count(count=1)

        self.count_item_sell_center = create_button_widget()
        self.count_item_sell_center.text = '50%'
        self.count_item_sell_center.on_click = lambda e: self._set_sell_count(percent=0.5)

        self.count_item_sell_all = create_button_widget()
        self.count_item_sell_all.text = 'All'
        self.count_item_sell_all.on_click = lambda e: self._set_sell_count(percent=1)

        count_input_row = ft.Row()
        count_input_row.controls = [
            self.count_item_sell_input,
            self.count_item_sell_one,
            self.count_item_sell_center,
            self.count_item_sell_all
        ]

        self.total_price_sell_input = create_input_widget()
        self.total_price_sell_input.disabled = True
        self.total_price_sell_input.label = 'Total Sell Price'
        self.total_price_get_input = create_input_widget()
        self.total_price_get_input.disabled = True
        self.total_price_get_input.label = 'Total Net Price'
        total_price_input_row = ft.Row()
        total_price_input_row.controls = [
            self.total_price_sell_input,
            self.total_price_get_input
        ]

        self.button_start_sell = create_button_widget()
        self.button_start_sell.text = "Start Sell"
        self.button_start_sell.expand = True
        self.button_start_sell.on_click = self._on_click_start_sell
        button_start_sell_row = ft.Row()
        button_start_sell_row.controls = [
            self.button_start_sell
        ]

        self.log_column = ft.ListView()
        self.log_column.padding = ft.padding.all(0)
        self.log_column.expand = True
        self.log_column.auto_scroll = True

        self.item_info_column = ft.Column()
        self.item_info_column.alignment = ft.MainAxisAlignment.START
        self.item_info_column.expand = True
        self.item_info_column.controls = [
            price_button_row,
            price_input_row,
            count_input_row,
            total_price_input_row,
            button_start_sell_row,
            self.log_column,
        ]
        # endregion

        # region Histogram Content
        self.sell_info_column = ft.Column()
        self.sell_info_column.scroll = ft.ScrollMode.AUTO
        self.sell_info_column.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.sell_info_column.alignment = ft.MainAxisAlignment.START

        self.buy_info_column = ft.Column()
        self.buy_info_column.scroll = ft.ScrollMode.AUTO
        self.buy_info_column.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.buy_info_column.alignment = ft.MainAxisAlignment.START
        # endregion

        # region Main Content
        self.content = ft.Row()
        self.content.width = 1000
        self.content.expand = True
        self.content.alignment = ft.MainAxisAlignment.START
        self.content.vertical_alignment = ft.CrossAxisAlignment.START
        self.content.controls = [
            self.item_info_column,
            ft.VerticalDivider(),
            self.sell_info_column,
            ft.VerticalDivider(),
            self.buy_info_column,
        ]
        # endregion

    def init(self, steam_api_utility: SteamAPIUtility, items_content: list['ItemRowContent']):
        self._last_updated = datetime.datetime.min
        self._steam_api_utility = steam_api_utility
        self._items_content = items_content

        self.title_image.src = next(item.item.get_icon_url(30, 30) for item in self._items_content if item.item)
        self.title_count_text.value = sum([item.item.get_amount() for item in self._items_content if item.item and item.item.marketable])
        self.title_name_text.value = next(item.item.name for item in self._items_content if item.item)
        self.title_name_text.color = next(item.item.get_color() for item in self._items_content if item.item)

        self.count_item_sell_input.suffix_text = f" | {self.title_count_text.value}"
    def update_histogram(self, histogram: ItemOrdersHistogram = None):
        if not histogram or not histogram.is_successful(): return False
        for item in self._items_content: item.update_histogram(histogram)

        self._histogram = histogram

        self.price_sell_input.prefix_text = histogram.price_prefix
        self.price_sell_input.suffix_text = f"{histogram.price_suffix} | шт."
        self.price_get_input.prefix_text = histogram.price_prefix
        self.price_get_input.suffix_text = f"{histogram.price_suffix} | шт."

        self.total_price_sell_input.prefix_text = histogram.price_prefix
        self.total_price_sell_input.suffix_text = histogram.price_suffix
        self.total_price_get_input.prefix_text = histogram.price_prefix
        self.total_price_get_input.suffix_text = histogram.price_suffix

        buy_order_summary_content = ft.Text()
        buy_order_summary_content.value = self.__parce_html_text(self._histogram.buy_order_summary)
        buy_order_content = [
            self._create_order_graph_content(order_graph, histogram.price_prefix, histogram.price_suffix)
            for order_graph in self._histogram.buy_order_graph.data_json
        ]

        sell_order_summary_content = ft.Text()
        sell_order_summary_content.value = self.__parce_html_text(self._histogram.sell_order_summary)
        sell_order_content = [
            self._create_order_graph_content(order_graph, histogram.price_prefix, histogram.price_suffix)
            for order_graph in self._histogram.sell_order_graph.data_json
        ]

        self.sell_info_column.controls = [sell_order_summary_content] + sell_order_content
        self.buy_info_column.controls = [buy_order_summary_content] + buy_order_content

        if self.page: self.update()


    def _on_click_start_sell(self, *args):
        if not self._price_get or not self._count_sell: return False
        if not self._steam_api_utility: return

        count_item_sell = int(self._count_sell)
        price_get = int(float(self._price_get if self._price_get else 0) * 100)

        _price_prefix = self.price_sell_input.prefix_text
        _price_suffix = self.price_sell_input.suffix_text
        _price_sell = f'{round(self._price_sell, 2):.2f}'
        _price_get = f'{round(self._price_get, 2):.2f}'

        for item_content in self._items_content:
            if not self.open: break
            if count_item_sell <= 0: break
            item: InventoryItemRgDescriptions = item_content.item
            if not item or not item.is_marketable(): continue

            items_list = item.get_amount_items(count_item_sell)
            selling_amount = items_list.get_amount()
            count_item_sell -= selling_amount

            for select_item in items_list.items:
                if select_item.amount <= 0: continue
                if not self.open:
                    select_item.amount = 0
                    continue
                logger.info(f"Sell initiated: name='{item.name}', "
                            f"amount={select_item.amount}, "
                            f"price_sell={_price_prefix}{_price_sell}{_price_suffix}, "
                            f"net_price={_price_prefix}{_price_get}{_price_suffix}, "
                            f"steam_price={price_get} | шт., "
                            f"assetid={select_item.assetid}")
                status = self._steam_api_utility.sell_item(select_item, amount=select_item.amount, price=price_get)
                if not status or not status.get('success', False): select_item.amount = 0
                logger.info(f"Sell finished: {status=}")
                self._add_log(status)
            succell_amount = items_list.get_amount()
            count_item_sell += selling_amount - succell_amount
            item.remove_items(items_list)
            item_content.update_widget()

        self._set_sell_count(count=count_item_sell)


    def did_mount(self):
        self.page.run_thread(self.__thread_update_price)
    def __thread_update_price(self):
        appid = next(item.item.appid for item in self._items_content if item.item)
        market_hash_name = next(item.item.market_hash_name for item in self._items_content if item.item)
        time_span_update = datetime.timedelta(seconds=15)
        while self.open:
            try:
                if self._last_updated + time_span_update > datetime.datetime.now(): continue
                self._last_updated = datetime.datetime.now()
                self.load_histogram(appid=appid, market_hash_name=market_hash_name)
            finally:
                second = max(0, int((self._last_updated + time_span_update - datetime.datetime.now()).total_seconds()))
                self.title_update_text.value = f'Update via {second} sec'
                if self.title_update_text.page: self.title_update_text.page.update()
                time.sleep(0.3)
    def load_histogram(self, appid: int, market_hash_name: str):
        if not appid or not market_hash_name or not self._steam_api_utility: return False
        histogram = self._steam_api_utility.fetch_market_itemordershistogram(appid=appid, market_hash_name=market_hash_name)
        self.update_histogram(histogram)
    def _create_order_graph_content(self, order_graph: list[int, int, str], prefix_currency: str, suffix_currency: str) -> ft.Container:
        price, count, text = order_graph

        item_price_text = ft.Text()
        item_price_text.value = f'{prefix_currency}{round(price, 2):.2f} {suffix_currency}'
        item_price_text.expand = True
        item_price_text.text_align = ft.TextAlign.RIGHT
        item_price_text.max_lines = 1
        item_price_text.overflow = ft.TextOverflow.ELLIPSIS

        item_count_text = ft.Text()
        item_count_text.value = f'{count} шт.'
        item_count_text.expand = True
        item_count_text.text_align = ft.TextAlign.RIGHT
        item_count_text.max_lines = 1
        item_count_text.overflow = ft.TextOverflow.ELLIPSIS

        item_row = ft.Row()
        item_row.controls = [ft.Container(width=100, content=item_price_text), ft.Container(width=100, content=item_count_text)]

        item_conrtol = ft.Container()
        item_conrtol.ink = True
        item_conrtol.tooltip = str(text).strip() if text else ''
        item_conrtol.on_click = lambda e, _price=price, _count=count: self._set_multiply_info(price_sell=_price, count_sell=_count)
        item_conrtol.content = item_row
        return item_conrtol


    def __on_change_count(self, *args):
        self._set_sell_count(int(self.count_item_sell_input.value))
    def __on_change_get_price(self, *args):
        price_get_input_new = parce_value(self.price_get_input.value)
        self._set_price_get(price_get_input_new)
    def __on_change_sell_price(self, *args):
        price_sell_input_new = parce_value(self.price_sell_input.value)
        self._set_price_sell(price_sell_input_new)

    def _set_multiply_info(self, price_get: float = None, price_sell: float = None, count_sell: int = None):
        self._set_price_get(price_get, is_update=True)
        self._set_price_sell(price_sell, is_update=True)
        self._set_sell_count(count_sell)
    def _set_price_get_percent(self, price_sell_percent: float = None):
        if price_sell_percent is None: return

        if self._price_sell:
            price_sell_now = self._price_sell
        elif self._histogram:
            price_sell_now = self._histogram.get_lowest_sell_order()
        else:
            return
        self._set_price_sell(price_sell_now * price_sell_percent, is_update=True)
    def _set_price_get(self, price_get: float = None, is_update: bool = False):
        if price_get is None: return
        min_commission = 0.02

        self._price_get = price_get
        self._price_sell = price_get / 100 * 115
        if self._price_sell - self._price_get < min_commission:
            self._price_sell = self._price_get + min_commission
        if self._price_get < 0.01 or self._price_sell < 0.01:
            self._price_get = 0.01
            self._price_sell = 0.03

        if is_update:
            self.price_get_input.value = f'{round(self._price_get, 2):.2f}'
            if self.price_get_input.page: self.price_get_input.update()

        self.price_sell_input.value = f'{round(self._price_sell, 2):.2f}'
        if self.price_sell_input.page: self.price_sell_input.update()
        self._update_total_price()
    def _set_price_sell(self, price_sell: float = None, is_update: bool = False):
        if price_sell is None: return
        min_commission = 0.02

        self._price_get = price_sell / 115 * 100
        self._price_sell = price_sell
        if self._price_sell - self._price_get < min_commission:
            self._price_get = self._price_sell - min_commission
        if self._price_get < 0.01 or self._price_sell < 0.01:
            self._price_get = 0.01
            self._price_sell = 0.03

        if is_update:
            self.price_sell_input.value = f'{round(self._price_sell, 2):.2f}'
            if self.price_sell_input.page: self.price_sell_input.update()

        self.price_get_input.value = f'{round(self._price_get, 2):.2f}'
        self._update_total_price()
    def _set_sell_count(self, count: int = None, percent: float = None):
        if count is None and not percent: return
        items_amount = sum([item.item.get_amount() for item in self._items_content if item.item and item.item.marketable])

        self.title_count_text.value = sum([item.item.get_amount() for item in self._items_content if item.item and item.item.marketable])
        if self.title_count_text.page: self.title_count_text.update()

        if percent:
            count = int(items_amount * percent)

        self._count_sell = int(count)

        if self._count_sell > items_amount:
            self._count_sell = items_amount
        elif self._count_sell < 0:
            self._count_sell = 0

        self.count_item_sell_input.value = f'{self._count_sell}'
        self.count_item_sell_input.suffix_text = f" | {items_amount}"
        if self.count_item_sell_input.page: self.count_item_sell_input.update()

        self._update_total_price()
    def _update_total_price(self):
        price_get = self._price_get if self._price_get else 0
        price_sell = self._price_sell if self._price_sell else 0

        self.total_price_sell_input.value = f'{round(price_sell * self._count_sell, 2):.2f}'
        if self.total_price_sell_input.page: self.total_price_sell_input.update()

        self.total_price_get_input.value = f'{round(price_get * self._count_sell, 2):.2f}'
        if self.total_price_get_input.page: self.total_price_get_input.update()

        self.button_start_sell.text = f"Start Sell {self._count_sell}"
        if self._histogram:
            prefix = self._histogram.price_prefix
            suffix = self._histogram.price_suffix
            total_price_get = f'{round(price_get * self._count_sell, 2):.2f}'
            total_price_sell = f'{round(price_sell * self._count_sell, 2):.2f}'
            price_text = f"{prefix}{total_price_sell}{suffix}({prefix}{total_price_get}{suffix})"
            self.button_start_sell.text = f"Start Sell {self._count_sell} Items {price_text}"
        self.button_start_sell.disabled = bool(not price_get or not price_sell or not self._count_sell)
        if self.button_start_sell.page: self.button_start_sell.update()


    def _add_log(self, text):
        self.log_column.controls.append(ft.Text(f"{text}"))
        if self.log_column.page: self.log_column.page.update()


    @staticmethod
    def __parce_html_text(html_content: str):
        content_with_newlines = re.sub(r'<br\s*/?>', '\n', html_content)
        return re.sub(r'<[^>]+>', '', content_with_newlines)


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
        self.market_listen: MarketListenItem | None = None
        self.market_histogram: ItemOrdersHistogram | None = None
        # endregion

        # region Widgets
        self.item_image = ft.Image()
        self.item_image.width = 30
        self.item_image.height = 30

        self.name_text = ft.Text()
        self.name_text.size = 15
        self.name_text.width = 250
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

        self.market_description_text = ft.Text()
        self.market_description_text.size = 15
        self.market_description_text.max_lines = 1
        self.market_description_text.expand = True
        self.market_description_text.value = f"Market price not loaded"
        self.market_description_text.text_align = ft.TextAlign.CENTER
        self.market_description_text.color = ft.colors.RED

        self.one_market_price_text = ft.Text()
        self.one_market_price_text.size = 15
        self.one_market_price_text.max_lines = 1
        self.one_market_price_text.expand = True
        self.one_market_price_text.visible = False
        self.one_market_price_text.value = f""
        self.one_market_price_text.text_align = ft.TextAlign.RIGHT

        self.market_price_text = ft.Text()
        self.market_price_text.size = 15
        self.market_price_text.value = f""
        self.market_price_text.max_lines = 1
        self.market_price_text.expand = True
        self.market_price_text.visible = False
        self.market_price_text.text_align = ft.TextAlign.RIGHT

        self.min_sell_price_text = ft.Text()
        self.min_sell_price_text.size = 15
        self.min_sell_price_text.value = f""
        self.min_sell_price_text.max_lines = 1
        self.min_sell_price_text.expand = True
        self.min_sell_price_text.visible = False
        self.min_sell_price_text.text_align = ft.TextAlign.RIGHT

        self.auto_buy_price_text = ft.Text()
        self.auto_buy_price_text.size = 15
        self.auto_buy_price_text.value = f""
        self.auto_buy_price_text.max_lines = 1
        self.auto_buy_price_text.expand = True
        self.auto_buy_price_text.visible = False
        self.auto_buy_price_text.text_align = ft.TextAlign.RIGHT

        self.sell_button = ft.FilledTonalButton(height=25)
        self.sell_button.text = 'Sell'
        self.sell_button.style = ft.ButtonStyle()
        self.sell_button.style.icon_size = 20
        self.sell_button.style.padding = ft.padding.all(5)
        self.sell_button.style.alignment = ft.alignment.center
        self.sell_button.style.shape = ft.RoundedRectangleBorder(radius=5)
        self.sell_button.icon = ft.icons.ATTACH_MONEY

        self.row = ft.Row()
        self.row.spacing = 2
        self.row.expand = True
        self.row.alignment = ft.MainAxisAlignment.START
        self.row.vertical_alignment = ft.CrossAxisAlignment.CENTER
        self.row.controls = [
            self.item_image,
            self.name_text,
            self.amount_text,
            self.market_description_text,
            self.one_market_price_text,
            self.market_price_text,
            self.min_sell_price_text,
            self.auto_buy_price_text,
            self.sell_button
        ]

        self.content = self.row
        self.update_item_data(item)
        # endregion


    def update_item_data(self, item: InventoryItemRgDescriptions = None):
        if not item: return
        self.item = item

        self.url = self.item.get_market_url()
        self.on_click = None

        self.item_image.src = self.item.get_icon_url(width=29, height=29)

        self.name_text.value = self.item.name
        self.name_text.color = self.item.get_color()

        self.sell_button.icon_color = ft.colors.GREEN if self.item.marketable and self.item.get_amount() > 0 else ft.colors.RED

        self.amount_text.value = f"{self.item.get_amount()} pcs."

        self._update_descriptions()

        self._update_market_description()

        if self.page: self.update()

    def update_market_listen(self, market_listen: MarketListenItem = None):
        if not market_listen: return
        if self.item.classid != market_listen.asset_description.classid: return
        self.market_listen = market_listen

        self.one_market_price_text.value = market_listen.multiply_price_by(1)
        self.market_price_text.value = market_listen.multiply_price_by(self.item.get_amount())

        self._update_market_description()

        if self.page: self.update()

    def update_histogram(self, histogram: ItemOrdersHistogram = None):
        if not histogram or not histogram.is_successful(): return
        self.market_histogram = histogram
        self.min_sell_price_text.value = self.market_histogram.get_lowest_sell_order_str()
        self.auto_buy_price_text.value = self.market_histogram.get_highest_buy_order_str()

        if not self.market_listen:
            self.one_market_price_text.value = self.market_histogram.get_lowest_sell_order_str()
            self.market_price_text.value = self.market_histogram.get_lowest_sell_order_str_by_amount(self.item.get_amount())
            self.one_market_price_text.color = ft.colors.RED
            self.market_price_text.color = ft.colors.RED

        self._update_market_description()

        if self.page: self.update()

    def update_widget(self):
        if self.item:
            self.url = self.item.get_market_url()
            self.on_click = None
            self.item_image.src = self.item.get_icon_url(width=29, height=29)
            self.name_text.value = self.item.name
            self.name_text.color = self.item.get_color()
            self.amount_text.value = f"{self.item.get_amount()} pcs."
            self.sell_button.icon_color = ft.colors.GREEN if self.item.marketable and self.item.get_amount() > 0 else ft.colors.RED
            self._update_descriptions()
        if self.market_listen:
            self.one_market_price_text.value = self.market_listen.multiply_price_by(1)
            self.market_price_text.value = self.market_listen.multiply_price_by(self.item.get_amount())
            self._update_market_description()
        if self.market_histogram:
            self.min_sell_price_text.value = self.market_histogram.get_lowest_sell_order_str()
            self.auto_buy_price_text.value = self.market_histogram.get_highest_buy_order_str()
            if not self.market_listen:
                self.one_market_price_text.value = self.market_histogram.get_lowest_sell_order_str()
                self.market_price_text.value = self.market_histogram.get_lowest_sell_order_str_by_amount(self.item.get_amount())
                self.one_market_price_text.color = ft.colors.RED
                self.market_price_text.color = ft.colors.RED
                self._update_market_description()

        if self.page: self.update()


    def _update_descriptions(self):
        self.name_text.tooltip = None
        self.item_image.tooltip = None

        if not self.item: return

        descriptions = [desc.value.replace("<br>", "\n") for desc in self.item.descriptions]
        tags = [f"{tag.category}: {tag.internal_name}\n" for tag in self.item.tags]

        tooltip_text = ""
        if descriptions: tooltip_text += f"DESCRIPTION\n{', '.join(descriptions)}"
        if tags: tooltip_text += f"\n\nTAGS\n{''.join(tags)}"

        styled_tooltip = ft.Tooltip(message=tooltip_text.strip())
        styled_tooltip.border_radius = 8
        styled_tooltip.prefer_below = True
        styled_tooltip.bgcolor = ft.colors.GREY
        styled_tooltip.text_align = ft.TextAlign.CENTER
        styled_tooltip.border = ft.border.all(1, "#ccc")
        styled_tooltip.shadow = [ft.BoxShadow(blur_radius=6, color="#00000033")]

        self.name_text.tooltip = styled_tooltip
        self.item_image.tooltip = styled_tooltip

    def _update_market_description(self):
        def set_visibility(description, description_visible, one_price_visible, market_price_visible, min_price_visible, auto_buy_visible):
            self.market_description_text.value = description
            self.market_description_text.visible = description_visible
            self.one_market_price_text.visible = one_price_visible
            self.market_price_text.visible = market_price_visible
            self.min_sell_price_text.visible = min_price_visible
            self.auto_buy_price_text.visible = auto_buy_visible

        if self.item:
            marketable_date = self.item.end_ban_marketable()
            is_marketable = self.item.marketable
        else:
            marketable_date = ''
            is_marketable = False

        if marketable_date:
            set_visibility(marketable_date, True, False, False, False, False)
        elif not is_marketable:
            set_visibility("Not Marketable", True, False, False, False, False)
        elif not self.market_listen and not self.market_histogram:
            set_visibility("Price is unknown", True, False, False, False, False)
        else:
            set_visibility("Marketable", False, True, True, True, True)


    def get_market_listen_price(self, is_all: bool = False):
        histogram_price = self.get_histogram_price() * 100
        amount = self.item.get_amount() if self.item else 1

        if self.market_listen:
            if is_all:
                if self.market_price_text.visible:
                    return self.market_listen.sell_price * amount
            else:
                if self.one_market_price_text.visible:
                    return self.market_listen.sell_price

        return histogram_price * amount if is_all else histogram_price

    def get_histogram_price(self, is_buy: bool = False):
        if not self.market_histogram: return 0
        if is_buy:
            return self.market_histogram.get_highest_buy_order()
        else:
            return self.market_histogram.get_lowest_sell_order()


class InventoryPageContent(ft.Column):
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
        # endregion

        # region settings Title
        self.title = Title('Inventory')
        self.title.expand = True
        self.app_id_selector = AppIDSelector(height=25, padding=ft.padding.all(5))
        self.app_id_selector.use_config = True
        self.app_id_selector.on_app_id_select = self._on_select_app_id

        self.inventory_update_interval = IntervalInventoryUpdate()
        self.inventory_update_interval.on_select_interval = self._on_interval_change

        self.title_row = ft.Row()
        self.title_row.expand = True
        self.title_row.alignment = ft.MainAxisAlignment.CENTER
        self.title_row.controls = [
            self.title,
            self.app_id_selector,
            self.inventory_update_interval
        ]
        # endregion

        # region Sort Buttons
        style = ft.ButtonStyle()
        style.padding = ft.padding.all(0)
        style.alignment = ft.alignment.center
        style.icon_size = 20

        self.sort_item_image = ft.Image(width=30, src=' ')

        self.sort_name_button = ft.FilledTonalButton()
        self.sort_name_button.text = 'Name'
        self.sort_name_button.width = 250
        self.sort_name_button.style = style
        self.sort_name_button.on_click = self._on_click_sort

        self.sort_amount_button = ft.FilledTonalButton()
        self.sort_amount_button.text = 'Quantity'
        self.sort_amount_button.icon = ft.icons.ARROW_UPWARD
        self.sort_amount_button.icon_color = ft.colors.GREEN
        self.sort_amount_button.width = 110
        self.sort_amount_button.style = style
        self.sort_amount_button.on_click = self._on_click_sort

        self.sort_one_market_price_button = ft.FilledTonalButton()
        self.sort_one_market_price_button.text = 'Unit Price'
        self.sort_one_market_price_button.expand = True
        self.sort_one_market_price_button.style = style
        self.sort_one_market_price_button.on_click = self._on_click_sort

        self.sort_price_button = ft.FilledTonalButton()
        self.sort_price_button.text = 'Total Price'
        self.sort_price_button.expand = True
        self.sort_price_button.style = style
        self.sort_price_button.on_click = self._on_click_sort

        self.sort_min_price_button = ft.FilledTonalButton()
        self.sort_min_price_button.text = 'Min Price'
        self.sort_min_price_button.expand = True
        self.sort_min_price_button.style = style
        self.sort_min_price_button.on_click = self._on_click_sort

        self.sort_auto_buy_price_button = ft.FilledTonalButton()
        self.sort_auto_buy_price_button.text = 'AutoBuy Price'
        self.sort_auto_buy_price_button.expand = True
        self.sort_auto_buy_price_button.style = style
        self.sort_auto_buy_price_button.on_click = self._on_click_sort

        self.sort_plaseholder_row = ft.Row()
        self.sort_plaseholder_row.width = 60

        self.sort_row = ft.Row()
        self.sort_row.spacing = 2
        self.sort_row.height = 25
        self.sort_row.alignment = ft.MainAxisAlignment.START
        self.sort_row.vertical_alignment = ft.CrossAxisAlignment.CENTER
        self.sort_row.controls = [
            self.sort_item_image,
            self.sort_name_button,
            self.sort_amount_button,
            self.sort_one_market_price_button,
            self.sort_price_button,
            self.sort_min_price_button,
            self.sort_auto_buy_price_button,
            self.sort_plaseholder_row
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

        self.bottom_load_individual_price_button = ft.FilledTonalButton()
        self.bottom_load_individual_price_button.text = 'Load Individual Prices'
        self.bottom_load_individual_price_button.icon = ft.icons.DOWNLOAD
        self.bottom_load_individual_price_button.icon_color = ft.colors.GREEN
        self.bottom_load_individual_price_button.expand = True
        self.bottom_load_individual_price_button.style = style
        self.bottom_load_individual_price_button.on_click = self._on_click_load_individual_price

        self.bottom_sell_all_items_button = ft.FilledTonalButton()
        self.bottom_sell_all_items_button.text = 'Sell all items'
        self.bottom_sell_all_items_button.icon = ft.icons.SELL
        self.bottom_sell_all_items_button.expand = True
        self.bottom_sell_all_items_button.style = style
        self.bottom_sell_all_items_button.on_click = self._on_click_sell_all_items

        self.botton_row = ft.Row()
        self.botton_row.spacing = 2
        self.botton_row.height = 25
        self.botton_row.disabled = True
        self.botton_row.alignment = ft.MainAxisAlignment.START
        self.botton_row.vertical_alignment = ft.CrossAxisAlignment.CENTER
        self.botton_row.controls = [
            self.bottom_load_individual_price_button,
            self.bottom_sell_all_items_button,
        ]
        # endregion

        # region Main Content
        items_column = ft.Column()
        items_column.expand = True
        items_column.spacing = 0
        items_column.controls = [
            self.sort_row,
            self._items_column,
            # self.botton_row,
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
            self.botton_row
        ]
        # endregion

    def _on_interval_change(self, e: datetime.timedelta | None):
        # TODO: Save params and use them
        # print('InventoryPageContent._on_interval_change', e)
        ...

    def _on_select_app_id(self, app_id: str):
        try:
            self.app_id_selector.update_button(disabled=True, icon=ft.icons.UPDATE, icon_color=ft.colors.BLUE, text='Loading...')
            self._items_column.controls = []
            if self._items_column.page: self._items_column.update()

            if not app_id: return
            self.__last_inventory = self._steam_api_utility.get_inventory_items(appid=app_id)

            inventory = self.__last_inventory.inventory if self.__last_inventory else []
            market_listing = self._steam_api_utility.get_market_listings(appid=app_id)
            market_listing_kv = {str(item.asset_description.classid): item for item in market_listing}

            self.botton_row.disabled = len(inventory) <= 0
            if self.botton_row.page: self.botton_row.update()

            app_inventory = self.__items_content.get(str(app_id), {})

            inventory_kv = {item.get_item_id(): item for item in inventory}
            for item_id, item in inventory_kv.items():
                if item_id in app_inventory:
                    app_inventory[item_id].update_item_data(item)
                else:
                    item_content = ItemRowContent(item)
                    item_content.sell_button.on_click = lambda e, _item_content=item_content: self._on_click_sell_item(item_content=_item_content)
                    app_inventory[item_id] = item_content

                market_listing_item = market_listing_kv.get(str(item.classid), None)
                if market_listing_item:
                    app_inventory[item_id].update_market_listen(market_listing_item)

            self.__items_content[str(app_id)] = app_inventory
            self._items_column.controls = [item_content for item_content in app_inventory.values()]
            self.__sort_items()
            if self._items_column.page: self._items_column.update()
        finally:
            self.app_id_selector.update_button()

    def _on_click_sort(self, e: ft.ControlEvent):
        button: ft.FilledTonalButton = e.control
        if not button: return

        if button.icon == ft.icons.ARROW_DOWNWARD:
            button.icon = None
            button.icon_color = None
        elif button.icon == ft.icons.ARROW_UPWARD:
            button.icon = ft.icons.ARROW_DOWNWARD
            button.icon_color = ft.colors.RED
        else:
            button.icon = ft.icons.ARROW_UPWARD
            button.icon_color = ft.colors.GREEN

        for b in [
            self.sort_name_button,
            self.sort_amount_button,
            self.sort_one_market_price_button,
            self.sort_price_button,
            self.sort_min_price_button,
            self.sort_auto_buy_price_button,
        ]:
            if b != button:
                b.icon = None
                b.icon_color = None

        self.__sort_items()
        if self.page: self.update()

    def __sort_items(self):
        def _get_sort_value(button: ft.FilledTonalButton) -> int:
            if button.icon == ft.icons.ARROW_DOWNWARD: return 1
            elif button.icon == ft.icons.ARROW_UPWARD: return -1
            else: return 0

        sort_name = _get_sort_value(self.sort_name_button)
        sort_amount = _get_sort_value(self.sort_amount_button)
        sort_one_market_price = _get_sort_value(self.sort_one_market_price_button)
        sort_price = _get_sort_value(self.sort_price_button)
        sort_min_price = _get_sort_value(self.sort_min_price_button)
        sort_auto_buy_price = _get_sort_value(self.sort_auto_buy_price_button)

        sorting_criteria = [
            (sort_name, lambda x: x.item.name),
            (sort_amount, lambda x: x.item.get_amount()),
            (sort_one_market_price, lambda x: x.get_market_listen_price()),
            (sort_price, lambda x: x.get_market_listen_price(is_all=True)),
            (sort_min_price, lambda x: x.get_histogram_price(is_buy=False)),
            (sort_auto_buy_price, lambda x: x.get_histogram_price(is_buy=True)),
        ]

        active_criteria = [(order, key) for order, key in sorting_criteria if order != 0]

        for order, key in reversed(active_criteria):
            self._items_column.controls.sort(key=key, reverse=(order == -1))


    def __update_button_text(self, button: ft.FilledTonalButton, text: str):
        button.text = text
        if button.page: button.update()
    def _on_click_load_individual_price(self, e: ft.ControlEvent):
        try:
            self.bottom_load_individual_price_button.disabled = True
            self.bottom_load_individual_price_button.icon = ft.icons.HOURGLASS_EMPTY
            self.bottom_load_individual_price_button.icon_color = ft.colors.RED
            self.__update_button_text(self.bottom_load_individual_price_button, 'Loading Individual Prices ...')
            self._account.load_wallet_info()
            total_length = len(self._items_column.controls)
            for number, item_content in enumerate(self._items_column.controls.copy(), start=1):
                item_content: ItemRowContent
                if not item_content.item or not item_content.item.marketable: continue
                self.__update_button_text(self.bottom_load_individual_price_button, f'({number}/{total_length}) Loading {item_content.item.name}')
                histogram = self._steam_api_utility.fetch_market_itemordershistogram(appid=item_content.item.appid, market_hash_name=item_content.item.market_hash_name)
                item_content.update_histogram(histogram)
        finally:
            self.bottom_load_individual_price_button.disabled = False
            self.bottom_load_individual_price_button.icon = ft.icons.DOWNLOAD
            self.bottom_load_individual_price_button.icon_color = ft.colors.GREEN
            self.__update_button_text(self.bottom_load_individual_price_button, 'Load Individual Prices')


    def _on_click_sell_all_items(self, *args):
        sell_all_dialog = SellAllItemsDialog()
        sell_all_dialog.init(steam_api_utility=self._steam_api_utility, items_content=self._items_column.controls)

        if self.page: self.page.open(sell_all_dialog)

    def _on_click_sell_item(self, item_content: ItemRowContent):
        if not item_content: return
        all_items_column: list[ItemRowContent | ft.Control] = [item for item in self._items_column.controls.copy() if item_content.item and item_content.item.marketable]
        if not all_items_column: return
        items_content = [item for item in all_items_column if item.item.market_hash_name == item_content.item.market_hash_name]
        if not items_content: return
        sell_dialog = SellItemDialog()
        sell_dialog.init(steam_api_utility=self._steam_api_utility, items_content=items_content)

        histogram = next((item.market_histogram for item in items_content if item.market_histogram), None)
        sell_dialog.update_histogram(histogram)

        if self.page: self.page.open(sell_dialog)

    def on_update_account(self, account: Account = None):
        self._account = account
        self._steam_api_utility.account = account

        self._items_column.controls = []
        if self._items_column.page: self._items_column.update()
        self.__is_init_inventory = False

    def did_mount(self):
        if not self.__is_init_inventory:
            self.__is_init_inventory = True
            self._on_select_app_id(self.app_id_selector.get_config_value())


class InventoryPage(BasePage):
    load_position = 3
    def __init__(self):
        super().__init__()
        self.name = 'inventory'
        self.label = 'Inventory'
        self.icon = ft.icons.SHOPPING_BAG_OUTLINED
        self.selected_icon = ft.icons.SHOPPING_BAG

        self.disabled_is_logout = True

        self.page_content = InventoryPageContent()

    def on_callback_authenticated(self, account: Account):
        self.page_content.on_update_account(account)
    def on_callback_logout(self):
        self.page_content.on_update_account()
