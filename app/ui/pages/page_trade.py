import re

import flet as ft

from app.core import Account
from app.ui.widgets import AppIDSelector
from app.ui.pages import BasePage, Title
from app.package.data_collectors import get_steam_profile_info, get_steam_id_from_url
from app.package.data_collectors.steam_api_utility import SteamAPIUtility, InventoryItemRgDescriptions, InventoryManager


class TradeItemsContent(ft.Column):
    def __init__(self):
        super().__init__()

        # Class variables
        if True:
            self.visible = False
            self.spacing = 0
            self.alignment = ft.MainAxisAlignment.START
            self.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        # Variables
        if True:
            self.self_items: list[InventoryItemRgDescriptions] = []
            self.partner_items: list[InventoryItemRgDescriptions] = []
            self.self_steam_id = None
            self.partner_steam_id = None
            self.callback_remove_item = None

        # Controls
        if True:
            self.self_user_avatar = ft.CircleAvatar(radius=10)
            self.self_user_avatar.foreground_image_url = None
            self.self_user_nickname = ft.Text(size=15, max_lines=1, selectable=True, expand=True, color=ft.colors.BLUE)
            self.self_user_nickname.value = ''
            self.self_user_nickname.text_align = ft.TextAlign.CENTER
            self.self_user_count_item = ft.Text(size=15, max_lines=1, selectable=True, expand=True, color=ft.colors.GREEN)
            self.self_user_count_item.value = ''
            self.self_user_count_item.text_align = ft.TextAlign.CENTER

            self.self_user_row = ft.Row(spacing=2)
            self.self_user_row.controls = [
                self.self_user_avatar,
                self.self_user_nickname,
                self.self_user_count_item
            ]

            self.self_items_column = ft.Column(spacing=1, expand=True, scroll=ft.ScrollMode.AUTO)
            self.self_items_column.alignment = ft.MainAxisAlignment.START
            self.self_items_column.horizontal_alignment = ft.CrossAxisAlignment.CENTER
            self.self_items_column.controls = []

            self.self_column = ft.Column(expand=True)
            self.self_column.visible = False
            self.self_column.alignment = ft.MainAxisAlignment.START
            self.self_column.horizontal_alignment = ft.CrossAxisAlignment.CENTER
            self.self_column.controls = [
                self.self_user_row,
                self.self_items_column
            ]

            self.partner_user_avatar = ft.CircleAvatar(radius=10)
            self.partner_user_avatar.foreground_image_url = None
            self.partner_user_nickname = ft.Text(size=15, max_lines=1, selectable=True, expand=True, color=ft.colors.BLUE)
            self.partner_user_nickname.value = ''
            self.partner_user_nickname.text_align = ft.TextAlign.CENTER
            self.partner_user_count_item = ft.Text(size=15, max_lines=1, selectable=True, expand=True, color=ft.colors.GREEN)
            self.partner_user_count_item.value = ''
            self.partner_user_count_item.text_align = ft.TextAlign.CENTER

            self.partner_user_row = ft.Row(spacing=2)
            self.partner_user_row.controls = [
                self.partner_user_avatar,
                self.partner_user_nickname,
                self.partner_user_count_item
            ]

            self.partner_items_column = ft.Column(spacing=1, expand=True, scroll=ft.ScrollMode.AUTO)
            self.partner_items_column.alignment = ft.MainAxisAlignment.START
            self.partner_items_column.horizontal_alignment = ft.CrossAxisAlignment.CENTER
            self.partner_items_column.controls = []

            self.partner_column = ft.Column(expand=True)
            self.partner_column.visible = False
            self.partner_column.alignment = ft.MainAxisAlignment.START
            self.partner_column.horizontal_alignment = ft.CrossAxisAlignment.CENTER
            self.partner_column.controls = [
                self.partner_user_row,
                self.partner_items_column
            ]

        # Title
        if True:
            self.title_text = ft.Text(size=25, max_lines=1, color=ft.colors.BLUE, weight=ft.FontWeight.BOLD)
            self.title_text.value = 'Items in trade'
            self.title_text.text_align = ft.TextAlign.CENTER

        self.controls = [
            self.title_text,
            self.self_column,
            ft.Divider(),
            self.partner_column
        ]

    def add_item(self, steam_id, item: InventoryItemRgDescriptions):
        if steam_id != self.self_steam_id and steam_id != self.partner_steam_id: return
        if item.get_amount() <= 0: return

        if steam_id == self.self_steam_id:
            self.add_self_item(item)
        elif steam_id == self.partner_steam_id:
            self.add_partner_item(item)

        self.__update_visible()
        if self.page: self.update()

    def add_self_item(self, item: InventoryItemRgDescriptions):
        original_item = next((i for i in self.self_items if i.instanceid == item.instanceid and i.classid == item.classid), None)
        if original_item:
            original_item.add_items(item)
            original_widget = next((i for i in self.self_items_column.controls if i.item == original_item), None)
            if original_widget:
                original_widget.count_item_text.value = f'Count: {original_widget.item.get_amount()}'
        else:
            self.self_items.append(item)
            item_widget = self.__create_item_widget(item, self.self_steam_id)
            self.self_items_column.controls.append(item_widget)

        amount_items = sum(i.get_amount() for i in self.self_items)
        self.self_user_count_item.value = '' if amount_items == 0 else f"Count: {amount_items}"

        self.self_items_column.controls.sort(key=lambda x: x.item.get_amount(), reverse=True)

    def add_partner_item(self, item: InventoryItemRgDescriptions):
        original_item = next((i for i in self.partner_items if i.instanceid == item.instanceid and i.classid == item.classid), None)
        if original_item:
            original_item.add_items(item)
            original_widget = next((i for i in self.partner_items_column.controls if i.item == original_item), None)
            if original_widget:
                original_widget.count_item_text.value = f'Count: {original_widget.item.get_amount()}'
        else:
            self.partner_items.append(item)
            item_widget = self.__create_item_widget(item, self.partner_steam_id)
            self.partner_items_column.controls.append(item_widget)

        amount_items = sum(i.get_amount() for i in self.partner_items)
        self.partner_user_count_item.value = '' if amount_items == 0 else f"Count: {amount_items}"

        self.partner_items_column.controls.sort(key=lambda x: x.item.get_amount(), reverse=True)

    def __create_item_widget(self, item, owner_steam_id):
        item_row = ft.Row(spacing=1)
        item_row.item = item

        item_row.icon_item_image = ft.Image(width=20, height=20, src=item.get_icon_url())

        item_row.name_item_text = ft.Text(size=15, max_lines=1, selectable=True, text_align=ft.TextAlign.LEFT, width=100, expand=True)
        item_row.name_item_text.value = item.name
        item_row.name_item_text.color = item.get_color()

        item_row.count_item_text = ft.Text(size=15, max_lines=1, selectable=True, text_align=ft.TextAlign.LEFT, width=100, expand=True)
        item_row.count_item_text.value = f'Count: {item.get_amount()}'

        item_row.button_remove_item = ft.IconButton(icon=ft.icons.CLOSE, icon_color=ft.colors.RED, width=20, height=20)
        item_row.button_remove_item.style = ft.ButtonStyle(padding=ft.padding.all(0), alignment=ft.alignment.center)
        item_row.button_remove_item.tooltip = 'Remove item'
        item_row.button_remove_item.visual_density = ft.VisualDensity.COMPACT
        item_row.button_remove_item.on_click = lambda _: self.on_click_button_remove_item(owner_steam_id=owner_steam_id, item=item)

        item_row.controls = [
            item_row.icon_item_image,
            item_row.name_item_text,
            item_row.count_item_text,
            item_row.button_remove_item,
            ft.VerticalDivider(width=10),
        ]

        return item_row

    def __update_visible(self):
        self_amount_items = sum(i.get_amount() for i in self.self_items)
        partner_amount_items = sum(i.get_amount() for i in self.partner_items)
        self.visible = self_amount_items + partner_amount_items > 0
        self.self_column.visible = self_amount_items > 0
        self.partner_column.visible = partner_amount_items > 0

    def on_click_button_remove_item(self, *args, item: InventoryItemRgDescriptions, owner_steam_id: str | int):
        if owner_steam_id != self.self_steam_id and owner_steam_id != self.partner_steam_id: return

        items = self.self_items if owner_steam_id == self.self_steam_id else self.partner_items
        items_column = self.self_items_column if owner_steam_id == self.self_steam_id else self.partner_items_column
        count_item = self.self_user_count_item if owner_steam_id == self.self_steam_id else self.partner_user_count_item

        original_item = next((i for i in items if i.instanceid == item.instanceid and i.classid == item.classid), None)
        if original_item:
            items.remove(original_item)
        original_widget = next((i for i in items_column.controls if i.item == original_item), None)
        if original_widget:
            items_column.controls.remove(original_widget)

        amount_items = sum(i.get_amount() for i in items)
        count_item.value = '' if amount_items == 0 else f"Count: {amount_items}"

        self.__update_visible()
        if self.page: self.update()

        if self.callback_remove_item:
            self.callback_remove_item(owner_steam_id, item)

    def create_comment_trade(self):
        def format_items(items):
            items_dict = {}
            for item in items:
                amount = item.get_amount()
                if amount <= 0:
                    continue
                app_id = str(item.appid)
                items_dict[app_id] = items_dict.get(app_id, 0) + amount
            total = sum(items_dict.values())
            if not items_dict:
                return "No items."
            items_formatted = '\n'.join(f"- AppID {key}: {value} pcs." for key, value in items_dict.items())
            return f"{total} pcs.\n{items_formatted}"

        my_items_formatted = format_items(self.self_items)
        partner_items_formatted = format_items(self.partner_items)

        comment = (
            f"My Items (SteamID: {self.self_steam_id})\n"
            f"Total: {my_items_formatted}\n\n"
            f"Your Items (SteamID: {self.partner_steam_id})\n"
            f"Total: {partner_items_formatted}\n\n"
            f"Please review all items carefully before confirming the trade."
        )
        return comment

    def create_trade_data(self, *args):
        self_items = []
        for item in self.self_items:
            if item.get_amount() <= 0: continue
            self_items.extend(
                [
                    {
                        'appid': item_data.appid,
                        'contextid': item_data.contextid,
                        'amount': str(item_data.amount),
                        'assetid': item_data.assetid
                    }
                    for item_data in item.items if item_data.amount > 0
                ]
            )

        partner_items = []
        for item in self.partner_items:
            if item.get_amount() <= 0: continue
            partner_items.extend(
                [
                    {
                        'appid': item_data.appid,
                        'contextid': item_data.contextid,
                        'amount': str(item_data.amount),
                        'assetid': item_data.assetid
                    }
                    for item_data in item.items if item_data.amount > 0
                ]
            )

        if not self_items and not partner_items: return None

        return {
            'newversion': True,
            'version': 4,
            'me': {
                'assets': self_items,
                'currency': [],
                'ready': False
            },
            'them': {
                'assets': partner_items,
                'currency': [],
                'ready': False
            }
        }

    def clear_items(self):
        self.self_items = []
        self.partner_items = []
        self.self_items_column.controls = []
        self.partner_items_column.controls = []
        self.self_user_count_item.value = ''
        self.partner_user_count_item.value = ''
        self.__update_visible()
        if self.page: self.update()


