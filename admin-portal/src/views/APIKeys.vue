<template>
  <div class="api-keys">
    <h1>Global API Keys</h1>
    
    <el-card>
      <template #header>
        <h3>System-wide API Keys</h3>
        <p>These keys are used as fallbacks when tenant-specific keys are not configured.</p>
      </template>
      
      <el-form
        ref="apiKeysFormRef"
        :model="apiKeys"
        label-width="200px"
      >
        <el-form-item label="OpenAI API Key">
          <div class="api-key-row">
            <el-input
              v-model="apiKeys.openai_api_key"
              type="password"
              placeholder="Enter OpenAI API key"
              show-password
            >
              <template #append>
                <el-button @click="testAPI('openai')" :loading="testing.openai">
                  Test
                </el-button>
              </template>
            </el-input>
            <el-tag 
              :type="getStatusColor(apiStatus.openai)" 
              class="status-tag"
              size="large"
            >
              {{ getStatusText(apiStatus.openai) }}
            </el-tag>
          </div>
          <div class="help-text">
            Used for AI analysis and lead scoring. Get your key from 
            <a href="https://platform.openai.com/api-keys" target="_blank">OpenAI Platform</a>
          </div>
        </el-form-item>
        
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
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

export default {
  name: 'APIKeys',
  setup() {
    const saving = ref(false)
    const apiKeysFormRef = ref()
    const testResults = ref([])
    
    const apiKeys = reactive({
      openai_api_key: '',
      companies_house_api_key: '',
      google_maps_api_key: ''
    })
    
    const testing = reactive({
      openai: false,
      companies_house: false,
      google_maps: false
    })
    
    const usageStats = reactive({
      openai_calls: 0,
      companies_house_calls: 0,
      google_maps_calls: 0
    })
    
    const apiStatus = reactive({
      openai: 'not_configured', // not_configured, not_tested, working
      companies_house: 'not_configured',
      google_maps: 'not_configured'
    })
    
    const updateAPIStatus = () => {
      // Update status based on whether keys are configured and tested
      apiStatus.openai = apiKeys.openai_api_key ? 'not_tested' : 'not_configured'
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
          }
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
      testAPI
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
