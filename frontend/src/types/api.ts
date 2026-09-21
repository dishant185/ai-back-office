export interface ComponentHealth {
  status: string
  connected: boolean
  details?: {
    provider?: string
    model?: string
    configured?: boolean
    connected?: boolean
    [key: string]: any
  }
}

export interface HealthResponse {
  status: string
  service: string
  version: string
  database?: ComponentHealth
}

export interface ReadinessResponse {
  status: 'ready' | 'degraded' | string
  service: string
  version: string
  environment: string
  database: ComponentHealth
  llm: ComponentHealth
}

