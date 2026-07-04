param(
    [switch]$SkipImageLoad,
    [switch]$KeepExistingData,
    [string]$PublicHost = "47.111.163.239"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PackageRoot = Split-Path -Parent $ScriptDir
$SourceRoot = Join-Path $PackageRoot "source"
$BackupRoot = Join-Path $PackageRoot "backups"
$ImageTar = Join-Path $PackageRoot "images\school-agent-images.tar"
$ComposeFile = Join-Path $SourceRoot "deploy\docker-compose.offline.yml"
$PostgresSql = Join-Path $BackupRoot "postgres_rag.sql"
$MinioTar = Join-Path $BackupRoot "minio-data.tar"

if (-not (Test-Path $ComposeFile)) { throw "Compose file not found: $ComposeFile" }
if (-not (Test-Path $PostgresSql)) { throw "PostgreSQL backup not found: $PostgresSql" }
if (-not (Test-Path $MinioTar)) { throw "MinIO backup not found: $MinioTar" }

if (-not $SkipImageLoad) {
    if (-not (Test-Path $ImageTar)) { throw "Docker image archive not found: $ImageTar" }
    docker load -i $ImageTar
}

docker compose -f $ComposeFile down

if (-not $KeepExistingData) {
    docker volume rm -f deploy_rag_postgres_data deploy_rag_minio_data 2>$null | Out-Null
}

docker volume create deploy_rag_postgres_data | Out-Null
docker volume create deploy_rag_minio_data | Out-Null

if (-not $KeepExistingData) {
    docker run --rm -v deploy_rag_minio_data:/data -v "${BackupRoot}:/backup" busybox:1.36 sh -c "tar -C /data -xf /backup/minio-data.tar"
}

docker compose -f $ComposeFile up -d postgres redis minio

$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    docker compose -f $ComposeFile exec -T postgres pg_isready -U rag -d rag | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $ready = $true
        break
    }
    Start-Sleep -Seconds 2
}
if (-not $ready) { throw "PostgreSQL did not become ready in time." }

if (-not $KeepExistingData) {
    Get-Content -LiteralPath $PostgresSql -Encoding UTF8 | docker compose -f $ComposeFile exec -T postgres psql -U rag -d rag
}

docker compose -f $ComposeFile up -d backend worker frontend

for ($i = 0; $i -lt 30; $i++) {
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:8010/api/v1/health" -TimeoutSec 5
        if ($health.code -eq 0) {
            Write-Host "Backend health ok."
            break
        }
    } catch {
        Start-Sleep -Seconds 2
    }
}

Write-Host "Deployment restored."
Write-Host "Frontend:  http://$PublicHost/"
Write-Host "API base:  http://$PublicHost"
Write-Host "Health:    http://$PublicHost/api/v1/health"
Write-Host "Readiness: http://$PublicHost/api/v1/readiness"
Write-Host "MinIO:     http://${PublicHost}:9003"
