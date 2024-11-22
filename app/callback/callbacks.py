from concurrent.futures import ThreadPoolExecutor
from enum import Enum

class EventName(Enum):
    ON_GET_JWT_TOKEN = "on_get_jwt_token"
    ON_SECRET_KEY_LOADED = "on_secret_key_loaded"
    ON_AUTHENTICATED_SUCCESS = "on_authenticated_success"
    ON_UNAUTHENTICATED = "on_unauthenticated"
    ON_NEED_REFRESH_TOKEN = "on_need_refresh_token"
    ON_BALANCE_UPDATE = "on_balance_update"
    ON_STEAM_PROFILE_LOADED = "on_steam_profile_loaded"


class CallbackManager:
    """
    CallbackManager обеспечивает управление callback-ами для различных событий.

    Доступные события (event_name):\n
    - "on_start": Вызывается при старте процесса.
    - "on_finish": Вызывается при завершении процесса.
    - "on_error": Вызывается при возникновении ошибки.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(CallbackManager, cls).__new__(cls)
            cls._instance._executor = ThreadPoolExecutor(max_workers=kwargs.get('max_workers', 10))
            cls._instance._callbacks = {}
        return cls._instance

    def register(self, event_name, callback):
        if event_name not in self._callbacks:
            self._callbacks[event_name] = []
        self._callbacks[event_name].append(callback)

    def unregister(self, event_name, callback):
        if event_name in self._callbacks:
            self._callbacks[event_name].remove(callback)

    def trigger(self, event_name, *args, **kwargs):
        """Вызывает все callback-и для указанного события асинхронно."""
        if event_name in self._callbacks:
            for callback in self._callbacks[event_name]:
                self._executor.submit(callback, *args, **kwargs)
callback_manager = CallbackManager(max_workers=5)
