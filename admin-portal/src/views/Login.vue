<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <h2>CCS Admin Portal</h2>
          <p>System Administration</p>
        </div>
      </template>
      
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="rules"
        label-width="100px"
        @submit.prevent="handleLogin"
      >
        <el-form-item label="Email" prop="email">
          <el-input
            v-model="loginForm.email"
            type="email"
            placeholder="Enter admin email"
          />
        </el-form-item>
        
        <el-form-item label="Password" prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="Enter password"
            show-password
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            @click="handleLogin"
            style="width: 100%"
          >
            Login
          </el-button>
        </el-form-item>
      </el-form>
      
      <div v-if="error" class="error-message">
        <el-alert :title="error" type="error" show-icon />
      </div>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

export default {
  name: 'Login',
  setup() {
    const router = useRouter()
    const loginFormRef = ref()
    const loading = ref(false)
    const error = ref('')
    
    const loginForm = reactive({
      email: 'admin@ccs.com',
      password: 'admin123'
    })
    
    const rules = {
      email: [
        { required: true, message: 'Please enter email', trigger: 'blur' },
        { type: 'email', message: 'Please enter valid email', trigger: 'blur' }
      ],
      password: [
        { required: true, message: 'Please enter password', trigger: 'blur' }
      ]
    }
    
    const handleLogin = async () => {
      // Validate form first
      if (!loginFormRef.value) return
      
      await loginFormRef.value.validate(async (valid) => {
        if (!valid) {
          return false
        }
        
        try {
          loading.value = true
          error.value = ''
          
          console.log('Attempting login with:', loginForm.email)
          
          // Fetch CSRF token first (for cross-origin support)
          let csrfToken = null
          try {
            const csrfResponse = await axios.get('http://localhost:8000/api/v1/auth/csrf-token', {
              withCredentials: true  // Include cookies
            })
            csrfToken = csrfResponse.data.csrf_token
            // Also read from cookie if available (cookie takes precedence)
            const cookieToken = document.cookie.split('; ').find(row => row.startsWith('csrf_token='))
            if (cookieToken) {
              csrfToken = cookieToken.split('=')[1]
            }
          } catch (csrfErr) {
            console.warn('CSRF token fetch failed, continuing without it:', csrfErr)
          }
          
          // Use regular auth login endpoint - must send as URL encoded form data
          const params = new URLSearchParams()
          params.append('username', loginForm.email)
          params.append('password', loginForm.password)
          
          const headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
          }
          
          // Add CSRF token if available (required for POST requests)
          if (csrfToken) {
            headers['X-CSRF-Token'] = csrfToken
          }
          
          const response = await axios.post('http://localhost:8000/api/v1/auth/login', params, {
            headers: headers,
            withCredentials: true  // Include cookies for cross-origin
          })
          
          console.log('Login response:', response.data)
          
          // SECURITY: For cross-origin admin portal, we still use tokens in response body
          // (HttpOnly cookies don't work cross-origin)
          if (response.data.access_token) {
            localStorage.setItem('admin_token', response.data.access_token)
            if (response.data.refresh_token) {
              localStorage.setItem('admin_refresh_token', response.data.refresh_token)
            }
            
            // Verify user is admin
            const userResponse = await axios.get('http://localhost:8000/api/v1/auth/me', {
              headers: {
                'Authorization': `Bearer ${response.data.access_token}`
              },
              withCredentials: true
            })
            
            if (userResponse.data.role !== 'super_admin') {
              localStorage.removeItem('admin_token')
              localStorage.removeItem('admin_refresh_token')
              error.value = 'Admin access required (super_admin role needed)'
              ElMessage.error('Admin access required')
              return
            }
            
            ElMessage.success('Login successful!')
            router.push('/dashboard')
          }
        } catch (err) {
          console.error('Login error:', err)
          console.error('Error response:', err.response)
          error.value = err.response?.data?.detail || err.response?.data?.message || err.message || 'Login failed'
          ElMessage.error(error.value)
        } finally {
          loading.value = false
        }
      })
    }
    
    return {
      loginFormRef,
      loginForm,
      rules,
      loading,
      error,
      handleLogin
    }
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 400px;
}

.card-header {
  text-align: center;
}

.card-header h2 {
  margin: 0 0 10px 0;
  color: #303133;
}

.card-header p {
  margin: 0;
  color: #909399;
}

.error-message {
  margin-top: 20px;
}
</style>
