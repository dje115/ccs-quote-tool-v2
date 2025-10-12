# Stop Production Environment

Write-Host "Stopping production environment..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml down
Write-Host "Production environment stopped." -ForegroundColor Green

