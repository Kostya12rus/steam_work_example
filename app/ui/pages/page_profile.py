import datetime
import flet as ft
from app.ui.pages.base import BasePage, Title

from app.core import Account
from app.package.data_collectors import get_steam_profile_info, get_cs_profile_data, get_cs_matchmaking_stats_data


class ProfileContent(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.spacing = 2

        self.__account: Account = None
        self.__steam_profile_data = {}
        self.__cs_profile_data = {}
        self.__cs_matchmaking_stats = []


        self.page_title = Title('Account Information')

        self.update_info_button = ft.FilledTonalButton(expand=True, height=30)
        self.update_info_button.text = 'Update Profile Information'
        self.update_info_button.icon = ft.icons.UPDATE
        self.update_info_button.on_click = self.update_profile_data
        self.update_info_row = ft.Row()
        self.update_info_row.controls = [self.update_info_button]


        self.steam_title = Title('Steam Profile Information')

        self.steam_avatar = ft.CircleAvatar(height=40)
        self.steam_avatar.foreground_image_url = None
        self.steam_nickname = ft.Text(size=30, max_lines=1, selectable=True)
        self.steam_nickname.value = ''
        self.steam_nickname.text_align = ft.TextAlign.LEFT
        self.steam_avatar_nickname_row = ft.Row(expand=True, spacing=2)
        self.steam_avatar_nickname_row.alignment = ft.MainAxisAlignment.CENTER
        self.steam_avatar_nickname_row.controls = [
            self.steam_avatar,
            self.steam_nickname
        ]

        self.steam_description = ft.Text(max_lines=1, selectable=True, expand=True)
        self.steam_description.value = ''
        self.steam_description.text_align = ft.TextAlign.CENTER

        self.steam_registration = ft.Text(max_lines=1, expand=True)
        self.steam_registration.value = 'Registration: '
        self.steam_registration.text_align = ft.TextAlign.CENTER
        self.steam_status = ft.Text(max_lines=1, expand=True)
        self.steam_status.value = 'Status: '
        self.steam_status.text_align = ft.TextAlign.CENTER
        self.steam_privacy = ft.Text(max_lines=1, expand=True)
        self.steam_privacy.value = 'Privacy: '
        self.steam_privacy.text_align = ft.TextAlign.CENTER

        self.steam_registration_status_steam_privacy_row = ft.Row()
        self.steam_registration_status_steam_privacy_row.alignment = ft.MainAxisAlignment.SPACE_AROUND
        self.steam_registration_status_steam_privacy_row.controls = [
            self.steam_registration,
            self.steam_status,
            self.steam_privacy
        ]

        self.steam_games_title = Title('Last Played Games')
        self.steam_games_column = ft.Column(expand=True, spacing=2)
        self.steam_games_column.scroll = ft.ScrollMode.ALWAYS

        self.steam_column = ft.Column(expand=True)
        self.steam_column.controls = [
            self.steam_title,
            ft.Row(controls=[self.steam_avatar_nickname_row]),
            ft.Row(controls=[self.steam_description]),
            self.steam_registration_status_steam_privacy_row,
            self.steam_games_title,
            self.steam_games_column,
        ]


        self.cs_profile_title = Title('CS Profile Information')

        self.cs_level = ft.Text(max_lines=1)
        self.cs_level.value = 'Level: '
        self.cs_exp = ft.Text(max_lines=1)
        self.cs_exp.value = 'EXP: '

        self.cs_level_exp_row = ft.Row(expand=True)
        self.cs_level_exp_row.alignment = ft.MainAxisAlignment.SPACE_EVENLY
        self.cs_level_exp_row.controls = [self.cs_level, self.cs_exp]

        self.cs_first_enter = ft.Text(max_lines=1, expand=True)
        self.cs_first_enter.text_align = ft.TextAlign.RIGHT
        self.cs_first_enter.value = 'First Enter: '

        self.cs_first_match = ft.Text(max_lines=1, expand=True)
        self.cs_first_match.text_align = ft.TextAlign.RIGHT
        self.cs_first_match.value = 'First Match: '

        self.cs_last_enter = ft.Text(max_lines=1, expand=True)
        self.cs_last_enter.text_align = ft.TextAlign.RIGHT
        self.cs_last_enter.value = 'Last Enter: '

        self.cs_last_logout = ft.Text(max_lines=1, expand=True)
        self.cs_last_logout.text_align = ft.TextAlign.RIGHT
        self.cs_last_logout.value = 'Last Logout: '

        self.cs_times_column = ft.Column()
        self.cs_times_column.alignment = ft.MainAxisAlignment.START
        self.cs_times_column.horizontal_alignment = ft.CrossAxisAlignment.END
        self.cs_times_column.controls = [
            ft.Row(controls=[self.cs_first_enter]),
            ft.Row(controls=[self.cs_first_match]),
            ft.Row(controls=[self.cs_last_enter]),
            ft.Row(controls=[self.cs_last_logout]),
        ]

        self.cs_matchmaking_stats_title = Title('CS Matchmaking Stats')
        self.cs_matchmaking_stats_table = ft.DataTable(columns=[], rows=[], visible=False, expand=True, heading_row_height=20, column_spacing=6)
        self.cs_matchmaking_stats_table.columns = [ft.DataColumn(ft.Text("."))]
        self.cs_matchmaking_stats_table.clip_behavior = ft.ClipBehavior.HARD_EDGE
        self.cs_matchmaking_stats_table.vertical_lines = ft.BorderSide(width=1, color=ft.colors.GREY)

        self.cs_profile_column = ft.Column(expand=True)
        self.cs_profile_column.controls = [
            self.cs_profile_title,
            ft.Row(controls=[self.cs_level_exp_row]),
            ft.Row(
                controls=[self.cs_times_column],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            self.cs_matchmaking_stats_title,
            self.cs_matchmaking_stats_table,
        ]


        self.main_row = ft.Row(expand=True)
        self.main_row.controls = [self.steam_column, ft.VerticalDivider(), self.cs_profile_column]

        self.controls = [self.page_title, self.update_info_row, self.main_row]

    def __add_steam_profile_game(self, game_data: dict = None):
        game_title = game_data.get('gameName', 'Unknown Game')
        game_logo_url = game_data.get('gameLogo', None)
        game_link_url = game_data.get('gameLink', None)
        game_hours_played = game_data.get('hoursPlayed', '0')
        game_hours_on_record = game_data.get('hoursOnRecord', '0')

        widget_logo = ft.Image(src=game_logo_url)
        widget_logo.fit = ft.ImageFit.CONTAIN
        widget_logo.repeat = ft.ImageRepeat.NO_REPEAT

        widget_title = ft.Text(game_title, expand=True, max_lines=1, size=20)
        widget_title.text_align = ft.TextAlign.CENTER
        widget_title.overflow = ft.TextOverflow.ELLIPSIS
        widget_title.weight = ft.FontWeight.BOLD

        widget_link = ft.FilledTonalButton(icon=ft.icons.LINK, url=game_link_url)
        widget_link.text = 'Open Game Url'

        widget_time = ft.Text(expand=True, max_lines=1)
        widget_time.value = f'Hours played: {game_hours_played}h|{game_hours_on_record}h'
        widget_time.text_align = ft.TextAlign.CENTER
        widget_time.overflow = ft.TextOverflow.ELLIPSIS

        widget_column = ft.Column(spacing=1, expand=True)
        widget_column.alignment = ft.MainAxisAlignment.CENTER
        widget_column.controls = [
            ft.Row(controls=[widget_title]),
            ft.Row(controls=[widget_link], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row(controls=[widget_time]),
        ]
        widget_row = ft.Row(spacing=1)
        widget_row.alignment = ft.MainAxisAlignment.CENTER
        widget_row.controls = [
            widget_logo,
            widget_column,
            ft.VerticalDivider(width=10)
        ]

        container = ft.Container(padding=20)
        container.content = widget_row
        container.border = ft.border.all(1)
        container.border_radius = ft.border_radius.all(15)
        container.alignment = ft.alignment.center

        self.steam_games_column.controls.append(container)

    def __get_current_matchmaking_stats(self):
        return next(
            (
                table for table in self.__cs_matchmaking_stats
                if any(len(row) == 7 and 'Matchmaking Mode' in row for row in table)),
            None
        ) if self.__cs_matchmaking_stats else None

    def __update_widget_profile(self):
        self.steam_avatar.foreground_image_url = self.__steam_profile_data.get('avatarFull', None)
        self.steam_nickname.value = self.__steam_profile_data.get('steamID', 'Unknown Nickname')
        self.steam_description.value = self.__steam_profile_data.get('summary', '')
        self.steam_registration.value = f'Registration: {self.__steam_profile_data.get("memberSince", "Unknown")}'
        self.steam_status.value = f'Status: {self.__steam_profile_data.get("onlineState", "Unknown").upper()}'
        self.steam_privacy.value = f'Privacy: {self.__steam_profile_data.get("privacyState", "Unknown").upper()}'
        self.steam_games_column.controls = []
        mostPlayedGames = self.__steam_profile_data.get('mostPlayedGames', {}).get('mostPlayedGame', [])
        if isinstance(mostPlayedGames, list):
            for mostPlayedGame in mostPlayedGames:
                self.__add_steam_profile_game(mostPlayedGame)
        elif isinstance(mostPlayedGames, dict):
            self.__add_steam_profile_game(mostPlayedGames)

        self.cs_level.value = f'Level: {self.__cs_profile_data.get("level", "Unknown")}'
        self.cs_exp.value = f'EXP: {self.__cs_profile_data.get("exp", "Unknown")}'

        cs_first_enter_datatime = datetime.datetime.fromtimestamp(self.__cs_profile_data.get('first_time', 0))
        cs_first_match_datatime = datetime.datetime.fromtimestamp(self.__cs_profile_data.get('started_time', 0))
        cs_last_enter_datatime = datetime.datetime.fromtimestamp(self.__cs_profile_data.get('login_time', 0))
        cs_last_logout_datatime = datetime.datetime.fromtimestamp(self.__cs_profile_data.get('logout_time', 0))
        self.cs_first_enter.value = f'First Enter: {cs_first_enter_datatime.strftime("%d.%m.%Y %H:%M:%S")}'
        self.cs_first_match.value = f'First Match: {cs_first_match_datatime.strftime("%d.%m.%Y %H:%M:%S")}'
        self.cs_last_enter.value = f'Last Enter: {cs_last_enter_datatime.strftime("%d.%m.%Y %H:%M:%S")}'
        self.cs_last_logout.value = f'Last Logout: {cs_last_logout_datatime.strftime("%d.%m.%Y %H:%M:%S")}'

        is_has_matchmaking = self.__get_current_matchmaking_stats()
        if is_has_matchmaking:
            header = is_has_matchmaking[0]
            rows = is_has_matchmaking[1:]
            self.cs_matchmaking_stats_table.columns = [
                ft.DataColumn(
                    ft.Text(
                        text_header,
                        weight=ft.FontWeight.BOLD,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS
                    ),
                    heading_row_alignment=ft.MainAxisAlignment.CENTER
                )
                for text_header in header
            ]
            self.cs_matchmaking_stats_table.rows = []
            for row in rows:
                self.cs_matchmaking_stats_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(
                                ft.Row(
                                    run_spacing=0,
                                    spacing=0,
                                    controls=[
                                        ft.Text(
                                            text_row,
                                            expand=True,
                                            text_align=ft.TextAlign.CENTER,
                                            max_lines=1,
                                            overflow=ft.TextOverflow.ELLIPSIS
                                        )
                                    ]
                                )
                            )
                            for text_row in row
                        ]
                    )
                )
        self.cs_matchmaking_stats_table.visible = True if is_has_matchmaking else False

        if self.page:
            self.update()

    def update_profile_data(self, *args):
        self.__steam_profile_data = {}
        self.__cs_profile_data = {}
        self.__cs_matchmaking_stats = []
        if self.__account and self.__account.is_alive_session():
            self.__steam_profile_data = get_steam_profile_info(session=self.__account.session)
            self.__update_widget_profile()
            self.__cs_profile_data = get_cs_profile_data(session=self.__account.session)
            self.__update_widget_profile()
            self.__cs_matchmaking_stats = get_cs_matchmaking_stats_data(session=self.__account.session)
        self.__update_widget_profile()

    def update_account(self, account: Account = None):
        self.__account = account
        self.update_profile_data()


class ProfilePage(BasePage):
    def __init__(self):
        super().__init__()
        self.name = 'profile'
        self.label = 'Профиль'
        self.icon = ft.icons.PERSON_OUTLINED
        self.selected_icon = ft.icons.PERSON

        self.disabled = True
        self.disabled_is_logout = True

        self.page_content = ProfileContent()

    def on_callback_authenticated(self, account: Account):
        self.page_content.update_account(account)

    def on_callback_logout(self):
        self.page_content.update_account()
