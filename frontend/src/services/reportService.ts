import api from './api'
import type { ReportResponse, ReportSummaryItem } from '../types/report'

export const reportService = {
  generateReport: async (
    datasetId: string,
    filename?: string,
    mappings?: Array<Record<string, unknown>>
  ): Promise<ReportResponse> => {
    const response = await api.post<ReportResponse>('/api/v1/reports/generate', {
      dataset_id: datasetId,
      filename,
      mappings,
    })
    return response.data
  },

  getReport: async (reportId: string): Promise<ReportResponse> => {
    const response = await api.get<ReportResponse>(`/api/v1/reports/${reportId}`)
    return response.data
  },

  listReports: async (): Promise<ReportSummaryItem[]> => {
    const response = await api.get<ReportSummaryItem[]>('/api/v1/reports/list')
    return response.data
  },
}