class ItemRowContent(ft.Row):
    def __init__(self, item: InventoryItemRgDescriptions):
        super().__init__()

        # Class variables
        if True:
            self.spacing = 2

        # Variables
        if True:
            self.item = item
            self.callback_select_item = None

        # Image
        if True:
            self.icon_item_image = ft.Image(width=29, height=29, src=item.get_icon_url())

        # Name
        if True:
            self.name_item_text = ft.Text(size=15, max_lines=1, selectable=True, text_align=ft.TextAlign.LEFT, width=100, expand=True)
            self.name_item_text.value = item.name
            self.name_item_text.color = item.get_color()

        # Count select
        if True:
            self.count_item_input = ft.TextField(dense=True, content_padding=0, max_lines=1, multiline=False, width=100)
            self.count_item_input.label = 'Count'
            self.count_item_input.value = '0'
            self.count_item_input.suffix_text = f"|{self.item.get_amount()}"
            self.count_item_input.input_filter = ft.NumbersOnlyInputFilter()
            self.count_item_input.border_color = ft.colors.GREY
            self.count_item_input.on_change = self.on_change_count_item_input

            self.add_icon_button = ft.IconButton(icon=ft.icons.ADD, height=20)
            self.add_icon_button.style = ft.ButtonStyle(padding=ft.padding.all(0), alignment=ft.alignment.center)
            self.add_icon_button.tooltip = 'Add item to Trade'
            self.add_icon_button.visual_density = ft.VisualDensity.COMPACT
            self.add_icon_button.on_click = self.on_press_add_icon_button

            self.add_all_tonal_button = ft.FilledTonalButton(height=20)
            self.add_all_tonal_button.style = ft.ButtonStyle(padding=ft.padding.all(0), alignment=ft.alignment.center)
            self.add_all_tonal_button.text = 'All'
            self.add_all_tonal_button.tooltip = 'Add all item to Trade'
            self.add_all_tonal_button.icon = ft.icons.ADD
            self.add_all_tonal_button.on_click = self.on_press_add_all_tonal_button

            self.select_item_checkbox = ft.Checkbox(height=20)
            self.select_item_checkbox.value = True
            self.select_item_checkbox.tristate = True
            self.select_item_checkbox.tooltip = ''
            self.select_item_checkbox.on_change = self.on_change_select_item_checkbox

        self.controls = [
            self.select_item_checkbox,
            self.icon_item_image,
            self.name_item_text,
            self.count_item_input,
            self.add_icon_button,
            self.add_all_tonal_button,
            ft.VerticalDivider(width=10),
        ]

    def is_can_trade_item(self) -> bool:
        return self.select_item_checkbox.value

    def set_callback_select_item(self, callback_select_item: callable):
        self.callback_select_item = callback_select_item
        return self

    def on_press_add_icon_button(self, *args):
        if not self.count_item_input.value:
            self.count_item_input.value = '0'
            if self.page: self.count_item_input.update()
        amount_need = int(self.count_item_input.value)
        if amount_need <= 0: amount_need = 1

        select_items = self.item.get_amount_items(amount_need)
        self.item.remove_items(select_items)

        self.count_item_input.suffix_text = f"|{self.item.get_amount()}"
        self.count_item_input.value = '0'
        if self.page: self.count_item_input.update()

        if self.callback_select_item:
            self.callback_select_item(select_items)

    def on_press_add_all_tonal_button(self, *args):
        self.count_item_input.value = f'{self.item.get_amount()}'
        self.on_press_add_icon_button(*args)

        self.count_item_input.value = '0'
        if self.page: self.count_item_input.update()

    def on_change_select_item_checkbox(self, *args):
        if self.select_item_checkbox.value is False:
            self.select_item_checkbox.value = True

        self.add_icon_button.disabled = self.select_item_checkbox.value is None
        self.add_all_tonal_button.disabled = self.select_item_checkbox.value is None
        if self.page: self.update()

    def on_change_count_item_input(self, *args):
        if not self.count_item_input.value:
            self.count_item_input.value = '0'
        int_count_item_input = int(self.count_item_input.value)
        if int_count_item_input > self.item.get_amount():
            int_count_item_input = f'{self.item.get_amount()}'
        self.count_item_input.value = f'{int_count_item_input}'
        if self.page: self.count_item_input.update()


