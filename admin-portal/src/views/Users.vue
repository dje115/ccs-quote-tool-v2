<template>
  <div class="users-management">
    <div class="header">
      <h1>User Management</h1>
      <p>Manage all users across all tenants</p>
    </div>

    <!-- Search Bar -->
    <div class="search-bar">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search by name, email, or tenant..."
        class="search-input"
      />
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Loading users...</p>
    </div>

    <!-- Error State -->
    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <!-- Success Message -->
    <div v-if="successMessage" class="success-message">
      {{ successMessage }}
    </div>

    <!-- Users Table -->
    <div v-if="!loading && !error" class="users-table">
      <table>
        <thead>
          <tr>
            <th>Full Name</th>
            <th>Email</th>
            <th>Company</th>
            <th>Tenant</th>
            <th>Role</th>
            <th>Status</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in filteredUsers" :key="user.id">
            <td>
              <strong>{{ user.full_name }}</strong>
            </td>
            <td>{{ user.email }}</td>
            <td>
              <span class="company-badge">{{ user.company_name || 'Not set' }}</span>
            </td>
            <td>
              <span class="tenant-badge">{{ user.tenant_name }}</span>
            </td>
            <td>
              <span :class="['role-badge', `role-${user.role}`]">
                {{ user.role }}
              </span>
            </td>
            <td>
              <span :class="['status-badge', user.is_active ? 'active' : 'inactive']">
                {{ user.is_active ? 'Active' : 'Inactive' }}
              </span>
            </td>
            <td>{{ formatDate(user.created_at) }}</td>
            <td>
              <button
                @click="openResetPasswordDialog(user)"
                class="btn-reset"
                title="Reset Password"
              >
                🔑 Reset Password
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="filteredUsers.length === 0" class="no-results">
        <p>No users found matching your search.</p>
      </div>
    </div>

    <!-- Reset Password Dialog -->
    <div v-if="showResetDialog" class="modal-overlay" @click="closeResetDialog">
      <div class="modal-content" @click.stop>
        <h2>Reset Password</h2>
        <p>Reset password for: <strong>{{ selectedUser?.full_name }}</strong> ({{ selectedUser?.email }})</p>
        
        <div class="form-group">
          <label>New Password:</label>
          <input
            v-model="newPassword"
            type="text"
            placeholder="Enter new password"
            class="input-field"
          />
        </div>

        <div class="modal-actions">
          <button @click="closeResetDialog" class="btn-cancel">Cancel</button>
          <button @click="resetPassword" class="btn-confirm" :disabled="!newPassword || resetting">
            {{ resetting ? 'Resetting...' : 'Reset Password' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'UsersManagement',
  data() {
    return {
      users: [],
      loading: false,
      error: null,
      successMessage: null,
      searchQuery: '',
      showResetDialog: false,
      selectedUser: null,
      newPassword: '',
      resetting: false
    };
  },
  computed: {
    filteredUsers() {
      if (!this.searchQuery) {
        return this.users;
      }
      const query = this.searchQuery.toLowerCase();
      return this.users.filter(user =>
        user.full_name.toLowerCase().includes(query) ||
        user.email.toLowerCase().includes(query) ||
        user.tenant_name.toLowerCase().includes(query) ||
        (user.company_name && user.company_name.toLowerCase().includes(query))
      );
    }
  },
  mounted() {
    this.loadUsers();
  },
  methods: {
    async loadUsers() {
      this.loading = true;
      this.error = null;

      try {
        const token = localStorage.getItem('admin_token');
        const response = await axios.get('http://localhost:8000/api/v1/admin/users', {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });

        this.users = response.data.sort((a, b) => {
          // Sort by tenant name, then by full name
          if (a.tenant_name !== b.tenant_name) {
            return a.tenant_name.localeCompare(b.tenant_name);
          }
          return a.full_name.localeCompare(b.full_name);
        });
      } catch (err) {
        console.error('Error loading users:', err);
        this.error = err.response?.data?.detail || 'Failed to load users';
      } finally {
        this.loading = false;
      }
    },
    openResetPasswordDialog(user) {
      this.selectedUser = user;
      this.newPassword = '';
      this.showResetDialog = true;
    },
    closeResetDialog() {
      this.showResetDialog = false;
      this.selectedUser = null;
      this.newPassword = '';
    },
    async resetPassword() {
      if (!this.newPassword || !this.selectedUser) return;

      this.resetting = true;
      this.error = null;
      this.successMessage = null;

      try {
        const token = localStorage.getItem('admin_token');
        await axios.post(
          `http://localhost:8000/api/v1/admin/users/${this.selectedUser.id}/reset-password`,
          { new_password: this.newPassword },
          {
            headers: {
              Authorization: `Bearer ${token}`
            }
          }
        );

        this.successMessage = `Password reset successfully for ${this.selectedUser.email}`;
        this.closeResetDialog();

        // Clear success message after 5 seconds
        setTimeout(() => {
          this.successMessage = null;
        }, 5000);
      } catch (err) {
        console.error('Error resetting password:', err);
        this.error = err.response?.data?.detail || 'Failed to reset password';
      } finally {
        this.resetting = false;
      }
    },
    formatDate(dateString) {
      if (!dateString) return 'N/A';
      const date = new Date(dateString);
      return date.toLocaleDateString('en-GB', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    }
  }
};
</script>

<style scoped>
.users-management {
  padding: 2rem;
}

.header {
  margin-bottom: 2rem;
}

.header h1 {
  margin: 0 0 0.5rem 0;
  color: #1a237e;
}

.header p {
  margin: 0;
  color: #666;
}

.search-bar {
  margin-bottom: 2rem;
}

.search-input {
  width: 100%;
  max-width: 500px;
  padding: 12px 20px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 0.3s;
}

.search-input:focus {
  outline: none;
  border-color: #1976d2;
}

.loading {
  text-align: center;
  padding: 3rem;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #1976d2;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  background-color: #ffebee;
  color: #c62828;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  border-left: 4px solid #c62828;
}

.success-message {
  background-color: #e8f5e9;
  color: #2e7d32;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  border-left: 4px solid #2e7d32;
}

.users-table {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background-color: #f5f5f5;
}

th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  color: #333;
  border-bottom: 2px solid #e0e0e0;
}

td {
  padding: 1rem;
  border-bottom: 1px solid #f0f0f0;
}

tr:hover {
  background-color: #fafafa;
}

.company-badge {
  display: inline-block;
  padding: 4px 12px;
  background-color: #f3e5f5;
  color: #6a1b9a;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
}

.tenant-badge {
  display: inline-block;
  padding: 4px 12px;
  background-color: #e3f2fd;
  color: #1565c0;
  border-radius: 12px;
  font-size: 0.875rem;
  font-weight: 500;
}

.role-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.875rem;
  font-weight: 500;
}

