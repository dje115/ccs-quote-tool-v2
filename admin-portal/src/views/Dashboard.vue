<template>
  <div class="dashboard">
    <h1>Admin Dashboard</h1>
    
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon active">
              <el-icon><OfficeBuilding /></el-icon>
            </div>
            <div class="stat-info">
              <h3>{{ stats.activeTenants }}</h3>
              <p>Active Tenants</p>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon trial">
              <el-icon><Clock /></el-icon>
            </div>
            <div class="stat-info">
              <h3>{{ stats.trialTenants }}</h3>
              <p>Trial Tenants</p>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon suspended">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <h3>{{ stats.suspendedTenants }}</h3>
              <p>Suspended Tenants</p>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon total">
              <el-icon><User /></el-icon>
            </div>
            <div class="stat-info">
              <h3>{{ stats.totalUsers }}</h3>
              <p>Total Users</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>Recent Tenants</h3>
              <el-button type="primary" @click="$router.push('/tenants')">
                View All
              </el-button>
            </div>
          </template>
          
          <el-table :data="recentTenants" style="width: 100%">
            <el-table-column prop="name" label="Name" />
            <el-table-column prop="slug" label="Slug" />
            <el-table-column prop="status" label="Status">
              <template #default="scope">
                <el-tag :type="getStatusType(scope.row.status)">
                  {{ scope.row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="Created" />
            <el-table-column label="Actions">
              <template #default="scope">
                <el-button size="small" @click="viewTenant(scope.row)">
                  View
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card>
          <template #header>
            <h3>System Status</h3>
          </template>
          
          <div class="status-item">
            <span>Database</span>
            <el-tag type="success">Connected</el-tag>
          </div>
          
          <div class="status-item">
            <span>Redis</span>
            <el-tag type="success">Connected</el-tag>
          </div>
          
          <div class="status-item">
            <span>Frontend</span>
            <el-tag type="success">Running</el-tag>
          </div>
          
          <div class="status-item">
            <span>Backend</span>
            <el-tag type="success">Running</el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

export default {
  name: 'Dashboard',
  setup() {
    const router = useRouter()
    
    const stats = reactive({
      activeTenants: 0,
      trialTenants: 0,
      suspendedTenants: 0,
      totalUsers: 0
    })
    
    const recentTenants = ref([])
    
    const getStatusType = (status) => {
      switch (status) {
        case 'active': return 'success'
        case 'trial': return 'warning'
        case 'suspended': return 'danger'
        default: return 'info'
      }
    }
    
    const viewTenant = (tenant) => {
      router.push(`/tenants/${tenant.id}`)
    }
    
    const loadDashboardData = async () => {
      try {
        const token = localStorage.getItem('admin_token')
        
        const response = await axios.get('http://localhost:8000/api/v1/admin/dashboard', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        
        // Convert snake_case to camelCase for frontend
        stats.activeTenants = response.data.stats.active_tenants
        stats.trialTenants = response.data.stats.trial_tenants
        stats.suspendedTenants = response.data.stats.suspended_tenants
        stats.totalUsers = response.data.stats.total_users
        recentTenants.value = response.data.recent_tenants
      } catch (error) {
        console.error('Failed to load dashboard data:', error)
        if (error.response?.status === 401) {
          // Token expired, redirect to login
          localStorage.removeItem('admin_token')
          router.push('/login')
        } else {
          ElMessage.error('Failed to load dashboard data')
        }
      }
    }
    
    onMounted(() => {
      loadDashboardData()
    })
    
    return {
      stats,
      recentTenants,
      getStatusType,
      viewTenant
    }
  }
}
</script>

<style scoped>
.dashboard h1 {
  margin-bottom: 20px;
  color: #303133;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  height: 120px;
}

.stat-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20px;
  font-size: 24px;
  color: white;
}

.stat-icon.active {
  background-color: #67c23a;
}

.stat-icon.trial {
  background-color: #e6a23c;
}

.stat-icon.suspended {
  background-color: #f56c6c;
}

.stat-icon.total {
  background-color: #409eff;
}

.stat-info h3 {
  margin: 0;
  font-size: 32px;
  font-weight: bold;
  color: #303133;
}

.stat-info p {
  margin: 5px 0 0 0;
  color: #909399;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #ebeef5;
}

.status-item:last-child {
  border-bottom: none;
}
</style>
