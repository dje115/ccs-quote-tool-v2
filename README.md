# CCS Quote Tool v2 - World-Class AI-Powered CRM & Quoting System

**Version:** 3.1.0  
**Status:** Production Ready  
**Architecture:** Multi-Tenant SaaS

---

## 🎯 Quick Start

### Development Mode (Hot-Reload)

```powershell
# Start development environment with hot-reload
docker-compose up -d

# View logs
docker-compose logs -f
```

**Access:**
- Frontend (CRM): http://localhost:3000
- Admin Portal: http://localhost:3010  
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

**Default Login:**
- Email: `admin@ccs.com`
- Password: `admin123`

### Production Mode (Optimized Build)

```powershell
# Build and start production environment
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## 📚 Documentation

**IMPORTANT:** Read these guides for complete understanding:

1. **[DEVELOPMENT_ENVIRONMENT.md](./DEVELOPMENT_ENVIRONMENT.md)** ⭐ **START HERE**
   - Development vs Production modes
   - Hot-reload configuration
   - Docker setup and workflow
   - Troubleshooting guide

2. **[AI_DISCOVERY_ANALYSIS.md](./AI_DISCOVERY_ANALYSIS.md)** 🤖 **NEW**
   - AI-powered discovery analysis
   - Automatic contact extraction
   - Business intelligence features
   - Usage guide and best practices

3. **[USER_PERMISSIONS_SYSTEM.md](./USER_PERMISSIONS_SYSTEM.md)** 🔐 **NEW**
   - Role-based access control
   - Permission matrix
   - User management
   - Security features

4. **[DISCOVERY_TO_CRM_WORKFLOW.md](./DISCOVERY_TO_CRM_WORKFLOW.md)**
   - Discovery to CRM lead conversion
   - Status progression workflow
   - Multi-select and bulk operations

5. **[CAMPAIGNS_GUIDE.md](./CAMPAIGNS_GUIDE.md)**
   - Lead generation system
   - Campaign types and configuration
   - AI-powered lead discovery
   - Best practices

6. **[CAMPAIGN_MIGRATION.md](./CAMPAIGN_MIGRATION.md)**
   - Technical migration details from v1 to v2
   - Feature comparisons
   - Architecture improvements

7. **[SLA_AND_SUPPORT_CONTRACTS.md](./SLA_AND_SUPPORT_CONTRACTS.md)** 🆕 **NEW**
   - Complete SLA management system
   - Support contracts with SLA policies
   - SLA compliance tracking and reporting
   - Policy templates and configuration
   - Analytics and forecasting

8. **[CHANGELOG.md](./CHANGELOG.md)**
   - Version history
   - Recent changes and fixes

---

## 🏗️ Architecture

### Tech Stack

**Backend:**
- **FastAPI** - Modern Python web framework
- **PostgreSQL 16** - Primary database
- **Redis 7** - Caching and sessions
- **SQLAlchemy 2.0** - ORM
- **Alembic** - Database migrations
- **OpenAI API** - GPT-5-mini for AI features
- **Google Maps API** - Location services
- **Companies House API** - UK business verification

**Frontend:**
- **React 18** - Main CRM interface
- **Material-UI (MUI)** - Component library
- **Vite** - Build tool and dev server
- **TypeScript** - Type safety
- **React Router v7** - Navigation (upgraded from v6)
- **Axios** - HTTP client

**Admin Portal:**
- **Vue.js 3** - Admin interface
- **Element Plus** - UI components
- **Vite** - Build tool
- **TypeScript** - Type safety

**Infrastructure:**
- **Docker** - Containerization
- **Docker Compose** - Orchestration
- **Nginx** - Production web server

---

## 🚀 Features

### ✨ Core CRM Features
- **Multi-tenant SaaS architecture**
- **Customer management** with AI analysis
- **Contact management** with multiple contacts per customer
- **Lead scoring** and qualification
- **Customer status workflow:** DISCOVERY → LEAD → PROSPECT → OPPORTUNITY → CUSTOMER
- **AI-powered company analysis** using GPT-5-mini
- **Financial analysis** from Companies House data
- **Director information** with "Add as Contact" functionality
- **Multiple addresses** per customer with Google Maps integration
- **LinkedIn and website analysis**
- **Sales activity tracking**
- **Notes and interactions history**

### 🎯 Lead Generation Campaigns
- **AI-powered lead discovery** using GPT-5-mini with web search
- **Dynamic campaign prompts** that adapt to each tenant's business profile
- **13+ campaign types** including new advanced types:
  - **Dynamic Business Search** - AI adapts to tenant's services and target markets
  - **Service Gap Analysis** - Find businesses missing tenant's services
  - **Custom Search** - User-defined AI search queries with tenant context
  - **Company List Import** - Analyze specific companies with tenant targeting
  - **Similar Business Lookup** - Find companies like existing customers
  - Traditional types: IT/MSP, Education, Healthcare, Manufacturing, etc.
- **Enhanced campaign management** with working stop/start/restart functionality
- **Improved data extraction** with comprehensive Google Maps place details (phone, website)
- **Multi-source data enrichment:**
  - Google Maps API (locations, ratings)
  - Companies House API (financials, directors)
  - LinkedIn profiles
  - Website scraping
- **Intelligent deduplication** against customers and existing leads
- **Background processing** (3-10 minutes per campaign)
- **Real-time campaign monitoring**
- **Lead-to-customer conversion** with DISCOVERY status
- **Tenant-specific targeting** - Campaigns automatically use tenant's business profile

### 🔐 Authentication & Security
- **JWT-based authentication**
- **Role-based access control (RBAC)**
- **Row-level security (RLS)** for multi-tenant data isolation
- **Argon2 password hashing**
- **Session management** with Redis

### 🌍 Internationalization
- **Multi-language support** (i18next)
- **AI-powered translation** for UI elements
- **User-selectable language preferences**

### 🎨 Modern UI/UX
- **Colorful gradient statistics cards**
- **Tabbed interface** for better organization
- **Real-time updates** with auto-refresh
- **Responsive design** for all screen sizes
- **Dark mode support** (coming soon)
- **Emoji icons** for visual hierarchy
- **Advanced sorting functionality** with visual indicators
- **Enhanced table interactions** with clickable headers and hover effects
- **Improved campaign management** with working controls
- **Better data display** with proper campaign names and relationships

### 📊 SLA & Support Contracts System 🆕
- **Comprehensive SLA policy management** with flexible configuration
- **8 pre-configured SLA policy templates** (Standard, Extended, 24/7, Premium, etc.)
- **Real-time SLA compliance tracking** and monitoring
- **SLA breach detection** with warning and critical levels
- **Auto-escalation workflow** on SLA breaches (priority escalation, auto-assignment, system comments)
- **Email notifications** for SLA breaches to assigned agents and admins
- **Scheduled SLA compliance reports** (daily, weekly, monthly) via Celery Beat
- **Support contract management** with SLA policy linking
- **SLA breach indicators** (green/orange/red flags) on Customers and Leads list pages
- **Customer SLA widget** on customer detail page with compliance metrics
- **SLA compliance history** per customer with daily tracking and trends
- **Enhanced helpdesk dashboard** with SLA metrics cards
- **SLA Analytics Dashboard** with Chart.js visualizations (Doughnut, Bar, Line charts)
- **Custom Report Builder** for SLA and customer data with multiple export formats
- **Agent performance tracking** by SLA compliance
- **Historical trends analysis** with forecasting-ready data structure
- **SLA factors integrated** into customer health scoring

---

## 📁 Project Structure

```
CCS Quote Tool v2/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/v1/endpoints/  # API endpoints
│   │   ├── core/              # Core configuration
│   │   ├── models/            # Database models
│   │   ├── services/          # Business logic
│   │   └── migrations/        # Database migrations
│   ├── Dockerfile             # Production dockerfile
│   └── requirements.txt       # Python dependencies
│
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/             # Page components
│   │   ├── services/          # API services
│   │   └── i18n/              # Translations
│   ├── Dockerfile             # Production dockerfile
│   ├── Dockerfile.dev         # Development dockerfile
│   └── package.json           # Node dependencies
│
├── admin-portal/               # Vue.js admin portal
│   ├── src/
│   │   ├── components/        # Vue components
│   │   ├── views/             # Page views
│   │   └── api/               # API services
│   ├── Dockerfile             # Production dockerfile
│   ├── Dockerfile.dev         # Development dockerfile
│   └── package.json           # Node dependencies
│
├── docker-compose.yml         # Development config (default)
├── docker-compose.dev.yml     # Development config (explicit)
├── docker-compose.prod.yml    # Production config
├── dev-start.ps1              # Quick start script
│
└── Documentation/
    ├── README.md                      # This file
    ├── DEVELOPMENT_ENVIRONMENT.md     # Dev guide ⭐
    ├── CAMPAIGNS_GUIDE.md             # Campaign system guide
    ├── CAMPAIGN_MIGRATION.md          # Migration notes
    └── CHANGELOG.md                   # Version history
