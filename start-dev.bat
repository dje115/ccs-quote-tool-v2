@echo off
echo Starting CCS Quote Tool v2 Development Environment...
echo.

REM Check if Docker is running
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not installed or not running
    echo Please install Docker Desktop and start it, then try again
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo WARNING: .env file not found
    echo Copying from env.example...
    copy env.example .env
    echo.
    echo IMPORTANT: Please edit .env file with your API keys before continuing
    echo You need to add:
    echo - OPENAI_API_KEY
    echo - COMPANIES_HOUSE_API_KEY  
    echo - GOOGLE_MAPS_API_KEY
    echo.
    pause
)

REM Start Docker Compose
echo Starting Docker containers...
docker-compose up -d

echo.
echo Waiting for services to start...
timeout /t 10 /nobreak >nul

echo.
echo CCS Quote Tool v2 is starting up!
echo.
echo Services:
echo - Frontend: http://localhost:3000
echo - Backend API: http://localhost:8000
echo - API Docs: http://localhost:8000/docs
echo.
echo Default Login:
echo - Email: admin@ccs.com
echo - Password: admin123
echo.
echo To view logs: docker-compose logs -f
echo To stop: docker-compose down
echo.
pause







