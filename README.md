# CCS Quote Tool v2 - Multi-Tenant SaaS Platform
## Modern CRM & Quoting Platform with AI-Powered Features

[![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)](https://github.com/dje115/ccs-quote-tool-v2)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://docker.com)
[![Multi-tenant](https://img.shields.io/badge/multi--tenant-enabled-green.svg)](#)
[![AI-Powered](https://img.shields.io/badge/AI--powered-orange.svg)](#)

A modern, scalable, multi-tenant SaaS platform for customer relationship management and quoting with AI-powered lead generation, **multilingual support with 10 languages**, **Argon2 security**, and real-time collaboration.

## ✨ **Latest Features (v2.1.0)**

- 🌍 **Multilingual Support**: 10 languages (EN, ES, FR, DE, IT, PT, NL, RU, JA, ZH) with AI-powered translation
- 🛡️ **Argon2 Security**: Industry-leading password hashing (winner of Password Hashing Competition 2015)
- 🤖 **AI Integration**: GPT-5-powered features and dynamic translations
- 🏢 **Multi-Tenant SaaS**: Complete tenant isolation with row-level security
- 📱 **Modern UI**: Material-UI with responsive design and working language selector

## 🚀 **Quick Start**

### **Prerequisites**
- Docker & Docker Compose
- Git

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
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

5. **Default Login**
   - Email: admin@ccs.com
   - Password: admin123

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React SPA     │    │   FastAPI       │    │   PostgreSQL    │
│   (Frontend)    │◄──►│   (Backend)     │◄──►│   (Database)    │
│                 │    │                 │    │                 │
│ • Material-UI   │    │ • Multi-tenant  │    │ • Row-level     │
│ • Redux Toolkit │    │ • JWT Auth      │    │   Security      │
│ • Socket.io     │    │ • AI Integration│    │ • Tenant        │
│ • PWA Support   │    │ • Real-time     │    │   Isolation     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🏢 **Multi-Tenant Features**

- **Tenant Isolation**: Secure data separation
- **Custom Branding**: White-label solution
- **API Key Management**: Per-tenant or system-wide keys
- **Scalable**: Support unlimited tenants

## 🤖 **AI-Powered Features**

- **GPT-5 Integration**: Advanced AI with web search
- **Lead Generation**: Automated prospect discovery
- **Customer Intelligence**: AI-powered business analysis
- **Multilingual Support**: AI-powered translation

## 📊 **Key Features**

- **Real-time Dashboard**: Live updates and collaboration
- **Companies House Integration**: UK business data
- **Google Maps Integration**: Location discovery
- **Professional Quoting**: Dynamic quote generation
- **Mobile-Ready**: Responsive PWA design

## 🛠️ **Tech Stack**

### **Frontend**
- React 18 + TypeScript
- Material-UI (MUI)
- Redux Toolkit
- Socket.io

### **Backend**
- FastAPI + Python 3.13
- PostgreSQL + Redis
- Celery + SQLAlchemy 2.0

### **Infrastructure**
- Docker + Docker Compose
- Nginx reverse proxy
- Cloud-ready deployment

## 📄 **License**

MIT License - see [LICENSE](LICENSE) file for details.

---

**CCS Quote Tool v2** - The future of CRM and quoting platforms.

**Version**: 2.0.0  
**Status**: Development  
**Last Updated**: October 9, 2025
