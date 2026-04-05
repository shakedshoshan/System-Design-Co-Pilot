# Start Postgres (pgvector) from this repo's docker-compose.yml.
# Requires Docker Desktop running on Windows.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "Starting postgres (docker compose)..." -ForegroundColor Cyan
docker compose up -d postgres
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker failed. Is Docker Desktop started?" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Waiting for health..." -ForegroundColor Cyan
$deadline = (Get-Date).AddMinutes(2)
do {
    $status = docker inspect -f "{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}" sdc-postgres 2>$null
    if ($status -eq "healthy") { break }
    Start-Sleep -Seconds 2
} while ((Get-Date) -lt $deadline)

docker compose ps postgres
Write-Host ""
Write-Host "DATABASE_URL (see .env): postgresql+psycopg://app:app@localhost:5433/system_design_copilot" -ForegroundColor Green
Write-Host "Next: poetry run migrate upgrade head" -ForegroundColor Green
