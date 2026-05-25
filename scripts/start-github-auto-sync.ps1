param(
    [int]$IntervalSeconds = 60
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$syncScript = Join-Path $PSScriptRoot "git-safe-sync.ps1"
$tmpDir = Join-Path $repoRoot ".omx\tmp"
$logDir = Join-Path $repoRoot ".omx\logs"
$pidFile = Join-Path $tmpDir "github-auto-sync.pid"
$outLog = Join-Path $logDir "github-auto-sync.out.log"
$errLog = Join-Path $logDir "github-auto-sync.err.log"

New-Item -ItemType Directory -Force -Path $tmpDir, $logDir | Out-Null

if (Test-Path -LiteralPath $pidFile) {
    $existingPid = (Get-Content -LiteralPath $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
    if ($existingPid -and (Get-Process -Id ([int]$existingPid) -ErrorAction SilentlyContinue)) {
        Write-Host "GitHub auto-sync is already running with PID $existingPid"
        exit 0
    }
}

$arguments = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", "`"$syncScript`"",
    "-Watch",
    "-IntervalSeconds", $IntervalSeconds.ToString()
)

$process = Start-Process `
    -FilePath "powershell.exe" `
    -ArgumentList $arguments `
    -WorkingDirectory $repoRoot `
    -WindowStyle Hidden `
    -RedirectStandardOutput $outLog `
    -RedirectStandardError $errLog `
    -PassThru

Set-Content -LiteralPath $pidFile -Value $process.Id -Encoding ASCII
Write-Host "GitHub auto-sync started with PID $($process.Id). Logs: $outLog"
