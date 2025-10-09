# CCS Quote Tool v2 - Development Guide

## 🚀 **Project Status**

**Version**: 2.0.0  
**Status**: Development Ready  
**Repository**: https://github.com/dje115/ccs-quote-tool-v2  
**Last Updated**: October 9, 2025

## 📋 **Current Progress**

### ✅ **Completed**
- [x] Project structure with Docker
- [x] Multi-tenant database models
- [x] FastAPI backend foundation
- [x] React frontend setup
- [x] GitHub repository setup
- [x] Docker Compose configuration

### 🔄 **In Progress**
- [ ] Complete FastAPI backend implementation
- [ ] JWT authentication system
- [ ] API routes for all features
- [ ] React frontend components

### 📋 **Pending**
- [ ] Migrate API keys from v1
- [ ] Implement multilingual support
- [ ] Migrate all v1 features
- [ ] AI integration (GPT-5)
- [ ] Companies House integration
- [ ] Google Maps integration

## 🏗️ **Architecture Overview**

### **Multi-Tenant SaaS Design**
```
┌─────────────────────────────────────────────────────────┐
│                    CCS Quote Tool v2                   │
├─────────────────────────────────────────────────────────┤
│  Super Admin (System-wide)                             │
│  ├── Tenant Management                                  │
│  ├── System Configuration                              │
│  └── API Key Management                                │
├─────────────────────────────────────────────────────────┤
│  Tenant: CCS (Default)                                 │
│  ├── Users: admin@ccs.com                              │
│  ├── Customers: Isolated per tenant                    │
│  ├── Leads: Isolated per tenant                        │
│  └── Quotes: Isolated per tenant                       │
├─────────────────────────────────────────────────────────┤
│  Future Tenants                                        │
│  ├── Tenant: Company A                                 │
│  ├── Tenant: Company B                                 │
│  └── Tenant: Company C                                 │
└─────────────────────────────────────────────────────────┘
```

### **Technology Stack**
- **Frontend**: React 18 + TypeScript + Material-UI
- **Backend**: FastAPI + Python 3.13
- **Database**: PostgreSQL with Row-Level Security
- **Cache**: Redis
- **Background Tasks**: Celery
- **Containerization**: Docker + Docker Compose
- **AI**: GPT-5 (OpenAI)
- **External APIs**: Companies House, Google Maps

## 🔧 **Development Setup**

### **Prerequisites**
- Docker Desktop
- Git
- Code Editor (VS Code recommended)

### **Quick Start**
```bash
# Clone the repository
git clone https://github.com/dje115/ccs-quote-tool-v2.git
cd ccs-quote-tool-v2

# Copy environment template
copy env.example .env

# Edit .env with your API keys
# - OPENAI_API_KEY
# - COMPANIES_HOUSE_API_KEY
# - GOOGLE_MAPS_API_KEY

# Start development environment
start-dev.bat  # Windows
# OR
docker-compose up -d  # Linux/Mac
```

### **Access Points**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Default Login**: admin@ccs.com / admin123

## 📁 **Project Structure**

```
ccs-quote-tool-v2/
├── docker-compose.yml          # Development environment
├── README.md                   # Project overview
├── DEVELOPMENT.md              # This file
├── env.example                 # Environment template
├── start-dev.bat               # Windows startup script
├── backend/                    # FastAPI backend
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                 # FastAPI application
│   └── app/
│       ├── api/                # API routes
│       ├── core/               # Core functionality
│       │   ├── config.py       # Settings
│       │   └── database.py     # Database setup
│       ├── models/             # Database models
│       │   ├── base.py         # Base model classes
│       │   ├── tenant.py       # Tenant & User models
│       │   ├── crm.py          # CRM models
│       │   ├── leads.py        # Lead generation models
│       │   └── quotes.py       # Quote models
│       ├── services/           # Business logic
│       ├── utils/              # Utilities
│       └── schemas/            # Pydantic schemas
├── frontend/                   # React frontend
│   ├── Dockerfile
│   ├── package.json
│   └── src/                    # React source code
└── shared/                     # Shared types
    └── types.ts                # TypeScript definitions
```

