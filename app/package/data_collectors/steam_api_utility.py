from __future__ import annotations
import re
import copy
import json
import time
import datetime
import urllib.parse

from app.core import Account
from app.database import sql_manager


class SteamAPIUtility:
    def __init__(self, account: Account = None):
        self.account = account
        self.session_id: str | None = None

    def create_trade_offer(self, partner_steam32id: str, partner_token: str, items: dict = None, tradeoffermessage: str = ''):
        if not self.account or not self.account.is_alive_session(): return
        if not partner_steam32id: return False
        text_steam_send = ""
        session_id = self.account.session.cookies.get('sessionid', domain='steamcommunity.com')
        try:
            if not items: return
            url = 'https://steamcommunity.com/tradeoffer/new/send'
            headers = {'Referer': "https://steamcommunity.com/tradeoffer/new",
                       'Origin': "https://steamcommunity.com"}
            trade_offer_create_params = {} if not partner_token else {'trade_offer_access_token': partner_token}
            params = {
                'sessionid': session_id,
                'serverid': 1,
                'partner': partner_steam32id,
                'tradeoffermessage': tradeoffermessage,
                'json_tradeoffer': json.dumps(items),
                'captcha': '',
                'trade_offer_create_params': json.dumps(trade_offer_create_params)
            }

            print(f"respons: params = {params}")
            respons = self.account.session.post(url, data=params, headers=headers)
            print(f"respons: status_code = {respons.status_code}")
            print(f"respons: text = {respons.text}")
            if respons.ok:
                text_json: dict = json.loads(respons.text)
                print(text_json)
                return True
            else:
                text_steam_send = f"{respons.status_code}\n{respons.text}\n"
        except:
            pass
        if len(text_steam_send) > 1:
            print(f"Обмен не отправлен, Steam ответил: {text_steam_send}")
            return


    def fetch_session_id(self):
        if self.session_id: return self.session_id
        if not self.account or not self.account.is_alive_session(): return
        url = "https://steamcommunity.com/market/"
        try:
            response = self.account.session.get(url, timeout=10)
            if response.ok:
                match = re.search(r'g_sessionID\s*=\s*"([^"]+)"', response.text)
                if match:
                    self.session_id = match.group(1)
                    return self.session_id
            return None
        except Exception as e:
            print(f"Error fetching session ID: {e}")
            return None

    def fetch_market_priceoverview(self, market_hash_name: str, appid: int = 3017120, currency: int = 37) -> dict | None:
        if not self.account or not self.account.is_alive_session(): return
        url = f"https://steamcommunity.com/market/priceoverview/"
        params = {'country': 'RU', 'appid': appid, 'currency': currency, 'market_hash_name': market_hash_name}
        market_info = self.account.session.get(f"{url}?{urllib.parse.urlencode(params)}", timeout=10)
        return market_info.json() if market_info.ok else None


    def get_inventory_items(self, steam_id: str | int = None, appid=3017120, start=0, context_id=2):
        if not self.account or not self.account.is_alive_session(): return
        if not steam_id: steam_id = self.account.steam_id
        if str(self.account.steam_id) == str(steam_id):
            return self.__get_myinventory_items(steam_id=steam_id, appid=appid, start=start, context_id=context_id)
        else:
            return self.__get_partnerinventory_items(steam_id=steam_id, appid=appid, start=start, context_id=context_id)
    def __get_myinventory_items(self, steam_id: str | int, appid=3017120, start=0, context_id=2):
        def_url = f'https://steamcommunity.com/inventory/{steam_id}/{appid}/{context_id}?count=5000'
        if start:
            def_url += f'&start_assetid={start}'
        try:
            req = self.account.session.get(url=def_url, timeout=10)
            if not req.ok: return None
            req_json = req.json()
            if not req_json.get('success', False): return None

            inventory = InventoryManager(req_json, context_id=context_id)
            if req_json.get('more_items', False):
                more_start = req_json.get('last_assetid', None)
                if more_start:
                    next_inventory = self.__get_myinventory_items(steam_id=steam_id, appid=appid, start=more_start, context_id=context_id)
                    if next_inventory:
                        inventory.add_next_invent(next_inventory)
            return inventory
        except:
            time.sleep(5)
        return None
    def __get_partnerinventory_items(self, steam_id: str | int, appid=3017120, context_id=2, start=0):
        session_id = self.account.session.cookies.get('sessionid', domain='steamcommunity.com')
        params = {
            'sessionid': session_id,
            'partner': steam_id,
            'appid': appid,
            'contextid': context_id
        }
        if start:
            params['start'] = start
        def_url = f'https://steamcommunity.com/tradeoffer/new/partnerinventory/'

        try:
            headers = {
                'referer': "https://steamcommunity.com/tradeoffer/new",
                'host': "steamcommunity.com"
            }
            req = self.account.session.get(url=def_url, params=params, headers=headers, timeout=10)
            if not req.ok: return None
            req_json = req.json()
            if not req_json.get('success', False): return None

            inventory = InventoryManager(req_json, context_id=context_id)
            if req_json.get('more', False):
                more_start = req_json.get('more_start', None)
                if more_start:
                    next_inventory = self.__get_partnerinventory_items(steam_id=steam_id, appid=appid, context_id=context_id, start=more_start)
                    if next_inventory:
                        inventory.add_next_invent(next_inventory)
            return inventory
        except:
            time.sleep(5)
        return None


    def get_market_listings(self, appid: int | str = 3017120, start: int = 0, max_items_load: int = 1000) -> list[MarketListenItem]:
        if not self.account or not self.account.is_alive_session(): return []
        market_listings = self.__load_market_listings(appid=appid, start=start, max_items_load=max_items_load)
        return [MarketListenItem(item) for item in market_listings]
    def __load_market_listings(self, appid: int | str = 3017120, start: int = 0, max_items_load: int = 1000) -> list:
        search_params = {
            'start': start,
            'count': 100,
            'search_descriptions': 0,
            'sort_column': 'popular',
            'sort_dir': 'desc',
            'appid': appid,
            'norender': 1,
        }
        search_url = "https://steamcommunity.com/market/search/render/"
        market_items = []
        max_attempts = 2
        max_items_load = max_items_load

        for attempt in range(max_attempts):
            try:
                market_response = self.account.session.get(search_url, params=search_params, timeout=10)
                if market_response.ok:
                    response_data = market_response.json()
                    if response_data.get('success', False):
                        market_items.extend(response_data.get('results', []))
                        total_items_available = response_data.get('total_count', 0)
                        new_start = start + 100
                        if total_items_available > new_start and new_start < max_items_load:
                            market_items.extend(self.__load_market_listings(appid, new_start, max_items_load))
                        return market_items
            except:
                pass
            time.sleep(5)

        return market_items


    def fetch_item_nameid(self, market_hash_name: str, appid: int = 3017120) -> int | None:
        saved_item_nameid = sql_manager.item_nameid_get(appid=appid, market_hash_name=market_hash_name)
        if saved_item_nameid: return saved_item_nameid

        item_nameid = self.__load_item_nameid(market_hash_name=market_hash_name, appid=appid)
        if not item_nameid: return None

        sql_manager.item_nameid_save(appid=appid, market_hash_name=market_hash_name, nameid=item_nameid)
        return item_nameid
    def __load_item_nameid(self, market_hash_name: str, appid: int = 3017120) -> int | None:
        if not market_hash_name or not appid: return None
        if not self.account or not self.account.is_alive_session(): return None

        encoded_market_hash_name = urllib.parse.quote(market_hash_name)
        url = f"https://steamcommunity.com/market/listings/{appid}/{encoded_market_hash_name}"
        try:
            response = self.account.session.get(url, timeout=10)
            if response.ok:
                _match = re.search(r'\bMarket_LoadOrderSpread\(\s*(\d+)\s*\);', response.text)
                if not _match:
                    _match = re.search(r'\bItemActivityTicker\.Start\(\s*(\d+)\s*\);', response.text)
                if _match:
                    item_nameid = int(_match.group(1))
                    return item_nameid
            return None
        except Exception as e:
            print(f"Error fetching market item ID: {e}")
            return None

    def fetch_market_itemordershistogram(self, market_hash_name: str, appid: int = 3017120) -> ItemOrdersHistogram | None:
        if not self.account or not self.account.is_alive_session(): return None
        item_nameid = self.fetch_item_nameid(market_hash_name=market_hash_name, appid=appid)
        self.account.load_wallet_info()
        country = self.account.wallet_country
        currency = self.account.wallet_currency
        json_itemordershistogram = self.__load_market_itemordershistogram(country=country, currency=currency, item_nameid=item_nameid)
        if not json_itemordershistogram: return
        class_itemordershistogram = ItemOrdersHistogram(json_itemordershistogram)
        if not class_itemordershistogram.is_successful(): return
        return class_itemordershistogram
    def __load_market_itemordershistogram(self, country='KZ', language='english', currency=37, item_nameid=None) -> dict | None:
        if not item_nameid: return None
        url = f"https://steamcommunity.com/market/itemordershistogram"
        params = {'country': country, 'language': language, 'currency': currency, 'item_nameid': item_nameid}
        market_info = self.account.session.get(f"{url}?{urllib.parse.urlencode(params)}", timeout=10)
        return market_info.json() if market_info.ok else None


    def sell_item(self, item: InventoryItem, amount: int | str = 1, price: int | str = 0) -> dict | None:
        if not item or not amount or not price: return
        return self._start_market_sellitem(appid=item.appid, contextid=item.contextid, assetid=item.assetid, amount=amount, price=price)
    def _start_market_sellitem(self, appid: int | str = 3017120, contextid: int | str = 2, assetid: int | str = 0, amount: int | str = 1, price: int | str = 0) -> dict | None:
        if not self.account or not self.account.is_alive_session(): return
        sessionid = self.fetch_session_id()
        if not assetid or not sessionid: return None
        url = 'https://steamcommunity.com/market/sellitem/'
        params = {'sessionid': sessionid, 'appid': appid, 'contextid': contextid, 'assetid': assetid, 'amount': amount, 'price': price}
        headers = {
            "accept": "*/*",
            "accept-language": "ru,en;q=0.9",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "Referer": f"https://steamcommunity.com/profiles/{self.account.steam_id}/inventory",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
        }
        market_info = self.account.session.post(url=url, timeout=10, headers=headers, data=params)
        return market_info.json() if market_info.ok else None


