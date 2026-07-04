param(
    [switch]$Build,
    [string]$PublicHost = "47.111.163.239"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PackageRoot = Split-Path -Parent $ScriptDir
$SourceRoot = Join-Path $PackageRoot "source"
$OfflineComposeFile = Join-Path $SourceRoot "deploy\docker-compose.offline.yml"
$BuildComposeFile = Join-Path $SourceRoot "deploy\docker-compose.yml"

if ($Build) {
    docker compose -f $BuildComposeFile up -d --build
} else {
    docker compose -f $OfflineComposeFile up -d
}

Write-Host "Frontend:  http://$PublicHost/"
Write-Host "API base:  http://$PublicHost"
Write-Host "Health:    http://$PublicHost/api/v1/health"
Write-Host "Readiness: http://$PublicHost/api/v1/readiness"
Write-Host "Local backend: http://127.0.0.1:8010"
