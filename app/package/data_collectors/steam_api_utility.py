from __future__ import annotations
import re
import copy
import json
import time
import datetime
import urllib.parse
from enum import Enum

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


    def combine_itemstacks(self, fromitem: InventoryItem, destitem: InventoryItem) -> str | None:
        if not fromitem or not destitem: return
        if fromitem.appid != destitem.appid: return
        if fromitem.assetid == destitem.assetid: return
        fromitemid = fromitem.assetid
        destitemid = destitem.assetid
        quantity = fromitem.amount
        return self._start_stack_items(appid=fromitem.appid, fromitemid=fromitemid, destitemid=destitemid, quantity=quantity)
    def _start_stack_items(self, appid: int | str, fromitemid: int | str, destitemid: int | str, quantity: int | str):
        if not self.account or not self.account.is_alive_session(): return
        access_token = self.account.get_steam_web_token()
        if not access_token: return
        steam_id = self.account.steam_id
        try:
            url = 'https://api.steampowered.com/IInventoryService/CombineItemStacks/v1/'
            data = {
                'access_token': access_token,
                'appid': appid,
                'fromitemid': fromitemid,
                'destitemid': destitemid,
                'quantity': quantity,
                'steamid': steam_id,
            }
            response = self.account.session.post(url, data=data, timeout=10)
            return response
        except:
            return None


    def fetch_my_listings(self) -> MarketListingsManager | None:
        return self.__load_mylistings()
    def __load_mylistings(self, start: int = 0, count: int = 100) -> MarketListingsManager | None:
        if not self.account or not self.account.is_alive_session(): return None
        def_url = f'https://steamcommunity.com/market/mylistings'
        def_params = {
            'norender': 1,
            'start': start,
            'count': count,
        }
        try:
            req = self.account.session.get(url=def_url, params=def_params, timeout=10)
            if not req.ok: return None
            req_json = req.json()
            if not req_json.get('success', False): return None

            listings = MarketListingsManager(req_json)
            next_page_start = listings.get_next_page_start()
            if next_page_start is not None:
                next_listings = self.__load_mylistings(start=next_page_start, count=count)
                listings.add_next_page(next_listings)
            return listings
        except:
            time.sleep(5)
        return None

    def remove_my_listing(self, item: MarketListingsListing) -> bool:
        if not item or not item.listingid: return False
        return self.__start_remove_my_listing(item.listingid)
    def __start_remove_my_listing(self, listingid: str | int) -> bool:
        if not self.account or not self.account.is_alive_session(): return False
        sessionid = self.fetch_session_id()
        if not sessionid: return False
        try:
            url = f'https://steamcommunity.com/market/removelisting/{listingid}'
            params = {
                "sessionid": sessionid
            }
            headers = {
                "Origin": f"https://steamcommunity.com",
                "Referer": f"https://steamcommunity.com/market/",
            }
            market_info = self.account.session.post(url=url, timeout=10, headers=headers, data=params)
            return market_info.ok
        except:
            return False
    
    def fetch_market_myhistory(self, amount: int = 500):
        return self.__load_market_history(fetch_amount=amount)
    def __load_market_history(self, fetch_amount: int = 500, start: int = 0, count: int = 500):
        if not self.account or not self.account.is_alive_session(): return False
        def_url = f'https://steamcommunity.com/market/myhistory/render/'
        def_params = {
            'query': None,
            'norender': 1,
            'start': start,
            'count': count,
        }
        try:
            req = self.account.session.get(url=def_url, params=def_params, timeout=10)
            if not req.ok: return None
            req_json = req.json()
            if not req_json.get('success', False): return None
            history = MarketMyHistoryManager(req_json)
            next_page_start = history.get_next_page_start(max_count=fetch_amount)
            if next_page_start is not None:
                next_listings = self.__load_market_history(fetch_amount=fetch_amount, start=next_page_start, count=count)
                history.add_next_page(next_listings)
            return history
        except:
            time.sleep(5)
        return None