## 🔑 **API Key Migration from v1**

### **Current v1 API Keys** (To be migrated)
From the existing project, we need to extract:
- OpenAI API Key
- Companies House API Key  
- Google Maps API Key

### **Migration Strategy**
1. **System-wide Keys**: Use v1 keys as default system keys
2. **Tenant-specific Keys**: Allow tenants to override with their own keys
3. **Usage Tracking**: Monitor API usage per tenant
4. **Cost Management**: Track and bill API usage

## 🎯 **Next Development Steps**

### **Phase 1: Core Backend (Week 1-2)**
1. **Complete FastAPI Setup**
   - JWT authentication
   - Middleware for tenant isolation
   - API route structure

2. **Database Implementation**
   - Row-level security setup
   - Migration scripts
   - Seed data for default tenant

3. **Authentication System**
   - User login/logout
   - Token management
   - Permission system

### **Phase 2: Feature Migration (Week 3-4)**
1. **CRM Features**
   - Customer management
   - Contact management
   - Interaction tracking

2. **Lead Generation**
   - Campaign management
   - AI-powered lead discovery
   - Companies House integration

3. **Quoting System**
   - Quote creation and management
   - Template system
   - PDF generation

### **Phase 3: Advanced Features (Week 5-6)**
1. **AI Integration**
   - GPT-5 implementation
   - Customer intelligence
   - Lead scoring

2. **External Integrations**
   - Google Maps API
   - Companies House API
   - Email system

3. **Multilingual Support**
   - AI-powered translation
   - Language detection
   - Localization

## 🔄 **Migration from v1**

### **Data Migration Strategy**
1. **Customers**: Migrate all customer data with tenant assignment
2. **Leads**: Migrate lead generation campaigns and results
3. **Quotes**: Migrate existing quotes and templates
4. **Users**: Create admin user for CCS tenant
5. **Settings**: Migrate configuration and preferences

### **Feature Parity Checklist**
- [ ] Customer management
- [ ] Lead generation campaigns
- [ ] AI-powered lead discovery
- [ ] Companies House integration
- [ ] Google Maps integration
- [ ] Quote generation
- [ ] PDF export
- [ ] Dashboard analytics
- [ ] Address management
- [ ] Director information
- [ ] Financial data display
- [ ] Competitor analysis
- [ ] Contact management
- [ ] Interaction tracking

## 🚀 **Deployment Strategy**

### **Development**
- Local Docker environment
- Hot reloading for development
- Comprehensive logging

### **Production**
- Docker containers
- PostgreSQL database
- Redis cache
- Nginx reverse proxy
- SSL certificates
- Backup strategy

### **Scaling Considerations**
- Horizontal scaling with load balancers
- Database read replicas
- CDN for static assets
- Background task scaling
- Monitoring and alerting

## 📊 **Success Metrics**

### **Technical Metrics**
- API response times < 200ms
- 99.9% uptime
- Zero data leaks between tenants
- Successful migration of all v1 data

### **Business Metrics**
- All v1 features working in v2
- Improved user experience
- Multi-tenant capability
- Scalable architecture

## 🤝 **Development Workflow**

### **Git Workflow**
```bash
# Feature development
git checkout -b feature/new-feature
# Make changes
git add .
git commit -m "feat: add new feature"
git push origin feature/new-feature
# Create pull request
```

### **Code Standards**
- Python: Black formatting, type hints
- TypeScript: ESLint, Prettier
- Commits: Conventional commit messages
- Tests: Unit tests for critical functionality

## 📞 **Support & Resources**

- **Repository**: https://github.com/dje115/ccs-quote-tool-v2
- **Issues**: GitHub Issues for bug reports
- **Documentation**: In-code documentation
- **API Docs**: http://localhost:8000/docs (when running)

---

**Ready to build the future of CRM and quoting platforms!** 🚀
