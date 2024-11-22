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


class CreateSteamSession:
    def __init__(self):
        self.__path_js_dir = pathlib.Path(os.path.abspath(__file__)).parent

        self.already_work = False

        self.callback_logout = []
        self.callback_session_expired = []
        self.callback_authenticated = []
        self.callback_authenticated_error = []

        self.callback_qr_code_ready = []
        self.callback_qr_code_timeout = []

        self.callback_request_confirmation_device = []
        self.callback_request_confirmation_email = []

    def register_callback_logout(self, func):
        if not callable(func): return
        if func in self.callback_logout: return
        self.callback_logout.append(func)
    def register_callback_session_expired(self, func):
        if not callable(func): return
        if func in self.callback_session_expired: return
        self.callback_session_expired.append(func)
    def register_callback_authenticated(self, func):
        if not callable(func): return
        if func in self.callback_authenticated: return
        self.callback_authenticated.append(func)
    def register_callback_authenticated_error(self, func):
        if not callable(func): return
        if func in self.callback_authenticated_error: return
        self.callback_authenticated_error.append(func)
    def register_callback_qr_code_ready(self, func):
        if not callable(func): return
        if func in self.callback_qr_code_ready: return
        self.callback_qr_code_ready.append(func)
    def register_callback_qr_code_timeout(self, func):
        if not callable(func): return
        if func in self.callback_qr_code_timeout: return
        self.callback_qr_code_timeout.append(func)
    def register_callback_request_confirmation_device(self, func):
        if not callable(func): return
        if func in self.callback_request_confirmation_device: return
        self.callback_request_confirmation_device.append(func)
    def register_callback_request_confirmation_email(self, func):
        if not callable(func): return
        if func in self.callback_request_confirmation_email: return
        self.callback_request_confirmation_email.append(func)

    def unregister_callback_logout(self, func):
        if not callable(func): return
        if func in self.callback_logout:
            self.callback_logout.remove(func)
    def unregister_callback_session_expired(self, func):
        if not callable(func): return
        if func not in self.callback_session_expired: return
        self.callback_session_expired.remove(func)
    def unregister_callback_authenticated(self, func):
        if not callable(func): return
        if func in self.callback_authenticated:
            self.callback_authenticated.remove(func)
    def unregister_callback_authenticated_error(self, func):
        if not callable(func): return
        if func in self.callback_authenticated_error:
            self.callback_authenticated_error.remove(func)
    def unregister_callback_qr_code_ready(self, func):
        if not callable(func): return
        if func in self.callback_qr_code_ready:
            self.callback_qr_code_ready.remove(func)
    def unregister_callback_qr_code_timeout(self, func):
        if not callable(func): return
        if func in self.callback_qr_code_timeout:
            self.callback_qr_code_timeout.remove(func)
    def unregister_callback_request_confirmation_device(self, func):
        if not callable(func): return
        if func in self.callback_request_confirmation_device:
            self.callback_request_confirmation_device.remove(func)
    def unregister_callback_request_confirmation_email(self, func):
        if not callable(func): return
        if func in self.callback_request_confirmation_email:
            self.callback_request_confirmation_email.remove(func)

    def on_callback_logout(self):
        for callback in self.callback_logout:
            threading.Thread(target=callback).start()
    def __on_callback_callback_session_expired(self, account: Account):
        for callback in self.callback_session_expired:
            threading.Thread(target=callback, args=(account,)).start()
    def __on_callback_authenticated(self, account: Account):
        for callback in self.callback_authenticated:
            threading.Thread(target=callback, args=(account,)).start()
    def __on_callback_authenticated_error(self, error_message: str):
        for callback in self.callback_authenticated_error:
            threading.Thread(target=callback, args=(error_message,)).start()
    def __on_callback_qr_code_ready(self, qr_code_image):
        for callback in self.callback_qr_code_ready:
            threading.Thread(target=callback, args=(qr_code_image,)).start()
    def __on_callback_qr_code_timeout(self):
        for callback in self.callback_qr_code_timeout:
            threading.Thread(target=callback).start()
    def __on_callback_request_confirmation_device(self):
        for callback in self.callback_request_confirmation_device:
            threading.Thread(target=callback).start()
    def __on_callback_request_confirmation_email(self):
        for callback in self.callback_request_confirmation_email:
            threading.Thread(target=callback).start()

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
            self.__on_callback_authenticated_error(f"Скрипт {script_path} не найден.")
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
            account.register_callback_session_expired(self.__on_callback_callback_session_expired)

            def read_stdout():
                nonlocal qr_code_generated, account
                for line in process.stdout:
                    line = line.strip()
                    if line:
                        if line.startswith("http"):
                            qr_url = line
                            qr_code_image = self.__generate_qr_code(qr_url)
                            self.__on_callback_qr_code_ready(qr_code_image)
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
                    self.__on_callback_qr_code_timeout()
                    self.already_work = False
                    return
                time.sleep(0.5)

            if process.returncode == 0:
                self.__on_callback_authenticated(account)
            else:
                self.__on_callback_qr_code_timeout()
        except FileNotFoundError:
            self.__on_callback_authenticated_error("Node.js не установлен или не добавлен в PATH.")
        except Exception as e:
            self.__on_callback_authenticated_error(str(e))
        finally:
            self.already_work = False

    def create_login_password(self, login, password, guard_code):
        if self.already_work: return
        self.already_work = True

        script_path = self.__path_js_dir / 'session_login_password.js'
        if not script_path.is_file():
            print(f"Скрипт {script_path} не найден.")
            self.__on_callback_authenticated_error(f"Скрипт {script_path} не найден.")
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
            account.register_callback_session_expired(self.__on_callback_callback_session_expired)

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
                            self.__on_callback_request_confirmation_device()
                        elif 'EmailConfirmation' in line:
                            self.__on_callback_request_confirmation_email()

            stdout_thread = threading.Thread(target=read_stdout, daemon=True)
            stdout_thread.start()

            timeout = 120
            start_time = time.time()

            while True:
                if process.poll() is not None: break
                if time.time() - start_time > timeout:
                    process.terminate()
                    self.__on_callback_authenticated_error("Таймаут ожидания Входа в аккаунт.")
                    self.already_work = False
                    return
                time.sleep(0.5)

            if process.returncode == 0:
                self.__on_callback_authenticated(account)
            else:
                self.__on_callback_authenticated_error("Authentication failed.")
        except FileNotFoundError:
            self.__on_callback_authenticated_error("Node.js не установлен или не добавлен в PATH.")
        except Exception as e:
            self.__on_callback_authenticated_error(str(e))
        finally:
            self.already_work = False

    def create_refresh_token(self, account: Account):
        if not account or not account.refresh_token: return
        if self.already_work: return
        if account.is_alive_session():
            self.__on_callback_authenticated(account)
            return

        self.already_work = True

        script_path = self.__path_js_dir / 'session_refresh_token.js'
        if not script_path.is_file():
            print(f"Скрипт {script_path} не найден.")
            self.__on_callback_authenticated_error(f"Скрипт {script_path} не найден.")
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
                    self.__on_callback_authenticated_error("Таймаут ожидания Входа в аккаунт.")
                    self.already_work = False
                    return
                time.sleep(0.5)

            if process.returncode == 0:
                self.__on_callback_authenticated(account)
                account.register_callback_session_expired(self.__on_callback_callback_session_expired)
            else:
                self.__on_callback_authenticated_error("Ошибка входа")
        except FileNotFoundError:
            self.__on_callback_authenticated_error("Node.js не установлен или не добавлен в PATH.")
        except Exception as e:
            self.__on_callback_authenticated_error(str(e))
        finally:
            self.already_work = False

steam_session_manager = CreateSteamSession()