class ItemDescription:
    def __init__(self, description_dict: dict = None):
        if not description_dict: description_dict = {}
        self.type = description_dict.get('type', '')
        self.value = description_dict.get('value', '')
    def __repr__(self):
        return f"ItemDescription: type={self.type}, value={self.value}"
    def __str__(self):
        return f"ItemDescription: type={self.type}, value={self.value}"


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
        return [item for item in self.inventory if item.is_tradable()]

    def get_marketable_inventory(self) -> list[InventoryItemRgDescriptions]:
        return [item for item in self.inventory if item.is_marketable()]

    def get_amount_items(self, only_tradable=True) -> int:
        inventory = self.get_tradable_inventory() if only_tradable else self.inventory
        return sum([item.get_amount() for item in inventory])

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
    def get_items_amount(self) -> int:
        return len(self.items)
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
    def is_for_current_game(self, app_id: int | str) -> bool:
        return str(self.asset_description.appid) == str(app_id)

    def get_icon_url(self) -> str:
        if not self.asset_description.icon_url: return ' '
        return f'https://community.akamai.steamstatic.com/economy/image/{self.asset_description.icon_url}/330x192?allow_animated=1'
    def get_market_url(self) -> str:
        if not self.asset_description or not self.asset_description.appid or not self.asset_description.market_hash_name: return ''
        return f'https://steamcommunity.com/market/listings/{self.asset_description.appid}/{self.asset_description.market_hash_name}'
    def get_market_hash_name(self) -> str:
        return self.asset_description.market_hash_name
    def get_color(self) -> str:
        return f'#{self.asset_description.name_color.replace("#", "")}' if self.asset_description.name_color else ''

    def replace_currency_number(self, new_number: str) -> str:
        return re.sub(r'\d(?:\s?\d)*(?:[.,]\d+)?', new_number, self.sell_price_text)
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
        return max(order[0] for order in self.data_json) if self.data_json else 0
    def get_min_price(self):
        return min(order[0] for order in self.data_json) if self.data_json else 0
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


class MarketListingsManager:
    def __init__(self, data_json: dict = None):
        if not data_json: data_json = {}
        self.data_json = data_json
        self.success: bool = bool(data_json.get('success', 0))
        self.start: int = data_json.get('start', 0)
        self.pagesize: int = data_json.get('pagesize', 0)
        self.total_count: int = data_json.get('total_count', 0)
        self.num_active_listings: int = data_json.get('num_active_listings', 0)

        self.assets: dict[str, MarketListingsAsset] = self.__parce_assets(data_json.get('assets', {}))
        self.listings: list[MarketListingsListing] = self.__parce_listings(data_json.get('listings', []))
        self.listings_on_hold: list[MarketListingsListing] = self.__parce_listings(data_json.get('listings_on_hold', []))
        self.listings_to_confirm: list[MarketListingsListing] = self.__parce_listings(data_json.get('listings_to_confirm', []))
        self.buy_orders: list = [MarketListingsBuyOrder(listing) for listing in data_json.get('buy_orders', [])]
    def __str__(self):
        return f"MarketListingsManager: assets={len(self.assets)}, listings={len(self.listings)}, on_hold={len(self.listings_on_hold)}, to_confirm={len(self.listings_to_confirm)}, buy_orders={len(self.buy_orders)}"
    def __repr__(self):
        return f"MarketListingsManager: assets={len(self.assets)}, listings={len(self.listings)}, on_hold={len(self.listings_on_hold)}, to_confirm={len(self.listings_to_confirm)}, buy_orders={len(self.buy_orders)}"
    def __parce_listings(self, data_json: list) -> list[MarketListingsListing]:
        if not data_json: data_json = []
        listings = []

        for listing in data_json:
            class_listing = MarketListingsListing(listing)
            class_listing.asset_master = self.assets.get(class_listing.get_asset_master_id(), None)
            listings.append(class_listing)

        return listings
    def __parce_assets(self, data_json: dict) -> dict[str, MarketListingsAsset]:
        if not data_json: data_json = {}
        assets = {}

        for app_id, app_data in data_json.items():
            for contextid, context_data in app_data.items():
                for asset_id, asset_data in context_data.items():
                    assets[f'{app_id}_{contextid}_{asset_id}'] = MarketListingsAsset(asset_data)

        return assets

    def get_next_page_start(self) -> int | None:
        if not self.success: return None
        next_page = self.start + self.pagesize
        if next_page >= self.total_count: return None
        return next_page

    def add_next_page(self, next_page: MarketListingsManager):
        if not next_page or not next_page.success: return

        self.assets.update(next_page.assets)
        self.listings.extend(next_page.listings)
        self.listings_on_hold.extend(next_page.listings_on_hold)
        self.listings_to_confirm.extend(next_page.listings_to_confirm)
        self.buy_orders.extend(next_page.buy_orders)

        return self

