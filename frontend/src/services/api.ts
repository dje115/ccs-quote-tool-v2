import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken
          });
          
          const { access_token, refresh_token: newRefreshToken } = response.data;
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', newRefreshToken);
          
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return apiClient(originalRequest);
        } catch (refreshError) {
          localStorage.clear();
          window.location.href = '/login';
        }
      }
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;

// Auth API
export const authAPI = {
  login: (email: string, password: string) =>
    apiClient.post('/auth/login', new URLSearchParams({ username: email, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }),
  getCurrentUser: () => apiClient.get('/auth/me'),
  refresh: (refreshToken: string) => apiClient.post('/auth/refresh', { refresh_token: refreshToken }),
};

// Tenant API
export const tenantAPI = {
  list: () => apiClient.get('/tenants/'),
  create: (data: any) => apiClient.post('/tenants/', data),
  get: (id: string) => apiClient.get(`/tenants/${id}`),
  update: (id: string, data: any) => apiClient.put(`/tenants/${id}`, data),
  delete: (id: string) => apiClient.delete(`/tenants/${id}`),
  signup: (data: any) => apiClient.post('/tenants/signup', data),
};

// Dashboard API
export const dashboardAPI = {
  get: (endpoint: string) => apiClient.get(`/dashboard${endpoint}`),
  post: (endpoint: string, data?: any, config?: any) => apiClient.post(`/dashboard${endpoint}`, data, config),
};

// Customer API
export const customerAPI = {
  list: (params?: any) => apiClient.get('/customers/', { params }),
  create: (data: any) => apiClient.post('/customers/', data),
  get: (id: string) => apiClient.get(`/customers/${id}`),
  update: (id: string, data: any) => apiClient.put(`/customers/${id}`, data),
  delete: (id: string) => apiClient.delete(`/customers/${id}`),
  runAiAnalysis: (id: string) => apiClient.post(`/customers/${id}/ai-analysis`),
  confirmRegistration: (id: string, confirmed: boolean) => apiClient.post(`/customers/${id}/confirm-registration?confirmed=${confirmed}`),
};

// Lead API
export const leadAPI = {
  list: (params?: any) => apiClient.get('/leads/', { params }),
  get: (id: string) => apiClient.get(`/leads/${id}`),
  update: (id: string, data: any) => apiClient.put(`/leads/${id}`, data),
  delete: (id: string) => apiClient.delete(`/leads/${id}`),
};

// Campaign API
export const campaignAPI = {
  list: () => apiClient.get('/campaigns/'),
  create: (data: any) => apiClient.post('/campaigns/', data),
  get: (id: string) => apiClient.get(`/campaigns/${id}`),
  stop: (id: string) => apiClient.post(`/campaigns/${id}/stop`),
};

// Contact API
export const contactAPI = {
  list: (customerId: string) => apiClient.get(`/contacts/customer/${customerId}`),
  create: (data: any) => apiClient.post('/contacts/', data),
  update: (id: string, data: any) => apiClient.put(`/contacts/${id}`, data),
  delete: (id: string) => apiClient.delete(`/contacts/${id}`),
};

// Quote API
export const quoteAPI = {
  list: (params?: any) => apiClient.get('/quotes/', { params }),
  create: (data: any) => apiClient.post('/quotes/', data),
  get: (id: string) => apiClient.get(`/quotes/${id}`),
  update: (id: string, data: any) => apiClient.put(`/quotes/${id}`, data),
  delete: (id: string) => apiClient.delete(`/quotes/${id}`),
};

// User API
export const userAPI = {
  list: () => apiClient.get('/users/'),
  create: (data: any) => apiClient.post('/users/', data),
  getCurrentUser: () => apiClient.get('/users/me'),
  update: (id: string, data: any) => apiClient.put(`/users/${id}`, data),
  delete: (id: string) => apiClient.delete(`/users/${id}`),
};



