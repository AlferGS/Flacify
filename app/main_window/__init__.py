# app/components/__init__.py

from .home_window import HomeWindow
from .main_fluent_window import MainFluentWindow
from .settings_window import SettinsWindow

# Опционально: ограничиваем импорт по "звездочке"
__all__ = [
    "HomeWindow",
    "MainFluentWindow", 
    "SettinsWindow",
]