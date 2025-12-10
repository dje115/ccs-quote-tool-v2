<template>
  <div class="api-keys">
    <h1>Global API Keys</h1>
    
    <!-- Required Services (Companies House, Google Maps) -->
    <el-card>
      <template #header>
        <h3>Required Services API Keys</h3>
        <p>These keys are required for core functionality and used as fallbacks when tenant-specific keys are not configured.</p>
      </template>
      
      <el-form
        ref="apiKeysFormRef"
        :model="apiKeys"
        label-width="200px"
      >
        <el-form-item label="Companies House API Key">
          <div class="api-key-row">
            <el-input
              v-model="apiKeys.companies_house_api_key"
              type="password"
              placeholder="Enter Companies House API key"
              show-password
            >
              <template #append>
                <el-button @click="testAPI('companies-house')" :loading="testing.companies_house">
                  Test
                </el-button>
              </template>
            </el-input>
            <el-tag 
              :type="getStatusColor(apiStatus.companies_house)" 
              class="status-tag"
              size="large"
            >
              {{ getStatusText(apiStatus.companies_house) }}
            </el-tag>
          </div>
          <div class="help-text">
            Used for UK company data lookup. Get your key from 
            <a href="https://developer.company-information.service.gov.uk/" target="_blank">Companies House</a>
          </div>
        </el-form-item>
        
        <el-form-item label="Google Maps API Key">
          <div class="api-key-row">
            <el-input
              v-model="apiKeys.google_maps_api_key"
              type="password"
              placeholder="Enter Google Maps API key"
              show-password
            >
              <template #append>
                <el-button @click="testAPI('google-maps')" :loading="testing.google_maps">
                  Test
                </el-button>
              </template>
            </el-input>
            <el-tag 
              :type="getStatusColor(apiStatus.google_maps)" 
              class="status-tag"
              size="large"
            >
              {{ getStatusText(apiStatus.google_maps) }}
            </el-tag>
          </div>
          <div class="help-text">
            Used for location services and address verification. Get your key from 
            <a href="https://console.cloud.google.com/apis/credentials" target="_blank">Google Cloud Console</a>
          </div>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="saveAPIKeys" :loading="saving">
            Save API Keys
          </el-button>
          <el-button @click="loadAPIKeys">
            Reset
          </el-button>
        </el-form-item>
      </el-form>
      
      <!-- Test Results -->
      <div v-if="testResults.length > 0" class="test-results">
        <h4>Test Results</h4>
        <div v-for="result in testResults" :key="result.api" class="test-result">
          <el-alert
            :title="`${result.api.toUpperCase()} API`"
            :type="result.success ? 'success' : 'error'"
            :description="result.message"
            show-icon
          />
        </div>
      </div>
    </el-card>
    
    <!-- AI Provider Keys -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <h3>AI Provider API Keys</h3>
        <p>Configure API keys for multiple AI providers. These keys are used as system defaults and fallbacks for all tenants.</p>
      </template>
      
      <div v-if="loadingProviders" style="text-align: center; padding: 20px;">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span style="margin-left: 10px;">Loading providers...</span>
      </div>
      
      <div v-else>
        <el-table :data="providerStatus" style="width: 100%">
          <el-table-column prop="provider.name" label="Provider" width="200">
            <template #default="{ row }">
              <div>
                <strong>{{ row.provider.name }}</strong>
                <el-tag size="small" :type="row.provider.provider_type === 'on_premise' ? 'info' : 'success'" style="margin-left: 8px;">
                  {{ row.provider.provider_type === 'on_premise' ? 'On-Premise' : 'Cloud' }}
                </el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="API Key" min-width="300">
            <template #default="{ row }">
              <el-input
                v-model="providerKeys[row.provider.id]"
                type="password"
                :placeholder="`Enter ${row.provider.name} API key`"
                show-password
                size="small"
              >
                <template #append>
                  <el-button 
                    @click="testProviderKey(row.provider.id)" 
                    :loading="testingProviders[row.provider.id]"
                    size="small"
                  >
                    Test
                  </el-button>
                </template>
              </el-input>
            </template>
          </el-table-column>
          <el-table-column label="Status" width="150">
            <template #default="{ row }">
              <el-tag 
                :type="getProviderStatusColor(row)" 
                size="large"
              >
                {{ getProviderStatusText(row) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="Last Tested" width="180">
            <template #default="{ row }">
              <span v-if="row.last_tested">
                {{ new Date(row.last_tested).toLocaleString() }}
              </span>
              <span v-else style="color: #909399;">Never</span>
            </template>
          </el-table-column>
          <el-table-column label="Actions" width="200">
            <template #default="{ row }">
              <el-button 
                type="primary" 
                size="small" 
                @click="saveProviderKey(row.provider.id)"
                :loading="savingProviders[row.provider.id]"
              >
                Save
              </el-button>
              <el-button 
                type="info" 
                size="small" 
                @click="editProviderSettings(row.provider)"
              >
                Settings
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <div style="margin-top: 20px;">
          <el-button type="primary" @click="saveAllProviderKeys" :loading="savingAllProviders">
            Save All Provider Keys
          </el-button>
          <el-button @click="loadProviderKeys">
            Reset
          </el-button>
        </div>
      </div>
      
      <!-- Provider Test Results -->
      <div v-if="providerTestResults.length > 0" class="test-results" style="margin-top: 20px;">
        <h4>Test Results</h4>
        <div v-for="result in providerTestResults" :key="result.provider_id" class="test-result">
          <el-alert
            :title="`${result.provider_name} API`"
            :type="result.success ? 'success' : 'error'"
            :description="formatErrorMessage(result.message || result.error)"
            show-icon
            :closable="true"
            @close="providerTestResults = providerTestResults.filter(r => r.provider_id !== result.provider_id)"
          />
        </div>
      </div>
    </el-card>
    
    <!-- API Usage Stats -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <h3>API Usage Statistics</h3>
      </template>
      
      <el-row :gutter="20">
        <el-col :span="8">
          <div class="stat-item">
            <div class="stat-value">{{ usageStats.openai_calls }}</div>
            <div class="stat-label">OpenAI Calls This Month</div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="stat-item">
            <div class="stat-value">{{ usageStats.companies_house_calls }}</div>
            <div class="stat-label">Companies House Calls This Month</div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="stat-item">
            <div class="stat-value">{{ usageStats.google_maps_calls }}</div>
            <div class="stat-label">Google Maps Calls This Month</div>
          </div>
        </el-col>
      </el-row>
    </el-card>
    
    <!-- Provider Settings Dialog -->
    <el-dialog
      v-model="settingsDialogVisible"
      :title="`Edit Settings: ${editingProvider?.name || ''}`"
      width="600px"
    >
      <el-form :model="providerSettingsForm" label-width="150px">
        <el-form-item label="Base URL">
          <el-input
            v-model="providerSettingsForm.base_url"
            placeholder="e.g., https://api.openai.com/v1"
          />
          <div style="font-size: 12px; color: #909399; margin-top: 5px;">
            API endpoint URL. Leave empty for default.
          </div>
        </el-form-item>
        
        <el-form-item label="Supported Models">
          <el-input
            v-model="supportedModelsText"
            type="textarea"
            :rows="4"
            placeholder="Enter models separated by commas or newlines"
          />
          <div style="font-size: 12px; color: #909399; margin-top: 5px;">
            List of supported model names (one per line or comma-separated)
          </div>
        </el-form-item>
        
        <el-form-item label="Default Settings">
          <el-input
            v-model="defaultSettingsText"
            type="textarea"
            :rows="6"
            placeholder='{"temperature": 0.7, "max_tokens": 8000, "top_p": 1.0}'
          />
          <div style="font-size: 12px; color: #909399; margin-top: 5px;">
            JSON object with default settings (temperature, max_tokens, top_p, etc.)
          </div>
        </el-form-item>
        
        <el-form-item label="Active">
          <el-switch v-model="providerSettingsForm.is_active" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="settingsDialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="saveProviderSettings" :loading="savingSettings">
          Save Settings
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { Loading } from '@element-plus/icons-vue'

export default {
  name: 'APIKeys',
  components: {
    Loading
  },
  setup() {
    const router = useRouter()
    const saving = ref(false)
    const apiKeysFormRef = ref()
    const testResults = ref([])
    const loadingProviders = ref(false)
    const savingAllProviders = ref(false)
    
    const apiKeys = reactive({
      companies_house_api_key: '',
      google_maps_api_key: ''
    })
    
    const testing = reactive({
      companies_house: false,
      google_maps: false
    })
    
    const providerStatus = ref([])
    const providerKeys = reactive({})
    const testingProviders = reactive({})
    const savingProviders = reactive({})
    const providerTestResults = ref([])
    
    // Provider settings dialog
    const settingsDialogVisible = ref(false)
    const editingProvider = ref(null)
    const savingSettings = ref(false)
    const providerSettingsForm = reactive({
      base_url: '',
      supported_models: [],
      default_settings: {},
      is_active: true
    })
    const supportedModelsText = ref('')
    const defaultSettingsText = ref('')
    
    const usageStats = reactive({
      openai_calls: 0,
      companies_house_calls: 0,
      google_maps_calls: 0
    })
    
    const apiStatus = reactive({
      companies_house: 'not_configured',
      google_maps: 'not_configured'
    })
    
    const updateAPIStatus = () => {
      // Update status based on whether keys are configured and tested
      apiStatus.companies_house = apiKeys.companies_house_api_key ? 'not_tested' : 'not_configured'
      apiStatus.google_maps = apiKeys.google_maps_api_key ? 'not_tested' : 'not_configured'
      
      // Check test results to update to 'working' status
      testResults.value.forEach(result => {
        if (result.success) {
          apiStatus[result.api] = 'working'
        } else if (apiKeys[`${result.api}_api_key`]) {
          apiStatus[result.api] = 'not_tested'
        }
      })
    }
    
    const loadProviderKeys = async () => {
      loadingProviders.value = true
      try {
        const token = localStorage.getItem('admin_token')
        const response = await axios.get('http://localhost:8000/api/v1/provider-keys/status', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        
        providerStatus.value = response.data || []
        
        // Load existing keys into providerKeys reactive object
        providerStatus.value.forEach(status => {
          // Try to get key from system-level key (we'll need to fetch it separately or show masked)
          // For now, we'll just show empty and let user enter new key
          providerKeys[status.provider.id] = ''
        })
      } catch (error) {
        console.error('Failed to load provider keys:', error)
        if (error.response?.status === 401) {
          localStorage.removeItem('admin_token')
          router.push('/login')
        } else {
          ElMessage.error('Failed to load provider keys')
        }
      } finally {
        loadingProviders.value = false
      }
    }
    
    const saveProviderKey = async (providerId) => {
      savingProviders[providerId] = true
      try {
        const token = localStorage.getItem('admin_token')
        const response = await axios.put(
          `http://localhost:8000/api/v1/provider-keys/${providerId}?is_system=true`,
          {
            api_key: providerKeys[providerId] || '',
            test_on_save: true
          },
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        )
        
        ElMessage.success('Provider key saved and tested successfully!')
        await loadProviderKeys()
      } catch (error) {
        console.error('Failed to save provider key:', error)
        ElMessage.error('Failed to save provider key: ' + (error.response?.data?.detail || error.message))
      } finally {
        savingProviders[providerId] = false
      }
    }
    
    const saveAllProviderKeys = async () => {
      savingAllProviders.value = true
      try {
        const token = localStorage.getItem('admin_token')
        const promises = Object.keys(providerKeys).map(providerId => {
          if (providerKeys[providerId]) {
            return axios.put(
              `http://localhost:8000/api/v1/provider-keys/${providerId}?is_system=true`,
              {
                api_key: providerKeys[providerId],
                test_on_save: true
              },
              {
                headers: {
                  'Authorization': `Bearer ${token}`,
                  'Content-Type': 'application/json'
                }
              }
            )
          }
          return Promise.resolve()
        })
        
        await Promise.all(promises)
        ElMessage.success('All provider keys saved successfully!')
        await loadProviderKeys()
      } catch (error) {
        console.error('Failed to save provider keys:', error)
        ElMessage.error('Failed to save some provider keys')
      } finally {
        savingAllProviders.value = false
      }
    }
    
    const testProviderKey = async (providerId) => {
      testingProviders[providerId] = true
      try {
        const token = localStorage.getItem('admin_token')
        const response = await axios.post(
          `http://localhost:8000/api/v1/provider-keys/${providerId}/test?is_system=true`,
          providerKeys[providerId] ? { api_key: providerKeys[providerId] } : {},
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        )
        
        const provider = providerStatus.value.find(s => s.provider.id === providerId)?.provider
        const providerName = provider?.name || 'Provider'
        
        // Remove existing result
        providerTestResults.value = providerTestResults.value.filter(r => r.provider_id !== providerId)
        
        // Add new result
        providerTestResults.value.push({
          provider_id: providerId,
          provider_name: providerName,
          success: response.data.success,
          message: response.data.message,
          error: response.data.error
        })
        
        if (response.data.success) {
          ElMessage.success(`${providerName} API test successful!`)
        } else {
          ElMessage.error(`${providerName} API test failed: ${response.data.error || response.data.message}`)
        }
        
        // Reload to update status
        await loadProviderKeys()
      } catch (error) {
        const provider = providerStatus.value.find(s => s.provider.id === providerId)?.provider
        const providerName = provider?.name || 'Provider'
        
        providerTestResults.value = providerTestResults.value.filter(r => r.provider_id !== providerId)
        // Format error message properly
        let errorMessage = 'Test failed'
        if (error.response?.data) {
          const errorData = error.response.data
          if (errorData.detail) {
            if (Array.isArray(errorData.detail)) {
              errorMessage = errorData.detail.map(e => e.msg || JSON.stringify(e)).join(', ')
            } else if (typeof errorData.detail === 'string') {
              errorMessage = errorData.detail
            } else {
              errorMessage = JSON.stringify(errorData.detail)
            }
          } else if (errorData.message) {
            errorMessage = errorData.message
          }
        } else if (error.message) {
          errorMessage = error.message
        }
        
        providerTestResults.value.push({
          provider_id: providerId,
          provider_name: providerName,
          success: false,
          error: errorMessage
        })
        
        ElMessage.error(`${providerName} API test failed`)
      } finally {
        testingProviders[providerId] = false
      }
    }
    
    const getProviderStatusColor = (status) => {
      if (status.system_key_valid) return 'success'
      if (status.has_system_key) return 'warning'
      return 'danger'
    }
    
    const getProviderStatusText = (status) => {
      if (status.system_key_valid) return 'Valid'
      if (status.has_system_key) return 'Not Tested'
      return 'Not Configured'
    }
    
    const formatErrorMessage = (error) => {
      if (!error) return 'Unknown error'
      if (typeof error === 'string') return error
      if (typeof error === 'object') {
        // Handle Pydantic validation errors
        if (error.detail) {
          if (Array.isArray(error.detail)) {
            return error.detail.map(e => e.msg || JSON.stringify(e)).join(', ')
          }
          return error.detail
        }
        if (error.message) return error.message
        return JSON.stringify(error)
      }
      return String(error)
    }
    
    const editProviderSettings = (provider) => {
      editingProvider.value = provider
      providerSettingsForm.base_url = provider.base_url || ''
      providerSettingsForm.supported_models = provider.supported_models || []
      providerSettingsForm.default_settings = provider.default_settings || {}
      providerSettingsForm.is_active = provider.is_active !== false
      
      // Convert arrays/objects to text for editing
      supportedModelsText.value = Array.isArray(provider.supported_models) 
        ? provider.supported_models.join('\n')
        : ''
      defaultSettingsText.value = provider.default_settings
        ? JSON.stringify(provider.default_settings, null, 2)
        : '{}'
      
      settingsDialogVisible.value = true
    }
    
    const saveProviderSettings = async () => {
      savingSettings.value = true
      try {
        // Parse supported models from text
        const models = supportedModelsText.value
          .split(/[,\n]/)
          .map(m => m.trim())
          .filter(m => m.length > 0)
        
        // Parse default settings from JSON
        let defaultSettings = {}
        try {
          defaultSettings = JSON.parse(defaultSettingsText.value)
        } catch (e) {
          ElMessage.error('Invalid JSON in Default Settings')
          savingSettings.value = false
          return
        }
        
        const token = localStorage.getItem('admin_token')
        const response = await axios.put(
          `http://localhost:8000/api/v1/provider-keys/providers/${editingProvider.value.id}/settings`,
          {
            base_url: providerSettingsForm.base_url || null,
            supported_models: models,
            default_settings: defaultSettings,
            is_active: providerSettingsForm.is_active
          },
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        )
        
        ElMessage.success('Provider settings saved successfully!')
        settingsDialogVisible.value = false
        
        // Reload providers to show updated settings
        await loadProviderKeys()
      } catch (error) {
        console.error('Failed to save provider settings:', error)
        ElMessage.error('Failed to save provider settings: ' + (error.response?.data?.detail || error.message))
      } finally {
        savingSettings.value = false
      }
    }
    
    const getStatusColor = (status) => {
      switch (status) {
        case 'working': return 'success'
        case 'not_tested': return 'warning'
        case 'not_configured': return 'danger'
        default: return 'info'
      }
    }
    
    const getStatusText = (status) => {
      switch (status) {
        case 'working': return 'Working'
        case 'not_tested': return 'Not Tested'
        case 'not_configured': return 'Not Configured'
        default: return 'Unknown'
      }
    }
    
    const loadAPIKeys = async () => {
      try {
        const token = localStorage.getItem('admin_token')
        const response = await axios.get('http://localhost:8000/api/v1/admin/api-keys', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        Object.assign(apiKeys, response.data)
        updateAPIStatus()
      } catch (error) {
        console.error('Failed to load API keys:', error)
        if (error.response?.status === 401) {
          localStorage.removeItem('admin_token')
          router.push('/login')
        } else {
          ElMessage.error('Failed to load API keys')
        }
      }
    }
    
    const saveAPIKeys = async () => {
      saving.value = true
      try {
        const token = localStorage.getItem('admin_token')
        // Convert reactive object to plain object for axios - ONLY send the API key fields
        const payload = {
          openai_api_key: apiKeys.openai_api_key || '',
          companies_house_api_key: apiKeys.companies_house_api_key || '',
          google_maps_api_key: apiKeys.google_maps_api_key || ''
        }
        console.log('Sending API keys payload:', JSON.stringify(payload))
        await axios.post('http://localhost:8000/api/v1/admin/api-keys', payload, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })
        ElMessage.success('API keys saved successfully!')
        // Reset test results after saving new keys
        testResults.value = []
        updateAPIStatus()
      } catch (error) {
        console.error('Failed to save API keys:', error)
        if (error.response?.status === 401) {
          localStorage.removeItem('admin_token')
          router.push('/login')
        } else {
          ElMessage.error('Failed to save API keys')
        }
      } finally {
        saving.value = false
      }
    }
    
    const testAPI = async (apiType) => {
      // Normalize apiType for internal use (convert hyphens to underscores)
      const normalizedType = apiType.replace(/-/g, '_')
      
      testing[normalizedType] = true
      try {
        const token = localStorage.getItem('admin_token')
        const response = await axios.post(`http://localhost:8000/api/v1/admin/test-${apiType}`, {}, {
          headers: {
            'Authorization': `Bearer ${token}`
          },
          withCredentials: true
        })
        
        // Remove existing result for this API
        testResults.value = testResults.value.filter(r => r.api !== normalizedType)
        
        // Add new result
        testResults.value.push({
          api: normalizedType,
          success: response.data.success,
          message: response.data.message
        })
        
        if (response.data.success) {
          ElMessage.success(`${apiType.replace(/-/g, ' ').toUpperCase()} API test successful!`)
          // Update status to 'working'
          apiStatus[normalizedType] = 'working'
        } else {
          ElMessage.error(`${apiType.replace(/-/g, ' ').toUpperCase()} API test failed`)
        }
      } catch (error) {
        // Remove existing result for this API
        testResults.value = testResults.value.filter(r => r.api !== normalizedType)
        
        // Add error result
        testResults.value.push({
          api: normalizedType,
          success: false,
          message: error.response?.data?.detail || error.response?.data?.message || 'Test failed'
        })
        
        ElMessage.error(`${apiType.replace(/-/g, ' ').toUpperCase()} API test failed`)
      } finally {
        testing[normalizedType] = false
        updateAPIStatus()
      }
    }
    
    const loadUsageStats = async () => {
      try {
        const token = localStorage.getItem('admin_token')
        const response = await axios.get('http://localhost:8000/api/v1/admin/api-usage', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        Object.assign(usageStats, response.data)
      } catch (error) {
        console.error('Failed to load usage stats:', error)
        if (error.response?.status === 401) {
          localStorage.removeItem('admin_token')
          router.push('/login')
        } else {
          ElMessage.error('Failed to load usage statistics')
        }
      }
    }
    
    onMounted(() => {
      loadAPIKeys()
      loadProviderKeys()
      loadUsageStats()
    })
    
    return {
      saving,
      apiKeysFormRef,
      testResults,
      apiKeys,
      testing,
      usageStats,
      apiStatus,
      getStatusColor,
      getStatusText,
      loadAPIKeys,
      saveAPIKeys,
      testAPI,
      loadingProviders,
      providerStatus,
      providerKeys,
      testingProviders,
      savingProviders,
      savingAllProviders,
      providerTestResults,
      loadProviderKeys,
      saveProviderKey,
      saveAllProviderKeys,
      testProviderKey,
      getProviderStatusColor,
      getProviderStatusText,
      formatErrorMessage,
      settingsDialogVisible,
      editingProvider,
      savingSettings,
      providerSettingsForm,
      supportedModelsText,
      defaultSettingsText,
      editProviderSettings,
      saveProviderSettings
    }
  }
}
</script>

<style scoped>
.api-key-row {
  display: flex;
  align-items: center;
  gap: 15px;
}

.api-key-row .el-input {
  flex: 1;
}

.status-tag {
  min-width: 120px;
  text-align: center;
}

.help-text {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.help-text a {
  color: #409eff;
  text-decoration: none;
}

.help-text a:hover {
  text-decoration: underline;
}

.test-results {
  margin-top: 20px;
}

.test-result {
  margin-bottom: 10px;
}

.stat-item {
  text-align: center;
  padding: 20px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 10px;
}

.stat-label {
  color: #909399;
  font-size: 14px;
}
</style>
