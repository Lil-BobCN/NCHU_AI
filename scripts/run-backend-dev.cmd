@echo off
cd /d "%~dp0.."
set PYTHONPATH=backend
.\.venv311\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8010