class MarketListingsBuyOrderDescription:
    def __init__(self, data_json: dict = None):
        if not data_json: data_json = {}
        self.data_json = data_json

        self.appid = data_json.get('appid', 0)

        self.classid = data_json.get('classid', '')
        self.instanceid = data_json.get('instanceid', '')

        self.name = data_json.get('name', '')
        self.name_color = data_json.get('name_color', '')
        self.market_name = data_json.get('market_name', '')
        self.market_hash_name = data_json.get('market_hash_name', '')
        self.icon_url = data_json.get('icon_url', '')
        self.icon_url_large = data_json.get('icon_url_large', '')
        self.background_color = data_json.get('background_color', '')

        self.commodity = data_json.get('commodity', 0)
        self.tradable = data_json.get('tradable', 0)
        self.marketable = data_json.get('marketable', 0)

        self.currency = data_json.get('currency', 0)
        self.descriptions = data_json.get('descriptions', [])
        self.actions = data_json.get('actions', [])
        self.owner_descriptions = data_json.get('owner_descriptions', [])
        self.owner_actions = data_json.get('owner_actions', [])
        self.fraudwarnings = data_json.get('fraudwarnings', [])
        self.type = data_json.get('type', '')
        self.market_fee = data_json.get('market_fee')
        self.market_fee_app = data_json.get('market_fee_app')
        self.contained_item = data_json.get('contained_item')
        self.market_actions = data_json.get('market_actions', [])
        self.market_tradable_restriction = data_json.get('market_tradable_restriction', 0)
        self.market_marketable_restriction = data_json.get('market_marketable_restriction', 0)
        self.tags = data_json.get('tags', [])
        self.item_expiration = data_json.get('item_expiration')
        self.market_buy_country_restriction = data_json.get('market_buy_country_restriction')
        self.market_sell_country_restriction = data_json.get('market_sell_country_restriction')
        self.sealed = data_json.get('sealed')
    def __str__(self):
        return f"MarketListingsBuyOrderDescription(appid={self.appid}, name='{self.name}')"
    def __repr__(self):
        return self.__str__()
class MarketListingsBuyOrder:
    def __init__(self, data_json: dict = None):
        if not data_json:
            data_json = {}
        self.data_json = data_json

        self.appid = data_json.get('appid', 0)

        self.hash_name = data_json.get('hash_name', '')
        self.price = data_json.get('price', '0')
        self.quantity = data_json.get('quantity', '0')
        self.quantity_remaining = data_json.get('quantity_remaining', '0')

        self.wallet_currency = data_json.get('wallet_currency', 0)
        self.buy_orderid = data_json.get('buy_orderid', '')
        self.description = MarketListingsBuyOrderDescription(data_json.get('description', {}))

    def __str__(self):
        return (f"MarketListingsBuyOrder(appid={self.appid}, hash_name='{self.hash_name}', "
                f"price={self.price}, quantity={self.quantity}, buy_orderid='{self.buy_orderid}')")
    def __repr__(self):
        return self.__str__()

