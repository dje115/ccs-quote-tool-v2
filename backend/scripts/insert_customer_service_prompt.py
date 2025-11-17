#!/usr/bin/env python3
"""
Quick script to insert Customer Service prompt into database
Run this inside Docker: docker-compose exec backend python scripts/insert_customer_service_prompt.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.ai_prompt import AIPrompt, PromptCategory
from app.services.ai_prompt_service import AIPromptService
import asyncio


async def insert_prompt():
    """Insert Customer Service prompt"""
    db = SessionLocal()
    try:
        service = AIPromptService(db, tenant_id=None)
        
        # Check if prompt already exists
        existing = db.query(AIPrompt).filter(
            AIPrompt.category == PromptCategory.CUSTOMER_SERVICE.value,
            AIPrompt.is_system == True
        ).first()
        
        if existing:
            print(f"✅ Customer Service prompt already exists (ID: {existing.id})")
            return
        
        customer_service_prompt = """You are a customer service assistant. Analyze the following support ticket and:

1. Improve the description to be clear, professional, and customer-friendly (this will be shown to the customer)
2. Suggest next actions/questions that should be asked to gather more information
3. Suggest potential solutions if enough information is available

Original Ticket:
Subject: {ticket_subject}
Description: {ticket_description}
{customer_context}

IMPORTANT GUIDELINES:
- The improved description should be professional, clear, and customer-facing
- Keep all factual information from the original description
- Make it concise but complete
- Use proper grammar and professional language
- The improved description will be shown to the customer in the portal
- Preserve the original description for internal reference

SUGGESTIONS GUIDELINES:
- Next actions should be specific and actionable (e.g., "Ask customer for error logs" not "Gather more info")
- Questions should help diagnose the issue or gather necessary details
- Solutions should be practical and based on the information provided
- If insufficient information is available, focus on questions and next actions rather than solutions

Provide your response in JSON format:
{{
    "improved_description": "The improved, professional description that will be shown to the customer",
    "suggestions": {{
        "next_actions": [
            "Specific action 1 (e.g., 'Request error logs from customer')",
            "Specific action 2 (e.g., 'Check system logs for timestamp')"
        ],
        "questions": [
            "Question 1 to gather more information (e.g., 'What error message appears when this happens?')",
            "Question 2 to diagnose the issue (e.g., 'Does this happen on all devices or just one?')"
        ],
        "solutions": [
            "Potential solution 1 if enough info is available (e.g., 'Reset password and clear cache')",
            "Potential solution 2 if applicable (e.g., 'Update to latest version')"
        ]
    }}
}}

If you cannot provide solutions due to insufficient information, return an empty array for "solutions" but always provide "next_actions" and "questions"."""
        
        customer_service_system = """You are a customer service assistant specializing in analyzing support tickets. You improve ticket descriptions to be professional and customer-friendly, and provide actionable suggestions for resolving customer issues. Always respond with valid JSON matching the required format."""
        
        prompt = service.create_prompt(
            name="Customer Service - Ticket Analysis",
            category=PromptCategory.CUSTOMER_SERVICE.value,
            system_prompt=customer_service_system,
            user_prompt_template=customer_service_prompt,
            model="gpt-5-mini",
            temperature=0.7,
            max_tokens=2000,
            is_system=True,
            tenant_id=None,
            created_by=None,
            variables={
                "ticket_subject": "Ticket subject line",
                "ticket_description": "Original ticket description from agent",
                "customer_context": "Customer information including company name, business sector, and description (optional)"
            },
            description="Analyze support tickets to improve descriptions and suggest next actions, questions, and solutions"
        )
        
        db.commit()
        print(f"✅ Created Customer Service prompt (ID: {prompt.id})")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error inserting prompt: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(insert_prompt())

