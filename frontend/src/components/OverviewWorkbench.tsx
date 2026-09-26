import { useEffect, useMemo, useState } from 'react'
import { Activity, ArrowRight, Database } from 'lucide-react'
import { getChartSeries, listDatasets } from '../api/client'
import type { ChartSeries, Dataset } from '../api/types'

type Props = { instrument: string; onOpenData: () => void; onOpenForecast: () => void }

export default function OverviewWorkbench({ instrument, onOpenData, onOpenForecast }: Props) {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [series, setSeries] = useState<ChartSeries | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError('')
    setSeries(null)
    setSelectedId(null)
    listDatasets(instrument).then((items) => {
      if (cancelled) return
      setDatasets(items)
      setSelectedId(items[0]?.id ?? null)
      setLoading(false)
    }).catch((reason: unknown) => {
      if (cancelled) return
      setError(reason instanceof Error ? reason.message : '数据集读取失败')
      setDatasets([])
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [instrument])

  useEffect(() => {
    if (selectedId === null) { setSeries(null); return }
    let cancelled = false
    getChartSeries(selectedId).then((value) => { if (!cancelled) setSeries(value) })
      .catch((reason: unknown) => { if (!cancelled) setError(reason instanceof Error ? reason.message : '序列读取失败') })
    return () => { cancelled = true }
  }, [selectedId])

  const points = series?.points ?? []
  const latest = points[points.length - 1]
  const plotted = useMemo(() => {
    if (points.length < 2) return ''
    const times = points.map((point) => new Date(point.observed_at).getTime())
    const values = points.map((point) => point.value)
    const minX = times[0], maxX = times[times.length - 1]
    const minY = Math.min(...values), maxY = Math.max(...values)
    const spanX = maxX - minX || 1, spanY = maxY - minY || 1
    return points.map((point, index) => {
      const x = 48 + ((times[index] - minX) / spanX) * 820
      const y = 24 + (1 - (point.value - minY) / spanY) * 220
      return `${x.toFixed(1)},${y.toFixed(1)}`
    }).join(' ')
  }, [points])

  if (loading) return <section className="panel overview-empty"><Database size={20} /><strong>正在读取本地样本…</strong></section>
  if (error) return <section className="notice-banner"><div className="notice-icon"><Database size={17} /></div><div><strong>读取样本失败</strong><span>{error}</span></div></section>
  if (!datasets.length) return <section className="notice-banner"><div className="notice-icon"><Database size={17} /></div><div><strong>当前品种暂无已导入样本</strong><span>切换到已有样本的品种，或导入 CSV 时间序列后再查看。</span></div><button className="text-button" onClick={onOpenData}>去数据整理 →</button></section>

  return (
    <div className="overview-workbench">
      <section className="notice-banner overview-sample-banner"><div className="notice-icon"><Database size={17} /></div><div><strong>已连接本地时间序列样本</strong><span>{series?.name ?? datasets[0].name} · {datasets[0].source_name} · 现货样本，不是实时期货合约行情</span></div><span className="notice-badge">{instrument} · {points.length.toLocaleString()} 点</span></section>
      {datasets.length > 1 && <label className="overview-dataset-picker">查看序列<select value={selectedId ?? ''} onChange={(event) => setSelectedId(Number(event.target.value))}>{datasets.map((dataset) => <option value={dataset.id} key={dataset.id}>{dataset.name}</option>)}</select></label>}
      <section className="metric-grid overview-metrics">
        <article className="metric-card"><div className="metric-top"><span>最新样本值</span><span className="metric-icon"><Activity size={17} /></span></div><div className="metric-value">{latest ? latest.value.toLocaleString(undefined, { maximumFractionDigits: 4 }) : '—'}</div><div className="metric-bottom"><span>{series?.unit ?? datasets[0].unit}</span><span className="unavailable-label">历史样本</span></div></article>
        <article className="metric-card"><div className="metric-top"><span>最后观测日期</span></div><div className="metric-value overview-date">{latest ? new Date(latest.observed_at).toLocaleDateString() : '—'}</div><div className="metric-bottom"><span>{series?.frequency ?? datasets[0].frequency}频</span></div></article>
        <article className="metric-card"><div className="metric-top"><span>有效观测点</span></div><div className="metric-value">{points.length.toLocaleString()}</div><div className="metric-bottom"><span>已存入本地 PostgreSQL</span></div></article>
        <article className="metric-card overview-action-card"><div><strong>基线预测</strong><span>使用当前选中的时间序列</span></div><button className="text-button" onClick={onOpenForecast}>打开预测中心 <ArrowRight size={14} /></button></article>
      </section>
      <section className="panel chart-panel overview-chart-panel">
        <div className="panel-heading"><div><h2>{series?.name ?? datasets[0].name}</h2><p>{instrument} · {series?.frequency ?? datasets[0].frequency}频 · {series?.unit ?? datasets[0].unit} · {points.length.toLocaleString()} 个观测点</p></div></div>
        {points.length > 1 ? <div className="series-chart"><svg viewBox="0 0 900 280" role="img" aria-label={`${series?.name} 时间序列图`} preserveAspectRatio="none"><line x1="48" x2="868" y1="244" y2="244" /><line x1="48" x2="868" y1="134" y2="134" /><line x1="48" x2="868" y1="24" y2="24" /><polyline points={plotted} /></svg><div className="series-axis"><span>{new Date(points[0].observed_at).toLocaleDateString()}</span><span>{new Date(latest!.observed_at).toLocaleDateString()}</span></div></div> : <div className="workbench-empty"><Database size={22} /><strong>样本点不足，暂不能绘图</strong></div>}
      </section>
    </div>
  )
}
