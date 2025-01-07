import requests
from enum import Enum

from app.callback import callback_manager, EventName
from app.database.sqlite_manager import sql_manager


class AppsTable(Enum):
    TABLE_NAME = 'apps'
    APPID = 'appid'
    APP_DETAILS = 'app_details'

column_types = {
    AppsTable.APPID:        'INTEGER UNIQUE',
    AppsTable.APP_DETAILS:  'TEXT',
}
sql_manager.create_table(AppsTable.TABLE_NAME, column_types)


class AppDetails:
    def __init__(self, app_details: dict):
        self.__app_details = app_details
        self.appid = app_details.get('steam_appid', 0)
        self.name = app_details.get('name', '')
        self.image = app_details.get('header_image', '')
        self.price_overview = app_details.get('price_overview', {}).get('final_formatted', '')
        self.store_url = f'https://store.steampowered.com/app/{self.appid}/'

    def get_save_data(self) -> dict:
        return self.__app_details

    def is_real_app(self) -> bool:
        return bool(self.appid and self.appid != 0)

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

    def save(self):
        if not self.is_real_app(): return
        save_data = sql_manager.encrypt_data(self.get_save_data())

        status = sql_manager.save_data(
            table_name=AppsTable.TABLE_NAME.value,
            data={
                AppsTable.APPID.value: self.appid,
                AppsTable.APP_DETAILS.value: save_data
            }
        )

        if status: callback_manager.trigger(EventName.ON_APP_ID_ADDED, self)
    def delete(self):
        if not self.is_real_app(): return

        status = sql_manager.delete_data(
            table_name=AppsTable.TABLE_NAME.value,
            condition={
                AppsTable.APPID.value: self.appid,
            }
        )
        if status: callback_manager.trigger(EventName.ON_APP_ID_REMOVED, self)
    @classmethod
    def load(cls, appid: str | int) -> 'AppDetails':
        data = sql_manager.get_data(
            table_name=AppsTable.TABLE_NAME.value,
            condition={
                AppsTable.APPID.value: appid,
            }
        )
        if not data: return None

        # appid = data[0]
        try:
            app_details = sql_manager.decrypt_data(data[1])
        except:
            app_details = {}

        return cls(app_details)
    @classmethod
    def load_all(cls) -> list['AppDetails']:
        data = sql_manager.get_all_data(
            table_name=AppsTable.TABLE_NAME.value
        )
        return [AppDetails(sql_manager.decrypt_data(app[1])) for app in data]
