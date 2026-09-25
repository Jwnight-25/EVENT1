import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { Activity, Waves } from 'lucide-react'
import { getChartSeries, getForecastPoints, listDatasets, requestForecast } from '../api/client'
import type { ChartSeries, Dataset, ForecastPoint, ForecastRun } from '../api/types'

const horizons = [
  { value: '5m', label: '5 分钟' },
  { value: '30m', label: '30 分钟' },
  { value: '1d', label: '1 天' },
  { value: '1m', label: '1 个月' },
  { value: '3m', label: '3 个月' },
] as const

export default function ForecastWorkbench({ instrument }: { instrument: string }) {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [datasetId, setDatasetId] = useState('')
  const [horizon, setHorizon] = useState<(typeof horizons)[number]['value']>('1d')
  const [run, setRun] = useState<ForecastRun | null>(null)
  const [points, setPoints] = useState<ForecastPoint[]>([])
  const [history, setHistory] = useState<ChartSeries | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    setDatasetId('')
    setRun(null)
    setPoints([])
    setHistory(null)
    listDatasets(instrument).then((items) => {
      setDatasets(items)
      if (items[0]) setDatasetId(String(items[0].id))
    }).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : '数据集读取失败'))
  }, [instrument])

  const forecastLine = useMemo(() => {
    if (!history?.points.length || !points.length) return ''
    const combined = [
      ...history.points.map((point) => ({ at: new Date(point.observed_at).getTime(), value: point.value })),
      ...points.map((point) => ({ at: new Date(point.target_at).getTime(), value: point.predicted_value })),
    ]
    const minAt = combined[0].at
    const maxAt = combined[combined.length - 1].at
    const values = combined.map((point) => point.value)
    const minValue = Math.min(...values)
    const maxValue = Math.max(...values)
    const spanAt = maxAt - minAt || 1
    const spanValue = maxValue - minValue || 1
    const toPoint = (point: { at: number; value: number }) => `${48 + ((point.at - minAt) / spanAt) * 820},${24 + (1 - (point.value - minValue) / spanValue) * 220}`
    return {
      actual: history.points.map((point) => toPoint({ at: new Date(point.observed_at).getTime(), value: point.value })).join(' '),
      forecast: [
        toPoint({ at: new Date(history.points[history.points.length - 1].observed_at).getTime(), value: history.points[history.points.length - 1].value }),
        ...points.map((point) => toPoint({ at: new Date(point.target_at).getTime(), value: point.predicted_value })),
      ].join(' '),
    }
  }, [history, points])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!datasetId) return
    setBusy(true)
    setError('')
    setRun(null)
    setPoints([])
    try {
      const dataset = Number(datasetId)
      const [result, chart] = await Promise.all([
        requestForecast({ dataset_id: dataset, horizon, model_name: 'naive_baseline', validation_method: 'walk_forward' }),
        getChartSeries(dataset),
      ])
      const predicted = await getForecastPoints(result.id)
      setRun(result)
      setHistory(chart)
      setPoints(predicted)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '预测运行失败')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="data-workbench">
      <section className="panel import-panel">
        <div className="panel-heading"><div><h2>运行基线预测</h2><p>朴素基线：将最近观测值延续到目标周期，并以滚动回测误差给出经验区间。</p></div><Waves size={19} /></div>
        <form className="forecast-form" onSubmit={submit}>
          <label>数据集<select required value={datasetId} onChange={(event) => setDatasetId(event.target.value)}><option value="" disabled>选择数据集</option>{datasets.map((dataset) => <option key={dataset.id} value={dataset.id}>{dataset.name} · {dataset.frequency}</option>)}</select></label>
          <label>预测周期<select value={horizon} onChange={(event) => setHorizon(event.target.value as typeof horizon)}>{horizons.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>
          <button className="refresh-button" type="submit" disabled={!datasetId || busy}><Activity size={15} />{busy ? '正在回测并预测…' : '运行预测'}</button>
        </form>
        <p className="forecast-disclaimer">这是用于验证数据链路的简单基线，不构成交易建议。结果会保存模型版本、时间窗口和样本外误差。更复杂模型将在后续接入。</p>
        {error && <p className="form-feedback error">{error}</p>}
      </section>

      {run && <>
        <section className="metric-grid forecast-metrics">
          <article className="metric-card"><div className="metric-top"><span>运行状态</span></div><div className="metric-value status-value">{run.status === 'validated' ? '已验证' : '弱信号'}</div><div className="metric-bottom"><span>{run.model_name} · v{run.model_version}</span></div></article>
          <article className="metric-card"><div className="metric-top"><span>MAE</span></div><div className="metric-value">{formatMetric(run.validation_metrics.mae)}</div><div className="metric-bottom"><span>{history?.unit ?? '误差单位'}</span></div></article>
          <article className="metric-card"><div className="metric-top"><span>RMSE</span></div><div className="metric-value">{formatMetric(run.validation_metrics.rmse)}</div><div className="metric-bottom"><span>{run.validation_metrics.backtest_origin_count ?? 0} 个滚动验证点</span></div></article>
          <article className="metric-card"><div className="metric-top"><span>经验误差带 P90</span></div><div className="metric-value">±{formatMetric(run.validation_metrics.empirical_absolute_error_p90)}</div><div className="metric-bottom"><span>由回测残差估计</span></div></article>
        </section>
        <section className="panel series-panel">
          <div className="panel-heading"><div><h2>{history?.name ?? '时间序列'} · 历史与预测</h2><p>{horizons.find((item) => item.value === run.horizon)?.label} · {run.validation_method} · 点线为历史，虚线为基线预测</p></div></div>
          {forecastLine && <div className="series-chart forecast-chart"><svg viewBox="0 0 900 280" role="img" aria-label="历史序列与基线预测图" preserveAspectRatio="none"><line x1="48" x2="868" y1="244" y2="244" /><line x1="48" x2="868" y1="134" y2="134" /><line x1="48" x2="868" y1="24" y2="24" /><polyline className="history-line" points={forecastLine.actual} /><polyline className="forecast-line" points={forecastLine.forecast} /></svg></div>}
          <div className="forecast-points">{points.slice(0, 8).map((point) => <div className="forecast-point" key={point.id}><span>{new Date(point.target_at).toLocaleString()}</span><strong>{point.predicted_value.toLocaleString(undefined, { maximumFractionDigits: 4 })} {history?.unit}</strong><span>{point.lower_bound?.toLocaleString(undefined, { maximumFractionDigits: 4 })} — {point.upper_bound?.toLocaleString(undefined, { maximumFractionDigits: 4 })}</span></div>)}</div>
        </section>
      </>}
    </div>
  )
}

function formatMetric(value: number | string | null | undefined): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '—'
  return value.toLocaleString(undefined, { maximumFractionDigits: 4 })
}
