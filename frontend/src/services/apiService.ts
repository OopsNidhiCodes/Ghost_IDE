import { errorService, RetryConfig } from './errorService';
import { useNotificationStore } from '../store/useNotificationStore';

export interface ApiRequestConfig {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  body?: any;
  timeout?: number;
  retryConfig?: RetryConfig;
  showErrorNotification?: boolean;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

class ApiService {
  private baseUrl: string;
  private defaultTimeout = 10000;
  private defaultRetryConfig: RetryConfig = {
    maxAttempts: 3,
    delay: 1000,
    backoff: 'exponential',
    shouldRetry: (error: Error, attempt: number) => {
      // Retry on network errors and 5xx server errors
      return (
        error.message.includes('fetch') ||
        error.message.includes('network') ||
        error.message.includes('timeout') ||
        (error.message.includes('500') && attempt < 3)
      );
    },
  };

  constructor() {
    this.baseUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
  }

  /**
   * Make an API request with automatic error handling and retry logic
   */
  async request<T = any>(
    endpoint: string,
    config: ApiRequestConfig = {}
  ): Promise<ApiResponse<T>> {
    const {
      method = 'GET',
      headers = {},
      body,
      timeout = this.defaultTimeout,
      retryConfig = this.defaultRetryConfig,
      showErrorNotification = true,
    } = config;

    const url = `${this.baseUrl}${endpoint}`;
    
    const requestFn = async (): Promise<ApiResponse<T>> => {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      try {
        const requestHeaders: Record<string, string> = {
          'Content-Type': 'application/json',
          ...headers,
        };

        const response = await fetch(url, {
          method,
          headers: requestHeaders,
          body: body ? JSON.stringify(body) : undefined,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const errorText = await response.text();
          let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
          
          try {
            const errorData = JSON.parse(errorText);
            errorMessage = errorData.message || errorData.error || errorMessage;
          } catch {
            // Use the raw text if it's not JSON
            errorMessage = errorText || errorMessage;
          }

          throw new Error(errorMessage);
        }

        const data = await response.json();
        return {
          success: true,
          data,
        };
      } catch (error) {
        clearTimeout(timeoutId);
        
        if (error instanceof Error) {
          if (error.name === 'AbortError') {
            throw new Error('Request timeout');
          }
          throw error;
        }
        
        throw new Error('Unknown error occurred');
      }
    };

    try {
      return await errorService.withRetry(
        requestFn,
        retryConfig,
        {
          component: 'ApiService',
          action: `${method} ${endpoint}`,
        }
      );
    } catch (error) {
      const apiError = error as Error;
      
      if (showErrorNotification) {
        errorService.handleError(apiError, {
          component: 'ApiService',
          action: `${method} ${endpoint}`,
        });
      }

      return {
        success: false,
        error: apiError.message,
      };
    }
  }

  /**
   * GET request
   */
  async get<T = any>(endpoint: string, config?: Omit<ApiRequestConfig, 'method' | 'body'>): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'GET' });
  }

  /**
   * POST request
   */
  async post<T = any>(endpoint: string, body?: any, config?: Omit<ApiRequestConfig, 'method'>): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'POST', body });
  }

  /**
   * PUT request
   */
  async put<T = any>(endpoint: string, body?: any, config?: Omit<ApiRequestConfig, 'method'>): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'PUT', body });
  }

  /**
   * DELETE request
   */
  async delete<T = any>(endpoint: string, config?: Omit<ApiRequestConfig, 'method' | 'body'>): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'DELETE' });
  }

  /**
   * PATCH request
   */
  async patch<T = any>(endpoint: string, body?: any, config?: Omit<ApiRequestConfig, 'method'>): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'PATCH', body });
  }

  /**
   * Upload file with progress tracking
   */
  async uploadFile(
    endpoint: string,
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<ApiResponse> {
    return new Promise((resolve) => {
      const xhr = new XMLHttpRequest();
      const formData = new FormData();
      formData.append('file', file);

      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable && onProgress) {
          const progress = (event.loaded / event.total) * 100;
          onProgress(progress);
        }
      });

      xhr.addEventListener('load', () => {
        try {
          const response = JSON.parse(xhr.responseText);
          resolve({
            success: xhr.status >= 200 && xhr.status < 300,
            data: response,
            error: xhr.status >= 400 ? response.message || 'Upload failed' : undefined,
          });
        } catch (error) {
          resolve({
            success: false,
            error: 'Invalid response from server',
          });
        }
      });

      xhr.addEventListener('error', () => {
        errorService.handleError(new Error('Upload failed'), {
          component: 'ApiService',
          action: 'uploadFile',
        });
        
        resolve({
          success: false,
          error: 'Upload failed',
        });
      });

      xhr.addEventListener('timeout', () => {
        errorService.handleError(new Error('Upload timeout'), {
          component: 'ApiService',
          action: 'uploadFile',
        });
        
        resolve({
          success: false,
          error: 'Upload timeout',
        });
      });

      xhr.open('POST', `${this.baseUrl}${endpoint}`);
      xhr.timeout = 60000; // 60 second timeout for uploads
      xhr.send(formData);
    });
  }

  /**
   * Check if the API is healthy
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.get('/health', {
        timeout: 5000,
        showErrorNotification: false,
        retryConfig: {
          maxAttempts: 1,
          delay: 0,
        },
      });
      
      return response.success;
    } catch {
      return false;
    }
  }

  /**
   * Set base URL for API requests
   */
  setBaseUrl(url: string) {
    this.baseUrl = url;
  }

  /**
   * Get current base URL
   */
  getBaseUrl(): string {
    return this.baseUrl;
  }
}

export const apiService = new ApiService();