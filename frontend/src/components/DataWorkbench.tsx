import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { Database, FileUp, RefreshCw } from 'lucide-react'
import { getChartSeries, importTimeSeriesCsv, listDatasets } from '../api/client'
import type { ChartSeries, Dataset } from '../api/types'

function splitCsvHeader(line: string): string[] {
  const cells: string[] = []
  let cell = ''
  let quoted = false
  for (let index = 0; index < line.length; index += 1) {
    const char = line[index]
    if (char === '"' && line[index + 1] === '"' && quoted) { cell += '"'; index += 1 }
    else if (char === '"') quoted = !quoted
    else if (char === ',' && !quoted) { cells.push(cell.trim()); cell = '' }
    else cell += char
  }
  cells.push(cell.trim())
  return cells
}

export default function DataWorkbench() {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [series, setSeries] = useState<ChartSeries | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [columns, setColumns] = useState<string[]>([])
  const [timeColumn, setTimeColumn] = useState('')
  const [valueColumn, setValueColumn] = useState('')
  const [name, setName] = useState('')
  const [unit, setUnit] = useState('元/吨')
  const [frequency, setFrequency] = useState('日')
  const [sourceName, setSourceName] = useState('手动导入')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  async function refreshDatasets(preferredId?: number) {
    const items = await listDatasets()
    setDatasets(items)
    const nextId = preferredId ?? selectedId ?? items[0]?.id ?? null
    setSelectedId(nextId)
    if (nextId) setSeries(await getChartSeries(nextId))
    else setSeries(null)
  }

  useEffect(() => {
    refreshDatasets().catch((reason: unknown) => setError(reason instanceof Error ? reason.message : '数据集读取失败'))
  // Initial loading only; subsequent refreshes are triggered by user actions.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const points = series?.points ?? []
  const plotted = useMemo(() => {
    if (points.length < 2) return ''
    const times = points.map((point) => new Date(point.observed_at).getTime())
    const values = points.map((point) => point.value)
    const minX = times[0]
    const maxX = times[times.length - 1]
    const minY = Math.min(...values)
    const maxY = Math.max(...values)
    const spanX = maxX - minX || 1
    const spanY = maxY - minY || 1
    return points.map((point, index) => {
      const x = 48 + ((times[index] - minX) / spanX) * 820
      const y = 24 + (1 - (point.value - minY) / spanY) * 220
      return `${x.toFixed(1)},${y.toFixed(1)}`
    }).join(' ')
  }, [points])

  async function chooseFile(nextFile: File | null) {
    setFile(nextFile)
    setMessage('')
    setError('')
    if (!nextFile) return
    setName(nextFile.name.replace(/\.csv$/i, ''))
    try {
      const bytes = await nextFile.slice(0, 256 * 1024).arrayBuffer()
      let text: string
      try { text = new TextDecoder('utf-8', { fatal: true }).decode(bytes) }
      catch { text = new TextDecoder('gb18030').decode(bytes) }
      const header = text.split(/\r?\n/, 1)[0]
      const nextColumns = splitCsvHeader(header.replace(/^\uFEFF/, ''))
      setColumns(nextColumns)
      setTimeColumn(nextColumns[0] ?? '')
      setValueColumn(nextColumns[1] ?? '')
    } catch {
      setError('无法读取 CSV 文件的列名，请检查文件编码。')
    }
  }

  async function submitImport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!file) return
    setBusy(true)
    setError('')
    setMessage('')
    try {
      const result = await importTimeSeriesCsv(file, {
        name, unit, frequency, source_name: sourceName, time_column: timeColumn, value_column: valueColumn,
      })
      await refreshDatasets(result.dataset.id)
      setMessage(`已导入 ${result.rows_imported} 行，跳过重复时间点 ${result.rows_duplicate} 行。`)
      setFile(null)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '导入失败')
    } finally {
      setBusy(false)
    }
  }

  async function selectDataset(value: string) {
    const id = Number(value)
    setSelectedId(id)
    setError('')
    try { setSeries(await getChartSeries(id)) }
    catch (reason) { setError(reason instanceof Error ? reason.message : '序列读取失败') }
  }

  return (
    <div className="data-workbench">
      <section className="panel import-panel">
        <div className="panel-heading"><div><h2>导入时间序列</h2><p>支持 UTF-8 / GB18030 CSV，首行作为列名，单文件最大 25 MB。</p></div><FileUp size={19} /></div>
        <form className="import-form" onSubmit={submitImport}>
          <label className="file-picker">选择 CSV 文件<input type="file" accept=".csv,text/csv" onChange={(event) => chooseFile(event.target.files?.[0] ?? null)} /></label>
          <span className="selected-file">{file?.name ?? '尚未选择文件'}</span>
          <div className="form-grid">
            <label>数据集名称<input required value={name} onChange={(event) => setName(event.target.value)} /></label>
            <label>来源<input required value={sourceName} onChange={(event) => setSourceName(event.target.value)} /></label>
            <label>时间列<select required value={timeColumn} onChange={(event) => setTimeColumn(event.target.value)}>{columns.map((column) => <option key={column}>{column}</option>)}</select></label>
            <label>数值列<select required value={valueColumn} onChange={(event) => setValueColumn(event.target.value)}>{columns.map((column) => <option key={column}>{column}</option>)}</select></label>
            <label>单位<input required value={unit} onChange={(event) => setUnit(event.target.value)} /></label>
            <label>频率<input required value={frequency} onChange={(event) => setFrequency(event.target.value)} placeholder="如：5分钟、日、周" /></label>
          </div>
          <div className="import-actions"><span>无时区时间按中国标准时间解析。</span><button className="refresh-button" type="submit" disabled={!file || busy}>{busy ? '正在导入…' : '导入并查看'}</button></div>
          {message && <p className="form-feedback success">{message}</p>}
          {error && <p className="form-feedback error">{error}</p>}
        </form>
      </section>

      <section className="panel series-panel">
        <div className="panel-heading"><div><h2>时间序列图表</h2><p>{series ? `${series.frequency} · ${series.unit} · ${points.length.toLocaleString()} 个点` : '导入或选择一个数据集以查看折线图'}</p></div>
          <div className="series-actions"><select aria-label="选择数据集" value={selectedId ?? ''} onChange={(event) => selectDataset(event.target.value)}><option value="" disabled>选择数据集</option>{datasets.map((dataset) => <option key={dataset.id} value={dataset.id}>{dataset.name}</option>)}</select><button className="icon-button" aria-label="刷新数据" onClick={() => refreshDatasets().catch((reason: unknown) => setError(reason instanceof Error ? reason.message : '刷新失败'))}><RefreshCw size={16} /></button></div>
        </div>
        {points.length > 1 ? <div className="series-chart"><svg viewBox="0 0 900 280" role="img" aria-label={`${series?.name} 时间序列折线图`} preserveAspectRatio="none"><line x1="48" x2="868" y1="244" y2="244" /><line x1="48" x2="868" y1="134" y2="134" /><line x1="48" x2="868" y1="24" y2="24" /><polyline points={plotted} /></svg><div className="series-axis"><span>{new Date(points[0].observed_at).toLocaleString()}</span><span>{new Date(points[points.length - 1].observed_at).toLocaleString()}</span></div></div> : <div className="workbench-empty"><Database size={22} /><strong>{points.length === 1 ? '当前数据集只有一个数据点' : '还没有可展示的数据'}</strong><span>{points.length === 1 ? '至少需要两个时间点绘制折线。' : '导入时间列和数值列后，序列会显示在这里。'}</span></div>}
      </section>
    </div>
  )
}
