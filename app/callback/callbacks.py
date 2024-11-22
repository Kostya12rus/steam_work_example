from concurrent.futures import ThreadPoolExecutor
from enum import Enum

class EventName(Enum):
    ON_ACCOUNT_SESSION_EXPIRED = "on_account_session_expired"
    ON_ACCOUNT_LOGGED_IN = "on_account_logged_in"
    ON_ACCOUNT_LOGGED_ERROR = "on_account_logged_error"
    ON_ACCOUNT_LOGGED_OUT = "on_account_logged_out"

    ON_QR_CODE_READY = "on_qr_code_ready"
    ON_QR_CODE_TIMEOUT = "on_qr_code_timeout"
    ON_REQUEST_CONFIRMATION_DEVICE = "on_request_confirmation_device"
    ON_REQUEST_CONFIRMATION_EMAIL = "on_request_confirmation_email"


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