class InventoryManager:
    def __init__(self, items: dict, context_id=2):
        self.data_json = items
        self.descriptions: list = items.get('descriptions', []) or [description for name, description in items.get('rgDescriptions', {}).items()]
        self.assets: list = items.get('assets', []) or [asset for name, asset in items.get('rgInventory', {}).items()]
        self.success: bool = bool(items.get('success', False))

        self.inventory: list[InventoryItemRgDescriptions] = []
        self.context_id = context_id
        self.parse_inventory()

    def add_next_invent(self, next_invent: InventoryManager):
        if not isinstance(next_invent, InventoryManager): return
        self.assets.extend(next_invent.assets)
        for des in next_invent.descriptions:
            classid = des.get('classid', 0)
            instanceid = des.get('instanceid', 0)
            if any((des_d.get('classid', 0) == classid and des_d.get('instanceid', 0) == instanceid) for des_d in self.descriptions if des):
                continue
            self.descriptions.append(des)
        self.parse_inventory()

    def parse_inventory(self):
        inventory: list = self.descriptions

        for item in inventory:
            classid = item.get('classid', 0)
            if classid == 0: continue
            instanceid = item.get('instanceid', 0)
            item['items'] = [
                item_d for item_d in self.assets if item_d.get('classid', 0) == classid and item_d.get('instanceid', 0) == instanceid
            ]
        self.inventory = [InventoryItemRgDescriptions(item) for item in inventory]

    def get_tradable_inventory(self) -> list[InventoryItemRgDescriptions]:
        return [item for item in self.inventory if item.tradable]

    def get_amount_items(self, only_tradable=True) -> int:
        inventory = self.get_tradable_inventory() if only_tradable else self.inventory
        return sum([item.get_amount() for item in inventory])


