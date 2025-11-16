# Restart Instructions for Version 2.10.0

## Manual Docker Restart (Windows PowerShell)

Since automated Docker commands are hanging, please run these manually:

1. **Stop all containers:**
   ```powershell
   docker-compose down
   ```

2. **Rebuild frontend (to get new version):**
   ```powershell
   docker-compose build frontend
   ```

3. **Start all services:**
   ```powershell
   docker-compose up -d
   ```

4. **Check status:**
   ```powershell
   docker-compose ps
   ```

5. **View logs if needed:**
   ```powershell
   docker-compose logs -f frontend
   ```

## What Changed in v2.10.0

- Fixed AI Analysis dialog with checkboxes for controlling data updates
- Checkboxes default to OFF (unchecked) when data already exists
- Checkboxes default to ON (checked) when no data exists
- Version updated to 2.10.0

## Testing the AI Analysis Dialog

1. Navigate to a customer with existing data (like Stephen Sanderson Transport Ltd)
2. Click the "AI Analysis" button
3. You should see a dialog with two checkboxes:
   - **Update Financial Data (Companies House)** - defaults to OFF if data exists
   - **Update Addresses (Google Maps)** - defaults to OFF if data exists
4. You can check/uncheck these to control what gets updated