class MarketListingsListing:
    def __init__(self, data_json: dict = None):
        if not data_json:
            data_json = {}
        self.data_json = data_json

        self.listingid = data_json.get('listingid', '')                             # str: '5175294578385203531'
        self.active = data_json.get('active', 0)                                    # int: 1 (1 - активен, 0 - неактивен)
        self.status = data_json.get('status', 0)                                    # int: 2 (статус листинга)
        self.cancel_reason = data_json.get('cancel_reason', 0)                      # int: 0 (причина отмены)
        self.item_expired = data_json.get('item_expired', 0)                        # int: 0 (признак истечения)
        self.steamid_lister = data_json.get('steamid_lister', '')                   # str: '76561198061407679'

        self.asset = MarketListingsAsset(data_json.get('asset', {}))                # MarketListingsAsset
        self.asset_master = None

        self.time_created = data_json.get('time_created', 0)                        # int: 1733341062
        self.time_created_str = data_json.get('time_created_str', '')               # str: '4 дек'
        self.time_finish_hold = data_json.get('time_finish_hold', 0)                # int: 0

        self.currencyid = data_json.get('currencyid', '')                           # str: '2037'
        self.converted_currencyid = data_json.get('converted_currencyid', '')       # str: '2037'

        self.original_amount_listed = data_json.get('original_amount_listed', 0)                        # int: 3

        self.price = data_json.get('price', 0)                                                          # int: 2892 (цена в сотых долях)
        self.original_price = data_json.get('original_price', 0)                                        # int: 4338
        self.original_price_per_unit = data_json.get('original_price_per_unit', 0)                      # int: 1446
        self.converted_price = data_json.get('converted_price', 0)                                      # int: 2892
        self.converted_price_per_unit = data_json.get('converted_price_per_unit', 0)                    # int: 1446

        self.publisher_fee_app = data_json.get('publisher_fee_app', 0)                                  # int: 3037410
        self.publisher_fee_percent = data_json.get('publisher_fee_percent', '0.0')                      # str: '0.100000001490116119'

        self.publisher_fee = data_json.get('publisher_fee', 0)                                          # int: 289
        self.publisher_fee_per_unit = data_json.get('publisher_fee_per_unit', 0)                        # int: 144
        self.converted_publisher_fee = data_json.get('converted_publisher_fee', 0)                      # int: 289
        self.converted_publisher_fee_per_unit = data_json.get('converted_publisher_fee_per_unit', 0)    # int: 144

        self.fee = data_json.get('fee', 0)                                                              # int: 433 (комиссия в сотых долях)
        self.fee_per_unit = data_json.get('fee_per_unit', 0)                                            # int: 216
        self.converted_fee = data_json.get('converted_fee', 0)                                          # int: 433
        self.converted_fee_per_unit = data_json.get('converted_fee_per_unit', 0)                        # int: 216

        self.steam_fee = data_json.get('steam_fee', 0)                                                  # int: 144
        self.steam_fee_per_unit = data_json.get('steam_fee_per_unit', 0)                                # int: 72
        self.converted_steam_fee = data_json.get('converted_steam_fee', 0)                              # int: 144
        self.converted_steam_fee_per_unit = data_json.get('converted_steam_fee_per_unit', 0)            # int: 72

    def __str__(self):
        return (
            f"Listing ID: {self.listingid}, Name: {self.asset.name}, "
            f"Price: {self.price / 100:.2f}, Status: {self.status}, Active: {self.active}, "
            f"Time Created: {self.time_created_str}"
        )
    def __repr__(self):
        return self.__str__()
    def get_app_class(self):
        asset = self.asset_master if self.asset_master else self.asset
        return MarketListingsApp(app_icon=asset.app_icon, appid=int(asset.appid))
    def get_amount_class(self) -> MarketListingsAmount:
        return MarketListingsAmount(self.asset)
    def get_item_class(self) -> MarketListingsItem:
        return MarketListingsItem(self.asset_master if self.asset_master else self.asset)
    def get_price_class(self) -> MarketListingsPrice:
        return MarketListingsPrice(self)
    def get_datetime_create(self) -> datetime.datetime:
        if not self.time_created: return datetime.datetime.min
        return datetime.datetime.fromtimestamp(self.time_created)
    def get_asset_master_id(self):
        return f"{self.asset.appid}_{self.asset.contextid}_{self.asset.id}"
class MarketListingsApp:
    def __init__(self, app_icon: str, appid: int):
        self.app_icon = app_icon
        self.appid = appid
    def get_steam_store_url(self) -> str:
        return f'https://store.steampowered.com/app/{self.appid}'
    def get_icon_url(self) -> str:
        return self.app_icon if self.app_icon else " "
class MarketListingsAmount:
    def __init__(self, accet: MarketListingsAsset):
        self.amount: int = int(accet.amount) if accet.amount else 0
        self.original_amount: int = int(accet.original_amount) if accet.original_amount else 0
    def get_amount_start(self) -> int:
        return self.original_amount

    def get_amount(self) -> int:
        return self.amount
    def get_amount_percent(self) -> float:
        if not self.original_amount: return 0
        return self.amount / self.original_amount
    def get_amount_percent_str(self) -> str:
        return f'{self.get_amount_percent()*100:.2f}%'

    def get_sell_amount(self) -> int:
        return self.original_amount - self.amount
    def get_sell_percent(self) -> float:
        if not self.original_amount: return 0
        return self.get_sell_amount() / self.original_amount
    def get_sell_percent_str(self) -> str:
        return f'{self.get_sell_percent()*100:.2f}%'

    def get_total(self, prefix: str = '', suffix: str = '') -> str:
        if self.amount == self.original_amount:
            return f'{prefix}{self.amount}{suffix}'
        return f'{prefix}{self.amount} <- {self.original_amount} (Sold: {self.get_sell_amount()}, {self.get_sell_percent_str()}){suffix}'
