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
    
    async def generate_support_contract_template(
        self,
        contract_type: str,
        description: str,
        requirements: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a support contract template using AI with SLA and renewal support
        
        Args:
            contract_type: Type of contract (e.g., "managed_services", "maintenance")
            description: Description of what the contract should cover
            requirements: Optional specific requirements (SLA levels, renewal preferences, etc.)
            user_id: User ID who requested the generation
        
        Returns:
            Dict with contract data including SLA, renewal terms, and pricing
        """
        try:
            # Get tenant context
            tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
            tenant_context = self._get_tenant_context(tenant)
            
            # Build prompt for support contract generation
            prompt_text = self._build_support_contract_generation_prompt(
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
                system_prompt = """You are a legal contract expert specializing in creating professional support contract templates for business services. 
Generate comprehensive, legally sound support contracts with SLA integration, renewal terms, and pricing structures.
Return a JSON object with contract fields including: contract_name, description, contract_type, monthly_value, annual_value, 
setup_fee, renewal_frequency, auto_renew, sla_level, support_hours_included, renewal_notice_days, cancellation_notice_days, and terms."""
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
                        "user_prompt": prompt_text,
                        "is_support_contract": "true"
                    }
                )
            else:
                # Fallback: direct generation
                provider_response = await self.provider_service.generate_text(
                    system_prompt=system_prompt,
                    user_prompt=prompt_text
                )
            
            contract_content = provider_response.content if hasattr(provider_response, 'content') else str(provider_response)
            
            # Try to parse as JSON first (if AI returns structured data)
            try:
                contract_data = json.loads(contract_content)
                # Calculate suggested dates based on renewal frequency
                from datetime import datetime, timedelta
                today = datetime.now().date()
                
                renewal_frequency = contract_data.get("renewal_frequency", "annual")
                renewal_days = {
                    "monthly": 30,
                    "quarterly": 90,
                    "semi_annual": 180,
                    "annual": 365,
                    "biennial": 730,
                    "triennial": 1095
                }.get(renewal_frequency, 365)
                
                suggested_start_date = today.isoformat()
                suggested_end_date = None
                if renewal_frequency != "one_time":
                    suggested_end_date = (today + timedelta(days=renewal_days)).isoformat()
                
                # Ensure all required fields are present
                return {
                    "contract_name": contract_data.get("contract_name", f"{contract_type.replace('_', ' ').title()} Contract"),
                    "description": contract_data.get("description", description),
                    "contract_type": contract_type,
                    "start_date": contract_data.get("start_date", suggested_start_date),
                    "end_date": contract_data.get("end_date", suggested_end_date),
                    "monthly_value": contract_data.get("monthly_value"),
                    "annual_value": contract_data.get("annual_value"),
                    "setup_fee": contract_data.get("setup_fee", 0),
                    "renewal_frequency": contract_data.get("renewal_frequency", "annual"),
                    "auto_renew": contract_data.get("auto_renew", True),
                    "sla_level": contract_data.get("sla_level", ""),
                    "support_hours_included": contract_data.get("support_hours_included"),
                    "renewal_notice_days": contract_data.get("renewal_notice_days", 90),
                    "cancellation_notice_days": contract_data.get("cancellation_notice_days", 30),
                    "terms": contract_data.get("terms", ""),
                    "notes": contract_data.get("notes", "")
                }
            except json.JSONDecodeError:
                # If not JSON, extract structured data from text
                return self._extract_support_contract_data(contract_content, contract_type, description, requirements)
            
        except Exception as e:
            print(f"Error generating support contract template: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _build_support_contract_generation_prompt(
        self,
        contract_type: str,
        description: str,
        requirements: Dict[str, Any],
        tenant_context: str
    ) -> str:
        """Build prompt for AI support contract generation"""
        sla_requirements = requirements.get("sla_requirements", "")
        renewal_preferences = requirements.get("renewal_preferences", "")
        additional_requirements = requirements.get("additional_requirements", "")
        
        return f"""Generate a professional {contract_type} support contract with the following specifications.

Tenant Context:
{tenant_context}

Contract Description:
{description}

SLA Requirements:
{sla_requirements if sla_requirements else "Standard business hours support"}

Renewal Preferences:
{renewal_preferences if renewal_preferences else "Annual renewal with auto-renew enabled"}

Additional Requirements:
{additional_requirements if additional_requirements else "None specified"}

Instructions:
1. Generate a complete support contract structure as a JSON object
2. Include ALL standard support contract fields:
   - contract_name: A descriptive, professional name for the contract (e.g., "Managed IT Services Agreement - [Customer Name]")
   - description: Detailed description of services covered, scope, and deliverables
   - start_date: Suggested start date in YYYY-MM-DD format (default to today's date)
   - end_date: Suggested end date in YYYY-MM-DD format (calculate based on renewal_frequency, or null for ongoing contracts)
   - monthly_value: Monthly recurring charge in GBP (if applicable, otherwise null)
   - annual_value: Annual value of the contract in GBP (calculate if monthly_value provided, or set directly)
   - setup_fee: One-time setup fee in GBP (default: 0 if not specified)
   - renewal_frequency: How often the contract renews (monthly, quarterly, semi_annual, annual, biennial, triennial, one_time)
   - auto_renew: Whether the contract auto-renews (true/false, default: true for recurring contracts)
   - sla_level: Service level agreement description (e.g., "24/7 Support", "Business Hours (9am-5pm)", "Next Business Day Response")
   - support_hours_included: Number of pre-paid support hours per month/year (if applicable, otherwise null)
   - renewal_notice_days: Days before renewal to send notice (default: 90, typical range: 30-90)
   - cancellation_notice_days: Days notice required for cancellation (default: 30, typical range: 30-90)
   - terms: Comprehensive terms and conditions text covering services, responsibilities, payment terms, termination, etc.
   - notes: Any additional notes or special conditions

3. Extract pricing information from the description if mentioned (e.g., "£500/month", "£6000 annually")
4. Calculate end_date based on start_date + renewal_frequency duration
5. Ensure the contract is suitable for UK legal compliance
6. Include appropriate renewal terms and auto-renewal clauses
7. Make it professional and suitable for business use
8. If pricing is not specified, provide reasonable estimates based on contract type and description

Return ONLY a valid JSON object with ALL the contract fields listed above. Do not include any explanatory text, only the JSON."""
    
    def _extract_support_contract_data(
        self,
        content: str,
        contract_type: str,
        description: str,
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract structured contract data from AI-generated text"""
        # Default values
        contract_data = {
            "contract_name": f"{contract_type.replace('_', ' ').title()} Contract",
            "description": description,
            "contract_type": contract_type,
            "monthly_value": None,
            "annual_value": None,
            "setup_fee": 0,
            "renewal_frequency": requirements.get("renewal_preferences", "annual"),
            "auto_renew": True,
            "sla_level": requirements.get("sla_requirements", ""),
            "support_hours_included": None,
            "renewal_notice_days": 90,
            "cancellation_notice_days": 30,
            "terms": content  # Use full content as terms if we can't parse JSON
        }
        
        # Try to extract values from text using regex patterns
        # This is a fallback if AI doesn't return JSON
        return contract_data
    
    async def generate_contract_from_description(
        self,
        contract_type: str,
        description: str,
        requirements: Optional[Dict[str, Any]] = None,
        is_support_contract: bool = False,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a contract (regular or support) from description
        
        Args:
            contract_type: Type of contract
            description: Description of what the contract should cover
            requirements: Optional specific requirements
            is_support_contract: Whether this is a support contract
            user_id: User ID who requested the generation
        
        Returns:
            Dict with contract data
        """
        if is_support_contract:
            return await self.generate_support_contract_template(
                contract_type=contract_type,
                description=description,
                requirements=requirements,
                user_id=user_id
            )
        else:
            # For regular contracts, return structured data similar to support contracts
            template_result = await self.generate_contract_template(
                contract_type=contract_type,
                description=description,
                requirements=requirements,
                user_id=user_id
            )
            
            # Extract contract name from description or use default
            contract_name = requirements.get("contract_name") if requirements else None
            if not contract_name:
                contract_name = f"{contract_type.replace('_', ' ').title()} Contract"
            
            return {
                "contract_name": contract_name,
                "description": description,
                "contract_type": contract_type,
                "template_content": template_result.get("template_content", ""),
                "placeholder_schema": template_result.get("placeholder_schema", {}),
                "default_values": template_result.get("default_values", {})
            }
    
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
    
    async def generate_contract_from_quote(
        self,
        quote_id: str,
        template_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a contract from an approved quote
        
        Args:
            quote_id: Quote ID to convert
            template_id: Optional contract template ID to use
            user_id: User ID creating the contract
        
        Returns:
            Dict with created contract data
        """
        from app.models.quotes import Quote, QuoteItem, QuoteStatus
        from app.models.contracts import Contract, ContractType, ContractStatus
        from app.models.support_contract import SupportContract, RenewalFrequency
        from app.models.enhanced_contract_templates import EnhancedContractTemplate, ContractTemplateVersion
        import uuid
        
        # Get quote
        quote = self.db.query(Quote).filter(
            Quote.id == quote_id,
            Quote.tenant_id == self.tenant_id
        ).first()
        
        if not quote:
            return {"success": False, "error": "Quote not found"}
        
        # Only allow conversion of accepted quotes
        if quote.status != QuoteStatus.ACCEPTED:
            return {"success": False, "error": "Only accepted quotes can be converted to contracts"}
        
        try:
            # Map quote data to contract data
            contract_data = self._map_quote_to_contract_data(quote)
            
            # If template specified, use it
            if template_id:
                template = self.db.query(EnhancedContractTemplate).filter(
                    EnhancedContractTemplate.id == template_id,
                    EnhancedContractTemplate.tenant_id == self.tenant_id
                ).first()
                
                if template:
                    # Get current version
                    current_version = self.db.query(ContractTemplateVersion).filter(
                        ContractTemplateVersion.template_id == template_id,
                        ContractTemplateVersion.is_current == True
                    ).first()
                    
                    if current_version:
                        # Fill template with quote data
                        contract_content = self.fill_contract_template(
                            current_version.template_content,
                            contract_data.get("placeholder_values", {})
                        )
                        contract_data["contract_content"] = contract_content
                        contract_data["template_id"] = template_id
                        contract_data["template_version_id"] = current_version.id
            
            # Determine contract type from quote
            contract_type = self._determine_contract_type_from_quote(quote)
            
            # Create contract based on type
            if contract_type in ["managed_services", "maintenance", "saas_subscription", "support_hours"]:
                # Create support contract
                contract = self._create_support_contract(contract_data, quote, user_id)
            else:
                # Create regular contract
                contract = self._create_regular_contract(contract_data, quote, user_id)
            
            # Link quote to contract
            quote.contract_id = contract.id if hasattr(contract, 'id') else None
            
            self.db.commit()
            self.db.refresh(contract)
            
            return {
                "success": True,
                "contract": contract,
                "contract_id": contract.id if hasattr(contract, 'id') else None,
                "contract_number": contract.contract_number if hasattr(contract, 'contract_number') else None
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    def _map_quote_to_contract_data(self, quote) -> Dict[str, Any]:
        """Map quote data to contract data structure"""
        from app.models.quotes import QuoteItem
        
        # Get quote items
        items = self.db.query(QuoteItem).filter(QuoteItem.quote_id == quote.id).all()
        
        # Build services list from items
        included_services = []
        for item in items:
            included_services.append({
                "description": item.description,
                "quantity": float(item.quantity),
                "unit_price": float(item.unit_price),
                "total_price": float(item.total_price)
            })
        
        # Calculate pricing
        monthly_value = None
        annual_value = None
        if quote.total_amount:
            # If quote has total, assume annual contract
            annual_value = float(quote.total_amount)
            monthly_value = annual_value / 12
        
        # Build placeholder values for template
        placeholder_values = {
            "customer_name": quote.customer.company_name if quote.customer else "",
            "quote_number": quote.quote_number,
            "quote_title": quote.title,
            "total_amount": float(quote.total_amount) if quote.total_amount else 0,
            "monthly_fee": monthly_value if monthly_value else 0,
            "annual_fee": annual_value if annual_value else 0,
            "start_date": datetime.now().strftime('%Y-%m-%d'),
            "description": quote.description or quote.title
        }
        
        return {
            "contract_name": f"{quote.title} - Contract",
            "description": quote.description or quote.title,
            "monthly_value": monthly_value,
            "annual_value": annual_value,
            "setup_fee": 0,
            "included_services": included_services,
            "terms": quote.notes or "",
            "placeholder_values": placeholder_values
        }
    
    def _determine_contract_type_from_quote(self, quote) -> str:
        """Determine contract type from quote type"""
        quote_type = quote.quote_type or ""
        quote_type_lower = quote_type.lower()
        
        # Map quote types to contract types
        if "managed" in quote_type_lower or "msp" in quote_type_lower:
            return "managed_services"
        elif "software" in quote_type_lower or "license" in quote_type_lower:
            return "software_license"
        elif "saas" in quote_type_lower or "subscription" in quote_type_lower:
            return "saas_subscription"
        elif "maintenance" in quote_type_lower:
            return "maintenance"
        elif "support" in quote_type_lower:
            return "support_hours"
        elif "consulting" in quote_type_lower:
            return "consulting"
        else:
            return "custom"
    
    def _create_support_contract(self, contract_data: Dict[str, Any], quote, user_id: Optional[str]) -> "SupportContract":
        """Create a support contract from quote data"""
        from app.models.support_contract import SupportContract, ContractType, ContractStatus, RenewalFrequency
        from datetime import datetime, timedelta
        
        # Generate contract number
        contract_number = self._generate_contract_number()
        
        # Calculate dates
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=365)  # Default 1 year
        
        contract = SupportContract(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            customer_id=quote.customer_id,
            contract_number=contract_number,
            contract_name=contract_data.get("contract_name", f"Contract for {quote.title}"),
            description=contract_data.get("description", ""),
            contract_type=ContractType.MANAGED_SERVICES,  # Default, can be adjusted
            status=ContractStatus.DRAFT,
            start_date=start_date,
            end_date=end_date,
            renewal_date=end_date,
            renewal_frequency=RenewalFrequency.ANNUAL,
            auto_renew=True,
            monthly_value=contract_data.get("monthly_value"),
            annual_value=contract_data.get("annual_value"),
            setup_fee=contract_data.get("setup_fee", 0),
            terms=contract_data.get("terms", ""),
            included_services=contract_data.get("included_services"),
            quote_id=quote.id
        )
        
        self.db.add(contract)
        return contract
    
    def _create_regular_contract(self, contract_data: Dict[str, Any], quote, user_id: Optional[str]) -> "Contract":
        """Create a regular contract from quote data"""
        from app.models.contracts import Contract, ContractType, ContractStatus
        from datetime import datetime, timedelta
        
        # Generate contract number
        contract_number = self._generate_contract_number()
        
        # Calculate dates
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=365)  # Default 1 year
        
        contract = Contract(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            customer_id=quote.customer_id,
            contract_number=contract_number,
            contract_name=contract_data.get("contract_name", f"Contract for {quote.title}"),
            description=contract_data.get("description", ""),
            contract_type=ContractType.CUSTOM,
            status=ContractStatus.DRAFT,
            start_date=start_date,
            end_date=end_date,
            monthly_value=contract_data.get("monthly_value"),
            annual_value=contract_data.get("annual_value"),
            setup_fee=contract_data.get("setup_fee", 0),
            contract_content=contract_data.get("contract_content", ""),
            placeholder_values=contract_data.get("placeholder_values", {}),
            terms=contract_data.get("terms", ""),
            included_services=contract_data.get("included_services"),
            quote_id=quote.id,
            template_id=contract_data.get("template_id"),
            template_version_id=contract_data.get("template_version_id")
        )
        
        self.db.add(contract)
        return contract
    
    def _generate_contract_number(self) -> str:
        """Generate unique contract number"""
        from datetime import datetime
        prefix = "CT"
        timestamp = datetime.now().strftime("%Y%m%d")
        # Get count of contracts today for sequence number
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        count = self.db.query(Contract).filter(
            Contract.tenant_id == self.tenant_id,
            Contract.created_at >= today_start
        ).count()
        sequence = str(count + 1).zfill(4)
        return f"{prefix}-{timestamp}-{sequence}"

