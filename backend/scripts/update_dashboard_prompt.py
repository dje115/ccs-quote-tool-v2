#!/usr/bin/env python3
"""
Update script for dashboard analytics prompt to include tenant context
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.ai_prompt import AIPrompt, PromptCategory

def update_dashboard_prompt():
    """Update the dashboard analytics prompt with tenant context"""
    db = SessionLocal()
    try:
        prompt = db.query(AIPrompt).filter(
            AIPrompt.category == PromptCategory.DASHBOARD_ANALYTICS.value,
            AIPrompt.is_system == True
        ).first()
        
        if not prompt:
            print("❌ Dashboard analytics prompt not found!")
            return
        
        # Update prompt template
        prompt.user_prompt_template = """You are a CRM analytics assistant. Analyze the provided CRM data and answer user questions clearly and concisely. Provide actionable insights and recommendations based on the data, keeping responses relevant to the company's business context.

=== COMPANY CONTEXT ===
{tenant_context}

=== CRM DATA SNAPSHOT ===

{context}

=== USER QUESTION ===
{query}

=== INSTRUCTIONS ===
- Provide a clear, actionable answer based on the data above
- Frame all recommendations and insights in the context of the company's products/services and unique selling points
- When suggesting actions (e.g., "Contact the top 3 leads"), tailor the approach to match the company's offerings
- If the data doesn't support the question, explain what information is available
- Use natural, conversational language
- Include relevant numbers and trends to support your answer
- Be concise but comprehensive
- Always consider how recommendations align with the company's business model and services"""
        
        # Update system prompt
        prompt.system_prompt = "You are a CRM analytics assistant specializing in analyzing CRM data and providing actionable insights tailored to the specific company's business context. Answer questions clearly and concisely, ensuring all recommendations align with the company's products, services, and unique selling points."
        
        # Update variables
        prompt.variables = {
            "tenant_context": "Company business profile including description, products/services, and unique selling points",
            "context": "CRM data snapshot including customers, leads, trends, and metrics",
            "query": "User's question about the CRM data"
        }
        
        db.commit()
        print(f"✅ Updated dashboard_analytics prompt (ID: {prompt.id})")
        print(f"   - Updated user_prompt_template")
        print(f"   - Updated system_prompt")
        print(f"   - Updated variables to include tenant_context")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error updating prompt: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    update_dashboard_prompt()


