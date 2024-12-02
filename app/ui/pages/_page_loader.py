import os
import pathlib
import sys
import importlib
from typing import Type
from . import BasePage

class PageManager:
    def __init__(self):
        self.pages: list[Type[BasePage]] = []

        self.__parce_directories()
        self.__load_pages()

    def get_pages(self):
        return [page() for page in self.pages]

    def __parce_directories(self):
        local_path = pathlib.Path()
        user_pages_path = local_path / "user_pages"
        user_pages_path.mkdir(parents=True, exist_ok=True)
        sys.path.append(local_path.absolute().as_posix())

        self.pages.extend(self.__load_pages(pathlib.Path(os.path.abspath(__file__)).parent))
        for sys_path in sys.path:
            if not sys_path: continue
            user_pages = self.__load_pages(pathlib.Path(sys_path) / "user_pages")
            if not user_pages: continue
            self.pages.extend(user_pages)

    @staticmethod
    def __load_pages(directory: pathlib.Path=None):
        if not directory or not directory.is_dir(): return

        if directory not in sys.path:
            sys.path.append(directory.as_posix())
        pages = []
        for file in os.listdir(directory):
            if file.startswith("page_") and file.endswith(".py"):
                module_name = file[:-3]
                try:
                    module = importlib.import_module(module_name)
                    for attr in dir(module):
                        obj: BasePage = getattr(module, attr)
                        if isinstance(obj, type) and issubclass(obj, BasePage) and obj is not BasePage:
                            pages.append(obj)
                except Exception as e:
                    print(f"Ошибка при импорте {module_name}: {e}")
        pages.sort(key=lambda x: x.load_position)
        return pages
page_manager = PageManager()
