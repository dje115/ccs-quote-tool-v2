# Start Development Environment
# This script starts the CCS Quote Tool v2 in DEVELOPMENT mode with hot-reload enabled
# 
# Development URLs:
# - Frontend:      http://localhost:3001
# - Admin Portal:  http://localhost:3011
# - Backend API:   http://localhost:8001
#
# Features:
# - Hot-reload for frontend and admin portal (changes appear instantly)
# - Volume mounts for backend (manual restart needed for changes)
# - Development-optimized build

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CCS Quote Tool v2 - DEVELOPMENT MODE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting development environment..." -ForegroundColor Green
Write-Host ""
Write-Host "Access points:" -ForegroundColor Yellow
Write-Host "  Frontend:      http://localhost:3001" -ForegroundColor White
Write-Host "  Admin Portal:  http://localhost:3011" -ForegroundColor White
Write-Host "  Backend API:   http://localhost:8001" -ForegroundColor White
Write-Host ""

docker-compose -f docker-compose.dev.yml up -d

Write-Host ""
Write-Host "Development environment started!" -ForegroundColor Green
Write-Host "Hot-reload is enabled for frontend and admin portal." -ForegroundColor Green
Write-Host ""
Write-Host "To view logs: docker-compose -f docker-compose.dev.yml logs -f" -ForegroundColor Cyan
Write-Host "To stop:      docker-compose -f docker-compose.dev.yml down" -ForegroundColor Cyan
