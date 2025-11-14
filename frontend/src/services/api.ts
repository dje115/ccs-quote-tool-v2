import axios from 'axios';

// Vite uses import.meta.env instead of process.env
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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

// Supplier API
export const supplierAPI = {
  // Categories
  listCategories: () => apiClient.get('/suppliers/categories'),
  createCategory: (data: any) => apiClient.post('/suppliers/categories', data),
  getCategory: (id: string) => apiClient.get(`/suppliers/categories/${id}`),
  updateCategory: (id: string, data: any) => apiClient.put(`/suppliers/categories/${id}`, data),
  deleteCategory: (id: string) => apiClient.delete(`/suppliers/categories/${id}`),
  
  // Suppliers
  list: (params?: any) => apiClient.get('/suppliers/', { params }),
  create: (data: any) => apiClient.post('/suppliers/', data),
  get: (id: string) => apiClient.get(`/suppliers/${id}`),
  update: (id: string, data: any) => apiClient.put(`/suppliers/${id}`, data),
  delete: (id: string) => apiClient.delete(`/suppliers/${id}`),
  
  // Pricing
  getPricingSummary: () => apiClient.get('/suppliers/pricing/summary'),
  refreshAllPricing: () => apiClient.post('/suppliers/pricing/refresh-all'),
  refreshSupplierPricing: (id: string) => apiClient.post(`/suppliers/${id}/pricing/refresh`),
  getSupplierPricingSummary: (id: string) => apiClient.get(`/suppliers/${id}/pricing/summary`),
  testPricing: (supplierName: string, productName: string, forceRefresh?: boolean) => 
    apiClient.get(`/suppliers/pricing/test/${supplierName}/${productName}`, { params: { force_refresh: forceRefresh } }),
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
  excludeAddress: (id: string, locationId: string) => apiClient.post(`/customers/${id}/addresses/exclude`, { location_id: locationId }),
  includeAddress: (id: string, locationId: string) => apiClient.post(`/customers/${id}/addresses/include`, { location_id: locationId }),
  updateKnownFacts: (id: string, knownFacts: string) => apiClient.put(`/customers/${id}/known-facts`, { known_facts: knownFacts }),
  changeStatus: (id: string, status: string) => apiClient.patch(`/customers/${id}/status`, { status }),
  getCompetitors: (params?: any) => apiClient.get('/customers/competitors', { params }),
};

// Lead API
export const leadAPI = {
  list: (params?: any) => apiClient.get('/leads/', { params }),
  get: (id: string) => apiClient.get(`/leads/${id}`),
  update: (id: string, data: any) => apiClient.put(`/leads/${id}`, data),
  delete: (id: string) => apiClient.delete(`/leads/${id}`),
  createFromCompetitors: (data: { company_names: string[], source_customer_id?: string, source_customer_name?: string }) => 
    apiClient.post('/leads/from-competitors', data),
};

// Campaign API
export const campaignAPI = {
  list: (params?: any) => apiClient.get('/campaigns/', { params }),
  create: (data: any) => apiClient.post('/campaigns/', data),
  get: (id: string) => apiClient.get(`/campaigns/${id}`),
  update: (id: string, data: any) => apiClient.patch(`/campaigns/${id}`, data),
  delete: (id: string) => apiClient.delete(`/campaigns/${id}`),
  start: (id: string) => apiClient.post(`/campaigns/${id}/start`),
  restart: (id: string) => apiClient.post(`/campaigns/${id}/restart`),
  stop: (id: string) => apiClient.post(`/campaigns/${id}/stop`),
  resetToDraft: (id: string) => apiClient.post(`/campaigns/${id}/reset-to-draft`),
  getPromptTypes: () => apiClient.get('/campaigns/prompt-types'),
  getLeads: (campaignId: string, params?: any) => apiClient.get(`/campaigns/${campaignId}/leads`, { params }),
  convertLead: (leadId: string) => apiClient.post(`/campaigns/leads/${leadId}/convert`),
  analyzeLead: (leadId: string) => apiClient.post(`/campaigns/leads/${leadId}/analyze`),
  listAllLeads: (params?: any) => apiClient.get('/campaigns/leads/all', { params }),
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

// Settings API
export const settingsAPI = {
  get: (endpoint: string) => apiClient.get(`/settings${endpoint}`),
  post: (endpoint: string, data?: any) => apiClient.post(`/settings${endpoint}`, data),
  put: (endpoint: string, data?: any) => apiClient.put(`/settings${endpoint}`, data),
};

// Activity API
export const activityAPI = {
  createActivity: (data: any) => apiClient.post('/activities/', data),
  getCustomerActivities: (customerId: string, params?: any) => apiClient.get(`/activities/customer/${customerId}`, { params }),
  getActionSuggestions: (customerId: string, forceRefresh: boolean = false) => apiClient.get(`/activities/customer/${customerId}/suggestions`, { params: { force_refresh: forceRefresh } }),
  refreshSuggestionsBackground: (customerId: string) => apiClient.post(`/activities/customer/${customerId}/suggestions/refresh`),
  getPendingFollowUps: (daysAhead?: number) => apiClient.get('/activities/pending-followups', { params: { days_ahead: daysAhead } }),
};

// Planning API
export const planningAPI = {
  // Counties
  getCounties: () => apiClient.get('/planning/counties'),
  getCountyStatus: () => apiClient.get('/planning/counties/status'),
  runCounty: (countyCode: string) => apiClient.post(`/planning/counties/${countyCode}/run`),
  stopCounty: (countyCode: string) => apiClient.post(`/planning/counties/${countyCode}/stop`),
  updateCountySchedule: (countyCode: string, data: any) => apiClient.put(`/planning/counties/${countyCode}/schedule`, data),
  
  // Campaigns (legacy - kept for compatibility)
  listCampaigns: (params?: any) => apiClient.get('/planning/campaigns', { params }),
  createCampaign: (data: any) => apiClient.post('/planning/campaigns', data),
  getCampaign: (id: string) => apiClient.get(`/planning/campaigns/${id}`),
  updateCampaign: (id: string, data: any) => apiClient.put(`/planning/campaigns/${id}`, data),
  deleteCampaign: (id: string) => apiClient.delete(`/planning/campaigns/${id}`),
  runCampaign: (id: string) => apiClient.post(`/planning/campaigns/${id}/run`),
  
  // Applications
  listApplications: (params?: any) => apiClient.get('/planning/applications', { params }),
  getApplication: (id: string) => apiClient.get(`/planning/applications/${id}`),
  updateApplication: (id: string, data: any) => apiClient.put(`/planning/applications/${id}`, data),
  archiveApplications: (applicationIds: string[], archived: boolean = true) => 
    apiClient.post('/planning/applications/archive', { 
      application_ids: applicationIds, 
      archived 
    }),
  
  // Keywords
  listKeywords: (params?: any) => apiClient.get('/planning/keywords', { params }),
  createKeyword: (data: any) => apiClient.post('/planning/keywords', data),
  deleteKeyword: (id: string) => apiClient.delete(`/planning/keywords/${id}`),
};

// Version API
export const versionAPI = {
  get: () => apiClient.get('/version'),
};



