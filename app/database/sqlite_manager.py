import json
import zlib
import pickle
import sqlite3
import threading

from app.logger import logger
from app.core import Account, AppDetails
from .cyber_safe import store_encrypted_data as encrypt, retrieve_encrypted_data as decrypt

tables_structure = {
    'setting':
        '''
            name        TEXT UNIQUE,
            value       TEXT
        ''',
    'accounts':
        '''
            login       TEXT UNIQUE,
            client      TEXT
        ''',
    'apps':
        '''
            appid           INTEGER UNIQUE,
            app_details     TEXT
        ''',
    'item_nameid':
        '''
            market_hash_name    TEXT UNIQUE,
            nameid              INTEGER
        ''',
}

class SqliteDatabaseManager:
    def __init__(self):
        self.db_name = 'data.db'
        self._secret_key = None
        self.__db_lock = threading.Lock()
        self.__create_all_tables()

    def __connect(self):
        return sqlite3.connect(self.db_name, check_same_thread=False)
    def __create_table(self, table_name: str, table_params: str) -> None:
        try:
            with self.__connect() as conn:
                cursor = conn.cursor()
                cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({table_params});")
        except sqlite3.OperationalError:
            pass
    def __create_all_tables(self) -> None:
        for table_name in tables_structure:
            self.__create_table(table_name, tables_structure[table_name])


    def account_save(self, account: 'Account'):
        if not isinstance(account, Account): return
        with self.__db_lock:
            try:
                with self.__connect() as conn:
                    cursor = conn.cursor()
                    save_data = account.get_save_data()
                    account_client = self.encrypt_data(save_data)
                    cursor.execute("INSERT OR REPLACE INTO accounts (login, client) VALUES (?, ?)", (account.account_name, account_client))
            except Exception:
                logger.exception(f"Ошибка при обновлении аккаунта '{account.account_name}'")
    def account_del(self, account: 'Account'):
        if not isinstance(account, Account): return
        with self.__db_lock:
            try:
                with self.__connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM accounts WHERE login=?", (account.account_name,))
            except Exception:
                logger.exception(f"Ошибка при обновлении аккаунта '{account.account_name}'")
    def account_get(self, account_name: str):
        with self.__db_lock:
            try:
                with self.__connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT client FROM accounts WHERE login=?", (account_name,))
                    row = cursor.fetchone()
                    if row:
                        value = row[0]
                        try:
                            return Account().set_save_data(self.decrypt_data(value))
                        except:
                            pass
                        return value
                    return None
            except Exception:
                logger.exception(f"Ошибка при получении аккаунта '{account_name}'")
    def account_all_get(self):
        with self.__db_lock:
            try:
                with self.__connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM accounts")
                    row = cursor.fetchall()
                    return {account[0]: Account().set_save_data(self.decrypt_data(account[1])) for account in row}
            except Exception:
                logger.exception(f"Ошибка при получении аккаунтов")


    def appdetails_save(self, app_details: 'AppDetails'):
        if not isinstance(app_details, AppDetails): return
        if not app_details.is_real_app(): return
        with self.__db_lock:
            try:
                with self.__connect() as conn:
                    cursor = conn.cursor()
                    save_data = app_details.get_save_data()
                    app_details_client = self.encrypt_data(save_data)
                    cursor.execute("INSERT OR REPLACE INTO apps (appid, app_details) VALUES (?, ?)", (app_details.appid, app_details_client))
            except Exception:
                logger.exception(f"Ошибка при обновлении приложения '{app_details.appid}'")
    def appdetails_del(self, app_details: 'AppDetails'):
        if not isinstance(app_details, AppDetails): return
        if not app_details.is_real_app(): return
        with self.__db_lock:
            try:
                with self.__connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM apps WHERE appid=?", (app_details.appid,))
            except Exception:
                logger.exception(f"Ошибка при обновлении приложения '{app_details.appid}'")
    def appdetails_get(self, appid: int):
        with self.__db_lock:
            try:
                with self.__connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT app_details FROM apps WHERE appid=?", (appid,))
                    row = cursor.fetchone()
                    if row:
                        value = row[0]
                        try:
                            return AppDetails(self.decrypt_data(value))
                        except:
                            pass
                        return value
                    return None
            except Exception:
                logger.exception(f"Ошибка при получении приложения '{appid}'")
    def appdetails_all_get(self):
        with self.__db_lock:
            try:
                with self.__connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM apps")
                    row = cursor.fetchall()
                    return [AppDetails(self.decrypt_data(app[1])) for app in row]
            except Exception:
                logger.exception(f"Ошибка при получении приложений")


    def item_nameid_save(self, appid: int | str, market_hash_name: str, nameid: int | str):
        if not appid or not market_hash_name or not nameid: return
        with self.__db_lock:
            try:
                with self.__connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT OR REPLACE INTO item_nameid (market_hash_name, nameid) VALUES (?, ?)", (f'{appid}__{market_hash_name}', nameid))
            except Exception:
                logger.exception(f"Ошибка при сохранении item_nameid {appid}__{market_hash_name} {nameid}")
    def item_nameid_del(self, appid: int | str, market_hash_name: str):
        if not appid or not market_hash_name: return
        with self.__db_lock:
            try:
                with self.__connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM item_nameid WHERE market_hash_name=?", (f'{appid}__{market_hash_name}',))
            except Exception:
                logger.exception(f"Ошибка при удалении item_nameid {appid}__{market_hash_name}")
    def item_nameid_get(self, appid: int | str, market_hash_name: str):
        if not appid or not market_hash_name: return
        with self.__db_lock:
            try:
                with self.__connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT nameid FROM item_nameid WHERE market_hash_name=?", (f'{appid}__{market_hash_name}',))
                    row = cursor.fetchone()
                    if row:
                        return row[0]
                    return None
            except Exception:
                logger.exception(f"Ошибка при получении item_nameid {appid}__{market_hash_name}")
    def item_nameid_all_get(self):
        with self.__db_lock:
            try:
                with self.__connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM item_nameid")
                    return cursor.fetchall()
            except Exception:
                logger.exception(f"Ошибка при получении приложений")


    def save_setting(self, name: str, value: str | list | dict):
        try:
            with self.__db_lock, self.__connect() as conn:
                if isinstance(value, (list, dict)):
                    value = json.dumps(value)
                cursor = conn.cursor()
                cursor.execute("INSERT OR REPLACE INTO setting (name, value) VALUES (?, ?)", (name, value))
        except Exception:
            logger.exception(f"Ошибка при обновлении настройки '{name}'")
    def get_setting(self, name: str) -> str | list | None:
        try:
            with self.__db_lock, self.__connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM setting WHERE name=?", (name,))
                row = cursor.fetchone()
                if row:
                    value = row[0]
                    try:
                        return json.loads(value)
                    except:
                        pass
                    return value
                return None
        except Exception:
            logger.exception(f"Ошибка при получении настройки '{name}'")


    def encrypt_data(self, data: any) -> bytes | None:
        """
        Шифрует и сжимает предоставленные данные.

        Этот метод сериализует и сжимает данные с использованием zlib, затем шифрует их,
        если установлен секретный ключ. Возвращает зашифрованные данные в байтовом формате.
        В случае ошибки записывает информацию об ошибке в лог и возвращает None.

        Args:
            data (any): Данные для шифрования и сжатия.

        Returns:
            bytes | None: Зашифрованные данные в байтовом формате или None в случае ошибки.
        """
        try:
            # Сериализация и сжатие данных
            serialized_data = zlib.compress(pickle.dumps(data))
            # Шифрование данных, если установлен секретный ключ
            if isinstance(self._secret_key, str | int | float):
                serialized_data = encrypt(serialized_data, str(self._secret_key))
            # Возврат зашифрованных данных
            return serialized_data
        except Exception as error:
            # Логирование ошибки при шифровании
            logger.exception(f"Ошибка при шифровании данных: {type(error).__name__}")
            return None
    def decrypt_data(self, data: bytes) -> any:
        """
        Дешифрует и разжимает предоставленные данные.

        Этот метод сначала пытается дешифровать данные с использованием секретного ключа,
        затем разжимает их. Возвращает десериализованные данные в случае успеха.
        В случае ошибки записывает информацию об ошибке в лог и возвращает None.

        Args:
            data (bytes): Данные для дешифрования и разжатия.

        Returns:
            Десериализованные данные после дешифрования и разжатия или None в случае ошибки.
        """
        try:
            # Подготовка данных для дешифрования
            compressed_data = data
            # Дешифрование данных, если установлен секретный ключ
            if isinstance(self._secret_key, str | int | float):
                compressed_data = decrypt(str(self._secret_key), compressed_data)
            # Разжатие и десериализация данных
            return pickle.loads(zlib.decompress(compressed_data))
        except Exception as error:
            # Логирование ошибки при дешифровании
            logger.exception(f"Ошибка при дешифровании данных: {type(error).__name__}")
            return None

sql_manager = SqliteDatabaseManager()
