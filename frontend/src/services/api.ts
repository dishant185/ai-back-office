import axios from 'axios'

import type { HealthResponse } from '../types/api'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 10000,
})

export const healthService = {
  getHealth: async (): Promise<HealthResponse> => {
    const response = await api.get<HealthResponse>('/health')
    return response.data
  },
}

export default api
