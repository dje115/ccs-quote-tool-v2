<template>
  <div class="tenants">
    <div class="page-header">
      <h1>Tenant Management</h1>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        Create New Tenant
      </el-button>
    </div>
    
    <!-- Filters -->
    <el-card class="filter-card">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-input
            v-model="filters.search"
            placeholder="Search tenants..."
            @input="loadTenants"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filters.status" placeholder="Status" @change="loadTenants">
            <el-option label="All" value="" />
            <el-option label="Active" value="active" />
            <el-option label="Trial" value="trial" />
            <el-option label="Suspended" value="suspended" />
          </el-select>
        </el-col>
      </el-row>
    </el-card>
    
    <!-- Tenants Table -->
    <el-card>
      <el-table :data="tenants" v-loading="loading" style="width: 100%">
        <el-table-column prop="name" label="Name" />
        <el-table-column prop="slug" label="Slug" />
        <el-table-column prop="domain" label="Domain" />
        <el-table-column prop="status" label="Status">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ scope.row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="plan" label="Plan" />
        <el-table-column prop="created_at" label="Created" />
        <el-table-column label="Actions" width="200">
          <template #default="scope">
            <el-button size="small" @click="editTenant(scope.row)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button
              size="small"
              :type="scope.row.status === 'active' ? 'warning' : 'success'"
              @click="toggleTenantStatus(scope.row)"
            >
              {{ scope.row.status === 'active' ? 'Suspend' : 'Activate' }}
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="deleteTenant(scope.row)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadTenants"
          @current-change="loadTenants"
        />
      </div>
    </el-card>
    
    <!-- Create/Edit Tenant Dialog -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingTenantId ? 'Edit Tenant' : 'Create New Tenant'"
      width="600px"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="120px"
      >
        <el-form-item label="Name" prop="name">
          <el-input v-model="createForm.name" placeholder="Tenant name" />
        </el-form-item>
        
        <el-form-item label="Slug" prop="slug">
          <el-input v-model="createForm.slug" placeholder="tenant-slug" />
        </el-form-item>
        
        <el-form-item label="Domain" prop="domain">
          <el-input v-model="createForm.domain" placeholder="tenant.example.com" />
        </el-form-item>
        
        <el-form-item label="Plan" prop="plan">
          <el-select v-model="createForm.plan" placeholder="Select plan">
            <el-option label="Trial" value="trial" />
            <el-option label="Basic" value="basic" />
            <el-option label="Professional" value="professional" />
            <el-option label="Enterprise" value="enterprise" />
          </el-select>
        </el-form-item>
        
        <el-form-item v-if="!editingTenantId" label="Admin Email" prop="admin_email">
          <el-input v-model="createForm.admin_email" type="email" placeholder="admin@tenant.com" />
        </el-form-item>
        
        <el-form-item v-if="!editingTenantId" label="Admin Password" prop="admin_password">
          <el-input v-model="createForm.admin_password" type="password" placeholder="Password" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateDialog = false">Cancel</el-button>
        <el-button type="primary" @click="createTenant" :loading="creating">
          {{ editingTenantId ? 'Update Tenant' : 'Create Tenant' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

export default {
  name: 'Tenants',
  setup() {
    const loading = ref(false)
    const creating = ref(false)
    const showCreateDialog = ref(false)
    const editingTenantId = ref(null)
    const tenants = ref([])
    const currentPage = ref(1)
    const pageSize = ref(20)
    const total = ref(0)
    
    const filters = reactive({
      search: '',
      status: ''
    })
    
    const createForm = reactive({
      name: '',
      slug: '',
      domain: '',
      plan: 'trial',
      admin_email: '',
      admin_password: ''
    })
    
    const createRules = {
      name: [{ required: true, message: 'Please enter tenant name', trigger: 'blur' }],
      slug: [{ required: true, message: 'Please enter tenant slug', trigger: 'blur' }],
      admin_email: [{ required: true, message: 'Please enter admin email', trigger: 'blur' }],
      admin_password: [{ required: true, message: 'Please enter admin password', trigger: 'blur' }]
    }
    
    const getStatusType = (status) => {
      switch (status) {
        case 'active': return 'success'
        case 'trial': return 'warning'
        case 'suspended': return 'danger'
        default: return 'info'
      }
    }
    
    const loadTenants = async () => {
      loading.value = true
      try {
        const token = localStorage.getItem('admin_token')
        
        const params = {
          page: currentPage.value,
          size: pageSize.value,
          search: filters.search,
          status: filters.status
        }
        
        const response = await axios.get('http://localhost:8000/api/v1/admin/tenants', { 
          params,
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        
        tenants.value = response.data.tenants
        total.value = response.data.total
      } catch (error) {
        console.error('Failed to load tenants:', error)
        if (error.response?.status === 401) {
          // Token expired, redirect to login
          localStorage.removeItem('admin_token')
          router.push('/login')
        } else {
          ElMessage.error('Failed to load tenants')
        }
      } finally {
        loading.value = false
      }
    }
    
    const createTenant = async () => {
      try {
        creating.value = true
        const token = localStorage.getItem('admin_token')
        
        if (editingTenantId.value) {
          // Update existing tenant
          await axios.put(`http://localhost:8000/api/v1/admin/tenants/${editingTenantId.value}`, createForm, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })
          ElMessage.success('Tenant updated successfully!')
        } else {
          // Create new tenant
          await axios.post('http://localhost:8000/api/v1/admin/tenants', createForm, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })
          ElMessage.success('Tenant created successfully!')
        }
        
        showCreateDialog.value = false
        editingTenantId.value = null
        loadTenants()
        
        // Reset form
        Object.assign(createForm, {
          name: '',
          slug: '',
          domain: '',
          plan: 'trial',
          admin_email: '',
          admin_password: ''
        })
      } catch (error) {
        console.error('Failed to save tenant:', error)
        if (error.response?.status === 401) {
          localStorage.removeItem('admin_token')
          router.push('/login')
        } else {
          ElMessage.error(error.response?.data?.detail || 'Failed to save tenant')
        }
      } finally {
        creating.value = false
      }
    }
    
    const editTenant = (tenant) => {
      // Pre-fill the create form with existing tenant data
      Object.assign(createForm, {
        name: tenant.name,
        slug: tenant.slug,
        domain: tenant.domain,
        plan: tenant.plan,
        admin_email: '', // Don't show current admin email for security
        admin_password: '' // Don't show current password for security
      })
      
      // Store the tenant ID for update
      editingTenantId.value = tenant.id
      showCreateDialog.value = true
    }
    
    const toggleTenantStatus = async (tenant) => {
      try {
        const token = localStorage.getItem('admin_token')
        let newStatus, action
        
        if (tenant.status === 'active') {
          newStatus = 'suspended'
          action = 'suspended'
        } else if (tenant.status === 'trial') {
          newStatus = 'active'
          action = 'activated'
        } else {
          newStatus = 'active'
          action = 'activated'
        }
        
        await axios.patch(`http://localhost:8000/api/v1/admin/tenants/${tenant.id}/status`, {
          status: newStatus
        }, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        ElMessage.success(`Tenant ${action} successfully!`)
        loadTenants()
      } catch (error) {
        console.error('Failed to update tenant status:', error)
        if (error.response?.status === 401) {
          localStorage.removeItem('admin_token')
          router.push('/login')
        } else {
          ElMessage.error('Failed to update tenant status')
        }
      }
    }
    
    const deleteTenant = async (tenant) => {
      try {
        await ElMessageBox.confirm(
          `Are you sure you want to delete tenant "${tenant.name}"? This action cannot be undone.`,
          'Confirm Delete',
          {
            confirmButtonText: 'Delete',
            cancelButtonText: 'Cancel',
            type: 'warning'
          }
        )
        
        const token = localStorage.getItem('admin_token')
        await axios.delete(`http://localhost:8000/api/v1/admin/tenants/${tenant.id}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        ElMessage.success('Tenant deleted successfully!')
        loadTenants()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('Failed to delete tenant:', error)
          if (error.response?.status === 401) {
            localStorage.removeItem('admin_token')
            router.push('/login')
          } else {
            ElMessage.error('Failed to delete tenant')
          }
        }
      }
    }
    
    onMounted(() => {
      loadTenants()
    })
    
    return {
      loading,
      creating,
      showCreateDialog,
      editingTenantId,
      tenants,
      currentPage,
      pageSize,
      total,
      filters,
      createForm,
      createRules,
      getStatusType,
      loadTenants,
      createTenant,
      editTenant,
      toggleTenantStatus,
      deleteTenant
    }
  }
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  color: #303133;
}

.filter-card {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  text-align: center;
}
</style>
