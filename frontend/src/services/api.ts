import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

// Vite uses import.meta.env instead of process.env
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,  // IMPORTANT: Required for HttpOnly cookies
});

// Track refresh token request to prevent infinite loops
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: any) => void;
  reject: (reason?: any) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  
  failedQueue = [];
};

// Add auth token to requests
// SECURITY: HttpOnly cookies are sent automatically by the browser with withCredentials: true
// We no longer use localStorage tokens to prevent XSS attacks
apiClient.interceptors.request.use(
  (config) => {
    // HttpOnly cookies are sent automatically - no need to manually add Authorization header
    // The backend will read tokens from cookies first, then fall back to Authorization header
    return config;
  },
  (error) => Promise.reject(error)
);

// Handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    
    // Prevent infinite loops: don't retry refresh endpoint or if already retrying
    if (
      !originalRequest ||
      originalRequest._retry ||
      originalRequest.url?.includes('/auth/refresh') ||
      error.response?.status !== 401
    ) {
      return Promise.reject(error);
    }
    
    // If already refreshing, queue this request
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      })
        .then((token) => {
          if (token && originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${token}`;
          }
          return apiClient(originalRequest);
        })
        .catch((err) => {
          return Promise.reject(err);
        });
    }
    
    originalRequest._retry = true;
    isRefreshing = true;
    
    // SECURITY: HttpOnly cookies are sent automatically with withCredentials: true
    // No need to read refresh_token from localStorage - backend reads from cookie
    try {
      // Refresh token endpoint will use HttpOnly cookie automatically
      // IMPORTANT: Use axios directly (not apiClient) to avoid triggering interceptor
      const refreshResponse = await axios.post(
        `${API_BASE_URL}/api/v1/auth/refresh`,
        {}, // Empty body - refresh token comes from HttpOnly cookie
        {
          withCredentials: true,
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
      
      const newAccessToken = refreshResponse.data.access_token;
      const newRefreshToken = refreshResponse.data.refresh_token;
      
      // SECURITY: Do NOT store tokens in localStorage - HttpOnly cookies are set automatically by the server
      // If backend returns tokens in response, they're for backward compatibility only
      // We rely entirely on HttpOnly cookies for security
      
      // Update authorization header for retry (if token provided in response)
      // But prefer HttpOnly cookie which is sent automatically
      if (newAccessToken && originalRequest.headers) {
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
      }
      
      // Process queued requests
      processQueue(null, newAccessToken);
      
      // Retry original request
      return apiClient(originalRequest);
    } catch (refreshError) {
      // Refresh failed - clear queue and auth data
      processQueue(refreshError, null);
      
      // Clear user data (tokens are in HttpOnly cookies, cleared by backend on logout)
      localStorage.removeItem('user');
      
      // Only redirect if not already on login page
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
      
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
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
  logout: () => apiClient.post('/auth/logout'),
};

// AI Analysis API
export const aiAnalysisAPI = {
  getStatus: () => apiClient.get('/ai-analysis/status'),
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
  list: (params?: any, config?: any) => apiClient.get('/customers/', { params, ...config }),
  create: (data: any) => apiClient.post('/customers/', data),
  get: (id: string, config?: any) => apiClient.get(`/customers/${id}`, config),
  update: (id: string, data: any) => apiClient.put(`/customers/${id}`, data),
  delete: (id: string) => apiClient.delete(`/customers/${id}`),
  runAiAnalysis: (id: string, options?: { update_financial_data?: boolean; update_addresses?: boolean }) => 
    apiClient.post(`/customers/${id}/ai-analysis`, options || {}),
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
  list: (customerId: string, config?: any) => apiClient.get(`/contacts/customer/${customerId}`, config),
  create: (data: any) => apiClient.post('/contacts/', data),
  update: (id: string, data: any) => apiClient.put(`/contacts/${id}`, data),
  delete: (id: string) => apiClient.delete(`/contacts/${id}`),
};

// Quote API
export const quoteAPI = {
  list: (params?: any, config?: any) => apiClient.get('/quotes/', { params, ...config }),
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

// AI Prompts API
export const promptsAPI = {
  list: (params?: any) => apiClient.get('/prompts/', { params }),
  get: (id: string) => apiClient.get(`/prompts/${id}`),
  create: (data: any) => apiClient.post('/prompts/', data),
  update: (id: string, data: any) => apiClient.put(`/prompts/${id}`, data),
  delete: (id: string, softDelete: boolean = true) => apiClient.delete(`/prompts/${id}`, { params: { soft_delete: softDelete } }),
  getVersions: (id: string) => apiClient.get(`/prompts/${id}/versions`),
  rollback: (id: string, version: number) => apiClient.post(`/prompts/${id}/rollback/${version}`),
  test: (id: string, variables: any) => apiClient.post(`/prompts/${id}/test`, { variables }),
  getAvailableProviders: () => apiClient.get('/prompts/available-providers'),
  getAvailableModels: (providerId: string) => apiClient.get(`/prompts/available-models/${providerId}`),
};

// Provider Keys API
export const providerKeysAPI = {
  listProviders: () => apiClient.get('/provider-keys/providers'),
  getStatus: () => apiClient.get('/provider-keys/status'),
  saveKey: (providerId: string, data: any, isSystem: boolean = false) => 
    apiClient.put(`/provider-keys/${providerId}?is_system=${isSystem}`, data),
  testKey: (providerId: string, data?: any, isSystem: boolean = false) => 
    apiClient.post(`/provider-keys/${providerId}/test?is_system=${isSystem}`, data),
  deleteKey: (providerId: string, isSystem: boolean = false) => 
    apiClient.delete(`/provider-keys/${providerId}?is_system=${isSystem}`),
};

// Helpdesk API
export const helpdeskAPI = {
  getTickets: (params?: any, config?: any) => apiClient.get('/helpdesk/tickets', { params, ...config }),
  getTicket: (id: string) => apiClient.get(`/helpdesk/tickets/${id}`),
  createTicket: (data: any) => apiClient.post('/helpdesk/tickets', data),
  updateTicket: (id: string, data: any) => apiClient.put(`/helpdesk/tickets/${id}`, data),
  addComment: (ticketId: string, data: { comment: string; is_internal?: boolean }) => 
    apiClient.post(`/helpdesk/tickets/${ticketId}/comments`, data),
  updateStatus: (id: string, status: string) => 
    apiClient.patch(`/helpdesk/tickets/${id}/status`, { status }),
  assignTicket: (id: string, userId: string) => 
    apiClient.post(`/helpdesk/tickets/${id}/assign`, { user_id: userId }),
  analyzeTicket: (id: string) => apiClient.post(`/helpdesk/tickets/${id}/analyze`),
  getTicketStats: () => apiClient.get('/helpdesk/tickets/stats'),
  searchKnowledgeBase: (query: string, category?: string) => 
    apiClient.get('/helpdesk/knowledge-base/search', { params: { query, category } }),
  // AI-powered endpoints
  analyzeTicketWithAI: (id: string, updateFields?: any) => 
    apiClient.post(`/helpdesk/tickets/${id}/ai/analyze`, { update_fields: updateFields }),
  improveTicketDescription: (id: string, description: string) => 
    apiClient.post(`/helpdesk/tickets/${id}/ai/improve-description`, { description }),
  generateAutoResponse: (id: string, responseType: string = 'acknowledgment') => 
    apiClient.post(`/helpdesk/tickets/${id}/ai/auto-response`, { response_type: responseType }),
  getKnowledgeBaseSuggestions: (id: string, limit: number = 5) => 
    apiClient.get(`/helpdesk/tickets/${id}/ai/knowledge-base`, { params: { limit } }),
};

// Customer Health API
export const customerHealthAPI = {
  getHealth: (customerId: string, daysBack: number = 90) => 
    apiClient.get(`/customers/${customerId}/health`, { params: { days_back: daysBack } }),
  getTimeline: (customerId: string, limit: number = 50, activityTypes?: string[]) => 
    apiClient.get(`/customers/${customerId}/timeline`, { params: { limit, activity_types: activityTypes } }),
  getDailySummary: (customerId: string, date?: string) => 
    apiClient.get(`/customers/${customerId}/timeline/daily-summary`, { params: { date } }),
};

// Quote AI Copilot API
export const quoteAICopilotAPI = {
  analyzeScope: (quoteId: string) => apiClient.get(`/quotes/${quoteId}/ai/scope-analysis`),
  getClarifyingQuestions: (quoteId: string) => apiClient.get(`/quotes/${quoteId}/ai/clarifying-questions`),
  getUpsells: (quoteId: string) => apiClient.get(`/quotes/${quoteId}/ai/upsells`),
  getCrossSells: (quoteId: string) => apiClient.get(`/quotes/${quoteId}/ai/cross-sells`),
  getExecutiveSummary: (quoteId: string) => apiClient.get(`/quotes/${quoteId}/ai/executive-summary`),
  generateEmailCopy: (quoteId: string, emailType: string = 'send_quote') => 
    apiClient.post(`/quotes/${quoteId}/ai/email-copy`, { email_type: emailType }),
};

// Lead Intelligence API
export const leadIntelligenceAPI = {
  analyzeLead: (leadId: string) => apiClient.get(`/leads/${leadId}/ai/analyze`),
  getOutreachPlan: (leadId: string) => apiClient.get(`/leads/${leadId}/ai/outreach-plan`),
  getSimilarLeads: (leadId: string) => apiClient.get(`/leads/${leadId}/ai/similar-leads`),
};

// Trend Detection API
export const trendsAPI = {
  getRecurringDefects: (daysBack: number = 30, minOccurrences: number = 3) => 
    apiClient.get('/trends/recurring-defects', { params: { days_back: daysBack, min_occurrences: minOccurrences } }),
  getQuoteHurdles: (daysBack: number = 30) => 
    apiClient.get('/trends/quote-hurdles', { params: { days_back: daysBack } }),
  getChurnSignals: (daysBack: number = 90) => 
    apiClient.get('/trends/churn-signals', { params: { days_back: daysBack } }),
  getTrendReport: (daysBack: number = 30) => 
    apiClient.get('/trends/report', { params: { days_back: daysBack } }),
};

// Metrics API
export const metricsAPI = {
  getSLA: (startDate?: string, endDate?: string) => 
    apiClient.get('/metrics/sla', { params: { start_date: startDate, end_date: endDate } }),
  getAIUsage: (startDate?: string, endDate?: string) => 
    apiClient.get('/metrics/ai-usage', { params: { start_date: startDate, end_date: endDate } }),
  getLeadVelocity: (startDate?: string, endDate?: string) => 
    apiClient.get('/metrics/lead-velocity', { params: { start_date: startDate, end_date: endDate } }),
  getQuoteCycleTime: (startDate?: string, endDate?: string) => 
    apiClient.get('/metrics/quote-cycle-time', { params: { start_date: startDate, end_date: endDate } }),
  getCSAT: (startDate?: string, endDate?: string) => 
    apiClient.get('/metrics/csat', { params: { start_date: startDate, end_date: endDate } }),
  getDashboard: () => apiClient.get('/metrics/dashboard'),
};



