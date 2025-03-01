import datetime
import json
import re
import requests
import threading
from enum import Enum

from app.callback import callback_manager, EventName
from app.database.sqlite_manager import sql_manager


class AccountTable(Enum):
    TABLE_NAME = 'accounts'
    LOGIN = 'login'
    CLIENT = 'client'


column_types = {
    AccountTable.LOGIN: 'TEXT UNIQUE',
    AccountTable.CLIENT: 'TEXT',
}
sql_manager.create_table(AccountTable.TABLE_NAME, column_types)


class Account:
    def __init__(self):
        self.password = None
        self.steam_id = None
        self.account_name = None
        self.refresh_token = None
        self.session = requests.Session()
        self.wallet_currency: int | None = None
        self.wallet_country: str | None = None

        self.__access_token = None
        self.__wallet_info: dict | None = None
        self.__lock = threading.Lock()
        self.__last_check_status = None
        self.__last_check_time = datetime.datetime.min
        self.__lock_check_session = threading.Lock()

    def is_alive_session(self, is_callback: bool = True) -> bool:
        with self.__lock_check_session:
            if self.__last_check_status and self.__last_check_time + datetime.timedelta(seconds=30) > datetime.datetime.now():
                return self.__last_check_status
            self.__last_check_time = datetime.datetime.now()

            req = self.session.get("https://steamcommunity.com")
            self.__last_check_status = req.ok and self.account_name.lower() in req.text.lower()
            if is_callback and not self.__last_check_status: callback_manager.trigger(EventName.ON_ACCOUNT_SESSION_EXPIRED, self)
            print(f'is_alive_session: {self.__last_check_status}')
            return self.__last_check_status

    def get_steam_web_token(self):
        with self.__lock:
            if self.__access_token: return self.__access_token
            if not self.is_alive_session(): return
            try:
                response = self.session.get('https://steamcommunity.com/my/', timeout=10)

                token_pattern = re.compile(r'loyalty_webapi_token\s*=\s*"([^"]+)"')
                match = token_pattern.search(response.text)

                if match:
                    token = match.group(1).replace('&quot;', '')
                    self.__access_token = token
                    return token
            except:
                return None

    def load_wallet_info(self):
        if self.__wallet_info: return self.__wallet_info
        if not self.is_alive_session(): return
        url = "https://steamcommunity.com/market/"
        try:
            response = self.session.get(url, timeout=10)
            if response.ok:
                wallet_info_match = re.search(r'var g_rgWalletInfo = ({.*?});', response.text)

                if wallet_info_match:
                    wallet_info_json = wallet_info_match.group(1)
                    self.__wallet_info = json.loads(wallet_info_json)
                    self.wallet_currency = self.__wallet_info.get('wallet_currency', None)
                    self.wallet_country = self.__wallet_info.get('wallet_country', None)
                    print(f"Wallet info loaded. Currency: {self.wallet_currency}, Country: {self.wallet_country}")
                    return self.__wallet_info
        except Exception as e:
            print(f"Error fetching wallet info: {e}")

    def get_save_data(self):
        return {
            'account_name': self.account_name,
            'password': self.password,
            'steam_id': self.steam_id,
            'refresh_token': self.refresh_token,
            'session': self.session
        }

    def set_save_data(self, data: dict):
        self.account_name = data.get('account_name', None)
        self.password = data.get('password', None)
        self.steam_id = data.get('steam_id', None)
        self.refresh_token = data.get('refresh_token', None)
        session = data.get('session', None)
        if session: self.session = session
        return self

    def save(self):
        login = self.account_name
        if not login: return
        client = sql_manager.encrypt_data(self.get_save_data())

        sql_manager.save_data(
            table_name=AccountTable.TABLE_NAME.value,
            data={
                AccountTable.LOGIN.value: login,
                AccountTable.CLIENT.value: client
            }
        )

    def delete(self):
        login = self.account_name
        if not login: return

        sql_manager.delete_data(
            table_name=AccountTable.TABLE_NAME.value,
            condition={
                AccountTable.LOGIN.value: login
            }
        )

    @classmethod
    def load(cls, account_name: str) -> 'Account':
        data = sql_manager.get_data(
            table_name=AccountTable.TABLE_NAME.value,
            condition={
                AccountTable.LOGIN.value: account_name
            }
        )
        if not data: return None

        # login = data[0]
        try:
            client = sql_manager.decrypt_data(data[1])
        except:
            client = {}

        return cls().set_save_data(client)

    @classmethod
    def load_all(cls) -> dict[str, 'Account']:
        data = sql_manager.get_all_data(
            table_name=AccountTable.TABLE_NAME.value
        )
        try:
            return {account[0]: Account().set_save_data(sql_manager.decrypt_data(account[1])) for account in data}
        except:
            return {}
