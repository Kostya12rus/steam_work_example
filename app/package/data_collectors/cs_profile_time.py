import datetime
import re

import requests
from bs4 import BeautifulSoup


def steam_time_to_timestamp(time_str: str) -> int:
    return int(datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S GMT').replace(tzinfo=datetime.timezone.utc).timestamp())


def get_cs_profile_time(body_content) -> dict[str, int]:
    soup_cs = BeautifulSoup(body_content, 'html.parser')

    time_data = {}
    logout_time_match = re.search(
        r'Logged out of CS:GO\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} GMT)',
        soup_cs.get_text()
    )
    logout_time_str = logout_time_match.group(1) if logout_time_match else "Not found"
    time_data['logout_time'] = 0
    if logout_time_str != "Not found":
        time_data['logout_time'] = steam_time_to_timestamp(logout_time_str)

    login_time_match = re.search(
        r'Launched CS:GO using Steam Client\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} GMT)',
        soup_cs.get_text()
    )
    login_time_str = login_time_match.group(1) if login_time_match else "Not found"
    time_data['login_time'] = 0
    if login_time_str != "Not found":
        time_data['login_time'] = steam_time_to_timestamp(login_time_str)

    started_time_match = re.search(
        r'Started playing CS:GO\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} GMT)',
        soup_cs.get_text()
    )
    started_time_str = started_time_match.group(1) if started_time_match else "Not found"
    time_data['started_time'] = 0
    if started_time_str != "Not found":
        time_data['started_time'] = steam_time_to_timestamp(started_time_str)

    first_time_match = re.search(
        r'First Counter-Strike franchise game\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} GMT)',
        soup_cs.get_text()
    )
    first_time_str = first_time_match.group(1) if first_time_match else "Not found"
    time_data['first_time'] = 0
    if first_time_str != "Not found":
        time_data['first_time'] = steam_time_to_timestamp(first_time_str)

    return time_data


def get_cs_profile_level(body_content) -> dict[str, int]:
    try:
        soup = BeautifulSoup(body_content, 'html.parser')
        rank_text = exp_text = None

        for text in soup.stripped_strings:
            if "CS:GO Profile Rank" in text:
                rank_text = text
            elif "Experience points earned towards next rank" in text:
                exp_text = text

        rank_number = int(re.search(r'\d+', rank_text).group()) if rank_text else None
        exp_number = int(re.search(r'\d+', exp_text).group()) if exp_text else None
        return {'level': rank_number, 'exp': exp_number}
    except:
        pass

    return {}


def get_cs_profile_data(session: requests.Session) -> dict[str, int]:
    req = session.get('https://steamcommunity.com/my/gcpd/730?tab=accountmain')
    if not req.ok: return {}
    cs_profile_data = {}
    cs_level = get_cs_profile_level(req.text)
    if cs_level:
        cs_profile_data.update(cs_level)
    cs_time = get_cs_profile_time(req.text)
    if cs_time:
        cs_profile_data.update(cs_time)
    return cs_profile_data
