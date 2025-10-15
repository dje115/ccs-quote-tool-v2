# Start Production Environment
# This script starts the CCS Quote Tool v2 in PRODUCTION mode
# 
# Production URLs:
# - Frontend:      http://localhost:3000
# - Admin Portal:  http://localhost:3010
# - Backend API:   http://localhost:8000
#
# Features:
# - Optimized production builds
# - No hot-reload (requires rebuild for changes)
# - Production-ready configuration

Write-Host "========================================" -ForegroundColor Magenta
Write-Host "  CCS Quote Tool v2 - PRODUCTION MODE" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""
Write-Host "Starting production environment..." -ForegroundColor Green
Write-Host ""
Write-Host "Access points:" -ForegroundColor Yellow
Write-Host "  Frontend:      http://localhost:3000" -ForegroundColor White
Write-Host "  Admin Portal:  http://localhost:3010" -ForegroundColor White
Write-Host "  Backend API:   http://localhost:8000" -ForegroundColor White
Write-Host ""

docker-compose -f docker-compose.prod.yml up -d

Write-Host ""
Write-Host "Production environment started!" -ForegroundColor Green
Write-Host ""
Write-Host "To view logs: docker-compose -f docker-compose.prod.yml logs -f" -ForegroundColor Cyan
Write-Host "To stop:      docker-compose -f docker-compose.prod.yml down" -ForegroundColor Cyan


