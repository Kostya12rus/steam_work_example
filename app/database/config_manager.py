from typing import Callable, Any, Dict

from app.callback import callback_manager
from app.database.sqlite_manager import sql_manager


def make_property(key_name: str, type_value: type = str, default_return=None):
    """
    Создаёт свойство для класса с возможностью чтения и записи значения в базу данных.

    Args:
        key_name (str): Ключевое имя для извлечения или записи в базу данных.
        type_value (type): Ожидаемый тип данных значения.
        default_return (str | None): Значение, которое будет возвращено, если значение в базе данных отсутствует.

    Returns:
        property: Свойство для класса с методами getter и setter.
    """

    def getter(self: 'Config'):
        """Метод для получения значения из базы данных."""
        value = sql_manager.get_setting(key_name)
        # Если значение существует, возвращаем его, иначе возвращаем значение по умолчанию
        return value if value is not None else default_return

    def setter(self: 'Config', value):
        """Метод для записи значения в базу данных."""
        # Если значение соответствует ожидаемому типу, сохраняем его в базу данных
        if isinstance(value, type_value):
            sql_manager.save_setting(key_name, value)

        # Вызов обратных вызовов, если они существуют
        callback_manager.trigger(key_name, value)

    return property(getter, setter)


class Config:
    interval_update_inventory = make_property('interval_update_inventory', str, 'Not Update')

    def __init__(self):
        self._properties: Dict[str, property] = {}  # Хранилище свойств

    @staticmethod
    def register_callback(key_name: str, callback: Callable[[Any], None]):
        """
        Регистрирует callback для указанного свойства.

        Callback будет вызван при изменении значения свойства с указанным ключом.
        Это позволяет выполнять произвольные действия (например, обновление интерфейса, логирование),
        когда значение свойства обновляется.

        Args:
            key_name (str): Имя свойства, для которого регистрируется callback.
            callback (Callable[[Any], None]): Функция, которая будет вызвана при изменении значения.
                                               Функция должна принимать один аргумент — новое значение свойства.

        Example:
            def on_account_change(value):
                print(f"Account changed to: {value}")

            config.register_callback("current_account", on_account_change)
        """
        callback_manager.register(key_name, callback)

    @staticmethod
    def unregister_callback(key_name: str, callback: Callable[[Any], None]):
        """
        Удаляет зарегистрированный callback для указанного свойства.

        Это предотвращает вызов callback-функции при изменении значения свойства.

        Args:
            key_name (str): Имя свойства, для которого нужно удалить callback.
            callback (Callable[[Any], None]): Функция, ранее зарегистрированная как callback.

        Example:
            config.unregister_callback("current_account", on_account_change)
        """
        callback_manager.unregister(key_name, callback)

    def add_property(self, key_name: str, type_value: type = str, default_return=None):
        """
        Динамически добавляет новое свойство в класс.

        Args:
            key_name (str): Имя свойства.
            type_value (type): Тип значения свойства.
            default_return (Any): Значение по умолчанию.

        Raises:
            AttributeError: Если свойство с таким именем уже существует.
        """
        if key_name in self._properties:
            return

        prop = make_property(key_name, type_value, default_return)
        self._properties[key_name] = prop
        setattr(self.__class__, key_name, prop)

    def get_property(self, key_name: str):
        """
        Возвращает значение свойства, если оно существует.

        Args:
            key_name (str): Имя свойства.

        Returns:
            Any: Значение свойства.

        Raises:
            AttributeError: Если свойства с указанным именем не существует.
        """
        if key_name not in self._properties: return None
        return getattr(self, key_name)

    def set_property(self, key_name: str, value):
        if key_name not in self._properties: return None
        setattr(self, key_name, value)


config = Config()
