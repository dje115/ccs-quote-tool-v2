<template>
  <div class="settings">
    <h1>System Settings</h1>
    
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <h3>System Configuration</h3>
          </template>
          
          <el-form :model="settings" label-width="150px">
            <el-form-item label="System Name">
              <el-input v-model="settings.system_name" />
            </el-form-item>
            
            <el-form-item label="Default Tenant">
              <el-input v-model="settings.default_tenant" />
            </el-form-item>
            
            <el-form-item label="Max API Calls/Month">
              <el-input-number v-model="settings.max_api_calls" :min="1000" :max="1000000" />
            </el-form-item>
            
            <el-form-item label="Trial Period (Days)">
              <el-input-number v-model="settings.trial_period_days" :min="7" :max="90" />
            </el-form-item>
            
            <el-form-item label="Auto-suspend Inactive">
              <el-switch v-model="settings.auto_suspend_inactive" />
            </el-form-item>
            
            <el-form-item label="Inactive Threshold (Days)">
              <el-input-number v-model="settings.inactive_threshold_days" :min="30" :max="365" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <h3>Security Settings</h3>
          </template>
          
          <el-form :model="settings" label-width="150px">
            <el-form-item label="Session Timeout (Minutes)">
              <el-input-number v-model="settings.session_timeout" :min="15" :max="480" />
            </el-form-item>
            
            <el-form-item label="Password Min Length">
              <el-input-number v-model="settings.password_min_length" :min="6" :max="32" />
            </el-form-item>
            
            <el-form-item label="Require Strong Password">
              <el-switch v-model="settings.require_strong_password" />
            </el-form-item>
            
            <el-form-item label="Enable 2FA">
              <el-switch v-model="settings.enable_2fa" />
            </el-form-item>
            
            <el-form-item label="Max Login Attempts">
              <el-input-number v-model="settings.max_login_attempts" :min="3" :max="10" />
            </el-form-item>
            
            <el-form-item label="Lockout Duration (Minutes)">
              <el-input-number v-model="settings.lockout_duration" :min="5" :max="60" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <h3>Email Settings</h3>
          </template>
          
          <el-form :model="settings" label-width="150px">
            <el-form-item label="SMTP Host">
              <el-input v-model="settings.smtp_host" />
            </el-form-item>
            
            <el-form-item label="SMTP Port">
              <el-input-number v-model="settings.smtp_port" :min="1" :max="65535" />
            </el-form-item>
            
            <el-form-item label="SMTP Username">
              <el-input v-model="settings.smtp_username" />
            </el-form-item>
            
            <el-form-item label="SMTP Password">
              <el-input v-model="settings.smtp_password" type="password" show-password />
            </el-form-item>
            
            <el-form-item label="From Email">
              <el-input v-model="settings.from_email" type="email" />
            </el-form-item>
            
            <el-form-item label="Enable TLS">
              <el-switch v-model="settings.smtp_tls" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <h3>Backup Settings</h3>
          </template>
          
          <el-form :model="settings" label-width="150px">
            <el-form-item label="Auto Backup">
              <el-switch v-model="settings.auto_backup" />
            </el-form-item>
            
            <el-form-item label="Backup Frequency">
              <el-select v-model="settings.backup_frequency">
                <el-option label="Daily" value="daily" />
                <el-option label="Weekly" value="weekly" />
                <el-option label="Monthly" value="monthly" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="Backup Retention (Days)">
              <el-input-number v-model="settings.backup_retention_days" :min="7" :max="365" />
            </el-form-item>
            
            <el-form-item label="Backup Location">
              <el-input v-model="settings.backup_location" />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="createBackup">
                Create Backup Now
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
    
    <div class="save-section">
      <el-button type="primary" size="large" @click="saveSettings" :loading="saving">
        Save All Settings
      </el-button>
      <el-button size="large" @click="resetSettings">
        Reset to Defaults
      </el-button>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

export default {
  name: 'Settings',
  setup() {
    const saving = ref(false)
    
    const settings = reactive({
      // System Configuration
      system_name: 'CCS Quote Tool',
      default_tenant: 'ccs',
      max_api_calls: 100000,
      trial_period_days: 30,
      auto_suspend_inactive: true,
      inactive_threshold_days: 90,
      
      // Security Settings
      session_timeout: 60,
      password_min_length: 8,
      require_strong_password: true,
      enable_2fa: false,
      max_login_attempts: 5,
      lockout_duration: 15,
      
      // Email Settings
      smtp_host: '',
      smtp_port: 587,
      smtp_username: '',
      smtp_password: '',
      from_email: '',
      smtp_tls: true,
      
      // Backup Settings
      auto_backup: true,
      backup_frequency: 'daily',
      backup_retention_days: 30,
      backup_location: '/backups'
    })
    
    const loadSettings = async () => {
      try {
        const token = localStorage.getItem('admin_token')
        const response = await axios.get('http://localhost:8000/api/v1/admin/settings', {
          headers: {
            'Authorization': `Bearer ${token}`
          },
          withCredentials: true
        })
        Object.assign(settings, response.data)
      } catch (error) {
        console.error('Failed to load settings:', error)
        // Keep default values
      }
    }
    
    const saveSettings = async () => {
      saving.value = true
      try {
        const token = localStorage.getItem('admin_token')
        await axios.post('http://localhost:8000/api/v1/admin/settings', settings, {
          headers: {
            'Authorization': `Bearer ${token}`
          },
          withCredentials: true
        })
        ElMessage.success('Settings saved successfully!')
      } catch (error) {
        ElMessage.error('Failed to save settings')
      } finally {
        saving.value = false
      }
    }
    
    const resetSettings = () => {
      ElMessage.info('Reset functionality coming soon')
    }
    
    const createBackup = async () => {
      try {
        const token = localStorage.getItem('admin_token')
        await axios.post('http://localhost:8000/api/v1/admin/backup', {}, {
          headers: {
            'Authorization': `Bearer ${token}`
          },
          withCredentials: true
        })
        ElMessage.success('Backup created successfully!')
      } catch (error) {
        ElMessage.error('Failed to create backup')
      }
    }
    
    onMounted(() => {
      loadSettings()
    })
    
    return {
      saving,
      settings,
      saveSettings,
      resetSettings,
      createBackup
    }
  }
}
</script>

<style scoped>
.save-section {
  margin-top: 30px;
  text-align: center;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.save-section .el-button {
  margin: 0 10px;
}
</style>







