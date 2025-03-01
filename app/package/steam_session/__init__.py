"""
    Пакет для управления Steam-сессиями и утилитами Node.js.
"""
__version__ = "1.0.0"
__author__ = "Kostya12rus"

__all__ = ["steam_session_manager", "note_js_utility"]

from .manager_session import steam_session_manager
from .update_or_install import note_js_utility
