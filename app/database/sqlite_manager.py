import json
import zlib
import pickle
import sqlite3
import threading

from enum import Enum
from app.logger import logger
from .cyber_safe import store_encrypted_data as encrypt, retrieve_encrypted_data as decrypt

tables_structure = {
    'setting':
        '''
            name        TEXT UNIQUE,
            value       TEXT
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
    def create_table(self, table_name: Enum, table_params: dict[Enum, str]) -> None:
        columns = ', '.join(f"{name_column.value} {type_column}" for name_column, type_column in table_params.items())
        self.__create_table(table_name.value, columns)
    def __create_all_tables(self) -> None:
        for table_name in tables_structure:
            self.__create_table(table_name, tables_structure[table_name])


    def save_data(self, table_name: str, data: dict) -> bool:
        try:
            with self.__db_lock, self.__connect() as conn:
                cursor = conn.cursor()
                columns = ', '.join(data.keys())
                placeholders = ', '.join('?' for _ in data)
                values = tuple(data.values())
                query = f"INSERT OR REPLACE INTO {table_name} ({columns}) VALUES ({placeholders})"
                cursor.execute(query, values)
                return True
        except Exception:
            logger.exception(f"Ошибка при сохранении данных в таблицу '{table_name}'")
    def delete_data(self, table_name: str, condition: dict) -> bool:
        try:
            with self.__db_lock, self.__connect() as conn:
                cursor = conn.cursor()
                condition_column, condition_value = next(iter(condition.items()))
                query = f"DELETE FROM {table_name} WHERE {condition_column}=?"
                cursor.execute(query, (condition_value,))
                return True
        except Exception:
            logger.exception(f"Ошибка при удалении данных из таблицы '{table_name}'")
    def get_data(self, table_name: str, condition: dict):
        try:
            with self.__db_lock, self.__connect() as conn:
                cursor = conn.cursor()
                condition_column, condition_value = next(iter(condition.items()))
                query = f"SELECT * FROM {table_name} WHERE {condition_column}=?"
                cursor.execute(query, (condition_value,))
                row = cursor.fetchone()
                return row
        except Exception:
            logger.exception(f"Ошибка при получении данных из таблицы '{table_name}'")
    def get_all_data(self, table_name: str):
        try:
            with self.__db_lock, self.__connect() as conn:
                cursor = conn.cursor()
                query = f"SELECT * FROM {table_name}"
                cursor.execute(query)
                rows = cursor.fetchall()
                return rows
        except Exception:
            logger.exception(f"Ошибка при получении всех данных из таблицы '{table_name}'")


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
