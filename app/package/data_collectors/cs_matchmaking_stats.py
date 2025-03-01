import datetime

import requests
from bs4 import BeautifulSoup


def steam_time_to_timestamp(time_str: str) -> int:
    return int(datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S GMT').replace(tzinfo=datetime.timezone.utc).timestamp())


def steam_time_to_str(time_str: str) -> str:
    return datetime.datetime.fromtimestamp(steam_time_to_timestamp(time_str)).strftime("%d.%m.%Y %H:%M:%S")


def parse_html_table(table) -> list:
    rows = table.find_all('tr')
    if not rows: return

    header_row = rows[0]
    headers = [th.get_text(strip=True) for th in header_row.find_all('th')]
    if not headers: return

    table_data = [headers]
    for row in rows[1:]:
        cells = row.find_all('td')
        if len(cells) != len(headers): continue
        row_data = []
        for cell in cells:
            cell_text = cell.get_text(strip=True).replace('\xa0', ' ')
            if 'GMT' in cell_text:
                cell_text = steam_time_to_str(cell_text)
            row_data.append(cell_text)
        table_data.append(row_data)
    return table_data


def get_cs_matchmaking_parse(body_content: str) -> list:
    soup_cs = BeautifulSoup(body_content, 'html.parser')
    tables = soup_cs.find_all('table', class_='generic_kv_table')
    all_tables_data = []

    for table_index, table in enumerate(tables, start=1):
        table_data = parse_html_table(table)
        if not table_data: continue
        all_tables_data.append(table_data)
    return all_tables_data


def get_cs_matchmaking_stats_data(session: requests.Session) -> dict[str, int]:
    req = session.get('https://steamcommunity.com/my/gcpd/730?tab=matchmaking')
    if not req.ok: return {}
    tables = get_cs_matchmaking_parse(req.text)
    return tables
