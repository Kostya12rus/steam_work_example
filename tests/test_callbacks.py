import pytest
from unittest.mock import Mock
import time
from app.callback.callbacks import CallbackManager, EventName
from loguru import logger


@pytest.fixture(autouse=True)
def add_loguru_to_caplog(caplog):
    """Fixture to redirect Loguru logs to pytest's caplog."""
    handler_id = logger.add(caplog.handler, format="{message}", level="DEBUG")
    yield
    logger.remove(handler_id)


@pytest.fixture
def callback_manager():
    """Fixture to initialize the CallbackManager instance."""
    return CallbackManager()


def test_singleton(callback_manager):
    """Test that CallbackManager acts as a singleton."""
    another_instance = CallbackManager()
    assert callback_manager is another_instance


def test_register_callback(callback_manager):
    """Test registering a callback for a specific event."""
    mock_callback = Mock()
    callback_manager.register(EventName.ON_ACCOUNT_LOGGED_IN, mock_callback)

    assert EventName.ON_ACCOUNT_LOGGED_IN in callback_manager._callbacks
    assert mock_callback in callback_manager._callbacks[EventName.ON_ACCOUNT_LOGGED_IN]


def test_unregister_callback(callback_manager):
    """Test unregistering a callback from a specific event."""
    mock_callback = Mock()
    callback_manager.register(EventName.ON_ACCOUNT_LOGGED_IN, mock_callback)
    callback_manager.unregister(EventName.ON_ACCOUNT_LOGGED_IN, mock_callback)

    assert mock_callback not in callback_manager._callbacks[EventName.ON_ACCOUNT_LOGGED_IN]


def test_trigger_event(callback_manager):
    """Test triggering an event and ensuring the registered callback is executed."""
    mock_callback = Mock()
    callback_manager.register(EventName.ON_ACCOUNT_LOGGED_IN, mock_callback)
    callback_manager.trigger(EventName.ON_ACCOUNT_LOGGED_IN, arg_str="test", arg_list=[1, 2, 3])

    # Allow some time for the thread to execute the callback
    mock_callback.assert_called_once_with(arg_str="test", arg_list=[1, 2, 3])


def test_trigger_event_with_exception_handling(callback_manager, caplog):
    """Test triggering an event with a callback that raises an exception and ensure it's logged."""

    def faulty_callback(*args, **kwargs):
        raise ValueError("Test error")

    callback_manager.register(EventName.ON_ACCOUNT_LOGGED_IN, faulty_callback)
    callback_manager.trigger(EventName.ON_ACCOUNT_LOGGED_IN)

    # Allow some time for the thread to handle the exception
    time.sleep(0.5)

    assert any("Test error" in record.message for record in caplog.records)


def test_unregister_nonexistent_callback(callback_manager):
    """Test attempting to unregister a callback that was never registered."""
    mock_callback = Mock()
    callback_manager.unregister(EventName.ON_ACCOUNT_LOGGED_IN, mock_callback)
    # Ensure no exception is raised for unregistering a non-existent callback
