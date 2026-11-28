@echo off
rem Opens the ion beam agent console (scripts\agent_gui.py) using the project virtual environment.
cd /d "%~dp0"
".venv\Scripts\python.exe" scripts\agent_gui.py %*
