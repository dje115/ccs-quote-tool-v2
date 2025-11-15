#!/usr/bin/env python3
"""
Seed script to populate ai_providers table with initial providers
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.ai_provider import AIProvider
import uuid


def seed_providers(db: Session):
    """Seed initial AI providers"""
    
    providers = [
        {
            "name": "OpenAI",
            "slug": "openai",
            "provider_type": "cloud",
            "base_url": None,  # Uses default OpenAI API URL
            "supported_models": [
                "gpt-4",
                "gpt-4-turbo",
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-5",
                "gpt-5-mini",
                "o1",
                "o1-mini"
            ],
            "default_settings": {
                "temperature": 0.7,
                "max_tokens": 8000,
                "top_p": 1.0
            },
            "is_active": True
        },
        {
            "name": "Google",
            "slug": "google",
            "provider_type": "cloud",
            "base_url": None,
            "supported_models": [
                "gemini-pro",
                "gemini-pro-vision",
                "gemini-1.5-pro",
                "gemini-1.5-flash",
                "gemini-2.0-flash-exp"
            ],
            "default_settings": {
                "temperature": 0.7,
                "max_tokens": 8000,
                "top_p": 0.95,
                "top_k": 40
            },
            "is_active": True
        },
        {
            "name": "Anthropic",
            "slug": "anthropic",
            "provider_type": "cloud",
            "base_url": None,
            "supported_models": [
                "claude-3-opus",
                "claude-3-sonnet",
                "claude-3-haiku",
                "claude-3-5-sonnet",
                "claude-3-5-haiku"
            ],
            "default_settings": {
                "temperature": 0.7,
                "max_tokens": 8000,
                "top_p": 0.9,
                "top_k": 5
            },
            "is_active": True
        },
        {
            "name": "Cohere",
            "slug": "cohere",
            "provider_type": "cloud",
            "base_url": None,
            "supported_models": [
                "command",
                "command-light",
                "command-r",
                "command-r-plus"
            ],
            "default_settings": {
                "temperature": 0.7,
                "max_tokens": 8000,
                "top_p": 0.9,
                "top_k": 0
            },
            "is_active": True
        },
        {
            "name": "Mistral",
            "slug": "mistral",
            "provider_type": "cloud",
            "base_url": None,
            "supported_models": [
                "mistral-tiny",
                "mistral-small",
                "mistral-medium",
                "mistral-large",
                "pixtral-12b"
            ],
            "default_settings": {
                "temperature": 0.7,
                "max_tokens": 8000,
                "top_p": 1.0
            },
            "is_active": True
        },
        {
            "name": "DeepSeek",
            "slug": "deepseek",
            "provider_type": "cloud",
            "base_url": None,
            "supported_models": [
                "deepseek-chat",
                "deepseek-coder"
            ],
            "default_settings": {
                "temperature": 0.7,
                "max_tokens": 8000,
                "top_p": 1.0
            },
            "is_active": True
        },
        {
            "name": "Grok",
            "slug": "grok",
            "provider_type": "cloud",
            "base_url": None,
            "supported_models": [
                "grok-beta",
                "grok-2"
            ],
            "default_settings": {
                "temperature": 0.7,
                "max_tokens": 8000,
                "top_p": 1.0
            },
            "is_active": True
        },
        {
            "name": "Ollama",
            "slug": "ollama",
            "provider_type": "on_premise",
            "base_url": "http://localhost:11434",  # Default Ollama URL
            "supported_models": [
                "llama2",
                "llama3",
                "mistral",
                "codellama",
                "phi",
                "neural-chat",
                "starling-lm",
                "qwen",
                "llava"
            ],
            "default_settings": {
                "temperature": 0.7,
                "num_predict": 8000,
                "top_p": 0.9,
                "top_k": 40
            },
            "is_active": True
        },
        {
            "name": "OpenAI Compatible",
            "slug": "openai-compatible",
            "provider_type": "on_premise",
            "base_url": "http://localhost:8000/v1",  # Default for self-hosted models
            "supported_models": [
                "custom-model-1",
                "custom-model-2"
            ],
            "default_settings": {
                "temperature": 0.7,
                "max_tokens": 8000,
                "top_p": 1.0
            },
            "is_active": True
        }
    ]
    
    created_count = 0
    skipped_count = 0
    
    for provider_data in providers:
        # Check if provider already exists
        existing = db.query(AIProvider).filter(AIProvider.slug == provider_data["slug"]).first()
        
        if existing:
            print(f"⏭️  Provider '{provider_data['name']}' ({provider_data['slug']}) already exists")
            skipped_count += 1
            continue
        
        # Create new provider
        provider = AIProvider(
            id=str(uuid.uuid4()),
            name=provider_data["name"],
            slug=provider_data["slug"],
            provider_type=provider_data["provider_type"],
            base_url=provider_data["base_url"],
            supported_models=provider_data["supported_models"],
            default_settings=provider_data["default_settings"],
            is_active=provider_data["is_active"]
        )
        
        db.add(provider)
        print(f"✅ Created provider: {provider_data['name']} ({provider_data['slug']})")
        created_count += 1
    
    db.commit()
    
    print(f"\n📊 Summary:")
    print(f"   Created: {created_count} providers")
    print(f"   Skipped: {skipped_count} (already exist)")
    print("✅ Provider seeding complete!")


def main():
    db = SessionLocal()
    try:
        seed_providers(db)
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding providers: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

