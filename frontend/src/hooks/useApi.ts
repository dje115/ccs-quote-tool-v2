import { useState, useCallback } from 'react';
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

interface ApiResponse<T = any> {
  data: T;
  message?: string;
}

interface UseApiReturn {
  get: <T = any>(url: string, config?: AxiosRequestConfig) => Promise<T>;
  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) => Promise<T>;
  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) => Promise<T>;
  patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) => Promise<T>;
  delete: <T = any>(url: string, config?: AxiosRequestConfig) => Promise<T>;
  loading: boolean;
  error: string | null;
}

export const useApi = (): UseApiReturn => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Create axios instance with base configuration
  const apiClient: AxiosInstance = axios.create({
    baseURL: import.meta.env.DEV ? 'http://localhost:8000/api/v1' : '/api/v1',
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
    withCredentials: true,  // IMPORTANT: Required for HttpOnly cookies and RLS
  });

  // SECURITY: HttpOnly cookies are sent automatically with withCredentials: true
  // Do NOT add Authorization header from localStorage - tokens are vulnerable to XSS
  // The backend will read tokens from cookies first, then fall back to Authorization header if needed
  // No request interceptor needed for authentication - cookies handle it automatically

  // Add response interceptor for error handling
  apiClient.interceptors.response.use(
    (response: AxiosResponse) => {
      return response;
    },
    (error) => {
      if (error.response?.status === 401) {
        // Handle unauthorized access
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
      return Promise.reject(error);
    }
  );

  const makeRequest = useCallback(async <T = any>(
    requestFn: () => Promise<AxiosResponse<T>>
  ): Promise<T> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await requestFn();
      return response.data;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'An error occurred';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const get = useCallback(async <T = any>(
    url: string, 
    config?: AxiosRequestConfig
  ): Promise<T> => {
    return makeRequest<T>(() => apiClient.get(url, config));
  }, [makeRequest]);

  const post = useCallback(async <T = any>(
    url: string, 
    data?: any, 
    config?: AxiosRequestConfig
  ): Promise<T> => {
    return makeRequest<T>(() => apiClient.post(url, data, config));
  }, [makeRequest]);

  const put = useCallback(async <T = any>(
    url: string, 
    data?: any, 
    config?: AxiosRequestConfig
  ): Promise<T> => {
    return makeRequest<T>(() => apiClient.put(url, data, config));
  }, [makeRequest]);

  const patch = useCallback(async <T = any>(
    url: string, 
    data?: any, 
    config?: AxiosRequestConfig
  ): Promise<T> => {
    return makeRequest<T>(() => apiClient.patch(url, data, config));
  }, [makeRequest]);

  const deleteRequest = useCallback(async <T = any>(
    url: string, 
    config?: AxiosRequestConfig
  ): Promise<T> => {
    return makeRequest<T>(() => apiClient.delete(url, config));
  }, [makeRequest]);

  return {
    get,
    post,
    put,
    patch,
    delete: deleteRequest,
    loading,
    error,
  };
};
