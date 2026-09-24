import type {
  AIExplanation,
  AIExplanationRequest,
  ChartSeries,
  Dataset,
  ForecastPoint,
  ForecastRun,
  ForecastRunRequest,
} from './types'

const apiBase = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '')

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase}/api/v1${path}`, init)
  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    const detail = payload?.detail ?? `API 请求失败（${response.status}）`
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  return response.json() as Promise<T>
}

export function listDatasets(): Promise<Dataset[]> {
  return request('/datasets')
}

export function getDatasetSummary(datasetId: number): Promise<Record<string, unknown>> {
  return request(`/datasets/${datasetId}/summary`)
}

export function getObservations(datasetId: number, start?: string, end?: string): Promise<ChartSeries['points']> {
  const params = new URLSearchParams()
  if (start) params.set('start', start)
  if (end) params.set('end', end)
  const suffix = params.toString() ? `?${params.toString()}` : ''
  return request(`/datasets/${datasetId}/observations${suffix}`)
}

export function getChartSeries(datasetId: number, start?: string, end?: string): Promise<ChartSeries> {
  const params = new URLSearchParams()
  if (start) params.set('start', start)
  if (end) params.set('end', end)
  const suffix = params.toString() ? `?${params.toString()}` : ''
  return request(`/datasets/${datasetId}/chart${suffix}`)
}

export function importTimeSeriesCsv(
  file: File,
  metadata: {
    name: string
    unit: string
    frequency: string
    source_name: string
    time_column: string
    value_column: string
    instrument?: string
    timezone_name?: string
    source_url?: string
  },
) {
  const body = new FormData()
  body.set('file', file)
  Object.entries(metadata).forEach(([key, value]) => {
    if (value !== undefined) body.set(key, value)
  })
  return request<{ dataset: Dataset; rows_read: number; rows_imported: number; rows_duplicate: number }>(
    '/datasets/import', { method: 'POST', body },
  )
}

export function requestForecast(input: ForecastRunRequest): Promise<ForecastRun> {
  return request<ForecastRun>('/forecasts/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
}

export function listForecastRuns(): Promise<ForecastRun[]> {
  return request<ForecastRun[]>('/forecasts')
}

export function getForecastPoints(runId: number): Promise<ForecastPoint[]> {
  return request<ForecastPoint[]>(`/forecasts/${runId}/points`)
}

export function explainResults(input: AIExplanationRequest): Promise<AIExplanation> {
  return request('/ai/explanations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
}

export function getAICapabilities(): Promise<Record<string, unknown>> {
  return request('/ai/capabilities')
}
