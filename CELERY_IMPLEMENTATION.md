# Celery Background Task Implementation

## Overview
Successfully implemented production-ready Celery background task processing for long-running lead generation campaigns. This replaces the unreliable FastAPI `BackgroundTasks` with a robust, scalable solution.

## Date Implemented
October 12, 2025

## What Was Implemented

### 1. Celery Configuration (`backend/app/core/celery_app.py`)
- **Broker & Backend**: Redis (redis://redis:6379/0)
- **Task Serialization**: JSON
- **Worker Configuration**:
  - Prefetch multiplier: 1 (process one task at a time)
  - Max tasks per child: 50 (prevent memory leaks)
  - Task time limit: 2 hours
  - Soft time limit: 1h 55m
  - Late acknowledgment enabled
  - Reject on worker loss enabled

### 2. Campaign Task (`backend/app/tasks/campaign_tasks.py`)
- **`run_campaign_task`**: Main Celery task for campaign execution
  - Max retries: 3
  - Retry delay: 5 minutes
  - Automatic retry on transient errors (timeout, connection)
  - Comprehensive logging with banners
  - Error handling with campaign status updates

### 3. API Endpoints Updates (`backend/app/api/v1/endpoints/campaigns.py`)
- **POST `/campaigns/{id}/start`**: Start a DRAFT campaign
  - Validates status is DRAFT
  - Sets status to QUEUED
  - Queues task to Celery using `celery_app.send_task()`
  - Returns task_id for tracking

- **POST `/campaigns/{id}/restart`**: Restart completed/failed/cancelled campaigns
  - Resets all campaign statistics
  - Sets status to QUEUED
  - Queues task to Celery
  - Returns task_id

- **POST `/campaigns/{id}/stop`**: Stop running campaigns
  - Sets status to CANCELLED
  - Marks completion time

- **POST `/campaigns`**: Create campaign
  - Creates campaign in DRAFT status
  - Requires explicit `/start` call to execute

### 4. Campaign Status Flow
```
DRAFT → (user clicks Start) → QUEUED → (Celery picks up) → RUNNING → COMPLETED/FAILED
```

New statuses added:
- **QUEUED**: Campaign queued in Celery, waiting for worker
- **RUNNING**: Currently executing in Celery worker

### 5. Database Migration
- Added `QUEUED` status to `leadgenerationstatus` enum
- Migration file: `backend/migrations/add_queued_status.sql`

### 6. Docker Compose Updates (`docker-compose.dev.yml`)
Added two new services:

**celery-worker**:
```yaml
command: celery -A app.core.celery_app worker --loglevel=info --concurrency=2
depends_on: postgres, redis
restart: unless-stopped
```

**celery-beat** (for future scheduled tasks):
```yaml
command: celery -A app.core.celery_app beat --loglevel=info
depends_on: postgres, redis
restart: unless-stopped
```

### 7. Frontend Updates (`frontend/src/pages/Campaigns.tsx`)
- Added **Start** button (green play icon) for DRAFT campaigns
- Added **Restart** button (blue replay icon) for COMPLETED/FAILED/CANCELLED campaigns
- Added **Stop** button (red stop icon) for RUNNING campaigns
- Added **Queued** indicator for campaigns waiting in Celery queue
- Auto-refresh every 10 seconds to show status changes
- Actions column in campaigns table

### 8. Lead Generation Service Updates
**Fixed API Key Resolution**:
- Service now properly fetches Tenant object from database
- Uses `get_api_keys(db, tenant)` helper for key resolution
- Fallback order: Tenant keys → System keys
- Added comprehensive logging of key source

**OpenAI SDK Upgrade**:
- Upgraded from `openai==1.58.1` to `openai==2.1.0`
- Restored Responses API with web_search tool
- Using `gpt-5-mini` model with 20,000 tokens
- 240-second timeout for web search operations

## Key Benefits

### 1. **Reliability**
- Celery workers run in separate processes
- Automatic retry on failures
- Tasks survive API server restarts
- Proper task acknowledgment

### 2. **Scalability**
- Can add multiple Celery workers
- Tasks distributed across workers
- Horizontal scaling ready
- Queue-based architecture

### 3. **Monitoring**
- Real-time task status in database
- Celery task IDs for tracking
- Comprehensive logging
- Frontend shows live status updates

### 4. **User Experience**
- Campaigns don't block API
- Users can start multiple campaigns
- Clear status indicators
- Easy restart on failure

## Configuration

### Environment Variables
All services use the same environment variables:
```env
DATABASE_URL=postgresql://postgres:postgres_password_2025@postgres:5432/ccs_quote_tool
REDIS_URL=redis://redis:6379/0
SECRET_KEY=ccs_super_secret_key_2025_change_in_production
```

### API Keys
- Stored in database (`tenants` table)
- Tenant-specific keys checked first
- Falls back to System tenant keys
- Resolution happens in Celery worker

## Testing

### Manual Test Script
`test_celery_campaign.py` - Comprehensive test that:
1. Logs in
2. Creates test campaign
3. Starts campaign via API
4. Polls status until completion
5. Reports results

### Test Results
✅ Campaigns queue to Celery successfully
✅ Celery worker picks up tasks
✅ API keys resolve correctly (tenant → system fallback)
✅ OpenAI client initializes with Responses API
✅ Status updates flow correctly through system
✅ Frontend shows real-time status changes

## Monitoring Commands

### View Celery Worker Logs
```bash
docker logs ccs-celery-worker -f
```

### View Backend Logs
```bash
docker logs ccs-backend -f
```

### Check Campaign Status
```bash
docker exec ccs-postgres psql -U postgres -d ccs_quote_tool \
  -c "SELECT id, name, status, leads_created FROM lead_generation_campaigns ORDER BY created_at DESC LIMIT 10;"
```

### Restart Services
```bash
# Development
docker-compose -f docker-compose.dev.yml restart celery-worker backend

# Production
docker-compose -f docker-compose.prod.yml restart celery-worker backend
```

## Known Issues & Future Enhancements

### Current Limitations
1. **Stop functionality**: Currently sets status to CANCELLED but doesn't terminate running task
   - Future: Implement proper task revocation
2. **No task queue monitoring**: No UI for viewing Celery queue
   - Future: Add Flower (Celery monitoring tool)
3. **Single queue**: All tasks go to default 'celery' queue
   - Future: Separate queues for priority tasks

### Future Enhancements
1. **Scheduled Campaigns**: Use Celery Beat for recurring campaigns
2. **Progress Updates**: Real-time progress during execution
3. **Task Priorities**: Priority queue for urgent campaigns
4. **Batch Operations**: Bulk start/stop/restart
5. **Email Notifications**: Alert when campaign completes
6. **Webhook Support**: POST results to external systems

## Architecture Diagram

```
┌─────────────┐
│   Frontend  │
│  (React)    │
└──────┬──────┘
       │ HTTP POST /campaigns/{id}/start
       ▼
┌─────────────┐
│   Backend   │
│  (FastAPI)  │ ──┐
└──────┬──────┘   │ Send Task
       │          │
       │          ▼
       │     ┌──────────┐
       │     │  Redis   │◄────┐
       │     │ (Broker) │     │
       │     └──────────┘     │
       │                      │ Get Task
       │                      │
       ▼                      │
┌──────────────┐         ┌────┴─────┐
│  PostgreSQL  │◄────────│  Celery  │
│  (Database)  │  Update │  Worker  │
└──────────────┘  Status └──────────┘
                            │
                            │ Call OpenAI
                            │ Call Google Maps
                            │ Call Companies House
                            ▼
                      ┌──────────────┐
                      │ External APIs│
                      └──────────────┘
```

## Files Modified

### Backend
- `backend/requirements.txt` - Added/updated: celery==5.4.0, openai==2.1.0
- `backend/app/core/celery_app.py` - NEW: Celery configuration
- `backend/app/tasks/__init__.py` - NEW: Tasks package
- `backend/app/tasks/campaign_tasks.py` - NEW: Campaign tasks
- `backend/app/api/v1/endpoints/campaigns.py` - Updated: Start/restart/stop endpoints
- `backend/app/models/leads.py` - Updated: Added QUEUED status
- `backend/app/services/lead_generation_service.py` - Fixed: API key resolution, OpenAI Responses API
- `backend/migrations/add_queued_status.sql` - NEW: Database migration

### Frontend
- `frontend/src/pages/Campaigns.tsx` - Updated: Added action buttons, handlers
- `frontend/src/services/api.ts` - Updated: Added start/restart methods

### Docker
- `docker-compose.dev.yml` - Added: celery-worker, celery-beat services

### Documentation
- `CELERY_IMPLEMENTATION.md` - NEW: This file

## Conclusion

The Celery implementation provides a robust, production-ready solution for background task processing in the CCS Quote Tool v2. It enables reliable, scalable lead generation campaigns that can run for extended periods without blocking the API or affecting user experience.

**Status**: ✅ **PRODUCTION READY**
**Version**: 2.1.0
**Implementation Date**: October 12, 2025


