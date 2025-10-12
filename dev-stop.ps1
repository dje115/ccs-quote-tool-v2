# Stop Development Environment

Write-Host "Stopping development environment..." -ForegroundColor Yellow
docker-compose -f docker-compose.dev.yml down
Write-Host "Development environment stopped." -ForegroundColor Green

