#!/usr/bin/env python3
"""
AI Contract Generator Service
Generates contract templates using AI with JSON placeholders
"""

import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from app.services.ai_provider_service import AIProviderService
from app.services.ai_prompt_service import AIPromptService
from app.models.ai_prompt import PromptCategory
from app.models.tenant import Tenant


class ContractGeneratorService:
    """Service for AI-powered contract template generation"""
    
    def __init__(self, db, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.provider_service = AIProviderService(db, tenant_id=tenant_id)
        self.prompt_service = AIPromptService(db, tenant_id=tenant_id)
    
    async def generate_contract_template(
        self,
        contract_type: str,
        description: str,
        requirements: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a contract template using AI
        
        Args:
            contract_type: Type of contract (e.g., "managed_services", "software_license")
            description: Description of what the contract should cover
            requirements: Optional specific requirements (SLA levels, pricing structure, etc.)
            user_id: User ID who requested the generation
        
        Returns:
            Dict with template_content, placeholder_schema, and default_values
        """
        try:
            # Get tenant context
            tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
            tenant_context = self._get_tenant_context(tenant)
            
            # Build prompt for contract generation
            prompt_text = self._build_contract_generation_prompt(
                contract_type=contract_type,
                description=description,
                requirements=requirements or {},
                tenant_context=tenant_context
            )
            
            # Get or create contract generation prompt
            prompt_obj = await self.prompt_service.get_prompt_by_category(
                category=PromptCategory.CONTRACT_GENERATION,
                tenant_id=self.tenant_id
            )
            
            # If no prompt exists, use a default system prompt
            if not prompt_obj:
                system_prompt = """You are a legal contract expert specializing in creating professional contract templates for business services. 
Generate comprehensive, legally sound contract templates with JSON placeholders for dynamic content."""
            else:
                system_prompt = prompt_obj.system_prompt or ""
            
            # Generate contract using AI
            if prompt_obj:
                provider_response = await self.provider_service.generate(
                    prompt=prompt_obj,
                    variables={
                        "contract_type": contract_type,
                        "description": description,
                        "requirements": json.dumps(requirements or {}),
                        "tenant_context": tenant_context,
                        "user_prompt": prompt_text
                    }
                )
            else:
                # Fallback: direct generation
                provider_response = await self.provider_service.generate_text(
                    system_prompt=system_prompt,
                    user_prompt=prompt_text
                )
            
            contract_content = provider_response.content if hasattr(provider_response, 'content') else str(provider_response)
            
            # Extract placeholders from the generated content
            placeholders = self._extract_placeholders(contract_content)
            
            # Generate placeholder schema
            placeholder_schema = self._generate_placeholder_schema(placeholders, contract_type, requirements)
            
            # Generate default values
            default_values = self._generate_default_values(placeholder_schema)
            
            return {
                "template_content": contract_content,
                "placeholder_schema": placeholder_schema,
                "default_values": default_values,
                "placeholders_found": placeholders
            }
            
        except Exception as e:
            print(f"Error generating contract template: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _get_tenant_context(self, tenant: Tenant) -> str:
        """Get tenant context for contract generation"""
        context_parts = []
        
        if tenant.company_name:
            context_parts.append(f"Company: {tenant.company_name}")
        
        if tenant.company_description:
            context_parts.append(f"Description: {tenant.company_description}")
        
        if tenant.products_services:
            context_parts.append(f"Services: {', '.join(tenant.products_services)}")
        
        return "\n".join(context_parts) if context_parts else "General business services company"
    
    def _build_contract_generation_prompt(
        self,
        contract_type: str,
        description: str,
        requirements: Dict[str, Any],
        tenant_context: str
    ) -> str:
        """Build prompt for AI contract generation"""
        return f"""Generate a professional {contract_type} contract template.

Tenant Context:
{tenant_context}

Contract Description:
{description}

Requirements:
{json.dumps(requirements, indent=2)}

Instructions:
1. Create a comprehensive, legally sound contract template
2. Use JSON placeholders in the format {{placeholder_name}} for dynamic content
3. Include placeholders for: customer name, dates, pricing, service details, SLA levels, etc.
4. Use default values where appropriate: {{placeholder_name|default_value}}
5. Include standard contract sections: parties, services, terms, payment, termination, etc.
6. Make it professional and suitable for business use

Example placeholder formats:
- {{customer_name}} - Customer company name
- {{monthly_fee|0}} - Monthly fee with default of 0
- {{start_date|{{today}}}} - Start date with default of today
- {{sla_level|24/7}} - SLA level with default

Generate the contract template now:"""
    
    def _extract_placeholders(self, content: str) -> List[str]:
        """Extract all placeholders from contract content"""
        # Match {{placeholder}} or {{placeholder|default}}
        pattern = r'\{\{([^}]+)\}\}'
        matches = re.findall(pattern, content)
        
        placeholders = []
        for match in matches:
            # Extract placeholder name (before | if present)
            placeholder_name = match.split('|')[0].strip()
            if placeholder_name not in placeholders:
                placeholders.append(placeholder_name)
        
        return placeholders
    
    def _generate_placeholder_schema(
        self,
        placeholders: List[str],
        contract_type: str,
        requirements: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Generate JSON schema for placeholders"""
        schema = {}
        
        # Common placeholder types
        type_mapping = {
            'customer': 'string',
            'name': 'string',
            'date': 'date',
            'fee': 'number',
            'price': 'number',
            'amount': 'number',
            'value': 'number',
            'hours': 'number',
            'level': 'string',
            'email': 'string',
            'phone': 'string',
            'address': 'string',
        }
        
        for placeholder in placeholders:
            placeholder_lower = placeholder.lower()
            
            # Determine type
            field_type = 'string'  # default
            for key, value_type in type_mapping.items():
                if key in placeholder_lower:
                    field_type = value_type
                    break
            
            # Determine if required
            required = not any(word in placeholder_lower for word in ['optional', 'default', 'if'])
            
            # Generate description
            description = placeholder.replace('_', ' ').title()
            
            schema[placeholder] = {
                "type": field_type,
                "required": required,
                "description": description
            }
        
        return schema
    
    def _generate_default_values(self, schema: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Generate default values based on schema"""
        defaults = {}
        
        for placeholder, config in schema.items():
            field_type = config.get('type', 'string')
            
            if field_type == 'number':
                defaults[placeholder] = 0
            elif field_type == 'date':
                defaults[placeholder] = "{{today}}"
            elif field_type == 'string':
                defaults[placeholder] = ""
            else:
                defaults[placeholder] = ""
        
        return defaults
    
    def fill_contract_template(
        self,
        template_content: str,
        placeholder_values: Dict[str, Any]
    ) -> str:
        """
        Fill contract template with actual values
        
        Args:
            template_content: Contract template with placeholders
            placeholder_values: Dict of placeholder name -> value
        
        Returns:
            Filled contract content
        """
        filled_content = template_content
        
        # Replace placeholders with values
        for placeholder, value in placeholder_values.items():
            # Handle both {{placeholder}} and {{placeholder|default}} formats
            pattern = r'\{\{' + re.escape(placeholder) + r'(\|[^}]+)?\}\}'
            
            # Format value based on type
            if isinstance(value, (int, float)):
                formatted_value = str(value)
            elif isinstance(value, datetime):
                formatted_value = value.strftime('%Y-%m-%d')
            else:
                formatted_value = str(value) if value else ""
            
            filled_content = re.sub(pattern, formatted_value, filled_content)
        
        # Handle special placeholders
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        filled_content = filled_content.replace('{{today}}', today)
        
        return filled_content