class UserInventoryContent(ft.Column):
    def __init__(self):
        super().__init__()

        # Class variables
        if True:
            self.expand = True
            self.spacing = 0

        # Variables
        if True:
            self.items: dict[str, InventoryManager] = {}
            self.user_steam_id: str | None = None
            self.account: Account | None = None
            self.callback_select_item = None

        # Title widgets
        if True:
            self.user_count_item = ft.Text(size=15, max_lines=1, selectable=True, color=ft.colors.BLUE, expand=True)
            self.user_count_item.value = 'Count Items: 0'
            self.user_count_item.text_align = ft.TextAlign.RIGHT
            self.user_price_item = ft.Text(size=15, max_lines=1, selectable=True, color=ft.colors.GREEN, expand=True)
            self.user_price_item.value = 'Price Items: 0'
            self.user_price_item.text_align = ft.TextAlign.LEFT

            self.appid_input = AppIDSelector()
            self.appid_input.height = 20
            self.appid_input.use_config = False
            self.appid_input.on_app_id_select = self.__appid_input_on_app_id_select

            self.user_row = ft.Row(spacing=5)
            self.user_row.alignment = ft.MainAxisAlignment.CENTER
            self.user_row.vertical_alignment = ft.CrossAxisAlignment.CENTER
            self.user_row.controls = [
                self.user_count_item,
                self.user_price_item,
                self.appid_input,
            ]

        # Add item control widget
        if True:
            self.equilibrium_checkbox = ft.Checkbox(height=20)
            self.equilibrium_checkbox.value = False
            self.equilibrium_checkbox.tristate = False
            self.equilibrium_checkbox.tooltip = 'Equilibrium count items'
            # self.equilibrium_checkbox.on_change = self.on_change_equilibrium_checkbox

            self.count_per_item_input = ft.TextField(dense=True, content_padding=0, max_lines=1, multiline=False, expand=True)
            self.count_per_item_input.label = 'Max count per Item'
            self.count_per_item_input.value = '0'
            self.count_per_item_input.input_filter = ft.NumbersOnlyInputFilter()
            self.count_per_item_input.border_color = ft.colors.GREY
            self.count_per_item_input.on_change = self.on_change_count_per_item_input

            self.count_item_input = ft.TextField(dense=True, content_padding=0, max_lines=1, multiline=False, expand=True)
            self.count_item_input.label = 'Count'
            self.count_item_input.value = '0'
            self.count_item_input.input_filter = ft.NumbersOnlyInputFilter()
            self.count_item_input.border_color = ft.colors.GREY
            self.count_item_input.on_change = self.on_change_count_item_input

            self.add_icon_button = ft.IconButton(icon=ft.icons.ADD, height=20)
            self.add_icon_button.style = ft.ButtonStyle(padding=ft.padding.all(0), alignment=ft.alignment.center)
            self.add_icon_button.tooltip = 'Add items to Trade'
            self.add_icon_button.visual_density = ft.VisualDensity.COMPACT
            self.add_icon_button.on_click = self.on_press_add_icon_button

            self.add_all_tonal_button = ft.FilledTonalButton(height=20)
            self.add_all_tonal_button.style = ft.ButtonStyle(padding=ft.padding.all(0), alignment=ft.alignment.center)
            self.add_all_tonal_button.text = 'All'
            self.add_all_tonal_button.tooltip = 'Add all items to Trade'
            self.add_all_tonal_button.icon = ft.icons.ADD
            self.add_all_tonal_button.on_click = self.on_press_add_all_tonal_button

            self.add_item_control_row = ft.Row(spacing=2)
            self.add_item_control_row.controls = [
                ft.VerticalDivider(width=10),
                self.equilibrium_checkbox,
                self.count_per_item_input,
                self.count_item_input,
                self.add_icon_button,
                self.add_all_tonal_button,
                ft.VerticalDivider(width=10),
            ]

        # Items Column
        if True:
            self.items_column = ft.Column(expand=True, spacing=1, scroll=ft.ScrollMode.AUTO)

        self.controls = [
            self.user_row,
            self.add_item_control_row,
            ft.Divider(),
            self.items_column
        ]

    def set_items(self, items: list[InventoryItemRgDescriptions]):
        self.items_column.controls = [ItemRowContent(item).set_callback_select_item(self.on_callback_select_item) for item in items]
        self.items_column.controls.sort(key=lambda x: (x.item.get_amount()), reverse=True)
        if self.items_column.page: self.items_column.update()

    def __appid_input_on_app_id_select(self, app_id=None):
        if not app_id: return
        try:
            self.appid_input.disabled = True
            if self.appid_input.page: self.appid_input.update()
            if not self.account or not self.account.is_alive_session(): return
            appid_input = str(app_id).strip()

            if appid_input not in self.items:
                class_steam_api = SteamAPIUtility(account=self.account)
                items = class_steam_api.get_inventory_items(steam_id=self.user_steam_id, appid=appid_input)
                if items and items.success:
                    self.items[appid_input] = items
            else:
                items = self.items[appid_input]

            if items and items.success:
                self.user_count_item.value = f'Count Items: {items.get_amount_items()}'
                self.set_items(items.get_tradable_inventory())
        finally:
            self.appid_input.disabled = False
            if self.page: self.update()

    def on_change_count_item_input(self, *args):
        if not self.count_item_input.value:
            self.count_item_input.value = '0'

        self.count_item_input.value = f'{int(self.count_item_input.value)}'
        if self.page: self.count_item_input.update()

    def on_change_count_per_item_input(self, *args):
        if not self.count_per_item_input.value:
            self.count_per_item_input.value = '0'

        self.count_per_item_input.value = f'{int(self.count_per_item_input.value)}'
        if self.page: self.count_per_item_input.update()

    def on_press_add_icon_button(self, *args):
        if not self.count_item_input.value:
            self.count_item_input.value = '0'
            if self.page: self.count_item_input.update()
        amount_need = int(self.count_item_input.value)
        if amount_need <= 0: return

        if not self.count_per_item_input.value:
            self.count_per_item_input.value = '0'
            if self.page: self.count_per_item_input.update()
        count_per_item = int(self.count_per_item_input.value)
        is_equilibrium = self.equilibrium_checkbox.value

        ready_to_trade_items = [_item for _item in self.items_column.controls if _item.is_can_trade_item() and _item.item.tradable and _item.item.get_amount() > 0]

        total_items_count = {_item.item.get_item_id(): _item.item.get_amount() for _item in ready_to_trade_items}
        equilibrium_items_count = {}
        if is_equilibrium and sum(total_items_count.values()) > amount_need:
            remaining = amount_need
            while remaining > 0:
                for _item in ready_to_trade_items:
                    if remaining <= 0: break
                    _item_id = _item.item.get_item_id()
                    if _item_id not in equilibrium_items_count:
                        equilibrium_items_count[_item_id] = 0
                    count_to_trade = equilibrium_items_count.get(_item_id, 0)
                    count_total = total_items_count.get(_item_id, 0)
                    if count_to_trade >= count_total: continue
                    equilibrium_items_count[_item_id] += 1
                    remaining -= 1

        for item in ready_to_trade_items:
            if not item.is_can_trade_item(): continue
            if not item.item.tradable: continue
            if amount_need <= 0: break

            custom_count = amount_need
            equilibrium_count = equilibrium_items_count.get(item.item.get_item_id(), 0)
            if equilibrium_count > 0:
                custom_count = equilibrium_count
            if count_per_item > 0:
                custom_count = min(custom_count, count_per_item)

            select_items: InventoryItemRgDescriptions = item.item.get_amount_items(custom_count)
            item.item.remove_items(select_items)
            item.count_item_input.suffix_text = f"|{item.item.get_amount()}"

            amount_need -= select_items.get_amount()
            self.count_item_input.value = f'{amount_need}'

            if self.callback_select_item:
                self.callback_select_item(self.user_steam_id, select_items)

            items = self.items.get(str(item.item.appid), None)
            if items:
                self.user_count_item.value = f'Count Items: {items.get_amount_items(only_tradable=True)}'

        self.count_item_input.value = '0' if amount_need <= 0 else f'{amount_need}'
        self.items_column.controls.sort(key=lambda x: (x.item.get_amount()), reverse=True)
        if self.page: self.update()

    def on_press_add_all_tonal_button(self, *args):
        for item in self.items_column.controls:
            item: ItemRowContent
            if not item.is_can_trade_item(): continue
            if not item.item.tradable: continue

            select_items: InventoryItemRgDescriptions = item.item.get_amount_items(item.item.get_amount())
            item.item.remove_items(select_items)
            item.count_item_input.suffix_text = f"|{item.item.get_amount()}"

            if self.callback_select_item:
                self.callback_select_item(self.user_steam_id, select_items)

            items = self.items.get(str(item.item.appid), None)
            if items:
                self.user_count_item.value = f'Count Items: {items.get_amount_items(only_tradable=True)}'

        self.items_column.controls.sort(key=lambda x: (x.item.get_amount()), reverse=True)
        if self.page: self.update()

    def on_callback_select_item(self, item: InventoryItemRgDescriptions):
        if not item: return

        items = self.items.get(str(item.appid), None)
        if not items: return

        self.user_count_item.value = f'Count Items: {items.get_amount_items(only_tradable=True)}'
        self.items_column.controls.sort(key=lambda x: (x.item.get_amount()), reverse=True)

        if self.page: self.update()

        if self.callback_select_item:
            self.callback_select_item(self.user_steam_id, item)

    def on_callback_remove_item(self, item: InventoryItemRgDescriptions):
        if not item: return

        original_item: ItemRowContent = next((x for x in self.items_column.controls if x.item.classid == item.classid and x.item.instanceid == item.instanceid), None)
        if original_item:
            original_item.item.add_items(item)
            original_item.count_item_input.suffix_text = f"|{original_item.item.get_amount()}"
            if original_item.page: original_item.update()

        self.user_count_item.value = f'Count Items: {sum([x.item.get_amount() for x in self.items_column.controls])}'
        self.items_column.controls.sort(key=lambda x: (x.item.get_amount()), reverse=True)
        if self.page: self.update()