```

---

## 🔧 Development Workflow

### Daily Development

1. **Start development environment:**
   ```bash
   docker-compose up -d
   ```

2. **Edit code** - Changes are automatically detected:
   - Frontend: `frontend/src/**` → Browser auto-refreshes
   - Backend: `backend/app/**` → API auto-reloads
   - Admin: `admin-portal/src/**` → Portal auto-updates

3. **View logs** (optional):
   ```bash
   docker-compose logs -f [service-name]
   ```

4. **Stop when done:**
   ```bash
   docker-compose down
   ```

### Making Changes

**Frontend Changes:**
```bash
# Edit any file in frontend/src/
notepad frontend/src/pages/Campaigns.tsx

# Save - browser refreshes automatically within 1-2 seconds
```

**Backend Changes:**
```bash
# Edit any file in backend/app/
notepad backend/app/api/v1/endpoints/campaigns.py

# Save - API reloads automatically
```

**Database Migrations:**
```bash
# Run SQL migration
Get-Content "backend/migrations/my_migration.sql" | docker-compose exec -T postgres psql -U postgres -d ccs_quote_tool

# Restart backend
docker-compose restart backend
```

### Testing Production Build

```bash
# Stop development
docker-compose down

# Build and start production
docker-compose -f docker-compose.prod.yml up -d --build

# Test at http://localhost:3000

# Switch back to development
docker-compose -f docker-compose.prod.yml down
docker-compose up -d
```

---

## 🔑 Environment Variables

### Required API Keys

For full functionality, configure these API keys in the Settings page or `.env` file:

1. **OpenAI API Key** (Required for AI features)
   - Get from: https://platform.openai.com
   - Used for: Lead generation, company analysis, translations

2. **Google Maps API Key** (Recommended)
   - Get from: https://console.cloud.google.com
   - Used for: Location services, address verification

3. **Companies House API Key** (Recommended for UK)
   - Get from: https://developer.company-information.service.gov.uk
   - Used for: Company verification, financial data

### Configuration

**Option 1: Via UI (Recommended)**
- Login → Settings → API Keys
- Add keys per tenant or system-wide

**Option 2: Via .env file**
```env
OPENAI_API_KEY=sk-...
GOOGLE_MAPS_API_KEY=...
COMPANIES_HOUSE_API_KEY=...
```

---

## 🧪 Testing

### Test Campaign Creation

1. Navigate to **Campaigns** page
2. Click **New Campaign**
3. Fill in details:
   - Name: "Test Campaign"
   - Type: IT/MSP Expansion
   - Postcode: LE17 5NJ
   - Distance: 15 miles
   - Max Results: 20
4. Click **Start Campaign**
5. Wait 3-5 minutes
6. View generated leads

### Test Customer Management

1. Navigate to **Customers** page
2. Click **Add Customer**
3. Enter company name: "Central Technology Ltd"
4. Click **Save**
5. Click **Run AI Analysis**
6. View enriched data (Companies House, Google Maps, LinkedIn)

---

## 📊 System Requirements

### Minimum
- **RAM:** 4GB
- **CPU:** 2 cores
- **Disk:** 10GB
- **OS:** Windows 10+, macOS 10.15+, Linux

### Recommended
- **RAM:** 8GB+
- **CPU:** 4+ cores
- **Disk:** 20GB+
- **OS:** Windows 11, macOS 12+, Ubuntu 22.04+

### Software
- **Docker Desktop:** Latest version
- **Git:** Latest version
- **PowerShell:** 7+ (Windows)

---

## 🐛 Troubleshooting

### Frontend not updating?
```bash
docker-compose restart frontend
docker-compose logs -f frontend
```

### Backend not responding?
```bash
docker-compose restart backend
docker-compose logs -f backend
```

### Database connection issues?
```bash
docker-compose restart postgres
docker-compose exec postgres pg_isready
```

### Full reset (deletes all data):
```bash
docker-compose down -v
docker-compose up -d
```

### More help?
See **[DEVELOPMENT_ENVIRONMENT.md](./DEVELOPMENT_ENVIRONMENT.md)** for detailed troubleshooting.

---

## 📝 Version History

### v2.6.0 (Current) - October 2025

**Major Features:**
- ✅ Complete lead generation campaign system
- ✅ AI-powered lead discovery with GPT-5-mini
- ✅ Multi-source data enrichment
- ✅ DISCOVERY and OPPORTUNITY customer statuses
- ✅ Modern UI with gradient statistics cards
- ✅ Development environment with hot-reload
- ✅ Comprehensive documentation
- ✅ Enhanced campaign management with working controls
- ✅ Fixed dashboard statistics and lead counts
- ✅ Improved delete functionality across all components

**Technical:**
- ✅ Development/Production Docker configurations
- ✅ FastAPI BackgroundTasks for campaign processing
- ✅ React 18 with Material-UI and Vite
- ✅ React Router v7 (upgraded from v6)
- ✅ Vue.js admin portal
- ✅ PostgreSQL 16 + Redis 7
- ✅ Multi-tenant architecture
- ✅ Enhanced error handling and null safety

See **[CHANGELOG.md](./CHANGELOG.md)** for complete history.

---

## 🤝 Contributing

### Development Process

1. **Create feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes** in development mode

3. **Test locally:**
   ```bash
   # Test in development
   docker-compose up -d
   
   # Test in production
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

4. **Commit changes:**
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

5. **Push and create PR:**
   ```bash
   git push origin feature/your-feature-name
   ```

### Code Standards

- **Python:** PEP 8, type hints, docstrings
- **TypeScript:** ESLint, Prettier
- **Commits:** Conventional Commits format
- **Documentation:** Update relevant .md files

---

## 📞 Support

### Documentation
- **Development Guide:** [DEVELOPMENT_ENVIRONMENT.md](./DEVELOPMENT_ENVIRONMENT.md)
- **Campaign Guide:** [CAMPAIGNS_GUIDE.md](./CAMPAIGNS_GUIDE.md)
- **Migration Guide:** [CAMPAIGN_MIGRATION.md](./CAMPAIGN_MIGRATION.md)

### Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f frontend
docker-compose logs -f backend
```

### Database
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d ccs_quote_tool

# List tables
docker-compose exec postgres psql -U postgres -d ccs_quote_tool -c "\dt"
```

---

## 📜 License

Proprietary - CCS Technology Ltd  
All Rights Reserved

---

## 🎉 Credits

**Developed by:** CCS Development Team  
**AI Integration:** OpenAI GPT-5-mini  
**Location Services:** Google Maps API  
**Business Data:** Companies House API  

---

**🚀 Happy Coding!**

For detailed development instructions, always refer to **[DEVELOPMENT_ENVIRONMENT.md](./DEVELOPMENT_ENVIRONMENT.md)**
