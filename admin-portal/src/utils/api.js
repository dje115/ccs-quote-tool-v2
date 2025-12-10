/**
 * API utility for admin portal
 * Handles CSRF tokens and authentication headers
 */

import axios from 'axios'

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  withCredentials: true,  // Include cookies for cross-origin
  headers: {
    'Content-Type': 'application/json'
  }
})

// CSRF token cache
let csrfToken = null

/**
 * Get CSRF token from cookie or fetch from server
 */
async function getCsrfToken() {
  // Try to read from cookie first
  const cookieToken = document.cookie
    .split('; ')
    .find(row => row.startsWith('csrf_token='))
  
  if (cookieToken) {
    csrfToken = cookieToken.split('=')[1]
    return csrfToken
  }
  
  // Fetch from server if not in cookie
  try {
    const response = await axios.get('http://localhost:8000/api/v1/auth/csrf-token', {
      withCredentials: true
    })
    csrfToken = response.data.csrf_token
    return csrfToken
  } catch (error) {
    console.warn('Failed to fetch CSRF token:', error)
    return null
  }
}

// Request interceptor - add CSRF token and auth token
apiClient.interceptors.request.use(
  async (config) => {
    // Add authentication token from localStorage
    const token = localStorage.getItem('admin_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // Add CSRF token for state-changing operations
    if (config.method && ['post', 'put', 'delete', 'patch'].includes(config.method.toLowerCase())) {
      const token = await getCsrfToken()
      if (token) {
        config.headers['X-CSRF-Token'] = token
      }
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - handle errors
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  async (error) => {
    // Handle 401 - token expired
    if (error.response?.status === 401) {
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_refresh_token')
      // Redirect to login if not already there
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    
    return Promise.reject(error)
  }
)

export default apiClient

