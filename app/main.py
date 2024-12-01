import os

import flet as ft
from app.ui.main_page import MainPage

def main():
    main_page = MainPage('Steam Inventory Helper')
    ft.app(main_page.build)
    os.abort()

if __name__ == "__main__":
    main()

