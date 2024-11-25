import requests

from app.callback import callback_manager, EventName

class AppDetails:
    def __init__(self, app_details: dict):
        self.__app_details = app_details
        self.appid = app_details.get('steam_appid', 0)
        self.name = app_details.get('name', '')
        self.image = app_details.get('header_image', '')
        self.price_overview = app_details.get('price_overview', {}).get('final_formatted', '')
        self.store_url = f'https://store.steampowered.com/app/{self.appid}/'

    def get_save_data(self):
        return self.__app_details

    def is_real_app(self):
        return self.appid != 0

    def save(self):
        from app.database import sql_manager
        sql_manager.appdetails_save(self)
        callback_manager.trigger(EventName.ON_APP_ID_ADDED, self)

    def remove(self):
        from app.database import sql_manager
        sql_manager.appdetails_del(self)
        callback_manager.trigger(EventName.ON_APP_ID_REMOVED, self)

    @classmethod
    def create_from_appid(cls, appid: int | str):
        """Создает объект AppDetails на основе appid из API Steam."""
        url = f'https://store.steampowered.com/api/appdetails?appids={appid}'
        try:
            req = requests.get(url, timeout=5)
            req.raise_for_status()
            req_json = req.json()
            app_data = req_json.get(str(appid), {})
            if not app_data.get('success', False): return None
            return cls(app_data.get('data', {}))
        except:
            return None
