# User Permissions & Role-Based Access Control (RBAC)

## Overview
The CCS Quote Tool v2 includes a comprehensive permissions system that allows fine-grained control over what users can see and do within the application.

## User Roles

### 1. **Super Admin**
- Has ALL permissions automatically
- Cannot be restricted
- Typically for system administrators
- Can access admin portal

### 2. **Tenant Admin**
- Full access to all tenant features
- Can manage users and permissions
- Can manage API keys and settings
- Default permissions: All except super admin functions

### 3. **Manager**
- Can view analytics and reports
- Can manage customers, discoveries, campaigns, and quotes
- Can approve quotes
- Cannot delete users or manage system settings

### 4. **Sales Rep**
- Can create and edit customers
- Can convert discoveries to leads
- Can create and send quotes
- Cannot delete records or access admin functions

### 5. **User (Read-Only)**
- View-only access to most features
- Cannot create, edit, or delete records
- Suitable for reporting or audit purposes

## Permission Categories

### Dashboard
- `view_dashboard` - View main dashboard
- `view_analytics` - View analytics & reports

### Customers
- `view_customers` - View customer list and details
- `create_customers` - Create new customers
- `edit_customers` - Edit existing customers
- `delete_customers` - Delete customers
- `export_customers` - Export customer data

### Discoveries (Campaign Leads)
- `view_discoveries` - View discoveries from campaigns
- `convert_discoveries` - Convert discoveries to CRM leads
- `bulk_convert_discoveries` - Bulk convert multiple discoveries
- `export_discoveries` - Export discovery data

### Campaigns
- `view_campaigns` - View campaign list and details
- `create_campaigns` - Create new campaigns
- `edit_campaigns` - Edit existing campaigns
- `delete_campaigns` - Delete campaigns
- `start_campaigns` - Start/stop campaigns
- `view_campaign_results` - View campaign results and analytics

### Quotes
- `view_quotes` - View quotes
- `create_quotes` - Create new quotes
- `edit_quotes` - Edit existing quotes
- `delete_quotes` - Delete quotes
- `approve_quotes` - Approve quotes for sending
- `send_quotes` - Send quotes to customers
- `export_quotes` - Export quote data

### Users
- `view_users` - View user list
- `create_users` - Create new users
- `edit_users` - Edit existing users
- `delete_users` - Delete users
- `manage_permissions` - Manage user permissions

### Settings
- `view_settings` - View settings
- `edit_settings` - Edit settings
- `manage_api_keys` - Manage API keys (OpenAI, Google Maps, Companies House)
- `view_billing` - View billing information

## Default Permission Sets

### Super Admin
✅ **ALL PERMISSIONS** (automatic, cannot be restricted)

### Tenant Admin
✅ All Dashboard permissions
✅ All Customer permissions
✅ All Discovery permissions
✅ All Campaign permissions
✅ All Quote permissions
✅ All User permissions
✅ All Settings permissions

### Manager
✅ Dashboard: view_dashboard, view_analytics
✅ Customers: view, create, edit, export
✅ Discoveries: view, convert, bulk_convert, export
✅ Campaigns: view, create, edit, start, view_results
✅ Quotes: view, create, edit, approve, send, export
✅ Users: view only
✅ Settings: view only

### Sales Rep
✅ Dashboard: view_dashboard
✅ Customers: view, create, edit
✅ Discoveries: view, convert
✅ Campaigns: view, view_results
✅ Quotes: view, create, edit, send
✅ Settings: view only

### User (Read-Only)
✅ Dashboard: view_dashboard
✅ Customers: view only
✅ Discoveries: view only
✅ Campaigns: view only
✅ Quotes: view only
✅ Settings: view only

## Creating Users with Custom Permissions

### Backend API

#### Get Available Permissions
```http
GET /api/v1/users/permissions/available
Authorization: Bearer {token}
```

Response:
```json
{
  "permissions": {
    "dashboard": {
      "view_dashboard": "View Dashboard",
      "view_analytics": "View Analytics & Reports"
    },
    "customers": {
      "view_customers": "View Customers",
      "create_customers": "Create Customers",
      ...
    },
    ...
  },
  "roles": {
    "super_admin": "Super Admin (All Permissions)",
    "tenant_admin": "Tenant Admin",
    ...
  }
}
```

#### Get Default Permissions for Role
```http
GET /api/v1/users/permissions/defaults/{role}
Authorization: Bearer {token}
```

Response:
```json
{
  "role": "sales_rep",
  "permissions": [
    "view_dashboard",
    "view_customers",
    "create_customers",
    ...
  ]
}
```

#### Create User with Custom Permissions
```http
POST /api/v1/users/
Authorization: Bearer {token}
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "newuser",
  "first_name": "John",
  "last_name": "Doe",
  "password": "SecurePassword123!",
  "role": "sales_rep",
  "permissions": [
    "view_dashboard",
    "view_customers",
    "create_customers",
    "edit_customers"
  ]
}
```

### Frontend Implementation (To Be Built)

When creating/editing a user, the UI will:

1. **Role Selection Dropdown**
   - Select from: Super Admin, Tenant Admin, Manager, Sales Rep, User

2. **Auto-populate Permissions**
   - When role is selected, automatically check the default permissions for that role
   - User can then customize by checking/unchecking individual permissions

3. **Permission Checkboxes (Organized by Category)**
   ```
   📊 Dashboard
   ☑️ View Dashboard
   ☑️ View Analytics & Reports

   👥 Customers
   ☑️ View Customers
   ☑️ Create Customers
   ☑️ Edit Customers
   ☐ Delete Customers
   ☑️ Export Customer Data

   🔍 Discoveries
   ☑️ View Discoveries
   ☑️ Convert Discoveries to Leads
   ☐ Bulk Convert Discoveries
   ☑️ Export Discovery Data

   ... (continue for all categories)
   ```

