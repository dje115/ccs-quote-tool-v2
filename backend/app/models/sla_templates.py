#!/usr/bin/env python3
"""
SLA Policy Templates - Pre-configured templates for common SLA scenarios
"""

from typing import Dict, Any, List

# Template definitions
SLA_TEMPLATES: List[Dict[str, Any]] = [
    {
        "id": "standard_business_hours",
        "name": "Standard Business Hours (9-5 Mon-Fri)",
        "description": "Standard SLA for business hours support (Monday to Friday, 9 AM to 5 PM)",
        "sla_level": "Standard",
        "first_response_hours": 4,
        "first_response_hours_urgent": 1,
        "first_response_hours_high": 2,
        "first_response_hours_medium": 4,
        "first_response_hours_low": 8,
        "resolution_hours": 24,
        "resolution_hours_urgent": 4,
        "resolution_hours_high": 8,
        "resolution_hours_medium": 24,
        "resolution_hours_low": 48,
        "business_hours_start": "09:00",
        "business_hours_end": "17:00",
        "business_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "timezone": "Europe/London",
        "availability_hours": "Business Hours",
        "escalation_warning_percent": 80,
        "escalation_critical_percent": 95,
        "auto_escalate_on_breach": True
    },
    {
        "id": "extended_business_hours",
        "name": "Extended Business Hours (8-6 Mon-Fri)",
        "description": "Extended business hours support (Monday to Friday, 8 AM to 6 PM)",
        "sla_level": "Extended",
        "first_response_hours": 2,
        "first_response_hours_urgent": 1,
        "first_response_hours_high": 1,
        "first_response_hours_medium": 2,
        "first_response_hours_low": 4,
        "resolution_hours": 16,
        "resolution_hours_urgent": 2,
        "resolution_hours_high": 4,
        "resolution_hours_medium": 16,
        "resolution_hours_low": 32,
        "business_hours_start": "08:00",
        "business_hours_end": "18:00",
        "business_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "timezone": "Europe/London",
        "availability_hours": "Extended Business Hours",
        "escalation_warning_percent": 80,
        "escalation_critical_percent": 95,
        "auto_escalate_on_breach": True
    },
    {
        "id": "24_7_support",
        "name": "24/7 Support",
        "description": "Round-the-clock support with fast response times",
        "sla_level": "24/7",
        "first_response_hours": 1,
        "first_response_hours_urgent": 0.5,
        "first_response_hours_high": 0.5,
        "first_response_hours_medium": 1,
        "first_response_hours_low": 2,
        "resolution_hours": 8,
        "resolution_hours_urgent": 2,
        "resolution_hours_high": 4,
        "resolution_hours_medium": 8,
        "resolution_hours_low": 16,
        "business_hours_start": "00:00",
        "business_hours_end": "23:59",
        "business_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "timezone": "UTC",
        "availability_hours": "24/7",
        "escalation_warning_percent": 75,
        "escalation_critical_percent": 90,
        "auto_escalate_on_breach": True
    },
    {
        "id": "premium_support",
        "name": "Premium Support (Gold)",
        "description": "Premium SLA with guaranteed fast response and resolution times",
        "sla_level": "Gold",
        "first_response_hours": 0.5,
        "first_response_hours_urgent": 0.25,
        "first_response_hours_high": 0.25,
        "first_response_hours_medium": 0.5,
        "first_response_hours_low": 1,
        "resolution_hours": 4,
        "resolution_hours_urgent": 1,
        "resolution_hours_high": 2,
        "resolution_hours_medium": 4,
        "resolution_hours_low": 8,
        "business_hours_start": "08:00",
        "business_hours_end": "20:00",
        "business_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
        "timezone": "Europe/London",
        "availability_hours": "Extended Premium Hours",
        "uptime_target": 9995,  # 99.95%
        "escalation_warning_percent": 70,
        "escalation_critical_percent": 85,
        "auto_escalate_on_breach": True
    },
    {
        "id": "standard_support",
        "name": "Standard Support (Silver)",
        "description": "Standard SLA with reasonable response and resolution times",
        "sla_level": "Silver",
        "first_response_hours": 4,
        "first_response_hours_urgent": 1,
        "first_response_hours_high": 2,
        "first_response_hours_medium": 4,
        "first_response_hours_low": 8,
        "resolution_hours": 24,
        "resolution_hours_urgent": 4,
        "resolution_hours_high": 8,
        "resolution_hours_medium": 24,
        "resolution_hours_low": 48,
        "business_hours_start": "09:00",
        "business_hours_end": "17:00",
        "business_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "timezone": "Europe/London",
        "availability_hours": "Business Hours",
        "uptime_target": 9990,  # 99.90%
        "escalation_warning_percent": 80,
        "escalation_critical_percent": 95,
        "auto_escalate_on_breach": True
    },
    {
        "id": "basic_support",
        "name": "Basic Support (Bronze)",
        "description": "Basic SLA with standard response and resolution times",
        "sla_level": "Bronze",
        "first_response_hours": 8,
        "first_response_hours_urgent": 2,
        "first_response_hours_high": 4,
        "first_response_hours_medium": 8,
        "first_response_hours_low": 16,
        "resolution_hours": 48,
        "resolution_hours_urgent": 8,
        "resolution_hours_high": 16,
        "resolution_hours_medium": 48,
        "resolution_hours_low": 72,
        "business_hours_start": "09:00",
        "business_hours_end": "17:00",
        "business_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "timezone": "Europe/London",
        "availability_hours": "Business Hours",
        "uptime_target": 9950,  # 99.50%
        "escalation_warning_percent": 80,
        "escalation_critical_percent": 95,
        "auto_escalate_on_breach": False
    },
    {
        "id": "urgent_only",
        "name": "Urgent Priority Only",
        "description": "SLA policy that applies only to urgent priority tickets",
        "sla_level": "Urgent",
        "priority": "urgent",  # Only applies to urgent tickets
        "first_response_hours": 0.5,
        "resolution_hours": 2,
        "business_hours_start": "00:00",
        "business_hours_end": "23:59",
        "business_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "timezone": "UTC",
        "availability_hours": "24/7",
        "escalation_warning_percent": 70,
        "escalation_critical_percent": 85,
        "auto_escalate_on_breach": True
    },
    {
        "id": "technical_support",
        "name": "Technical Support SLA",
        "description": "SLA specifically for technical support tickets",
        "sla_level": "Technical",
        "ticket_type": "technical",
        "first_response_hours": 2,
        "first_response_hours_urgent": 0.5,
        "first_response_hours_high": 1,
        "first_response_hours_medium": 2,
        "first_response_hours_low": 4,
        "resolution_hours": 12,
        "resolution_hours_urgent": 2,
        "resolution_hours_high": 4,
        "resolution_hours_medium": 12,
        "resolution_hours_low": 24,
        "business_hours_start": "09:00",
        "business_hours_end": "17:00",
        "business_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "timezone": "Europe/London",
        "availability_hours": "Business Hours",
        "escalation_warning_percent": 80,
        "escalation_critical_percent": 95,
        "auto_escalate_on_breach": True
    }
]


def get_template(template_id: str) -> Dict[str, Any] | None:
    """Get a template by ID"""
    for template in SLA_TEMPLATES:
        if template["id"] == template_id:
            return template
    return None


def list_templates() -> List[Dict[str, Any]]:
    """List all available templates"""
    return SLA_TEMPLATES


def create_policy_from_template(template_id: str, name: str, tenant_id: str, **overrides) -> Dict[str, Any]:
    """Create an SLA policy from a template with optional overrides"""
    template = get_template(template_id)
    if not template:
        raise ValueError(f"Template {template_id} not found")
    
    policy_data = template.copy()
    policy_data["name"] = name
    policy_data["tenant_id"] = tenant_id
    policy_data.pop("id", None)  # Remove template ID
    
    # Apply overrides
    policy_data.update(overrides)
    
    return policy_data

