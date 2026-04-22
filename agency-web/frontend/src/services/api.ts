const API_BASE = import.meta.env.VITE_API_URL || '/api/v1'

interface ApiError {
  code: string
  message: string
  details?: Record<string, unknown>
}

interface ApiResponse<T> {
  data: T | null
  error: ApiError | null
  meta?: {
    page?: number
    per_page?: number
    total?: number
  }
}

class ApiClient {
  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    }
    
    const token = localStorage.getItem('agency-token')
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    return headers
  }

  private async handleResponse<T>(response: Response): Promise<ApiResponse<T>> {
    const data = await response.json()
    
    if (!response.ok) {
      return {
        data: null,
        error: data.error || { code: 'UNKNOWN_ERROR', message: 'An unknown error occurred' },
      }
    }
    
    return {
      data: data.data,
      error: null,
      meta: data.meta,
    }
  }

  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'GET',
      headers: this.getHeaders(),
    })
    return this.handleResponse<T>(response)
  }

  async post<T>(endpoint: string, body: unknown): Promise<ApiResponse<T>> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(body),
    })
    return this.handleResponse<T>(response)
  }

  async put<T>(endpoint: string, body: unknown): Promise<ApiResponse<T>> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(body),
    })
    return this.handleResponse<T>(response)
  }

  async patch<T>(endpoint: string, body: unknown): Promise<ApiResponse<T>> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'PATCH',
      headers: this.getHeaders(),
      body: JSON.stringify(body),
    })
    return this.handleResponse<T>(response)
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    })
    return this.handleResponse<T>(response)
  }
}

export const api = new ApiClient()
