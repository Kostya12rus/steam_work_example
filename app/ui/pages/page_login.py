import flet as ft
from app.ui.pages.base import BasePage, Title
from app.database import sql_manager
from app.core import Account
from app.package.steam_session import steam_session_manager

class Login(ft.Row):
    def __init__(self):
        super().__init__()
        self.expand = True

        self.title_login_password = Title('Login with password')

        self.login_input = ft.TextField(dense=True, content_padding=10, max_lines=2, multiline=False)
        self.login_input.label = 'Login'
        self.login_input.border_color = ft.colors.GREY

        self.password_input = ft.TextField(dense=True, content_padding=10, password=True, can_reveal_password=True, max_lines=2)
        self.password_input.label = 'Password'
        self.password_input.border_color = ft.colors.GREY

        self.guard_code_input = ft.TextField(dense=True, content_padding=10, max_lines=2)
        self.guard_code_input.label = '2FA Code (Optional)'
        self.guard_code_input.border_color = ft.colors.GREY

        self.login_button = ft.FilledTonalButton(height=30, width=200)
        self.login_button.text = 'Login'
        self.login_button.icon = ft.icons.LOGIN_OUTLINED
        self.login_button.on_click = self.on_press_login_button

        self.column_login_password = ft.Column(expand=True)
        self.column_login_password.alignment = ft.MainAxisAlignment.START
        self.column_login_password.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.column_login_password.controls = [
            self.title_login_password,
            self.login_input,
            self.password_input,
            self.guard_code_input,
            self.login_button
        ]


        self.qr_code_title = Title('Login with QR code')
        self.qr_code_button = ft.FilledTonalButton(height=30, width=200)
        self.qr_code_button.text = 'Get QR code'
        self.qr_code_button.icon = ft.icons.QR_CODE_2_OUTLINED
        self.qr_code_button.on_click = steam_session_manager.create_qr_code

        self.qr_code_image = ft.Image(visible=False, expand=True)

        self.qr_code_column = ft.Column(expand=True)
        self.qr_code_column.alignment = ft.MainAxisAlignment.START
        self.qr_code_column.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.qr_code_column.controls = [
            self.qr_code_title,
            self.qr_code_button,
            self.qr_code_image
        ]


        self.controls = [
            self.column_login_password,
            ft.VerticalDivider(),
            self.qr_code_column
        ]

    def on_press_login_button(self, *args):
        login = self.login_input.value
        password = self.password_input.value
        guard_code = self.guard_code_input.value
        steam_session_manager.create_login_password(login, password, guard_code)

    def on_login_success(self):
        self.login_input.value = ''
        self.password_input.value = ''
        self.guard_code_input.value = ''
        if self.page:
            self.update()

    def on_callback_qr_code(self, image_str: str = None):
        self.qr_code_image.src_base64 = image_str
        self.qr_code_image.visible = True if image_str else False
        if self.page:
            self.qr_code_image.update()

class AccountsList(ft.Column):
    def __init__(self):
        super().__init__()
        self.visible = False
        self.expand_loose = True
        self.height = 200
        self.spacing = 3

        self.accounts_title = Title('Ready accounts')

        self.accounts_update_button = ft.FilledTonalButton(expand=True, height=30)
        self.accounts_update_button.text = 'Update'
        self.accounts_update_button.icon = ft.icons.UPDATE
        self.accounts_update_button.on_click = self.load_all_accounts

        self.accounts_update_row = ft.Row(spacing=1)
        self.accounts_update_row.controls = [
            self.accounts_update_button,
            ft.VerticalDivider(width=10)
        ]

        self.accounts_column = ft.Column(expand=True, spacing=3)
        self.accounts_column.scroll = ft.ScrollMode.AUTO

        self.controls = [
            ft.Divider(),
            self.accounts_title,
            self.accounts_update_row,
            self.accounts_column
        ]
        self.load_all_accounts()

    def add_account(self, account: Account):
        self.visible = True

        account_row = ft.Row(spacing=1)

        account_button_login = ft.FilledTonalButton(expand=True, height=30)
        account_button_login.text = f'{account.account_name}({account.steam_id})'
        account_button_login.icon = ft.icons.MANAGE_ACCOUNTS_OUTLINED
        account_button_login.on_click = lambda e: steam_session_manager.create_refresh_token(account)

        account_button_login_row = ft.Row()
        account_button_login_row.expand = True
        account_button_login_row.controls = [account_button_login]

        account_button_open_profile = ft.IconButton(height=30)
        account_button_open_profile.tooltip = 'Open Profile'
        account_button_open_profile.icon = ft.icons.PERSON_OUTLINED
        account_button_open_profile.padding = ft.padding.all(0)
        account_button_open_profile.url = f'https://steamcommunity.com/profiles/{account.steam_id}'

        account_button_delete = ft.IconButton(height=30)
        account_button_delete.tooltip = 'Delete'
        account_button_delete.icon_color = ft.colors.RED
        account_button_delete.icon = ft.icons.DELETE_OUTLINED
        account_button_delete.padding = ft.padding.all(0)
        account_button_delete.on_click = lambda e: self.delete_account(account)

        scroll_vertical_divider = ft.VerticalDivider(width=10)

        account_row.controls = [account_button_login_row, account_button_open_profile, account_button_delete, scroll_vertical_divider]

        self.accounts_column.controls.append(account_row)
        if self.page:
            self.update()

    def delete_account(self, account: Account):
        sql_manager.account_del(account)
        self.load_all_accounts()

    def load_all_accounts(self, *args):
        accounts = sql_manager.account_all_get()
        self.accounts_column.controls = []
        if accounts:
            for account_name, account_class in accounts.items():
                self.add_account(account_class)

class LoginPage(BasePage):
    def __init__(self):
        super().__init__()
        self.name = 'login'
        self.label = 'Авторизация'
        self.icon = ft.icons.PERSON_ADD_ALT
        self.selected_icon = ft.icons.PERSON_ADD_ALT_ROUNDED

        self.disabled_is_login = True

        self.login_content = Login()
        self.accounts_content = AccountsList()

        self.page_content = ft.Column(expand=True)
        self.page_content.controls = [
            self.login_content,
            self.accounts_content
        ]

    def on_callback_qr_code_ready(self, image_str: str):
        self.login_content.on_callback_qr_code(image_str)
    def on_callback_qr_code_timeout(self):
        self.login_content.on_callback_qr_code()
    def on_callback_authenticated(self, account: Account):
        self.accounts_content.load_all_accounts()
        self.login_content.on_callback_qr_code()
        self.login_content.on_login_success()
    def on_callback_authenticated_error(self, *args):
        self.login_content.on_callback_qr_code()
