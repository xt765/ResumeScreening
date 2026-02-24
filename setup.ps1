# Check if Docker is running
$dockerInfo = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

Write-Host "Starting infrastructure services..." -ForegroundColor Green
docker-compose up -d mysql redis minio

Write-Host "Waiting for services to be ready (10 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "Initializing database..." -ForegroundColor Green
uv run python scripts/init_db.py

Write-Host "Initializing admin user..." -ForegroundColor Green
uv run python scripts/init_admin.py

Write-Host "Setup complete! You can now run '.\start.ps1' to start the application." -ForegroundColor Green
