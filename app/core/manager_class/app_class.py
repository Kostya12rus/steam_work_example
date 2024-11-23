
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
