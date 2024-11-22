@echo off
chcp 65001

cd /d "%~dp0"
python -m venv .venv
call ".venv\Scripts\activate.bat"

python -m pip install --upgrade pip setuptools wheel

pip install --force-reinstall git+https://github.com/Kostya12rus/steam_work_example.git

pause
