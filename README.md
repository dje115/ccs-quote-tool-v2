# CCS Quote Tool v2 - Multi-Tenant SaaS Platform
## Modern CRM & Quoting Platform with AI-Powered Features

[![Version](https://img.shields.io/badge/version-2.2.0-blue.svg)](https://github.com/dje115/ccs-quote-tool-v2)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://docker.com)
[![Multi-tenant](https://img.shields.io/badge/multi--tenant-enabled-green.svg)](#)
[![AI-Powered](https://img.shields.io/badge/AI--powered-GPT5-orange.svg)](#)

A modern, scalable, multi-tenant SaaS platform for customer relationship management and quoting with AI-powered lead generation, **multilingual support with 10 languages**, **Argon2 security**, and comprehensive business intelligence.

## ✨ **Latest Features (v2.2.0)**

### **CRM Module - COMPLETED** ✅
- 🎯 **Advanced Customer Management**: Multi-tab interface with AI-powered insights
- 👥 **Smart Contact Management**: Multiple emails/phones per contact with role management
- 🤖 **AI Business Intelligence**: Company analysis, lead scoring, competitor identification
- 📊 **Financial Analysis**: Multi-year financial data with trends and health scoring
- 🗺️ **Google Maps Integration**: Multi-location discovery with address validation
- 🏢 **Companies House Integration**: Director information, financial data, iXBRL parsing
- 📝 **Known Facts System**: User-provided context for improved AI accuracy
- 🌐 **Website & LinkedIn Analysis**: Social media and web presence insights

### **Core Features**
- 🌍 **Multilingual Support**: 10 languages (EN, ES, FR, DE, IT, PT, NL, RU, JA, ZH) with AI-powered translation
- 🛡️ **Argon2 Security**: Industry-leading password hashing (winner of Password Hashing Competition 2015)
- 🤖 **GPT-5 Integration**: All AI operations use GPT-5 models exclusively
- 🏢 **Multi-Tenant SaaS**: Complete tenant isolation with row-level security
- 📱 **Modern UI**: Material-UI with Vite build system for blazing-fast development

### **Admin Portal** (Port 3010)
- 🔑 **Global API Key Management**: Centralized API configuration with status indicators
- 👨‍💼 **Tenant Management**: Create, edit, activate, and manage tenants
- 👥 **User Management**: View all users, search by tenant, reset passwords
- 📊 **Dashboard Analytics**: Real-time tenant and user statistics

## 🚀 **Quick Start**

### **Prerequisites**
- Docker & Docker Compose
- Git
- OpenAI API Key (for GPT-5)
- Companies House API Key (optional)
- Google Maps API Key (optional)

### **Installation**

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-repo/ccs-quote-tool-v2.git
   cd ccs-quote-tool-v2
   ```

2. **Configure environment**
   ```bash
   copy env.example .env
   # Edit .env with your API keys
   ```

3. **Start the development environment**
   ```bash
   # Windows
   start-dev.bat
   
   # Linux/Mac
   docker-compose up -d
   ```

4. **Access the application**
   - **CRM Frontend**: http://localhost:3000
   - **Admin Portal**: http://localhost:3010
   - **Backend API**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs

5. **Default Login**
   - **CRM**: admin@ccs.com / admin123
   - **Admin Portal**: admin / admin123

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React SPA     │    │   FastAPI       │    │   PostgreSQL    │
│   (CRM - 3000)  │◄──►│   (Backend)     │◄──►│   (Database)    │
│                 │    │   Port 8000     │    │                 │
│ • Vite          │    │                 │    │ • Row-level     │
│ • Material-UI   │    │ • Multi-tenant  │    │   Security      │
│ • TypeScript    │    │ • JWT Auth      │    │ • Tenant        │
└─────────────────┘    │ • GPT-5 AI      │    │   Isolation     │
                       └─────────────────┘    └─────────────────┘
┌─────────────────┐              │
│   Vue.js Admin  │              │
│   (Port 3010)   │◄─────────────┘
│                 │
│ • Element Plus  │
│ • Admin Tools   │
└─────────────────┘
```

## 📊 **Key Features**

### **Customer Intelligence**
- ✅ AI-powered company analysis using GPT-5
- ✅ Automated lead scoring (0-100)
- ✅ Multi-year financial analysis with trends
- ✅ Director and officer information
- ✅ Competitor identification
- ✅ Risk factor analysis
- ✅ Opportunity recommendations
- ✅ Health score calculation

### **Contact Management**
- ✅ Multiple emails per contact (work/personal/other)
- ✅ Multiple phone numbers (mobile/work/home/other)
- ✅ Role-based contact categorization
- ✅ Primary contact designation
- ✅ Clickable contact cards with detailed views
- ✅ Edit contacts with reusable dialog
- ✅ Add directors as contacts with one click

### **Address Management**
- ✅ Google Maps multi-location discovery (70+ search queries)
- ✅ "Not this business" exclusion system
- ✅ Primary address selection
- ✅ Address type management (primary/billing/delivery)
- ✅ Manual address addition
- ✅ Google Maps integration links

### **Data Integration**
- ✅ Companies House API (company profiles, officers, financials)
- ✅ Companies House Document API (iXBRL parsing)
- ✅ Google Maps Places API v1 (comprehensive location search)
- ✅ OpenAI GPT-5 (business intelligence)
- ✅ Web scraping (LinkedIn, websites)

### **User Experience**
- ✅ Modern tabbed interface (Overview, AI Analysis, Financial, Addresses, Directors, Competitors)
- ✅ Persistent tab state (localStorage)
- ✅ Real-time data refresh
- ✅ Responsive design
- ✅ Loading states and error handling
- ✅ Success/error notifications

## 🛠️ **Tech Stack**

### **Frontend**
- **CRM**: React 18 + TypeScript + Vite
- **Admin**: Vue.js 3 + TypeScript + Element Plus
- **UI**: Material-UI (MUI) / Element Plus
- **State**: React hooks / Vue Composition API

### **Backend**
- FastAPI + Python 3.12
- PostgreSQL with Row-Level Security
- Redis for caching
- Celery for async tasks
- SQLAlchemy 2.0
- Alembic migrations

### **AI & External APIs**
- OpenAI GPT-5 / GPT-5-mini
- Companies House API
- Companies House Document API
- Google Maps Places API v1
- BeautifulSoup for web scraping

### **Infrastructure**
- Docker + Docker Compose
- Nginx reverse proxy
- Cloud-ready deployment
- Health checks and logging

## 📋 **Development Roadmap**

### **Current Version: 2.2.0** ✅
- ✅ Complete CRM module with AI integration
- ✅ Multi-tenant admin portal
- ✅ Contact management with multiple contact methods
- ✅ Advanced address management
- ✅ Financial analysis and business intelligence
- ✅ Known facts system for AI accuracy

### **Next Release: 2.3.0** 🚧
See [TODO.md](TODO.md) and [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) for detailed plans.

**Priority 1: Database-Driven AI Prompts**
- Move all AI prompts to database
- Admin interface to view/edit prompts
- Version control for prompts
- Tenant-specific prompt customization

**Priority 2: Lead Generation Module**
- Lead campaign management
- Address-based lead targeting
- Competitor-based lead discovery
- Email campaign integration
- Lead scoring and prioritization

**Priority 3: Quoting Module**
- Dynamic quote builder
- Product/service catalog
- Pricing rules engine
- Quote templates
- PDF generation
- Quote approval workflow

### **Future Enhancements** 🔮
- Integration with accounting packages (Xero, QuickBooks)
- Advanced reporting and analytics
- Email marketing automation
- Sales pipeline management
- Task and activity tracking
- Document management system
- Mobile app (React Native)

## 📁 **Project Structure**

```
CCS Quote Tool v2/
├── backend/                # FastAPI backend
│   ├── app/
│   │   ├── api/           # API routes
│   │   ├── core/          # Config, security
│   │   ├── models/        # SQLAlchemy models
│   │   ├── services/      # Business logic
│   │   └── main.py        # FastAPI app
│   ├── alembic/           # Database migrations
│   └── requirements.txt
├── frontend/              # React CRM frontend (Vite)
│   ├── src/
│   │   ├── components/    # Reusable components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API clients
│   │   └── App.tsx
│   └── package.json
├── admin-portal/          # Vue.js admin portal
│   ├── src/
│   │   ├── views/         # Admin pages
│   │   ├── components/    # Admin components
│   │   └── router/
│   └── package.json
├── docker-compose.yml     # Multi-container setup
├── TODO.md               # Detailed task list
├── DEVELOPMENT_PLAN.md   # Comprehensive dev plan
└── README.md             # This file
```

## 🔧 **Configuration**

### **API Keys** (Stored in Database)
API keys are managed through the Admin Portal Settings page:
- **OpenAI API Key**: Required for all AI features
- **Companies House API Key**: Required for UK company data
- **Google Maps API Key**: Required for location services

Keys can be configured at:
1. **System Level** (Admin Portal > Global API Keys)
2. **Tenant Level** (CRM > Settings > API Keys)

Tenant keys override system keys when provided.

### **Environment Variables**
See `env.example` for configuration options.

## 🧪 **Testing**

```bash
# Backend tests
docker-compose exec backend pytest

# Frontend tests
docker-compose exec frontend npm test

# Admin portal tests
docker-compose exec admin-portal npm test
```

## 📊 **Database Management**

```bash
# Create migration
docker-compose exec backend alembic revision --autogenerate -m "Description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback migration
docker-compose exec backend alembic downgrade -1
```

## 🐛 **Troubleshooting**

### **Port Conflicts**
- CRM Frontend: 3000
- Admin Portal: 3010
- Backend API: 8000
- PostgreSQL: 5432
- Redis: 6379

### **Reset Development Environment**
```bash
docker-compose down -v
docker-compose up -d --build
```

### **View Logs**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

## 📖 **Documentation**

- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **API Redoc**: http://localhost:8000/redoc
- **Development Plan**: See [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md)
- **TODO List**: See [TODO.md](TODO.md)

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 **License**

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🎯 **Version History**

### **v2.2.0** (October 11, 2025)
- ✅ Complete CRM module with AI integration
- ✅ Multiple emails/phones per contact
- ✅ Advanced address management
- ✅ Known facts system
- ✅ Contact detail dialogs
- ✅ Fixed customer update endpoint
- ✅ Backend contact notes support

### **v2.1.0** (October 9, 2025)
- ✅ Multilingual support (10 languages)
- ✅ Argon2 password hashing
- ✅ Admin portal with tenant management
- ✅ API key management system
- ✅ User management features

### **v2.0.0** (October 1, 2025)
- 🎉 Initial multi-tenant architecture
- 🎉 FastAPI backend with PostgreSQL
- 🎉 React frontend with Material-UI
- 🎉 JWT authentication
- 🎉 Docker containerization

---

**CCS Quote Tool v2** - The future of CRM and quoting platforms.

**Version**: 2.2.0  
**Status**: Active Development  
**Last Updated**: October 11, 2025