.role-admin {
  background-color: #fce4ec;
  color: #c2185b;
}

.role-user {
  background-color: #f3e5f5;
  color: #7b1fa2;
}

.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.875rem;
  font-weight: 500;
}

.status-badge.active {
  background-color: #e8f5e9;
  color: #2e7d32;
}

.status-badge.inactive {
  background-color: #ffebee;
  color: #c62828;
}

.btn-reset {
  padding: 8px 16px;
  background-color: #ff9800;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: background-color 0.3s;
}

.btn-reset:hover {
  background-color: #f57c00;
}

.no-results {
  text-align: center;
  padding: 3rem;
  color: #666;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  max-width: 500px;
  width: 90%;
}

.modal-content h2 {
  margin: 0 0 1rem 0;
  color: #1a237e;
}

.modal-content p {
  margin-bottom: 1.5rem;
  color: #666;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #333;
}

.input-field {
  width: 100%;
  padding: 12px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 0.3s;
}

.input-field:focus {
  outline: none;
  border-color: #1976d2;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

.btn-cancel {
  padding: 10px 24px;
  background-color: #f5f5f5;
  color: #333;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.3s;
}

.btn-cancel:hover {
  background-color: #e0e0e0;
}

.btn-confirm {
  padding: 10px 24px;
  background-color: #1976d2;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.3s;
}

.btn-confirm:hover:not(:disabled) {
  background-color: #1565c0;
}

.btn-confirm:disabled {
  background-color: #bdbdbd;
  cursor: not-allowed;
}
</style>