class MarketListingsPrice:
    def __init__(self, listing: MarketListingsListing):
        amount = listing.get_amount_class()
        self.amount = amount.get_amount()
        self.start_amount = amount.get_amount_start()

        self.fee = listing.fee
        self.per_unit_fee = listing.fee_per_unit

        self.price_per_unit_net = listing.original_price_per_unit
        self.price_per_unit = self.price_per_unit_net + self.per_unit_fee

        self.price_net = listing.price
        self.price = self.price_net + self.fee

        self.start_price_net = listing.original_price
        self.start_price = self.start_price_net + (self.per_unit_fee * self.start_amount)

    def get_price_per_unut(self, is_str: bool=False, prefix: str='', suffix: str='') -> str | float:
        price = self.price_per_unit * 0.01
        return f"{prefix}{price:.2f}{suffix}" if is_str else round(price, 2)
    def get_price_per_unut_net(self, is_str: bool=False, prefix: str='', suffix: str='') -> str | float:
        price = self.price_per_unit_net * 0.01
        return f"{prefix}{price:.2f}{suffix}" if is_str else round(price, 2)

    def get_now_price(self, is_str: bool=False, prefix: str='', suffix: str='') -> str | float:
        price = self.price * 0.01
        return f"{prefix}{price:.2f}{suffix}" if is_str else round(price, 2)
    def get_now_price_net(self, is_str: bool=False, prefix: str='', suffix: str='') -> str | float:
        price = self.price_net * 0.01
        return f"{prefix}{price:.2f}{suffix}" if is_str else round(price, 2)

    def get_start_price(self, is_str: bool=False, prefix: str='', suffix: str='') -> str | float:
        price = self.start_price * 0.01
        return f"{prefix}{price:.2f}{suffix}" if is_str else round(price, 2)
    def get_start_price_net(self, is_str: bool=False, prefix: str='', suffix: str='') -> str | float:
        price = self.start_price_net * 0.01
        return f"{prefix}{price:.2f}{suffix}" if is_str else round(price, 2)

    def get_total(self, prefix: str = '', suffix: str = '') -> str:
        price_per_unit_str = f'{self.get_price_per_unut()}({self.get_price_per_unut_net()})'
        start_price_str = f'{self.get_start_price()}({self.get_start_price_net()})' if self.amount != self.start_amount else ''
        now_price_str = f'{self.get_now_price()}({self.get_now_price_net()})' if self.start_amount != 1 else ''

        price_details = " <- ".join(filter(None, [now_price_str, start_price_str]))
        return f'{prefix} {price_per_unit_str} {price_details} {suffix}'.replace('  ', ' ').strip()
class MarketListingsItem:
    def __init__(self, accet: MarketListingsAsset):
        self.appid = accet.appid
        self.app_icon = accet.app_icon

        self.id = accet.id
        self.classid = accet.classid
        self.instanceid = accet.instanceid
        self.contextid = accet.contextid

        self.icon_url = accet.icon_url
        self.icon_url_large = accet.icon_url_large

        self.market_hash_name = accet.market_hash_name
        self.market_name = accet.market_name
        self.name = accet.name
        self.name_color = accet.name_color
        self.background_color = accet.background_color
        self.descriptions = accet.descriptions

        self.commodity = accet.commodity
        self.tradable = accet.tradable
        self.marketable = accet.marketable
    def get_item_id(self) -> str:
        return f'{self.classid}_{self.instanceid}'
    def get_app_class(self):
        return MarketListingsApp(app_icon=self.app_icon, appid=int(self.appid))
    def get_color(self):
        if not self.name_color: return ''
        clear_color = self.name_color.replace('#', '')
        return f'#{clear_color}'
    def get_market_url(self) -> str:
        if not self.market_hash_name: return ''
        return f'https://steamcommunity.com/market/listings/{self.appid}/{self.market_hash_name}'
    def get_icon_url(self, width: int = 64, height: int = 64) -> str:
        icon_url = self.icon_url if self.icon_url else self.icon_url_large
        if not icon_url: return ' '
        return f'https://community.akamai.steamstatic.com/economy/image/{icon_url}/{width}x{height}?allow_animated=1'
    def is_commodity(self):
        return bool(self.commodity)
    def is_tradable(self):
        return bool(self.tradable) and self.is_commodity()
    def is_marketable(self):
        return bool(self.marketable) and self.is_commodity()
