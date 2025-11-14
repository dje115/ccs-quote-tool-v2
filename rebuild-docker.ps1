# PowerShell script to rebuild Docker containers with version information
# This ensures the version displayed matches the VERSION file

param(
    [string]$Environment = "dev",
    [switch]$NoCache
)

# Read version from VERSION file
$versionFile = Join-Path $PSScriptRoot "VERSION"
if (Test-Path $versionFile) {
    $APP_VERSION = (Get-Content $versionFile -Raw).Trim()
    Write-Host "📦 Version from VERSION file: $APP_VERSION" -ForegroundColor Green
} else {
    $APP_VERSION = "2.5.0"
    Write-Host "⚠️  VERSION file not found, using default: $APP_VERSION" -ForegroundColor Yellow
}

# Get build date
$BUILD_DATE = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"

# Get git hash if available
$BUILD_HASH = ""
if (Get-Command git -ErrorAction SilentlyContinue) {
    $gitOutput = git rev-parse HEAD 2>&1
    if ($LASTEXITCODE -eq 0 -and $gitOutput) {
        $BUILD_HASH = $gitOutput.ToString().Trim()
        Write-Host "🔖 Git hash: $BUILD_HASH" -ForegroundColor Cyan
    }
}

# Set environment variables
$env:APP_VERSION = $APP_VERSION
$env:BUILD_DATE = $BUILD_DATE
if ($BUILD_HASH) {
    $env:BUILD_HASH = $BUILD_HASH
}

Write-Host "`n🚀 Rebuilding Docker containers..." -ForegroundColor Cyan
Write-Host "   Environment: $Environment" -ForegroundColor Cyan
Write-Host "   Version: $APP_VERSION" -ForegroundColor Cyan
Write-Host "   Build Date: $BUILD_DATE" -ForegroundColor Cyan
if ($BUILD_HASH) {
    Write-Host "   Build Hash: $BUILD_HASH" -ForegroundColor Cyan
}
Write-Host ""

# Determine docker-compose file
if ($Environment -eq "prod") {
    $composeFile = "docker-compose.prod.yml"
    Write-Host "📋 Using production configuration" -ForegroundColor Yellow
} else {
    $composeFile = "docker-compose.yml"
    Write-Host "📋 Using development configuration" -ForegroundColor Yellow
}

# Build arguments
$buildArgs = @()
if ($NoCache) {
    $buildArgs += "--no-cache"
}

# Stop existing containers
Write-Host "`n🛑 Stopping existing containers..." -ForegroundColor Yellow
docker-compose -f $composeFile down

# Rebuild and start
Write-Host "`n🔨 Building containers..." -ForegroundColor Cyan
docker-compose -f $composeFile build @buildArgs

Write-Host "`n▶️  Starting containers..." -ForegroundColor Green
docker-compose -f $composeFile up -d

Write-Host "`n✅ Rebuild complete!" -ForegroundColor Green
Write-Host "`n📊 Container status:" -ForegroundColor Cyan
docker-compose -f $composeFile ps

Write-Host "`n💡 To view logs: docker-compose -f $composeFile logs -f" -ForegroundColor Gray
Write-Host "💡 Version will be displayed in the UI footer" -ForegroundColor Gray

