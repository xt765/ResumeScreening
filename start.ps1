Write-Host "Starting Backend Service..." -ForegroundColor Green
Start-Process "uv" -ArgumentList "run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload"

Write-Host "Starting Frontend Service..." -ForegroundColor Green
Start-Process "powershell" -ArgumentList "-NoExit", "-Command", "cd frontend-new; python -m http.server 3000"

Write-Host "Application is launching in new windows..." -ForegroundColor Green
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "Backend API: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "MinIO Console: http://localhost:9001" -ForegroundColor Cyan