class MarketListingsAsset:
    def __init__(self, data_json: dict = None):
        if not data_json: data_json = {}
        self.data_json = data_json

        self.appid = data_json.get('appid', 0)
        self.app_icon = data_json.get('app_icon', '')

        self.status = data_json.get('status', 0)

        self.id = data_json.get('id', '')
        self.classid = data_json.get('classid', '')
        self.instanceid = data_json.get('instanceid', '')
        self.contextid = data_json.get('contextid', '')
        self.amount = data_json.get('amount', '0')
        self.original_amount = data_json.get('original_amount', '0')

        self.name = data_json.get('name', '')
        self.name_color = data_json.get('name_color', '')
        self.market_name = data_json.get('market_name', '')
        self.market_hash_name = data_json.get('market_hash_name', '')
        self.icon_url = data_json.get('icon_url', '')
        self.icon_url_large = data_json.get('icon_url_large', '')
        self.background_color = data_json.get('background_color', '')

        self.commodity = data_json.get('commodity', 0)
        self.tradable = data_json.get('tradable', 0)
        self.marketable = data_json.get('marketable', 0)

        self.currency = data_json.get('currency', 0)
        self.unowned_id = data_json.get('unowned_id', '')
        self.unowned_contextid = data_json.get('unowned_contextid', '')
        self.descriptions = [ItemDescription(item) for item in data_json.get('descriptions', [])]
        self.type = data_json.get('type', '')
        self.market_tradable_restriction = data_json.get('market_tradable_restriction', 0)
        self.market_marketable_restriction = data_json.get('market_marketable_restriction', 0)
        self.owner = data_json.get('owner', 0)
    def __str__(self):
        return f"MarketListing: {self.market_hash_name} (ID: {self.id}, Amount: {self.amount})"
    def __repr__(self):
        return self.__str__()


class MarketMyHistoryManager:
    def __init__(self, data_json: dict = None):
        if not data_json: data_json = {}
        self.data_json = data_json

        self.success: bool = bool(data_json.get('success', 0))
        self.pagesize: int = data_json.get('pagesize', 0)
        self.total_count: int = data_json.get('total_count', 0)
        self.start: int = data_json.get('start', 0)

        self.assets: dict[str, MarketMyHistoryAssets] = self.__parce_assets(data_json.get('assets', {}))
        self.events: list = [MarketMyHistoryEvents(event) for event in data_json.get('events', [])]
        self.purchases: dict = {key: MarketMyHistoryPurchases(value) for key, value in data_json.get('purchases', {}).items()}
        self.listings: dict = {key: MarketMyHistoryListings(value) for key, value in data_json.get('listings', {}).items()}

        self.parced_events: list[MarketMyHistoryParcedEvent] = self.__parce_events(data_json.get('events', []))
    def __parce_assets(self, data_json: dict) -> dict[str, MarketMyHistoryAssets]:
        if not data_json: data_json = {}
        assets = {}

        for app_id, app_data in data_json.items():
            for contextid, context_data in app_data.items():
                for asset_id, asset_data in context_data.items():
                    assets[f'{app_id}_{contextid}_{asset_id}'] = MarketMyHistoryAssets(asset_data)

        return assets
    def __parce_events(self, data_json: list) -> list[MarketMyHistoryParcedEvent]:
        events = []
        for event in data_json:
            event_class = MarketMyHistoryParcedEvent(event)
            event_class.listing = next((item for item in self.listings.values() if item.listingid == event_class.listingid), None)
            event_class.purchase = next((item for item in self.purchases.values() if item.purchaseid == event_class.purchaseid), None)
            if event_class.listing:
                event_class.asset = self.assets.get(f"{event_class.listing.asset.appid}_{event_class.listing.asset.contextid}_{event_class.listing.asset.id}", None)
            events.append(event_class)
        return events

    def get_next_page_start(self, max_count) -> int | None:
        if not self.success: return None
        next_page = self.start + self.pagesize
        if next_page >= self.total_count or next_page >= max_count: return None
        return next_page

    def add_next_page(self, next_page: MarketMyHistoryManager):
        if not next_page or not next_page.success: return

        self.assets.update(next_page.assets)
        self.events.extend(next_page.events)
        self.purchases.update(next_page.purchases)
        self.listings.update(next_page.listings)

        self.parced_events.extend(next_page.parced_events)

        self.parced_events.sort(key=lambda x: x.time_event, reverse=True)

        return self

class MarketMyHistoryEvent(Enum):
    CREATE_LISTING = 1
    CANCEL_LISTING = 2
    SELL_LISTING = 3
    BUY_LISTING = 4