class ItemDescription:
    def __init__(self, description_dict: dict = None):
        if not description_dict: description_dict = {}
        self.type = description_dict.get('type', '')
        self.value = description_dict.get('value', '')
class InventoryItemTag:
    def __init__(self, tag_dict: dict = None):
        if not tag_dict: tag_dict = {}
        self.category = tag_dict.get('category', '')
        self.internal_name = tag_dict.get('internal_name', '')
        self.category_name = tag_dict.get('category_name', '')
        self.name = tag_dict.get('name', '')
class InventoryItem:
    def __init__(self, item_dict: dict = None):
        if not item_dict: item_dict = {}
        self.data_json = item_dict
        self.appid = item_dict.get('appid', 0)
        self.contextid = item_dict.get('contextid', 2)
        self.assetid = item_dict.get('assetid', '') or item_dict.get('id', '')
        self.classid = item_dict.get('classid', '')
        self.instanceid = item_dict.get('instanceid', '')
        self.amount = int(item_dict.get('amount', 0))
        self.hide_in_china = item_dict.get('hide_in_china', 0)
        self.pos = item_dict.get('pos', 0)
    def __repr__(self):
        return f'<classid: {self.classid}, instanceid: {self.instanceid}, amount: {self.amount}, pos: {self.pos}>'
    def __str__(self):
        return f'<classid: {self.classid}, instanceid: {self.instanceid}, amount: {self.amount}, pos: {self.pos}>'
