@echo off
echo Checking Docker Build Status...
echo.

REM Check if containers are running
docker ps -a --filter "name=ccs-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo.
echo Checking Docker images...
docker images | findstr "ccs-"

echo.
echo To view build logs:
echo docker-compose logs -f backend
echo.
echo To view all logs:
echo docker-compose logs -f
echo.
pause