class MarketMyHistoryParcedEvent:
    def __init__(self, data_json: dict = None):
        if not data_json: data_json = {}
        self.data_json = data_json

        self.time_event: int = data_json.get("time_event", 0)
        self.datetime_event = datetime.datetime.fromtimestamp(self.time_event)
        self.event_type: int = data_json.get("event_type", 0)
        self.listingid: str = data_json.get("listingid", "")
        self.steamid_actor: str = data_json.get("steamid_actor", "")
        self.purchaseid: str = data_json.get("purchaseid", "")

        self.asset: MarketMyHistoryAssets | None = None
        self.listing: MarketMyHistoryListings | None = None
        self.purchase: MarketMyHistoryPurchases | None = None
    def __str__(self):
        return f"MarketMyHistoryParcedEvent: {self.datetime_event} (Type: {self.event_type}, ListingID: {self.listingid}, SteamID: {self.steamid_actor}, PurchaseID: {self.purchaseid})"
    def __repr__(self):
        return self.__str__()
    def get_app_steam_store_url(self) -> str:
        return f'https://store.steampowered.com/app/{self.asset.appid}' if self.asset and self.asset.appid else " "
    def get_app_icon_url(self) -> str:
        return self.asset.app_icon if self.asset and self.asset.app_icon else " "
    def get_buy_amount(self) -> int:
        if not self.purchase: return 0
        return int(self.purchase.asset.amount)
    def get_left_amount(self) -> int:
        if not self.listing: return 0
        return int(self.listing.asset.amount)
    def get_price(self, is_net_price: bool = False) -> float:
        if not self.purchase: return 0
        price = 0
        if self.event_type == MarketMyHistoryEvent.BUY_LISTING.value:
            price = self.purchase.paid_amount + (0 if is_net_price else self.purchase.paid_fee)
        if self.event_type == MarketMyHistoryEvent.SELL_LISTING.value:
            price = self.purchase.received_amount
        return round(price/100, 2)

    def get_item_color(self):
        if not self.asset or not self.asset.name_color: return ''
        clear_color = self.asset.name_color.replace('#', '')
        return f'#{clear_color}'
    def get_item_market_url(self) -> str:
        if not self.asset or not self.asset.market_hash_name: return ''
        return f'https://steamcommunity.com/market/listings/{self.asset.appid}/{self.asset.market_hash_name}'
    def get_item_icon_url(self, width: int = 64, height: int = 64) -> str:
        if not self.asset: return ' '
        icon_url = self.asset.icon_url if self.asset.icon_url else self.asset.icon_url_large
        if not icon_url: return ' '
        return f'https://community.akamai.steamstatic.com/economy/image/{icon_url}/{width}x{height}?allow_animated=1'
    def get_item_name(self) -> str:
        if not self.asset: return ''
        return self.asset.name

    def is_create(self) -> bool:
        return self.event_type == MarketMyHistoryEvent.CREATE_LISTING.value
    def is_cancel(self) -> bool:
        return self.event_type == MarketMyHistoryEvent.CANCEL_LISTING.value
    def is_buy(self) -> bool:
        return self.event_type == MarketMyHistoryEvent.BUY_LISTING.value
    def is_sell(self) -> bool:
        return self.event_type == MarketMyHistoryEvent.SELL_LISTING.value

# region ------ AUTO GENERATED MarketMyHistoryAssets ------
class MarketMyHistoryAssets:
    def __init__(self, data_json: dict = None):
        if not data_json: data_json = {}
        self.data_json = data_json

        self.actions: list = data_json.get("actions", [])
        self.amount: str = data_json.get("amount", "")
        self.app_icon: str = data_json.get("app_icon", "")
        self.appid: int = data_json.get("appid", 0)
        self.background_color: str = data_json.get("background_color", "")
        self.classid: str = data_json.get("classid", "")
        self.commodity: int = data_json.get("commodity", 0)
        self.contextid: str = data_json.get("contextid", "")
        self.currency: int = data_json.get("currency", 0)
        self.descriptions: list = data_json.get("descriptions", [])
        self.icon_url: str = data_json.get("icon_url", "")
        self.icon_url_large: str = data_json.get("icon_url_large", "")
        self.id: str = data_json.get("id", "")
        self.instanceid: str = data_json.get("instanceid", "")
        self.market_hash_name: str = data_json.get("market_hash_name", "")
        self.market_marketable_restriction: int = data_json.get("market_marketable_restriction", 0)
        self.market_name: str = data_json.get("market_name", "")
        self.market_tradable_restriction: int = data_json.get("market_tradable_restriction", 0)
        self.marketable: int = data_json.get("marketable", 0)
        self.name: str = data_json.get("name", "")
        self.name_color: str = data_json.get("name_color", "")
        self.original_amount: str = data_json.get("original_amount", "")
        self.owner: int = data_json.get("owner", 0)
        self.rollback_new_contextid: str = data_json.get("rollback_new_contextid", "")
        self.rollback_new_id: str = data_json.get("rollback_new_id", "")
        self.status: int = data_json.get("status", 0)
        self.tradable: int = data_json.get("tradable", 0)
        self.type: str = data_json.get("type", "")
        self.unowned_contextid: str = data_json.get("unowned_contextid", "")
        self.unowned_id: str = data_json.get("unowned_id", "")
