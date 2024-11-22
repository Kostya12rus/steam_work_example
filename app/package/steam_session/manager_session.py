import os
import io
import time
import base64
import qrcode
import pathlib
import requests
import threading
import subprocess

from app.core.manager_class import Account
from app.callback import callback_manager, EventName


class CreateSteamSession:
    def __init__(self):
        self.__path_js_dir = pathlib.Path(os.path.abspath(__file__)).parent
        self.already_work = False

    @staticmethod
    def __parse_cookie_line(line: str):
        parts = line.split('; ')
        if not parts: return

        main_cookie = parts[0]
        if '=' not in main_cookie: return

        name, value = main_cookie.split('=', 1)
        attributes = {}
        for attr in parts[1:]:
            if '=' in attr:
                key, val = attr.split('=', 1)
                attributes[key.lower()] = val
            else:
                attributes[attr.lower()] = True
        domain = attributes.get('domain', '')
        path = attributes.get('path', '/')
        cookie = requests.cookies.create_cookie(name=name, value=value, domain=domain, path=path)
        return cookie

    @staticmethod
    def __generate_qr_code(qr_url: str):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=1,
        )
        qr.add_data(qr_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffered = io.BytesIO()
        img.save(buffered)
        buffered.seek(0)
        img_base64 = base64.b64encode(buffered.getvalue()).decode()

        return img_base64
    def create_qr_code(self, *args):
        if self.already_work: return
        self.already_work = True

        script_path = self.__path_js_dir / 'session_qrcode.js'
        if not script_path.is_file():
            print(f"Скрипт {script_path} не найден.")
            callback_manager.trigger(EventName.ON_ACCOUNT_LOGGED_ERROR, f"Скрипт {script_path} не найден.")
            self.already_work = False
            return

        try:
            process = subprocess.Popen(
                ['node', str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            qr_code_generated = False
            account = Account()

            def read_stdout():
                nonlocal qr_code_generated, account
                for line in process.stdout:
                    line = line.strip()
                    if line:
                        if line.startswith("http"):
                            qr_url = line
                            qr_code_image = self.__generate_qr_code(qr_url)
                            callback_manager.trigger(EventName.ON_QR_CODE_READY, qr_code_image)
                            qr_code_generated = True
                        elif line.startswith("accountName"):
                            account_name = line.split("=")[1].strip()
                            account.account_name = account_name
                        elif line.startswith("steamID"):
                            steam_id = line.split("=")[1].strip()
                            account.steam_id = steam_id
                        elif line.startswith("refreshToken"):
                            refresh_token = line.split("=")[1].strip()
                            account.refresh_token = refresh_token
                        elif 'Domain=' in line:
                            cookie = self.__parse_cookie_line(line)
                            account.session.cookies.set_cookie(cookie)

            stdout_thread = threading.Thread(target=read_stdout, daemon=True)
            stdout_thread.start()

            timeout = 120
            start_time = time.time()

            while True:
                if process.poll() is not None: break
                if qr_code_generated: pass
                if time.time() - start_time > timeout:
                    print("Таймаут ожидания QR-кода.")
                    process.terminate()
                    callback_manager.trigger(EventName.ON_QR_CODE_TIMEOUT)
                    self.already_work = False
                    return
                time.sleep(0.5)

            if process.returncode == 0:
                callback_manager.trigger(EventName.ON_ACCOUNT_LOGGED_IN, account)
            else:
                callback_manager.trigger(EventName.ON_QR_CODE_TIMEOUT)
        except FileNotFoundError:
            callback_manager.trigger(EventName.ON_ACCOUNT_LOGGED_ERROR, "Node.js не установлен или не добавлен в PATH.")
        except Exception as e:
            callback_manager.trigger(EventName.ON_ACCOUNT_LOGGED_ERROR, str(e))
        finally:
            self.already_work = False

    def create_login_password(self, login, password, guard_code):
        if self.already_work: return
        self.already_work = True

        script_path = self.__path_js_dir / 'session_login_password.js'
        if not script_path.is_file():
            print(f"Скрипт {script_path} не найден.")
            callback_manager.trigger(EventName.ON_ACCOUNT_LOGGED_ERROR, f"Скрипт {script_path} не найден.")
            self.already_work = False
            return

        try:
            process = subprocess.Popen(
                ['node', str(script_path), f'{login}:{password}:{guard_code}'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            account = Account()
            account.account_name = login
            account.password = password

            def read_stdout():
                nonlocal account
                for line in process.stdout:
                    line = line.strip()
                    if line:
                        if line.startswith("accountName"):
                            account_name = line.split("=")[1].strip()
                            account.account_name = account_name
                        elif line.startswith("steamID"):
                            steam_id = line.split("=")[1].strip()
                            account.steam_id = steam_id
                        elif line.startswith("refreshToken"):
                            refresh_token = line.split("=")[1].strip()
                            account.refresh_token = refresh_token
                        elif 'Domain=' in line:
                            cookie = self.__parse_cookie_line(line)
                            account.session.cookies.set_cookie(cookie)
                        elif 'DeviceConfirmation' in line:
                            callback_manager.trigger(EventName.ON_REQUEST_CONFIRMATION_DEVICE)
                        elif 'EmailConfirmation' in line:
                            callback_manager.trigger(EventName.ON_REQUEST_CONFIRMATION_EMAIL)

            stdout_thread = threading.Thread(target=read_stdout, daemon=True)
            stdout_thread.start()

            timeout = 120
            start_time = time.time()

            while True:
                if process.poll() is not None: break
                if time.time() - start_time > timeout:
                    process.terminate()
                    callback_manager.trigger(EventName.ON_ACCOUNT_LOGGED_ERROR, "Таймаут ожидания Входа в аккаунт.")
                    self.already_work = False
                    return
                time.sleep(0.5)

            if process.returncode == 0:
                callback_manager.trigger(EventName.ON_ACCOUNT_LOGGED_IN, account)
            else:
                callback_manager.trigger(EventName.ON_ACCOUNT_LOGGED_ERROR, "Authentication failed.")
        except FileNotFoundError:
            callback_manager.trigger(EventName.ON_ACCOUNT_LOGGED_ERROR, "Node.js не установлен или не добавлен в PATH.")
        except Exception as e:
            callback_manager.trigger(EventName.ON_ACCOUNT_LOGGED_ERROR, str(e))
        finally:
            self.already_work = False

    def create_refresh_token(self, account: Account):
        if not account or not account.refresh_token: return
        if self.already_work: return
        if account.is_alive_session():
            callback_manager.trigger(EventName.ON_ACCOUNT_LOGGED_IN, account)
            return

        self.already_work = True

        script_path = self.__path_js_dir / 'session_refresh_token.js'
        if not script_path.is_file():
            print(f"Скрипт {script_path} не найден.")
            callback_manager.trigger(EventName.ON_ACCOUNT_LOGGED_ERROR, f"Скрипт {script_path} не найден.")
            self.already_work = False
            return

        try:
            process = subprocess.Popen(
                ['node', str(script_path), f'{account.refresh_token}'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            def read_stdout():
                nonlocal account
                for line in process.stdout:
                    line = line.strip()
                    if line:
                        if line.startswith("steamID"):
                            steam_id = line.split("=")[1].strip()
                            account.steam_id = steam_id
                        elif line.startswith("refreshToken"):
                            refresh_token = line.split("=")[1].strip()
                            account.refresh_token = refresh_token
                        elif 'Domain=' in line:
                            cookie = self.__parse_cookie_line(line)
                            account.session.cookies.set_cookie(cookie)

            stdout_thread = threading.Thread(target=read_stdout, daemon=True)
            stdout_thread.start()

            timeout = 120
            start_time = time.time()

            while True:
                if process.poll() is not None: break
                if time.time() - start_time > timeout:
                    process.terminate()
                    callback_manager.trigger(EventName.ON_ACCOUNT_LOGGED_ERROR, "Таймаут ожидания Входа в аккаунт.")
                    self.already_work = False
                    return
                time.sleep(0.5)

            if process.returncode == 0:
                callback_manager.trigger(EventName.ON_ACCOUNT_LOGGED_IN, account)
            else:
                callback_manager.trigger(EventName.ON_ACCOUNT_LOGGED_ERROR, "Authentication failed.")
        except FileNotFoundError:
            callback_manager.trigger(EventName.ON_ACCOUNT_LOGGED_ERROR, "Node.js не установлен или не добавлен в PATH.")
        except Exception as e:
            callback_manager.trigger(EventName.ON_ACCOUNT_LOGGED_ERROR, str(e))
        finally:
            self.already_work = False

steam_session_manager = CreateSteamSession()
