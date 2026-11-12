export interface ServiceStatus {
  id: string
  name: string
  category: 'infrastructure' | 'fruit' | 'database' | 'llm' | 'speech' | 'proxy' | 'control'
  fruit_id: string | null
  description: string
  status: 'healthy' | 'degraded' | 'stopped' | 'running'
  is_running: boolean
  is_healthy: boolean
  is_listening: boolean
  health_message: string
  pid: number | null
  host: string | null
  port: number | null
  memory_mb: number
  cpu_percent: number
  uptime_sec: number
  log_file: string
  task_scheduler_task: string | null
}

export interface FruitComponentStatus extends ServiceStatus {}

export interface FruitData {
  id: string
  name: string
  tagline: string
  icon: string | null
  category: string
  frontend_url: string | null
  frontend_upstream: string | null
  api_url: string | null
  api_upstream: string | null
  ws_url: string | null
  ws_upstream?: string | null
  mcp_url?: string | null
  mcp_upstream?: string | null
  is_redirector_enabled: boolean
  is_android_client: boolean
  components: string[]
  component_details?: FruitComponentStatus[]
  is_running: boolean
  frontend_live: boolean
  api_live: boolean
}

export interface OverviewMetrics {
  total_services: number
  running_services: number
  stopped_services: number
  healthy_services: number
  degraded_services: number
  total_routes: number
  live_routes: number
  unavailable_routes: number
  nginx_state: string
}

export interface SystemTelemetry {
  cpu: {
    utilization_pct: number
    logical_cores: number
    temperature_c?: number | null
  }
  memory: {
    used_bytes: number
    total_bytes: number
    used_gb: number
    total_gb: number
    utilization_pct: number
  }
  gpu: {
    available: boolean
    name: string | null
    gpu_utilization_pct: number
    temperature_c: number
    vram_used_mb: number
    vram_total_mb: number
    vram_pct: number
  }
}

export interface OperationRecord {
  id: string
  timestamp: string
  service_id: string
  action: string
  status: 'success' | 'failed'
  duration_ms: number
  error?: string | null
}

export interface RouteStatus {
  id: string
  service: string
  reverse_proxy_url: string
  actual_destination: string
  type: 'frontend' | 'api' | 'websocket' | 'infrastructure'
  fruit_id: string | null
  is_live: boolean
  status_code: number
  message: string
}

export interface NginxStatus {
  status: ServiceStatus
  listening_80: boolean
  listening_443: boolean
  config_path: string
}

export interface NginxValidationResult {
  valid: boolean
  exit_code: number
  stdout: string
  stderr: string
}

export interface ServiceActionResponse {
  success: boolean
  action: string
  status?: string
  pid?: number
  message: string
}

export interface AllServicesActionResponse {
  success: boolean
  action: string
  results?: Record<string, ServiceActionResponse>
  stop_results?: Record<string, any>
  start_results?: Record<string, any>
}

export interface FruitActionResponse {
  success: boolean
  action: string
  fruit_id: string
  components?: Record<string, ServiceActionResponse>
  message?: string
}

export interface ServiceLogs {
  service_id: string
  name: string
  line_count: number
  lines: string[]
}

export interface OverviewResponse {
  metrics: OverviewMetrics
  system: SystemTelemetry
  services: ServiceStatus[]
  fruits: FruitData[]
  recent_operations: OperationRecord[]
}

