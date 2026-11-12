import type {
  OverviewResponse,
  ServiceStatus,
  FruitData,
  RouteStatus,
  OperationRecord,
  NginxStatus,
  NginxValidationResult,
  ServiceLogs,
  ServiceActionResponse,
  AllServicesActionResponse,
  FruitActionResponse,
  SystemTelemetry,
} from '../types/api'

// Base URL: In dev via Vite proxy, '/api' routes to http://127.0.0.1:10020/api.
// In production via Nginx (basket.jam), '/api/' proxies to http://127.0.0.1:10020/api/.
const API_BASE = '/api'

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status} ${response.statusText}`
    try {
      const errJson = await response.json()
      if (errJson && errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail)
      } else if (errJson && errJson.message) {
        errorDetail = errJson.message
      }
    } catch {}
    throw new Error(errorDetail)
  }

  return response.json() as Promise<T>
}

export const api = {
  // Health & Overview
  getHealth: () => request<{ status: string; service: string; port: number }>('/health'),
  getOverview: () => request<OverviewResponse>('/overview'),
  getSystemTelemetry: () => request<SystemTelemetry>('/system/telemetry'),

  // Services
  getServices: () => request<ServiceStatus[]>('/services'),
  getService: (serviceId: string) => request<ServiceStatus>(`/services/${serviceId}`),
  startService: (serviceId: string) => request<ServiceActionResponse>(`/services/${serviceId}/start`, { method: 'POST' }),
  endService: (serviceId: string) => request<ServiceActionResponse>(`/services/${serviceId}/end`, { method: 'POST' }),
  restartService: (serviceId: string) => request<ServiceActionResponse>(`/services/${serviceId}/restart`, { method: 'POST' }),

  // Batch Services
  startAllServices: () => request<AllServicesActionResponse>('/services/all/start', { method: 'POST' }),
  endAllServices: () => request<AllServicesActionResponse>('/services/all/end', { method: 'POST' }),
  restartAllServices: () => request<AllServicesActionResponse>('/services/all/restart', { method: 'POST' }),

  // Fruits
  getFruits: () => request<FruitData[]>('/fruits'),
  startFruit: (fruitId: string) => request<FruitActionResponse>(`/fruits/${fruitId}/start`, { method: 'POST' }),
  endFruit: (fruitId: string) => request<FruitActionResponse>(`/fruits/${fruitId}/end`, { method: 'POST' }),
  restartFruit: (fruitId: string) => request<FruitActionResponse>(`/fruits/${fruitId}/restart`, { method: 'POST' }),

  // Logs
  getLogs: (serviceId: string, tail: number = 150) => request<ServiceLogs>(`/logs/${serviceId}?tail=${tail}`),

  // Routes
  getRoutes: () => request<RouteStatus[]>('/routes'),

  // Operations History
  getOperations: (limit: number = 50) => request<OperationRecord[]>(`/operations?limit=${limit}`),

  // AI Models Batch Control
  startModels: () => request<{ success: boolean; action: string; results: Record<string, any> }>('/models/start', { method: 'POST' }),
  endModels: () => request<{ success: boolean; action: string; results: Record<string, any> }>('/models/end', { method: 'POST' }),
  restartModels: () => request<{ success: boolean; action: string; results: Record<string, any> }>('/models/restart', { method: 'POST' }),

  // Nginx Edge
  getNginxStatus: () => request<NginxStatus>('/nginx/status'),
  validateNginx: () => request<NginxValidationResult>('/nginx/validate', { method: 'POST' }),
  reloadNginx: () => request<{ success: boolean; message: string; stderr?: string }>('/nginx/reload', { method: 'POST' }),
}

