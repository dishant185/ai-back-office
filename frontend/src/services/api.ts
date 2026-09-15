import axios from 'axios'

import type { HealthResponse } from '../types/api'
import type { AnalyticsResponse } from '../types/analytics'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 120000,
})

export const healthService = {
  getHealth: async (): Promise<HealthResponse> => {
    const response = await api.get<HealthResponse>('/health')
    return response.data
  },
}

export const analyticsService = {
  runAnalytics: async (datasetId: string): Promise<AnalyticsResponse> => {
    const response = await api.post<AnalyticsResponse>('/api/v1/analytics/run', {
      dataset_id: datasetId,
    })
    return response.data
  },
}

export { reportService } from './reportService'

export default api