class InventoryItemRgDescriptions:
    def __init__(self, rg_dict: dict = None):
        if not rg_dict: rg_dict = {}
        self.data_json = rg_dict
        self.appid = rg_dict.get('appid', '')
        self.classid = rg_dict.get('classid', '')
        self.instanceid = rg_dict.get('instanceid', '')
        self.currency = rg_dict.get('currency', 0)
        self.background_color = rg_dict.get('background_color', '')
        self.icon_url = rg_dict.get('icon_url', '')
        self.icon_url_large = rg_dict.get('icon_url_large', '')
        self.descriptions = [ItemDescription(d) for d in rg_dict.get('descriptions', [])]
        self.tradable = rg_dict.get('tradable', 0)
        self.name = rg_dict.get('name', '')
        self.name_color = rg_dict.get('name_color', '')
        self.type = rg_dict.get('type', '')
        self.market_name = rg_dict.get('market_name', '')
        self.market_hash_name = rg_dict.get('market_hash_name', '')
        self.commodity = rg_dict.get('commodity', 0)
        self.market_tradable_restriction = rg_dict.get('market_tradable_restriction', '')
        self.market_marketable_restriction = rg_dict.get('market_marketable_restriction', '')
        self.marketable = rg_dict.get('marketable', 0)
        self.tags = [InventoryItemTag(t) for t in rg_dict.get('tags', [])]
        self.items = [InventoryItem(i) for i in rg_dict.get('items', [])]
        for item in self.items:
            item.appid = self.appid

        self.icon_drag_url = rg_dict.get('icon_drag_url', '')
        self.cache_expiration = rg_dict.get('cache_expiration', '')
        self.owner_descriptions = [ItemDescription(d) for d in rg_dict.get('owner_descriptions', [])]
    def __extract_date_from_owner_descriptions(self):
        if not self.owner_descriptions: return None
        date_pattern = re.compile(r'\[date\](\d+)\[/date\]')
        for desc in self.owner_descriptions:
            if not desc.value.strip(): continue

            if "GMT" in desc.value:
                return desc.value

            match = date_pattern.search(desc.value)
            if match:
                timestamp = int(match.group(1))
                return datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)

            try:
                match = re.search(r"(\d{2})\s(\w+)\s(\d{4})\s\((\d{1,2}:\d{2}:\d{2})\)", desc.value)
                if match:
                    day, month_str, year, _time = match.groups()
                    months = {
                        "янв": "Jan", "фев": "Feb", "мар": "Mar", "апр": "Apr", "май": "May", "июн": "Jun",
                        "июл": "Jul", "авг": "Aug", "сен": "Sep", "окт": "Oct", "ноя": "Nov", "дек": "Dec"
                    }
                    month_static = month_str.lower()[:3]
                    month = months.get(month_static, month_static)
                    date_str = f"{day} {month} {year} {_time} GMT"
                    return datetime.datetime.strptime(date_str, "%d %b %Y %H:%M:%S %Z")
            except:
                pass
        return None
    def get_color(self):
        if not self.name_color: return ''
        clear_color = self.name_color.replace('#', '')
        return f'#{clear_color}'
    def get_amount(self):
        amount = sum([int(i.amount) for i in self.items])
        return amount if amount > 0 else 0
    def get_market_url(self) -> str | None:
        if not self.market_hash_name: return
        return f'https://steamcommunity.com/market/listings/{self.appid}/{self.market_hash_name}'
    def get_icon_url(self, width: int = 64, height: int = 64) -> str | None:
        if not self.icon_url: return None
        return f'https://community.akamai.steamstatic.com/economy/image/{self.icon_url}/{width}x{height}?allow_animated=1'
    def end_ban_marketable(self):
        return self.__extract_date_from_owner_descriptions()
    def is_tradable(self):
        return bool(self.tradable)
    def is_marketable(self):
        return bool(self.marketable)
    def is_current_app_id(self, app_id: int | str):
        return str(self.appid) == str(app_id)
    def get_item_id(self) -> str:
        return f'{self.classid}_{self.instanceid}'

    def get_amount_items(self, amount: int):
        return_class = InventoryItemRgDescriptions(self.data_json)
        return_class.items = copy.deepcopy(self.items)
        for item in return_class.items:
            if item.amount <= 0 or amount <= 0:
                item.amount = 0
                continue
            if item.amount >= amount:
                item.amount = amount
                amount = 0
            else:
                amount -= item.amount
        return return_class
    def add_items(self, item_class: 'InventoryItemRgDescriptions'):
        if not item_class: return
        if item_class.instanceid != self.instanceid or item_class.classid != self.classid: return
        for item in item_class.items:
            original_item = next((i for i in self.items if i.assetid == item.assetid), None)
            if not original_item:
                self.items.append(item)
            else:
                original_item.amount += item.amount
    def remove_items(self, item_class: 'InventoryItemRgDescriptions'):
        if not item_class: return
        if item_class.instanceid != self.instanceid or item_class.classid != self.classid: return
        for item in item_class.items:
            original_item = next((i for i in self.items if i.assetid == item.assetid), None)
            if not original_item: continue
            original_item.amount -= item.amount
    def __repr__(self):
        return f'<classid: {self.classid}, instanceid: {self.instanceid}, market_hash_name: {self.market_hash_name}, amount: {self.get_amount()}>'
    def __str__(self):
        return f'<classid: {self.classid}, instanceid: {self.instanceid}, market_hash_name: {self.market_hash_name}, amount: {self.get_amount()}>'


