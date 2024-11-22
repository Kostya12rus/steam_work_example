from setuptools import setup, find_packages
import pathlib

def parce_readme() -> str:
    file_path = pathlib.Path("README.md")
    if not file_path.is_file(): return ""
    with open(file_path, encoding="utf-8") as fh:
        return fh.read()

def parse_requirements() -> list[str]:
    file_path = pathlib.Path("requirements.txt")
    if not file_path.is_file(): return []
    with open(file_path, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


setup(
    name="steam_work_example",                      # Название проекта
    version="1.0.0",                            # Версия проекта
    author="Kostya12rus",                       # Автор проекта
    author_email="your_email@example.com",      # Email автора
    description="Пример десктопного приложения на Python",  # Краткое описание
    long_description=parce_readme(),          # Полное описание (например, из README.md)
    long_description_content_type="text/markdown",  # Тип содержимого (Markdown)
    url="https://github.com/username/repo",     # Ссылка на репозиторий или сайт проекта
    packages=find_packages(),                   # Автоматический поиск пакетов
    include_package_data=True,                  # Включение дополнительных файлов (ресурсов)
    package_data={
        # Указываем, какие файлы включить для конкретных пакетов
        "app.package.steam_session": ["*.js", "*.json"],
        "app.assets": ["*.json", "*.png"],
    },
    install_requires=parse_requirements(),    # Зависимости
    entry_points={                              # Точка входа для запуска приложения
        "console_scripts": [
            "steam_work_example=app.main:main", # Связывает команду с функцией main()
        ],
    },
    classifiers=[                               # Классификация проекта
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",                   # Минимальная версия Python
    license="MIT",                              # Лицензия
    keywords="desktop application PyQt GUI",    # Ключевые слова
    project_urls={                              # Дополнительные ссылки
        "Bug Tracker": "https://github.com/username/repo/issues",
        "Documentation": "https://github.com/username/repo/wiki",
    },
)
# а при >pip install . --no-cache-dir он устанавливает последнюю версию с гит хаба или нет?