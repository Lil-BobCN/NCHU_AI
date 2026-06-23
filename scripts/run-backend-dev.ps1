$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

$env:PYTHONPATH = "backend"
& ".\.venv311\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8010
