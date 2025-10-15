"""
User Permissions System

Defines granular permissions for role-based access control.
Super Admin has all permissions by default.
"""

from typing import List, Dict

# Permission categories and their individual permissions
PERMISSIONS = {
    "dashboard": {
        "view_dashboard": "View Dashboard",
        "view_analytics": "View Analytics & Reports"
    },
    "customers": {
        "view_customers": "View Customers",
        "create_customers": "Create Customers",
        "edit_customers": "Edit Customers",
        "delete_customers": "Delete Customers",
        "export_customers": "Export Customer Data"
    },
    "discoveries": {
        "view_discoveries": "View Discoveries",
        "convert_discoveries": "Convert Discoveries to Leads",
        "bulk_convert_discoveries": "Bulk Convert Discoveries",
        "export_discoveries": "Export Discovery Data"
    },
    "campaigns": {
        "view_campaigns": "View Campaigns",
        "create_campaigns": "Create Campaigns",
        "edit_campaigns": "Edit Campaigns",
        "delete_campaigns": "Delete Campaigns",
        "start_campaigns": "Start/Stop Campaigns",
        "view_campaign_results": "View Campaign Results"
    },
    "quotes": {
        "view_quotes": "View Quotes",
        "create_quotes": "Create Quotes",
        "edit_quotes": "Edit Quotes",
        "delete_quotes": "Delete Quotes",
        "approve_quotes": "Approve Quotes",
        "send_quotes": "Send Quotes to Customers",
        "export_quotes": "Export Quote Data"
    },
    "users": {
        "view_users": "View Users",
        "create_users": "Create Users",
        "edit_users": "Edit Users",
        "delete_users": "Delete Users",
        "manage_permissions": "Manage User Permissions"
    },
    "settings": {
        "view_settings": "View Settings",
        "edit_settings": "Edit Settings",
        "manage_api_keys": "Manage API Keys",
        "view_billing": "View Billing Information"
    }
}

# Default permission sets for each role
DEFAULT_ROLE_PERMISSIONS = {
    "super_admin": [],  # Super admin gets all permissions automatically
    "tenant_admin": [
        # Dashboard
        "view_dashboard", "view_analytics",
        # Customers
        "view_customers", "create_customers", "edit_customers", "delete_customers", "export_customers",
        # Discoveries
        "view_discoveries", "convert_discoveries", "bulk_convert_discoveries", "export_discoveries",
        # Campaigns
        "view_campaigns", "create_campaigns", "edit_campaigns", "delete_campaigns", 
        "start_campaigns", "view_campaign_results",
        # Quotes
        "view_quotes", "create_quotes", "edit_quotes", "delete_quotes", 
        "approve_quotes", "send_quotes", "export_quotes",
        # Users
        "view_users", "create_users", "edit_users", "delete_users", "manage_permissions",
        # Settings
        "view_settings", "edit_settings", "manage_api_keys", "view_billing"
    ],
    "manager": [
        # Dashboard
        "view_dashboard", "view_analytics",
        # Customers
        "view_customers", "create_customers", "edit_customers", "export_customers",
        # Discoveries
        "view_discoveries", "convert_discoveries", "bulk_convert_discoveries", "export_discoveries",
        # Campaigns
        "view_campaigns", "create_campaigns", "edit_campaigns", "start_campaigns", "view_campaign_results",
        # Quotes
        "view_quotes", "create_quotes", "edit_quotes", "approve_quotes", "send_quotes", "export_quotes",
        # Users
        "view_users",
        # Settings
        "view_settings"
    ],
    "sales_rep": [
        # Dashboard
        "view_dashboard",
        # Customers
        "view_customers", "create_customers", "edit_customers",
        # Discoveries
        "view_discoveries", "convert_discoveries",
        # Campaigns
        "view_campaigns", "view_campaign_results",
        # Quotes
        "view_quotes", "create_quotes", "edit_quotes", "send_quotes",
        # Settings
        "view_settings"
    ],
    "user": [
        # Dashboard
        "view_dashboard",
        # Customers
        "view_customers",
        # Discoveries
        "view_discoveries",
        # Campaigns
        "view_campaigns",
        # Quotes
        "view_quotes",
        # Settings
        "view_settings"
    ]
}


def get_all_permissions() -> List[str]:
    """Get a flat list of all permission keys"""
    all_perms = []
    for category in PERMISSIONS.values():
        all_perms.extend(category.keys())
    return all_perms


def get_permissions_by_category() -> Dict[str, Dict[str, str]]:
    """Get permissions organized by category"""
    return PERMISSIONS


def get_default_permissions(role: str) -> List[str]:
    """Get default permissions for a role"""
    return DEFAULT_ROLE_PERMISSIONS.get(role, DEFAULT_ROLE_PERMISSIONS["user"])


def has_permission(user_permissions: List[str], required_permission: str, user_role: str = None) -> bool:
    """
    Check if user has a specific permission
    
    Args:
        user_permissions: List of permission keys the user has
        required_permission: The permission key to check
        user_role: Optional user role (super_admin bypasses all checks)
    
    Returns:
        True if user has permission, False otherwise
    """
    # Super admin has all permissions
    if user_role == "super_admin":
        return True
    
    return required_permission in user_permissions


def has_any_permission(user_permissions: List[str], required_permissions: List[str], user_role: str = None) -> bool:
    """Check if user has any of the required permissions"""
    if user_role == "super_admin":
        return True
    
    return any(perm in user_permissions for perm in required_permissions)


def has_all_permissions(user_permissions: List[str], required_permissions: List[str], user_role: str = None) -> bool:
    """Check if user has all of the required permissions"""
    if user_role == "super_admin":
        return True
    
    return all(perm in user_permissions for perm in required_permissions)


