import api from './api'
import type { ReportResponse, ReportSummaryItem, ReportTypeStatus } from '../types/report'

export interface GenerateReportOptions {
  filename?: string
  reportType?: string
  datasetVersion?: number
  filters?: Record<string, any>
  mappings?: Array<Record<string, unknown>>
}

export const reportService = {
  generateReport: async (
    datasetId: string,
    options?: GenerateReportOptions
  ): Promise<ReportResponse> => {
    const response = await api.post<ReportResponse>('/api/v1/reports/generate', {
      dataset_id: datasetId,
      filename: options?.filename,
      report_type: options?.reportType || 'standard',
      dataset_version: options?.datasetVersion,
      filters: options?.filters || {},
      mappings: options?.mappings,
    })
    return response.data
  },

  getSupportedTypes: async (datasetId: string): Promise<ReportTypeStatus[]> => {
    const response = await api.get<ReportTypeStatus[]>('/api/v1/reports/types', {
      params: { dataset_id: datasetId },
    })
    return response.data
  },

  getReportIntelligence: async (datasetId: string): Promise<Record<string, any>> => {
    const response = await api.get<Record<string, any>>(`/api/v1/reports/intelligence/${datasetId}`)
    return response.data
  },

  getReport: async (reportId: string): Promise<ReportResponse> => {
    const response = await api.get<ReportResponse>(`/api/v1/reports/${reportId}`)
    return response.data
  },

  listReports: async (datasetId?: string): Promise<ReportSummaryItem[]> => {
    const response = await api.get<ReportSummaryItem[]>('/api/v1/reports', {
      params: datasetId ? { dataset_id: datasetId } : undefined,
    })
    return response.data
  },

  regenerateReport: async (reportId: string): Promise<ReportResponse> => {
    const response = await api.post<ReportResponse>(`/api/v1/reports/${reportId}/regenerate`)
    return response.data
  },

  downloadPdf: async (reportId: string, filename?: string): Promise<void> => {
    const response = await api.get(`/api/v1/reports/${reportId}/pdf`, {
      responseType: 'blob',
    })
    const blob = new Blob([response.data], { type: 'application/pdf' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename || `report_${reportId}.pdf`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },

  generateAiSummary: async (reportId: string, options?: { regenerate?: boolean }): Promise<Record<string, any>> => {
    const response = await api.post<Record<string, any>>(`/api/v1/reports/${reportId}/ai-summary`, options || { regenerate: false })
    return response.data
  },

  deleteReport: async (reportId: string): Promise<{ success: boolean; report_id: string }> => {
    const response = await api.delete<{ success: boolean; report_id: string }>(`/api/v1/reports/${reportId}`)
    return response.data
  },
}
