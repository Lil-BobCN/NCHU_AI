$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $repoRoot ".omx\tmp\github-auto-sync.pid"

if (-not (Test-Path -LiteralPath $pidFile)) {
    Write-Host "GitHub auto-sync is not running: PID file not found."
    exit 0
}

$pidValue = Get-Content -LiteralPath $pidFile | Select-Object -First 1
if (-not $pidValue) {
    Remove-Item -LiteralPath $pidFile -Force
    Write-Host "GitHub auto-sync PID file was empty and has been removed."
    exit 0
}

$process = Get-Process -Id ([int]$pidValue) -ErrorAction SilentlyContinue
if ($process) {
    Stop-Process -Id $process.Id -Force
    Write-Host "GitHub auto-sync stopped. PID $($process.Id)"
}
else {
    Write-Host "GitHub auto-sync process was not found. Removing stale PID file."
}

Remove-Item -LiteralPath $pidFile -Force