# endregion ------ AUTO GENERATED MarketMyHistoryAssets ------
# region ------ AUTO GENERATED MarketMyHistoryEvents ------
class MarketMyHistoryEvents:
    def __init__(self, data_json: dict = None):
        if not data_json: data_json = {}
        self.data_json = data_json

        self.date_event: str = data_json.get("date_event", "")
        self.event_type: int = data_json.get("event_type", 0)
        self.listingid: str = data_json.get("listingid", "")
        self.purchaseid: str = data_json.get("purchaseid", "")
        self.steamid_actor: str = data_json.get("steamid_actor", "")
        self.time_event: int = data_json.get("time_event", 0)
        self.time_event_fraction: int = data_json.get("time_event_fraction", 0)
# endregion ------ AUTO GENERATED MarketMyHistoryEvents ------
# region ------ AUTO GENERATED MarketMyHistoryPurchases ------
class MarketMyHistoryPurchases:
    def __init__(self, data_json: dict = None):
        if not data_json: data_json = {}
        self.data_json = data_json

        self.added_tax: int = data_json.get("added_tax", 0)
        self.asset: MarketMyHistoryAssets = MarketMyHistoryAssets(data_json.get("asset", {}))
        self.currencyid: str = data_json.get("currencyid", "")
        self.failed: int = data_json.get("failed", 0)
        self.funds_returned: int = data_json.get("funds_returned", 0)
        self.listingid: str = data_json.get("listingid", "")
        self.needs_rollback: int = data_json.get("needs_rollback", 0)
        self.paid_amount: int = data_json.get("paid_amount", 0)
        self.paid_fee: int = data_json.get("paid_fee", 0)
        self.publisher_fee: int = data_json.get("publisher_fee", 0)
        self.publisher_fee_app: int = data_json.get("publisher_fee_app", 0)
        self.publisher_fee_percent: str = data_json.get("publisher_fee_percent", "")
        self.purchaseid: str = data_json.get("purchaseid", "")
        self.received_amount: int = data_json.get("received_amount", 0)
        self.received_currencyid: str = data_json.get("received_currencyid", "")
        self.steam_fee: int = data_json.get("steam_fee", 0)
        self.steamid_purchaser: str = data_json.get("steamid_purchaser", "")
        self.time_sold: int = data_json.get("time_sold", 0)
# endregion ------ AUTO GENERATED MarketMyHistoryPurchases ------
# region ------ AUTO GENERATED MarketMyHistoryListings ------
class MarketMyHistoryListings:
    def __init__(self, data_json: dict = None):
        if not data_json: data_json = {}
        self.data_json = data_json

        self.asset: MarketMyHistoryAssets = MarketMyHistoryAssets(data_json.get("asset", {}))
        self.cancel_reason: str = data_json.get("cancel_reason", "")
        self.cancel_reason_short: str = data_json.get("cancel_reason_short", "")
        self.currencyid: int = data_json.get("currencyid", 0)
        self.fee: int = data_json.get("fee", 0)
        self.listingid: str = data_json.get("listingid", "")
        self.original_price: int = data_json.get("original_price", 0)
        self.price: int = data_json.get("price", 0)
        self.publisher_fee: int = data_json.get("publisher_fee", 0)
        self.publisher_fee_app: int = data_json.get("publisher_fee_app", 0)
        self.publisher_fee_percent: str = data_json.get("publisher_fee_percent", "")
        self.steam_fee: int = data_json.get("steam_fee", 0)
# endregion ------ AUTO GENERATED MarketMyHistoryListings ------
