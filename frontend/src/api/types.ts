export type DataStatus = 'available' | 'partial' | 'unavailable' | 'empty'

export interface Dataset {
  id: number
  name: string
  instrument: string
  description: string | null
  source_name: string
  source_url: string | null
  unit: string
  frequency: string
  timezone_name: string
  time_column: string
  value_column: string
  imported_at: string
}

export interface SeriesPoint {
  observed_at: string
  value: number
}

export interface ChartSeries {
  dataset_id: number
  name: string
  unit: string
  frequency: string
  chart_type: 'line'
  x_field: 'observed_at'
  y_field: 'value'
  as_of: string
  points: SeriesPoint[]
}

export interface ForecastRunRequest {
  dataset_id: number
  horizon: '5m' | '30m' | '1d' | '1m' | '3m'
  model_name?: string
  validation_method?: 'walk_forward' | 'expanding_window' | 'rolling_window'
}

export interface ForecastRun {
  id: number
  dataset_id: number
  horizon: string
  model_name: string
  model_version: string
  validation_method: string
  status: string
  validation_metrics: Record<string, number | string | null>
  created_at: string
}

export interface ForecastPoint {
  id: number
  target_at: string
  predicted_value: number
  lower_bound: number | null
  upper_bound: number | null
  actual_value: number | null
}

export interface AIExplanationRequest {
  question: string
  forecast_run_id: number
  web_search?: boolean
}

export interface AIExplanation {
  id: number
  provider: string
  model: string
  explanation: string
  sources: Array<{ title: string; url: string }>
  input_tokens: number | null
  output_tokens: number | null
  created_at: string
}
