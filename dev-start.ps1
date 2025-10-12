# Start the application in DEVELOPMENT mode
# This provides hot-reload for frontend changes

Write-Host "🚀 Starting CCS Quote Tool v2 in DEVELOPMENT mode..." -ForegroundColor Green
Write-Host ""
Write-Host "Features:" -ForegroundColor Cyan
Write-Host "  ✓ Hot-reload enabled for frontend" -ForegroundColor Gray
Write-Host "  ✓ Hot-reload enabled for admin portal" -ForegroundColor Gray
Write-Host "  ✓ Source code mounted as volumes" -ForegroundColor Gray
Write-Host "  ✓ Fast development iteration" -ForegroundColor Gray
Write-Host ""

# Stop any running containers
docker-compose down

# Start in development mode
docker-compose -f docker-compose.dev.yml up -d

Write-Host ""
Write-Host "✅ Development environment started!" -ForegroundColor Green
Write-Host ""
Write-Host "Access your applications:" -ForegroundColor Yellow
Write-Host "  📱 Frontend (CRM):     http://localhost:3000" -ForegroundColor White
Write-Host "  🎛️  Admin Portal:       http://localhost:3010" -ForegroundColor White
Write-Host "  🔧 Backend API:        http://localhost:8000" -ForegroundColor White
Write-Host "  📚 API Docs:           http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "To view logs: docker-compose logs -f" -ForegroundColor Gray
Write-Host "To stop:      docker-compose down" -ForegroundColor Gray
Write-Host ""