class TradePageContent(ft.Column):
    def __init__(self):
        super().__init__()
        # Class variables
        if True:
            self.expand = True
            self.spacing = 0

        # Variables
        if True:
            self.__account: Account | None = None
            self.__trade_url = ''
            self.partner_user_steam_id = None
            self.partner_user_trade_token = None

        # Title
        if True:
            self.title = Title('Create Trade Page')

        # TextField 'Steam Trade URL'
        if True:
            self.trade_url_input = ft.TextField(dense=True, content_padding=10, max_lines=1, multiline=False)
            self.trade_url_input.label = 'Steam Trade URL | Friend Steam URL | Friend Steam ID'
            self.trade_url_input.border_color = ft.colors.GREY
            self.trade_url_input.on_change = self.on_update_trade_url

        # Row Self and Partner user
        if True:
            self.self_user_avatar = ft.CircleAvatar(height=40)
            self.self_user_avatar.foreground_image_url = None
            self.self_user_nickname = ft.Text(size=30, max_lines=1, selectable=True, expand=True, color=ft.colors.BLUE)
            self.self_user_nickname.value = ''
            self.self_user_nickname.text_align = ft.TextAlign.CENTER
            self.self_user_count_item = ft.Text(size=20, max_lines=1, selectable=True, expand=True, color=ft.colors.GREEN)
            self.self_user_count_item.value = ''
            self.self_user_count_item.text_align = ft.TextAlign.CENTER
            self.self_user_price_item = ft.Text(size=20, max_lines=1, selectable=True, expand=True, color=ft.colors.GREEN)
            self.self_user_price_item.value = ''
            self.self_user_price_item.text_align = ft.TextAlign.CENTER
            self.self_user_row = ft.Row(spacing=0, expand=True)
            self.self_user_row.alignment = ft.MainAxisAlignment.START
            self.self_user_row.vertical_alignment = ft.CrossAxisAlignment.CENTER
            self.self_user_row.controls = [
                self.self_user_avatar,
                self.self_user_nickname,
                self.self_user_count_item,
                self.self_user_price_item
            ]

            self.partner_user_avatar = ft.CircleAvatar(height=40)
            self.partner_user_avatar.foreground_image_url = None
            self.partner_user_nickname = ft.Text(size=30, max_lines=1, selectable=True, expand=True, color=ft.colors.BLUE)
            self.partner_user_nickname.value = ''
            self.partner_user_nickname.text_align = ft.TextAlign.CENTER
            self.partner_user_count_item = ft.Text(size=20, max_lines=1, selectable=True, expand=True, color=ft.colors.RED)
            self.partner_user_count_item.value = ''
            self.partner_user_count_item.text_align = ft.TextAlign.CENTER
            self.partner_user_price_item = ft.Text(size=20, max_lines=1, selectable=True, expand=True, color=ft.colors.RED)
            self.partner_user_price_item.value = ''
            self.partner_user_price_item.text_align = ft.TextAlign.CENTER
            self.partner_user_row = ft.Row(spacing=0, expand=True)
            self.partner_user_row.alignment = ft.MainAxisAlignment.END
            self.partner_user_row.vertical_alignment = ft.CrossAxisAlignment.CENTER
            self.partner_user_row.controls = [
                self.self_user_price_item,
                self.self_user_count_item,
                self.partner_user_nickname,
                self.partner_user_avatar
            ]

            self.users_row = ft.Row(spacing=0)
            self.users_row.controls = [
                self.self_user_row,
                self.partner_user_row
            ]

        # Content Trade Items
        if True:
            self.user_inventory_row = UserInventoryContent()
            self.user_inventory_row.callback_select_item = self.on_callback_select_item

            self.partner_inventory_row = UserInventoryContent()
            self.partner_inventory_row.callback_select_item = self.on_callback_select_item

            self.trade_items_row = TradeItemsContent()
            self.trade_items_row.callback_remove_item = self.on_callback_remove_item

            self.trade_content_row = ft.Row(expand=True, spacing=0)
            self.trade_content_row.controls = [
                self.user_inventory_row,
                self.trade_items_row,
                self.partner_inventory_row
            ]

        # Button Create Trade
        if True:
            self.create_trade_button = ft.FilledTonalButton(expand=True, height=25)
            self.create_trade_button.text = 'Create Trade'
            self.create_trade_button.icon = ft.icons.PLAY_ARROW
            self.create_trade_button.on_click = self.on_click_create_trade_button

            self.create_trade_button_row = ft.Row()
            self.create_trade_button_row.controls = [
                self.create_trade_button
            ]

        self.controls = [
            self.title,
            self.trade_url_input,
            ft.Divider(),
            self.users_row,
            self.trade_content_row,
            self.create_trade_button_row,
        ]

    def update_self_user(self, account: Account):
        self.__account = account
        self_user_info = get_steam_profile_info(self.__account.session)
        self.self_user_nickname.value = self_user_info.get('steamID', 'Unknown Nickname')
        self.self_user_avatar.foreground_image_url = self_user_info.get('avatarFull', None)

        self.user_inventory_row.user_steam_id = self_user_info.get('steamID64', None)
        self.user_inventory_row.account = self.__account
        self.partner_inventory_row.account = self.__account
        if self.page: self.self_user_row.update()

        self.trade_items_row.self_user_avatar.foreground_image_url = self_user_info.get('avatarFull', None)
        self.trade_items_row.self_user_nickname.value = self_user_info.get('steamID', 'Unknown Nickname')
        self.trade_items_row.self_column.visible = True
        self.trade_items_row.self_steam_id = self_user_info.get('steamID64', None)
        if self.page: self.trade_items_row.update()

    def update_partner_user(self, steam_id: str | int):
        url_profile = f'https://steamcommunity.com/profiles/{steam_id}'
        self_user_info = get_steam_profile_info(self.__account.session, url_profile)
        self.partner_user_nickname.value = self_user_info.get('steamID', 'Unknown Nickname')
        self.partner_user_avatar.foreground_image_url = self_user_info.get('avatarFull', None)
        if self.page: self.partner_user_row.update()
        self.partner_inventory_row.user_steam_id = self_user_info.get('steamID64', None)

        self.trade_items_row.partner_user_avatar.foreground_image_url = self_user_info.get('avatarFull', None)
        self.trade_items_row.partner_user_nickname.value = self_user_info.get('steamID', 'Unknown Nickname')
        # self.trade_items_row.partner_column.visible = True
        self.trade_items_row.partner_steam_id = self_user_info.get('steamID64', None)
        if self.page: self.trade_items_row.update()

    def on_update_trade_url(self, *args):
        if not self.trade_url_input.value: return
        self.__trade_url = self.trade_url_input.value
        self.partner_user_steam_id, self.partner_user_trade_token = None, None
        temp = re.findall("partner=[0-9]+", self.__trade_url)
        if len(temp) > 0:
            self.partner_user_steam_id = int(str(temp[0]).replace("partner=", "")) + 76561197960265728
        temp = re.findall("token=.*", self.__trade_url)
        if len(temp) > 0:
            self.partner_user_trade_token = str(temp[0]).replace("token=", "")

        if not self.partner_user_steam_id:
            from_url = get_steam_id_from_url(self.__trade_url)
            if from_url:
                self.partner_user_steam_id = str(from_url)

        if not self.partner_user_steam_id and not self.partner_user_trade_token: return
        self.update_partner_user(self.partner_user_steam_id)

    def on_click_create_trade_button(self, *args):
        trade_items = self.trade_items_row.create_trade_data()
        comment_trade = self.trade_items_row.create_comment_trade()
        print(comment_trade)

        class_steam_api = SteamAPIUtility(account=self.__account)
        status_create_trade = class_steam_api.create_trade_offer(
            partner_steam32id=self.partner_user_steam_id,
            partner_token=self.partner_user_trade_token,
            items=trade_items,
            tradeoffermessage=''
        )

        print(f'{status_create_trade=}')
        if status_create_trade:
            self.trade_items_row.clear_items()

    def on_callback_select_item(self, steam_id: str | int, item: InventoryItemRgDescriptions):
        self.trade_items_row.add_item(steam_id, item)

    def on_callback_remove_item(self, steam_id: str | int, item: InventoryItemRgDescriptions):
        if self.user_inventory_row.user_steam_id == steam_id:
            self.user_inventory_row.on_callback_remove_item(item)
        elif self.partner_inventory_row.user_steam_id == steam_id:
            self.partner_inventory_row.on_callback_remove_item(item)


class TradePage(BasePage):
    load_position = 2
    def __init__(self):
        super().__init__()
        self.name = 'trade'
        self.label = 'Trade'
        self.icon = ft.icons.SWAP_VERTICAL_CIRCLE_OUTLINED
        self.selected_icon = ft.icons.SWAP_VERTICAL_CIRCLE

        self.disabled = True
        self.disabled_is_logout = True

        self.page_content = TradePageContent()

    def on_callback_authenticated(self, account: Account):
        self.page_content.update_self_user(account)
