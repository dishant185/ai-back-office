/**
 * AI status and hardware API service.
 */
import api from './api'
import type { AIStatusResponse, AIHardwareResponse, AIModelDetailsResponse } from '../types/ai'

export const aiApi = {
  getStatus: async (): Promise<AIStatusResponse> => {
    const response = await api.get<AIStatusResponse>('/api/v1/ai/status')
    return response.data
  },

  getHardware: async (): Promise<AIHardwareResponse> => {
    const response = await api.get<AIHardwareResponse>('/api/v1/ai/hardware')
    return response.data
  },

  getModelDetails: async (): Promise<AIModelDetailsResponse> => {
    const response = await api.get<AIModelDetailsResponse>('/api/v1/ai/model')
    return response.data
  },
}

