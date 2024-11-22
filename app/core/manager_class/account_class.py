import requests
import threading

class Account:
    def __init__(self):
        self.account_name = None
        self.password = None
        self.steam_id = None
        self.refresh_token = None
        self.session = requests.Session()
        self.callback_session_expired = []
    def is_alive_session(self, is_callback: bool = True) -> bool:
        req = self.session.get("https://steamcommunity.com")
        is_success = req.ok and self.account_name.lower() in req.text.lower()
        if is_callback and not is_success: threading.Thread(target=self.__on_callback_callback_session_expired).start()
        return is_success
    def register_callback_session_expired(self, func):
        if not callable(func): return
        if func in self.callback_session_expired: return
        self.callback_session_expired.append(func)
    def unregister_callback_session_expired(self, func):
        if not callable(func): return
        if func not in self.callback_session_expired: return
        self.callback_session_expired.remove(func)
    def __on_callback_callback_session_expired(self):
        for callback in self.callback_session_expired:
            threading.Thread(target=callback, args=(self,)).start()
    def get_save_data(self):
        return {
            'account_name': self.account_name,
            'password': self.password,
            'steam_id': self.steam_id,
            'refresh_token': self.refresh_token
        }
    def set_save_data(self, data: dict):
        self.account_name = data.get('account_name', None)
        self.password = data.get('password', None)
        self.steam_id = data.get('steam_id', None)
        self.refresh_token = data.get('refresh_token', None)
        return self
