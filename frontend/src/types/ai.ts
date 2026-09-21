/**
 * AI-related TypeScript types for the frontend.
 */

export type AIStatusState = 'ready' | 'loading' | 'offline' | 'error' | 'disabled' | 'low_memory'

export interface AIStatusResponse {
  enabled: boolean
  provider: string
  status: string
  model: string
  runtime: string
}

export interface AIHardwareResponse {
  ram_total_gb: number
  ram_available_gb: number
  cpu: string
  gpu: string
  cuda_available: boolean
  os: string
  recommended_model: string
  recommended_runtime: string
  recommended_quantization: string
  memory_warning?: string
}

export interface AnalystSourceItem {
  metric?: string
  field?: string
  operation?: string
  dataset?: string
  status?: string
  value?: string | number
  label?: string
}

export type AnalystSource = string | AnalystSourceItem

export interface AnalystSession {
  session_id: string
  dataset_id: string
  profile: string
  row_count: number
  capabilities: string[]
  metrics: Record<string, number>
  dimensions: Record<string, Record<string, number>>
  message_count: number
  created_at: string
  updated_at: string
}

export interface AnalystMessageResponse {
  answer: string
  sources: AnalystSource[]
  insights: string[]
  recommendations: string[]
  limitations: string[]
  ai_status?: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  sources?: AnalystSource[]
  insights?: string[]
  recommendations?: string[]
  limitations?: string[]
  isDeterministic?: boolean
  ai_status?: string
}

export interface SuggestedQuestion {
  category: string
  title: string
  query: string
}

export interface LoRAAdapterInfo {
  adapter_id: string
  name: string
  description: string
  path: string
  base_model: string
  target_modules: string[]
  lora_r: number
  lora_alpha: number
  lora_dropout: number
  status: string
  metrics?: {
    direct_metric_accuracy?: number
    grounding_fidelity?: number
    unsupported_rejection_rate?: number
    evaluation_loss?: number
    train_samples?: number
    validation_samples?: number
  }
  created_at?: string
}

export interface AIModelDetailsResponse {
  status_state: string
  runtime_status: string
  base_model: {
    name: string
    hf_repo_id: string
    local_dir?: string
    parameters?: string
    context_length?: number
    architecture?: string
  }
  active_adapter?: LoRAAdapterInfo | null
  adapters: LoRAAdapterInfo[]
  inference_runtime: {
    engine: string
    gguf_model?: string
    quantization?: string
    vram_required_gb?: number
    ram_required_gb?: number
    status?: string
    model?: string
  }
  last_updated?: string
}
