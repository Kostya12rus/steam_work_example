import requests
from app.callback import callback_manager, EventName

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
        if is_callback and not is_success: callback_manager.trigger(EventName.ON_ACCOUNT_SESSION_EXPIRED, self)
        return is_success
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
