import requests
from bs4 import BeautifulSoup, Tag


def get_cs_coplay_data(session: requests.Session) -> list[int | str]:
    if not session: return []
    url = 'https://steamcommunity.com/my/friends/coplay'
    try:
        response = session.get(url)
        if not response.ok: return []

        soup = BeautifulSoup(response.text, 'html.parser')

        friends_list: Tag = soup.find('div', id='friends_list', class_='profile_friends responsive_friendblocks')
        if not friends_list: return []

        coplay_groups = friends_list.find_all('div', class_='coplayGroup')
        if not coplay_groups: return []

        steam_ids: list[int | str] = []
        for group_index, group in enumerate(coplay_groups, start=1):
            friend_divs = group.find_all('div', class_=lambda x: x and 'selectable friend_block_v2 persona' in x)
            if not friend_divs: continue
            for friend_index, friend in enumerate(friend_divs, start=1):
                steamid_str = friend.get('data-steamid')
                if steamid_str:
                    steam_ids.append(steamid_str)
        return steam_ids
    except:
        pass

    return []
