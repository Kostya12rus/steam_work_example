import threading
import time

import requests
from bs4 import BeautifulSoup
from steam.steamid import make_steam64, SteamID


def get_steam_mini_profile_info(steam_id: int | str, session: requests.Session = None) -> dict:
    return_dict = {}
    steam_id64 = make_steam64(steam_id)
    if not steam_id64: return return_dict
    steam_class = SteamID(steam_id64)
    steam_id32 = steam_class.as_32
    url = f'https://steamcommunity.com/miniprofile/{steam_id32}'
    if session:
        req = session.get(url)
    else:
        req = requests.get(url)
    if not req.ok: return return_dict

    return_dict["steam_id"] = steam_class
    return_dict["account_id"] = steam_id32
    return_dict["miniprofile_url"] = url

    soup = BeautifulSoup(req.text, features="html.parser")
    playersection_avatar = soup.find('div', class_=lambda x: x and 'playersection_avatar border' in x)
    if playersection_avatar:
        img = playersection_avatar.find('img')
        if img:
            return_dict["avatar_url"] = img.get('src')

    player_content = soup.find('div', class_='player_content')
    if player_content:
        name = player_content.find('span', class_=lambda x: x and 'persona' in x)
        if name:
            return_dict['name'] = name.get_text(strip=True)

    return return_dict


steam_list_loaded = {}
steam_load_lock = threading.Lock()


class SteamMiniProfileInfo:
    def __init__(self, data_json: dict = None):
        if not data_json: data_json = {}
        self.data_json = data_json
        self.steam_id: SteamID | None = self.data_json.get("steam_id", None)
        self.account_id = self.data_json.get("account_id", None)
        self.miniprofile_url = self.data_json.get("miniprofile_url", None)
        self.avatar_url = self.data_json.get("avatar_url", ' ')
        self.name = self.data_json.get("name", '')


def load_steam_mini_profile_info(steam_id: int | str, session: requests.Session = None) -> SteamMiniProfileInfo | None:
    global steam_list_loaded

    steam_id64 = make_steam64(steam_id)
    if not steam_id64: return None
    steam_class = SteamID(steam_id64)
    steam_id32 = steam_class.as_32
    with steam_load_lock:
        if steam_id32 in steam_list_loaded: return steam_list_loaded[steam_id32]

        account_data = get_steam_mini_profile_info(steam_id=steam_id32, session=session)
        if not account_data: return None
        steam_miniprofile_class = SteamMiniProfileInfo(data_json=account_data)
        steam_list_loaded[steam_id32] = steam_miniprofile_class
        time.sleep(0.5)
        return steam_miniprofile_class
