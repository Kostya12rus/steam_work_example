from steam.steamid import SteamID, steam64_from_url, make_steam64


def get_steam_id_from_url(url: str):
    try:  # [U:1:37249****]
        make_steam64(url)
    except:
        pass
    try:  # 765611983327***
        steam_id = SteamID(url).as_64
        if steam_id:
            return steam_id
    except:
        pass
    try:  # https://steamcommunity.com/profiles/765611983327***
        steam_id = steam64_from_url(url)
        if steam_id:
            return steam_id
    except:
        pass
    return None
