# 🚀 CCS Quote Tool v2 - Quick Start Guide

**Version**: 2.0.0  
**Last Updated**: October 10, 2025

---

## ⚡ **Get Started in 3 Minutes**

### 1. **Start All Services**
```bash
cd "C:\Users\david\Documents\CCS quote tool\CCS Quote Tool v2"
docker-compose up -d
```

### 2. **Access the Application**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 3. **Login**
- **Email**: admin@ccs.com
- **Password**: admin123
- **Role**: Super Admin

---

## 🎯 **What You Can Do**

### As Super Admin
1. **Manage Tenants**
   - View all tenants
   - Create new tenants
   - Update tenant settings
   - Configure API keys per tenant

2. **Manage System**
   - View system-wide statistics
   - Monitor API usage
   - Configure system settings

### As Tenant Admin (CCS)
1. **Manage Customers**
   - Add/edit/delete customers
   - View customer details
   - AI-powered customer intelligence

2. **Generate Leads**
   - Create AI-powered campaigns
   - Find prospects automatically
   - Score and qualify leads

3. **Create Quotes**
   - Generate professional quotes
   - Track quote status
   - Manage pricing

4. **Manage Team**
   - Add users to your tenant
   - Assign roles and permissions
   - Track user activity

---

## 🆕 **Create a New Tenant (Self-Service)**

### Option 1: Via UI (When Frontend is Running)
1. Go to http://localhost:3000/signup
2. Fill in company details
3. Create admin account
4. Start 30-day free trial

### Option 2: Via API
```bash
curl -X POST http://localhost:8000/api/v1/tenants/signup \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Your Company Name",
    "slug": "yourcompany",
    "admin_email": "admin@yourcompany.com",
    "admin_password": "securepassword",
    "admin_first_name": "John",
    "admin_last_name": "Doe"
  }'
```

---

## 🔧 **Common Commands**

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Stop Services
```bash
docker-compose down
```

### Rebuild After Changes
```bash
# Rebuild backend
docker-compose build backend
docker-compose up -d backend

# Rebuild frontend
docker-compose build frontend
docker-compose up -d frontend
```

### Check Service Health
```bash
docker ps
curl http://localhost:8000/health
```

---

## 📊 **Service Status**

### Current Status
```
✅ Backend API      → Port 8000 (Healthy)
✅ PostgreSQL       → Port 5432 (Healthy)
✅ Redis            → Port 6379 (Healthy)
🔄 Frontend         → Port 3000 (Building...)
⏳ Celery Worker    → Not started yet
⏳ Celery Beat      → Not started yet
```

---

## 🎯 **Features Available**

### ✅ Working Now
- Multi-tenant architecture
- Tenant signup
- User authentication
- Customer management (API)
- Lead management (API)
- Campaign management (API)
- Quote management (API)
- AI lead generation
- Companies House integration
- Google Maps integration
- Multilingual translation

### 🔄 Coming Soon
- Full frontend UI
- Dashboard analytics
- Real-time updates
- Email notifications
- PDF quote generation
- Advanced reporting

---

## 🔑 **API Keys**

The system uses API keys from v1:
- ✅ OpenAI (GPT-5-mini)
- ✅ Companies House
- ✅ Google Maps

**Location**: `.env` file (gitignored for security)

---

## 📱 **Multi-Tenant Features**

### Tenant Isolation
- Each tenant has isolated data (customers, leads, quotes)
- Row-level security in database
- Tenant-specific API keys supported
- System-wide API keys as fallback

### User Roles
1. **Super Admin** - System-wide management
2. **Tenant Admin** - Full tenant management
3. **Manager** - Team and data management
4. **Sales Rep** - CRM and quoting
5. **User** - Read-only access

---

## 🆘 **Troubleshooting**

### Backend Not Starting
```bash
docker-compose logs backend
docker-compose restart backend
```

### Frontend Build Issues
```bash
docker-compose build --no-cache frontend
```

### Database Connection Issues
```bash
docker-compose restart postgres
docker-compose logs postgres
```

### Clear All and Start Fresh
```bash
docker-compose down -v
docker-compose up -d
```

---

## 📞 **Quick Reference**

### URLs
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Default Credentials
- Email: admin@ccs.com
- Password: admin123

### Database
- Host: localhost
- Port: 5432
- Database: ccs_quote_tool
- User: postgres
- Password: postgres_password_2025

---

**Ready to use! 🚀**

For detailed documentation, see:
- `README.md` - Project overview
- `DEVELOPMENT.md` - Development guide
- `PROGRESS_SUMMARY.md` - Current status
- `SESSION_COMPLETE.md` - Build details

