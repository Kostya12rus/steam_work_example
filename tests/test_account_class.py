import pytest
from unittest.mock import Mock, patch, PropertyMock
from app.database.sqlite_manager import sql_manager
from app.callback import callback_manager, EventName
from app.core.manager_class.account_class import Account,AccountTable


@pytest.fixture
def account():
    """Фикстура для создания экземпляра Account."""
    return Account()


def test_is_alive_session_true(account):
    """Тест проверки живой сессии при наличии валидного аккаунта."""
    with patch.object(account.session, 'get', return_value=Mock(ok=True, text="AccountName")):
        account.account_name = "AccountName"
        assert account.is_alive_session() is True


def test_is_alive_session_false(account):
    """Тест проверки мертвой сессии при отсутствии валидного аккаунта."""
    with patch.object(account.session, 'get', return_value=Mock(ok=True, text="InvalidName")):
        account.account_name = "AccountName"
        assert account.is_alive_session() is False


def test_get_steam_web_token(account):
    """Тест получения Steam Web Token."""
    account.is_alive_session = Mock(return_value=True)
    response_mock = Mock(text='loyalty_webapi_token = "test_token"')
    with patch.object(account.session, 'get', return_value=response_mock):
        token = account.get_steam_web_token()
        assert token == "test_token"


def test_load_wallet_info(account):
    """Тест загрузки информации о кошельке."""
    account.is_alive_session = Mock(return_value=True)
    response_mock = Mock(ok=True, text='var g_rgWalletInfo = {"wallet_currency": 1, "wallet_country": "US"};')
    with patch.object(account.session, 'get', return_value=response_mock):
        wallet_info = account.load_wallet_info()
        assert wallet_info['wallet_currency'] == 1
        assert wallet_info['wallet_country'] == "US"


def test_save(account):
    """Тест сохранения данных аккаунта в базе данных."""
    account.account_name = "test_account"
    account.get_save_data = Mock(return_value={"key": "value"})
    sql_manager.save_data = Mock()
    account.save()
    sql_manager.save_data.assert_called_once()


def test_delete(account):
    """Тест удаления данных аккаунта из базы данных."""
    account.account_name = "test_account"
    sql_manager.delete_data = Mock()
    account.delete()
    sql_manager.delete_data.assert_called_once_with(
        table_name=AccountTable.TABLE_NAME.value,
        condition={AccountTable.LOGIN.value: "test_account"}
    )


def test_load(account):
    """Тест загрузки данных аккаунта из базы данных."""
    sql_manager.get_data = Mock(return_value=["test_account", "encrypted_data"])
    sql_manager.decrypt_data = Mock(return_value={"account_name": "test_account"})
    loaded_account = Account.load("test_account")
    assert loaded_account.account_name == "test_account"


def test_load_all(account):
    """Тест загрузки всех данных аккаунтов из базы данных."""
    sql_manager.get_all_data = Mock(return_value=[["test_account", "encrypted_data"]])
    sql_manager.decrypt_data = Mock(return_value={"account_name": "test_account"})
    accounts = Account.load_all()
    assert "test_account" in accounts
    assert accounts["test_account"].account_name == "test_account"