class MarketAssetDescription:
    def __init__(self, asset_description_dict: dict):
        if not asset_description_dict: asset_description_dict = {}
        self.data_json = asset_description_dict

        self.appid = asset_description_dict.get('appid')
        self.classid = asset_description_dict.get('classid')
        self.instanceid = asset_description_dict.get('instanceid')
        self.name = asset_description_dict.get('name')
        self.name_color = asset_description_dict.get('name_color', '')
        self.market_name = asset_description_dict.get('market_name')
        self.market_hash_name = asset_description_dict.get('market_hash_name')

        self.tradable = bool(asset_description_dict.get('tradable', False))
        self.marketable = bool(asset_description_dict.get('marketable', False))
        self.commodity = bool(asset_description_dict.get('commodity', False))

        self.market_tradable_restriction = asset_description_dict.get('market_tradable_restriction', -1)
        self.market_marketable_restriction = asset_description_dict.get('market_marketable_restriction', -1)

        self.icon_url = asset_description_dict.get('icon_url')
        self.icon_url_large = asset_description_dict.get('icon_url_large')

        self.currency = asset_description_dict.get('currency')
        self.descriptions = [ItemDescription(d) for d in asset_description_dict.get('descriptions', [])]
        self.type = asset_description_dict.get('type', "")
        self.background_color = asset_description_dict.get('background_color', "")
