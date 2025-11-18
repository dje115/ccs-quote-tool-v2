#!/usr/bin/env python3
"""
Configuration settings for CCS Quote Tool v2
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
import os
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "CCS Quote Tool v2"
    VERSION: str = "2.10.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # Security
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440, env="ACCESS_TOKEN_EXPIRE_MINUTES")  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    
    # Redis
    REDIS_URL: str = Field(..., env="REDIS_URL")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3010", "http://127.0.0.1:3010"],
        env="CORS_ORIGINS"
    )
    
    # Multi-tenant
    DEFAULT_TENANT: str = Field(default="ccs", env="DEFAULT_TENANT")
    # SECURITY: Super admin credentials MUST be set via environment variables
    # Never use hardcoded defaults in production
    SUPER_ADMIN_EMAIL: str = Field(..., env="SUPER_ADMIN_EMAIL")
    SUPER_ADMIN_PASSWORD: str = Field(..., env="SUPER_ADMIN_PASSWORD")
    
    # API Keys (System-wide defaults)
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    COMPANIES_HOUSE_API_KEY: Optional[str] = Field(default=None, env="COMPANIES_HOUSE_API_KEY")
    GOOGLE_MAPS_API_KEY: Optional[str] = Field(default=None, env="GOOGLE_MAPS_API_KEY")
    
    # Email
    SMTP_HOST: Optional[str] = Field(default="mailhog", env="SMTP_HOST")  # Default to MailHog in development
    SMTP_PORT: int = Field(default=1025, env="SMTP_PORT")  # MailHog SMTP port
    SMTP_USERNAME: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    SMTP_TLS: bool = Field(default=False, env="SMTP_TLS")  # MailHog doesn't use TLS
    SMTP_FROM_EMAIL: str = Field(default="noreply@ccs.com", env="SMTP_FROM_EMAIL")
    SMTP_FROM_NAME: str = Field(default="CCS Quote Tool", env="SMTP_FROM_NAME")
    
    # File Storage
    UPLOAD_DIR: str = Field(default="uploads", env="UPLOAD_DIR")
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    
    # MinIO Configuration (Object Storage)
    MINIO_ENDPOINT: str = Field(default="minio:9000", env="MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin", env="MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str = Field(default="minioadmin123", env="MINIO_SECRET_KEY")
    MINIO_BUCKET: str = Field(default="ccs-quote-tool", env="MINIO_BUCKET")
    MINIO_SECURE: bool = Field(default=False, env="MINIO_SECURE")  # False for development
    MINIO_REGION: Optional[str] = Field(default=None, env="MINIO_REGION")
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = Field(default=20, env="DEFAULT_PAGE_SIZE")
    MAX_PAGE_SIZE: int = Field(default=100, env="MAX_PAGE_SIZE")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(default=60, env="RATE_LIMIT_WINDOW")  # seconds
    
    # Background Tasks
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")
    
    # AI Settings
    OPENAI_MODEL: str = Field(default="gpt-5", env="OPENAI_MODEL")
    OPENAI_MAX_TOKENS: int = Field(default=50000, env="OPENAI_MAX_TOKENS")
    OPENAI_TIMEOUT: int = Field(default=300, env="OPENAI_TIMEOUT")
    
    # Companies House API
    COMPANIES_HOUSE_BASE_URL: str = Field(
        default="https://api.company-information.service.gov.uk",
        env="COMPANIES_HOUSE_BASE_URL"
    )
    
    # Google Maps API
    GOOGLE_MAPS_BASE_URL: str = Field(
        default="https://maps.googleapis.com/maps/api",
        env="GOOGLE_MAPS_BASE_URL"
    )
    
    # Multilingual
    DEFAULT_LANGUAGE: str = Field(default="en", env="DEFAULT_LANGUAGE")
    SUPPORTED_LANGUAGES: List[str] = Field(
        default=["en", "es", "fr", "de", "it", "pt", "nl", "sv", "no", "da", "fi", "pl", "ru", "zh", "ja", "ko", "ar", "hi"],
        env="SUPPORTED_LANGUAGES"
    )
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", env="LOG_FORMAT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()
