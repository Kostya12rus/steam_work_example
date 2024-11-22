@echo off
chcp 65001

cd /d "%~dp0"
python -m venv .venv
call ".venv\Scripts\activate.bat"

steam_work_example

pause
