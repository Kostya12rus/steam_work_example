from setuptools import setup, find_packages
import pathlib

def parce_readme() -> str:
    file_path = pathlib.Path("README.md")
    if not file_path.is_file(): return ""
    with open(file_path, encoding="utf-8") as fh:
        return fh.read()

def parse_requirements() -> list[str]:
    file_path = pathlib.Path("requirements/base.txt")
    if not file_path.is_file(): return []
    with open(file_path, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="steam_work_example",
    version="1.0.0",
    author="Kostya12rus",
    description="Десктопное приложение на Python для работы в Steam",
    long_description=parce_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/Kostya12rus/steam_work_example",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "app.package.steam_session": ["*.js", "*.json"],
        "app.assets": ["*.json", "*.png"],
    },
    install_requires=parse_requirements(),
    entry_points={
        "console_scripts": [
            "steam_work_example=app.main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    license="MIT",
    keywords="desktop application Steam Flet GUI",
    project_urls={
        "Bug Tracker": "https://github.com/Kostya12rus/steam_work_example/issues",
        "Documentation": "https://github.com/Kostya12rus/steam_work_example/wiki",
    },
)
