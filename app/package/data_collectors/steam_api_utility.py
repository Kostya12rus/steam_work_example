import copy
import datetime
import json
import re
import time

from requests import Session
from app.core import Account


class SteamAPIUtility:
    def __init__(self, account: Account):
        self.account = account

    def __is_session_alive(self, session: Session) -> bool:
        main_page_response = session.get('https://steamcommunity.com')
        return self.account.account_name.lower() in main_page_response.text.lower()

    def is_session_alive(self):
        if not self.account.session: return False
        return self.__is_session_alive(self.account.session)

    def get_inventory_items(self, steam_id: str | int, appid=3017120, start=0, context_id=2):
        if not self.account or not self.account.is_alive_session(): return
        if str(self.account.steam_id) == str(steam_id):
            return self.__get_myinventory_items(steam_id=steam_id, appid=appid, start=start, context_id=context_id)
        else:
            return self.__get_partnerinventory_items(steam_id=steam_id, appid=appid, start=start, context_id=context_id)

    def __get_myinventory_items(self, steam_id: str | int, appid=3017120, start=0, context_id=2):
        # def_url = f'https://steamcommunity.com/profiles/{steam_id}/inventory/json/{appid}/{context_id}/?start={start}'
        def_url = f'https://steamcommunity.com/inventory/{steam_id}/{appid}/{context_id}?count=2000'
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

    def create_trade_offer(self, partner_steam32id: str, partner_token: str, items: dict = None, tradeoffermessage: str = ''):
        if not self.account or not self.account.is_alive_session(is_callback=True): return
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

    def get_steam_web_token(self):
        if not self.account or not self.account.is_alive_session(): return

        try:
            response = self.account.session.get('https://steamcommunity.com/my/', timeout=10)

            token_pattern = re.compile(r'loyalty_webapi_token\s*=\s*"([^"]+)"')
            match = token_pattern.search(response.text)

            if match:
                token = match.group(1).replace('&quot;', '')
                return token
        except:
            return None


class InventoryManager:
    def __init__(self, items: dict, context_id=2):
        self.data_json = items
        self.descriptions: list = items.get('descriptions', []) or [description for name, description in items.get('rgDescriptions', {}).items()]
        self.assets: list = items.get('assets', []) or [asset for name, asset in items.get('rgInventory', {}).items()]
        self.success: bool = bool(items.get('success', False))

        self.inventory: list[InventoryItemRgDescriptions] = []
        self.context_id = context_id
        self.parse_inventory()

    def add_next_invent(self, next_invent: 'InventoryManager'):
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

    def get_tradable_inventory(self) -> list['InventoryItemRgDescriptions']:
        return [item for item in self.inventory if item.tradable]

    def get_amount_items(self, only_tradable=True) -> int:
        inventory = self.get_tradable_inventory() if only_tradable else self.inventory
        return sum([item.get_amount() for item in inventory], start=0)

class InventoryItemDescription:
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
        self.descriptions = [InventoryItemDescription(d) for d in rg_dict.get('descriptions', [])]
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
        self.owner_descriptions = [InventoryItemDescription(d) for d in rg_dict.get('owner_descriptions', [])]
    def __extract_date_from_owner_descriptions(self):
        if not self.owner_descriptions: return None
        date_pattern = re.compile(r'\[date\](\d+)\[/date\]')
        for desc in self.owner_descriptions:
            match = date_pattern.search(desc.value)
            if match:
                timestamp = int(match.group(1))
                return datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
        return None
    def get_color(self):
        if not self.name_color: return ''
        clear_color = self.name_color.replace('#', '')
        return f'#{clear_color}'
    def get_amount(self):
        amount = sum([int(i.amount) for i in self.items], start=0)
        return amount if amount > 0 else 0
    def get_market_url(self) -> str | None:
        if not self.market_hash_name: return
        return f'https://steamcommunity.com/market/listings/{self.appid}/{self.market_hash_name}'
    def get_icon_url(self) -> str | None:
        if not self.icon_url: return None
        return f'https://community.akamai.steamstatic.com/economy/image/{self.icon_url}/330x192?allow_animated=1'
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
            if not original_item:
                self.items.append(item)
            else:
                original_item.amount -= item.amount
    def __repr__(self):
        return f'<classid: {self.classid}, instanceid: {self.instanceid}, market_hash_name: {self.market_hash_name}, amount: {self.get_amount()}>'
    def __str__(self):
        return f'<classid: {self.classid}, instanceid: {self.instanceid}, market_hash_name: {self.market_hash_name}, amount: {self.get_amount()}>'
