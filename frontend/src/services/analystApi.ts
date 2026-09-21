/**
 * AI Analyst session and messaging API service.
 */
import api from './api'
import type { AnalystSession, AnalystMessageResponse } from '../types/ai'

export const analystApi = {
  createSession: async (
    datasetId: string,
    reportContext?: Record<string, unknown>,
  ): Promise<AnalystSession> => {
    const response = await api.post<AnalystSession>('/api/v1/analyst/sessions', {
      dataset_id: datasetId,
      report_context: reportContext || null,
    })
    return response.data
  },

  getSession: async (sessionId: string): Promise<AnalystSession> => {
    const response = await api.get<AnalystSession>(`/api/v1/analyst/sessions/${sessionId}`)
    return response.data
  },

  sendMessage: async (
    sessionId: string,
    message: string,
  ): Promise<AnalystMessageResponse> => {
    const response = await api.post<AnalystMessageResponse>(
      `/api/v1/analyst/sessions/${sessionId}/messages`,
      { message },
    )
    return response.data
  },
}
