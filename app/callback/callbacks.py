import threading
from enum import Enum
from app.logger import logger

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
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(CallbackManager, cls).__new__(cls)
            cls._instance._lock = threading.Lock()
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
        with self._lock:
            if event_name in self._callbacks:
                for callback in self._callbacks[event_name]:
                    thread = threading.Thread(
                        target=self.__callback_errors,
                        args=(*args,),
                        kwargs={**kwargs, 'callback': callback}
                    )
                    thread.start()

    @staticmethod
    def __callback_errors(*args, callback=None, **kwargs):
        try:
            callback(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Error in callback {callback}: {e}")
callback_manager = CallbackManager(max_workers=5)
