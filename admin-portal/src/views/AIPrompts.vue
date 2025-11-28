<template>
  <div class="ai-prompts">
    <h1>AI Prompt Management</h1>
    
    <el-card>
      <template #header>
        <h3>System-wide AI Prompts</h3>
        <p>Manage AI prompts that serve as defaults for all tenants. These prompts can be overridden at the tenant level.</p>
      </template>
      
      <el-alert
        type="warning"
        :closable="false"
        style="margin-bottom: 20px;"
      >
        <template #title>
          <strong>Advanced Users Only</strong>
        </template>
        <p>This feature is for advanced users only. Be very careful when editing prompts. <strong>Do not modify JSON structure details in prompts</strong> unless you understand the impact. All changes are versioned and can be rolled back.</p>
      </el-alert>
      
      <el-form :inline="true" style="margin-bottom: 20px;">
        <el-form-item label="Filter by Category">
          <el-select v-model="selectedCategory" placeholder="All Categories" @change="loadPrompts">
            <el-option label="All Categories" value="all" />
            <el-option label="Customer Analysis" value="customer_analysis" />
            <el-option label="Quote Analysis" value="quote_analysis" />
            <el-option label="Product Search" value="product_search" />
            <el-option label="Building Analysis" value="building_analysis" />
            <el-option label="Activity Enhancement" value="activity_enhancement" />
            <el-option label="Action Suggestions" value="action_suggestions" />
            <el-option label="Lead Generation" value="lead_generation" />
            <el-option label="Company Profile Analysis" value="company_profile_analysis" />
            <el-option label="Manual Quote Review" value="manual_quote_review" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            Create System Prompt
          </el-button>
        </el-form-item>
      </el-form>
      
      <el-table :data="prompts" v-loading="loading" style="width: 100%">
        <el-table-column prop="name" label="Name" width="200" />
        <el-table-column prop="category" label="Category" width="150">
          <template #default="{ row }">
            <el-tag size="small">{{ row.category }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="quote_type" label="Quote Type" width="150">
          <template #default="{ row }">
            <el-tag v-if="row.quote_type" size="small" type="primary">{{ row.quote_type }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="version" label="Version" width="100">
          <template #default="{ row }">
            <el-tag size="small">v{{ row.version }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Provider" width="150">
          <template #default="{ row }">
            <el-tag v-if="row.use_system_default" size="small" type="info">System Default</el-tag>
            <el-tag v-else-if="row.provider_name" size="small" type="primary">{{ row.provider_name }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="model" label="Model" width="150" />
        <el-table-column label="Status" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? 'Active' : 'Inactive' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Actions" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="editPrompt(row)">Edit</el-button>
            <el-button size="small" @click="viewVersions(row)">Versions</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- Edit Dialog -->
    <el-dialog
      v-model="showEditDialog"
      title="Edit System Prompt"
      width="80%"
      :close-on-click-modal="false"
    >
      <el-tabs v-model="editTab">
        <el-tab-pane label="Basic Info" name="basic">
          <el-form :model="editForm" label-width="150px">
            <el-form-item label="Name">
              <el-input v-model="editForm.name" />
            </el-form-item>
            <el-form-item label="Category">
              <el-input v-model="editForm.category" disabled />
            </el-form-item>
            <el-form-item label="Description">
              <el-input v-model="editForm.description" type="textarea" :rows="2" />
            </el-form-item>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="System Prompt" name="system">
          <el-form :model="editForm" label-width="150px">
            <el-form-item label="System Prompt">
              <el-input v-model="editForm.system_prompt" type="textarea" :rows="10" />
            </el-form-item>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="User Prompt" name="user">
          <el-form :model="editForm" label-width="150px">
            <el-form-item label="User Prompt Template">
              <el-input v-model="editForm.user_prompt_template" type="textarea" :rows="15" />
            </el-form-item>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="Provider Settings" name="provider">
          <el-form :model="editForm" label-width="150px">
            <el-form-item>
              <el-switch
                v-model="editForm.use_system_default"
                active-text="Use System Default Provider"
              />
            </el-form-item>
            <template v-if="!editForm.use_system_default">
              <el-form-item label="AI Provider">
                <el-select v-model="editForm.provider_id" placeholder="Select Provider" @change="loadProviderModels">
                  <el-option
                    v-for="provider in availableProviders"
                    :key="provider.id"
                    :label="provider.name"
                    :value="provider.id"
                    :disabled="!provider.has_valid_key"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="Provider Model">
                <el-select v-model="editForm.provider_model" placeholder="Select Model" :disabled="!editForm.provider_id">
                  <el-option
                    v-for="model in availableModels"
                    :key="model"
                    :label="model"
                    :value="model"
                  />
                </el-select>
              </el-form-item>
            </template>
            <el-form-item label="Temperature">
              <el-input-number v-model="editForm.temperature" :min="0" :max="2" :step="0.1" />
            </el-form-item>
            <el-form-item label="Max Tokens">
              <el-input-number v-model="editForm.max_tokens" :min="1" :max="100000" />
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
      <template #footer>
        <el-button @click="showEditDialog = false">Cancel</el-button>
        <el-button type="primary" @click="savePrompt" :loading="saving">Save (Create New Version)</el-button>
      </template>
    </el-dialog>
    
    <!-- Versions Dialog -->
    <el-dialog
      v-model="showVersionsDialog"
      title="Version History"
      width="60%"
    >
      <el-table :data="versions" style="width: 100%">
        <el-table-column prop="version" label="Version" width="100" />
        <el-table-column prop="note" label="Note" />
        <el-table-column prop="created_at" label="Created" width="180">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column label="Actions" width="120">
          <template #default="{ row }">
            <el-button v-if="row.version !== currentVersion" size="small" @click="rollbackVersion(row.version)">
              Rollback
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { Plus, Loading } from '@element-plus/icons-vue'

export default {
  name: 'AIPrompts',
  components: {
    Plus,
    Loading
  },
  setup() {
    const loading = ref(false)
    const saving = ref(false)
    const prompts = ref([])
    const selectedCategory = ref('all')
    const showEditDialog = ref(false)
    const showVersionsDialog = ref(false)
    const showCreateDialog = ref(false)
    const editTab = ref('basic')
    const currentVersion = ref(1)
    const versions = ref([])
    const availableProviders = ref([])
    const availableModels = ref([])
    
    const editForm = reactive({
      id: '',
      name: '',
      category: '',
      description: '',
      system_prompt: '',
      user_prompt_template: '',
      provider_id: '',
      provider_model: '',
      use_system_default: true,
      temperature: 0.7,
      max_tokens: 8000,
      note: ''
    })
    
    const loadPrompts = async () => {
      loading.value = true
      try {
        const token = localStorage.getItem('admin_token')
        const params = { is_system: true, is_active: true }
        if (selectedCategory.value !== 'all') {
          params.category = selectedCategory.value
        }
        const response = await axios.get('http://localhost:8000/api/v1/prompts/', {
          headers: { 'Authorization': `Bearer ${token}` },
          params
        })
        prompts.value = response.data || []
      } catch (error) {
        console.error('Failed to load prompts:', error)
        ElMessage.error('Failed to load prompts')
      } finally {
        loading.value = false
      }
    }
    
    const loadAvailableProviders = async () => {
      try {
        const token = localStorage.getItem('admin_token')
        const response = await axios.get('http://localhost:8000/api/v1/prompts/available-providers', {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        availableProviders.value = response.data || []
      } catch (error) {
        console.error('Failed to load providers:', error)
      }
    }
    
    const loadProviderModels = async (providerId) => {
      if (!providerId) {
        availableModels.value = []
        return
      }
      try {
        const token = localStorage.getItem('admin_token')
        const response = await axios.get(`http://localhost:8000/api/v1/prompts/available-models/${providerId}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        availableModels.value = response.data || []
      } catch (error) {
        console.error('Failed to load models:', error)
        availableModels.value = []
      }
    }
    
    const editPrompt = async (prompt) => {
      Object.assign(editForm, {
        id: prompt.id,
        name: prompt.name,
        category: prompt.category,
        description: prompt.description || '',
        system_prompt: prompt.system_prompt,
        user_prompt_template: prompt.user_prompt_template,
        provider_id: prompt.provider_id || '',
        provider_model: prompt.provider_model || '',
        use_system_default: prompt.use_system_default !== undefined ? prompt.use_system_default : true,
        temperature: prompt.temperature,
        max_tokens: prompt.max_tokens,
        note: ''
      })
      currentVersion.value = prompt.version
      if (prompt.provider_id) {
        await loadProviderModels(prompt.provider_id)
      }
      showEditDialog.value = true
    }
    
    const viewVersions = async (prompt) => {
      try {
        const token = localStorage.getItem('admin_token')
        const response = await axios.get(`http://localhost:8000/api/v1/prompts/${prompt.id}/versions`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        versions.value = response.data || []
        currentVersion.value = prompt.version
        showVersionsDialog.value = true
      } catch (error) {
        ElMessage.error('Failed to load versions')
      }
    }
    
    const savePrompt = async () => {
      saving.value = true
      try {
        const token = localStorage.getItem('admin_token')
        await axios.put(`http://localhost:8000/api/v1/prompts/${editForm.id}`, {
          name: editForm.name,
          description: editForm.description,
          system_prompt: editForm.system_prompt,
          user_prompt_template: editForm.user_prompt_template,
          provider_id: editForm.provider_id || null,
          provider_model: editForm.provider_model || null,
          use_system_default: editForm.use_system_default,
          temperature: editForm.temperature,
          max_tokens: editForm.max_tokens,
          note: editForm.note || 'Updated system prompt'
        }, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        ElMessage.success('Prompt updated successfully!')
        showEditDialog.value = false
        loadPrompts()
      } catch (error) {
        ElMessage.error('Failed to update prompt: ' + (error.response?.data?.detail || error.message))
      } finally {
        saving.value = false
      }
    }
    
    const rollbackVersion = async (version) => {
      if (!confirm(`Rollback to version ${version}?`)) return
      try {
        const token = localStorage.getItem('admin_token')
        await axios.post(`http://localhost:8000/api/v1/prompts/${editForm.id}/rollback/${version}`, {}, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        ElMessage.success('Rolled back successfully!')
        showVersionsDialog.value = false
        loadPrompts()
      } catch (error) {
        ElMessage.error('Failed to rollback')
      }
    }
    
    onMounted(() => {
      loadPrompts()
      loadAvailableProviders()
    })
    
    return {
      loading,
      saving,
      prompts,
      selectedCategory,
      showEditDialog,
      showVersionsDialog,
      showCreateDialog,
      editTab,
      editForm,
      versions,
      currentVersion,
      availableProviders,
      availableModels,
      loadPrompts,
      editPrompt,
      viewVersions,
      savePrompt,
      rollbackVersion,
      loadProviderModels
    }
  }
}
</script>

<style scoped>
.ai-prompts {
  padding: 20px;
}
</style>

