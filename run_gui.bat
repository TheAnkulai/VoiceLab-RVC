@echo off
cd /d "%~dp0"
call .venv\Scripts\activate
python rvc_gui.py