4. **Super Admin Note**
   - When "Super Admin" role is selected, show message:
     "Super Admin has all permissions automatically. Permission checkboxes are disabled."
   - Disable all checkboxes for Super Admin role

5. **Save Behavior**
   - Save custom permissions array to user record
   - Permissions override role defaults if specified

## Permission Checking

### Backend (Python)
```python
from app.core.permissions import has_permission

# Check single permission
if has_permission(user.permissions, "create_customers", user.role.value):
    # User can create customers
    pass

# Check multiple permissions (any)
if has_any_permission(user.permissions, ["edit_customers", "delete_customers"], user.role.value):
    # User can edit OR delete customers
    pass

# Check multiple permissions (all)
if has_all_permissions(user.permissions, ["create_quotes", "send_quotes"], user.role.value):
    # User can create AND send quotes
    pass
```

### Frontend (React/TypeScript) - To Be Implemented
```typescript
// Check permission
const canCreateCustomers = hasPermission(user.permissions, 'create_customers');

// Conditionally render UI
{canCreateCustomers && (
  <Button onClick={handleCreateCustomer}>
    Create Customer
  </Button>
)}

// Disable features
<Button 
  disabled={!hasPermission(user.permissions, 'delete_customers')}
  onClick={handleDelete}
>
  Delete
</Button>
```

## Database Schema

### User Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    role VARCHAR(50) NOT NULL,  -- super_admin, tenant_admin, manager, sales_rep, user
    permissions JSONB DEFAULT '[]',  -- Array of permission strings
    ...
);
```

### Example Permissions Data
```json
[
  "view_dashboard",
  "view_analytics",
  "view_customers",
  "create_customers",
  "edit_customers",
  "view_discoveries",
  "convert_discoveries"
]
```

## Migration Path

### For Existing Users
1. Run migration to add `permissions` column (already exists)
2. Populate permissions based on current role:
   ```sql
   UPDATE users 
   SET permissions = (
     CASE role
       WHEN 'tenant_admin' THEN '["view_dashboard", "view_analytics", ...]'::jsonb
       WHEN 'manager' THEN '["view_dashboard", ...]'::jsonb
       ...
     END
   );
   ```

### For New Installations
- Users created with role automatically get default permissions
- Can be customized during creation or later via edit

## Security Considerations

1. **Super Admin Protection**
   - Super admin role always has all permissions
   - Cannot be restricted via permissions array
   - Hardcoded in `has_permission()` function

2. **Permission Validation**
   - Backend validates all permissions on every request
   - Frontend checks are for UX only (not security)
   - Never trust frontend permission checks alone

3. **Audit Trail**
   - Consider logging permission changes
   - Track who granted/revoked permissions
   - Monitor permission escalation attempts

4. **Least Privilege Principle**
   - Default to minimal permissions
   - Grant additional permissions as needed
   - Regularly review user permissions

## Future Enhancements

1. **Permission Groups**
   - Create reusable permission templates
   - e.g., "Sales Team", "Support Team", "Management"

2. **Time-Based Permissions**
   - Grant temporary elevated permissions
   - Auto-revoke after expiration

3. **IP-Based Restrictions**
   - Restrict certain permissions to office IP
   - e.g., Delete operations only from office

4. **Two-Factor for Sensitive Operations**
   - Require 2FA for user management
   - Require 2FA for API key changes

5. **Permission Inheritance**
   - Hierarchical permission structure
   - Child permissions inherit from parent

## Files Modified/Created

### Backend
- `backend/app/core/permissions.py` - Permission definitions and helper functions
- `backend/app/api/v1/endpoints/users.py` - Added permission endpoints
- `backend/app/models/tenant.py` - User model (already had permissions field)

### Frontend (To Be Implemented)
- `frontend/src/pages/Users.tsx` - Add permission checkboxes
- `frontend/src/components/PermissionMatrix.tsx` - New component for permission selection
- `frontend/src/hooks/usePermissions.ts` - Permission checking hooks
- `frontend/src/components/Layout.tsx` - Hide menu items based on permissions

## Testing

### Test Permission Checking
```python
# Test super admin bypass
assert has_permission([], "any_permission", "super_admin") == True

# Test regular user
user_perms = ["view_customers", "create_customers"]
assert has_permission(user_perms, "view_customers") == True
assert has_permission(user_perms, "delete_customers") == False

# Test multiple permissions
assert has_any_permission(user_perms, ["edit_customers", "create_customers"]) == True
assert has_all_permissions(user_perms, ["view_customers", "create_customers"]) == True
```

### Test User Creation
```python
# Create user with custom permissions
user_data = {
    "email": "test@example.com",
    "username": "testuser",
    "first_name": "Test",
    "last_name": "User",
    "password": "TestPass123!",
    "role": "sales_rep",
    "permissions": ["view_customers", "create_customers"]
}

response = client.post("/api/v1/users/", json=user_data)
assert response.status_code == 201
assert response.json()["permissions"] == ["view_customers", "create_customers"]
```

## Summary

The permissions system provides:
- ✅ Fine-grained access control
- ✅ Role-based defaults with custom overrides
- ✅ Easy-to-understand permission names
- ✅ Organized by feature category
- ✅ Super admin bypass for system administrators
- ✅ Backend API ready for frontend implementation
- ✅ Extensible for future permissions

Next steps:
1. Build frontend permission matrix UI
2. Implement permission checks in frontend components
3. Hide/disable menu items based on permissions
4. Add permission audit logging
5. Create permission management UI for admins