class MarketListenItem:
    def __init__(self, item_dict: dict = None):
        if not item_dict: item_dict = {}
        self.data_json = item_dict
        self.name = item_dict.get('name', ' ')
        self.hash_name = item_dict.get('hash_name', '')

        self.sell_listings = item_dict.get('sell_listings', 0)
        self.sell_price = item_dict.get('sell_price', 0)
        self.sell_price_text = item_dict.get('sell_price_text', '')
        self.sale_price_text = item_dict.get('sale_price_text', '')

        self.asset_description = MarketAssetDescription(item_dict.get('asset_description', {}))

        self.app_name = item_dict.get('app_name')
        self.app_icon = item_dict.get('app_icon')
    def __repr__(self):
        return f'<{self.__class__.__name__}> name: {self.name}, price: {self.sell_price_text}, listings: {self.sell_price}'
    def is_bug_item(self) -> bool:
        return self.hash_name != self.asset_description.market_hash_name
    def is_empty(self) -> bool:
        return self.hash_name == ''
    def is_for_current_game(self, app_id: int) -> bool:
        return str(self.asset_description.appid) == str(app_id)

    def get_icon_url(self) -> str:
        if not self.asset_description.icon_url: return ''
        return f'https://community.akamai.steamstatic.com/economy/image/{self.asset_description.icon_url}/330x192?allow_animated=1'
    def get_market_url(self) -> str:
        if not self.asset_description or not self.asset_description.appid or not self.asset_description.market_hash_name: return ''
        return f'https://steamcommunity.com/market/listings/{self.asset_description.appid}/{self.asset_description.market_hash_name}'
    def get_market_hash_name(self) -> str:
        return self.asset_description.market_hash_name
    def get_color(self) -> str:
        return f'#{self.asset_description.name_color.replace("#", "")}' if self.asset_description.name_color else ''

    def replace_currency_number(self, new_number: str) -> str:
        return re.sub(r'\d{1,3}(?:\s?\d{3})*(?:[,.]\d+)?', new_number, self.sell_price_text)
    def format_currency_number(self, new_number: float) -> str:
        return self.replace_currency_number(f"{round(new_number / 100, 2):.2f}")
    def multiply_price_by(self, count: int) -> str:
        return self.format_currency_number(self.sell_price * count)
    def calculate_commission(self, price: int = None) -> str:
        return self.format_currency_number(self.calculate_commission_amount(price))
    def calculate_commission_amount(self, price: int = None) -> int | float:
        if not price: price = self.sell_price
        commission = abs(price - (price / 115 * 100))
        return price - commission


class ItemOrdersHistogramOrderGraph:
    def __init__(self, data_json: list = None):
        if not data_json: data_json = []
        self.data_json = data_json
    def get_max_price(self):
        if self.data_json: return max(order[0] for order in self.data_json)
        return 0
    def get_min_price(self):
        if self.data_json: return min(order[0] for order in self.data_json)
        return 0
class ItemOrdersHistogram:
    def __init__(self, data_json: dict = None):
        if not data_json: data_json = {}
        self.data_json = data_json
        self.success = bool(data_json.get('success', 0))
        self.sell_order_table = data_json.get('sell_order_table', '')
        self.sell_order_summary = data_json.get('sell_order_summary', '')
        self.buy_order_table = data_json.get('buy_order_table', '')
        self.buy_order_summary = data_json.get('buy_order_summary', '')
        self.highest_buy_order = data_json.get('highest_buy_order', '')
        self.lowest_sell_order = data_json.get('lowest_sell_order', '')
        self.buy_order_graph = ItemOrdersHistogramOrderGraph(data_json.get('buy_order_graph', []))
        self.sell_order_graph = ItemOrdersHistogramOrderGraph(data_json.get('sell_order_graph', []))
        self.graph_max_y = data_json.get('graph_max_y', 0)
        self.graph_min_x = data_json.get('graph_min_x', 0.0)
        self.graph_max_x = data_json.get('graph_max_x', 0.0)
        self.price_prefix = data_json.get('price_prefix', '')
        self.price_suffix = data_json.get('price_suffix', '')
    def is_successful(self):
        return self.success

    def get_highest_buy_order(self) -> float:
        return float(self.buy_order_graph.get_max_price()) if self.buy_order_graph else 0
    def get_highest_buy_order_by_amount(self, amount: int) -> float:
        return float(self.buy_order_graph.get_max_price() * amount) if self.buy_order_graph else 0
    def get_highest_buy_order_str(self) -> str:
        return f'{self.price_prefix}{f"{self.get_highest_buy_order():.2f}"}{self.price_suffix}'
    def get_highest_buy_order_str_by_amount(self, amount: int) -> str:
        return f'{self.price_prefix}{f"{self.get_highest_buy_order_by_amount(amount=amount):.2f}"}{self.price_suffix}'

    def get_lowest_sell_order(self) -> float:
        return float(self.sell_order_graph.get_min_price()) if self.sell_order_graph else 0
    def get_lowest_sell_order_by_amount(self, amount: int) -> float:
        return float(self.sell_order_graph.get_min_price() * amount) if self.sell_order_graph else 0
    def get_lowest_sell_order_str(self) -> str:
        return f'{self.price_prefix}{f"{self.get_lowest_sell_order():.2f}"}{self.price_suffix}'
    def get_lowest_sell_order_str_by_amount(self, amount: int) -> str:
        return f'{self.price_prefix}{f"{self.get_lowest_sell_order_by_amount(amount=amount):.2f}"}{self.price_suffix}'
