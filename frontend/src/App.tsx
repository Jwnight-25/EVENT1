import { useEffect, useState } from 'react'
import {
  Activity, BarChart3, Bell, ChevronDown, CircleHelp, Database, FileUp,
  FileChartColumnIncreasing, LayoutDashboard, Newspaper,
  Settings2, Waves,
} from 'lucide-react'
import DataWorkbench from './components/DataWorkbench'
import ForecastWorkbench from './components/ForecastWorkbench'
import OverviewWorkbench from './components/OverviewWorkbench'

type InstrumentCode = 'BU' | 'LC'

const instruments: Record<InstrumentCode, { name: string; exchange: string }> = {
  BU: { name: '石油沥青', exchange: '上海期货交易所' },
  LC: { name: '碳酸锂', exchange: '广州期货交易所' },
}

const navItems = [
  { label: '市场总览', icon: LayoutDashboard },
  { label: '行情分析', icon: Activity },
  { label: '基本面 Profile', icon: Database },
  { label: '预测中心', icon: Waves },
  { label: '模型详情', icon: FileChartColumnIncreasing },
  { label: '新闻与事件', icon: Newspaper },
  { label: '数据整理', icon: FileUp },
]

const pageDetails: Record<string, { endpoint: string; intro: string; sections: string[] }> = {
  '市场总览': { endpoint: 'overview', intro: '聚焦所选期货品种的市场行情、产业基本面与多周期模型研究。', sections: ['主力合约行情', '多周期预测', '库存概览', '近期资讯'] },
  '行情分析': { endpoint: 'market', intro: '查看所选品种主力及近月合约行情、成交与期限结构。', sections: ['分时与K线', '成交量与持仓', '技术指标', '多合约对比'] },
  '基本面 Profile': { endpoint: 'fundamentals', intro: '追踪库存、供应、生产、贸易、需求与成本数据。', sections: ['总量及地区库存', '产量与开工率', '进出口与需求', '原油及季节性'] },
  '预测中心': { endpoint: 'forecasts', intro: '按五个时间周期查看经验证的模型结果与历史表现。', sections: ['短期预测 · 5m / 30m / 1D', '中长期预测 · 1M / 3M', '模型选择与主要驱动', '历史验证与不确定性'] },
  '模型详情': { endpoint: 'models', intro: '集中查看模型版本、训练过程、诊断和样本外评估。', sections: ['模型与数据窗口', '真实值与预测值 / Loss', '残差及时域 / 频域诊断', '特征重要性与评估'] },
  '新闻与事件': { endpoint: 'news', intro: '汇总所选品种及其产业链相关资讯与事件。', sections: ['最新资讯', '类别与关联主题', '事件时间线', '来源与更新时间'] },
  '数据整理': { endpoint: 'datasets', intro: '导入免费的时间序列 CSV，维护来源口径并查看序列图表。', sections: [] },
}

type ApiStatus = 'loading' | 'connected' | 'unavailable'

function App() {
  const [active, setActive] = useState('市场总览')
  const [instrument, setInstrument] = useState<InstrumentCode>('LC')
  const [apiStatus, setApiStatus] = useState<ApiStatus>('loading')
  const [dataMessage, setDataMessage] = useState('尚无已验证数据')

  useEffect(() => {
    const base = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '')
    fetch(`${base}/api/v1/health`)
      .then((response) => { if (!response.ok) throw new Error('API unavailable'); setApiStatus('connected') })
      .catch(() => setApiStatus('unavailable'))
    fetch(`${base}/api/v1/${pageDetails[active].endpoint}?instrument=${instrument}`)
      .then((response) => {
        if (!response.ok) throw new Error(`该模块暂不可用（${response.status}）`)
        return response.json()
      })
      .then((payload) => {
        setDataMessage(payload.message ?? (Array.isArray(payload) ? `已读取 ${payload.length} 个数据集` : '模块已连接'))
      })
      .catch((reason: unknown) => setDataMessage(reason instanceof Error ? reason.message : '模块连接失败'))
  }, [active, instrument])

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-lockup">
          <div className="brand-mark"><BarChart3 size={19} /></div>
          <div><strong>期货研究终端</strong><span>FUTURES INTELLIGENCE</span></div>
        </div>
        <div className="workspace-label">研究工作台</div>
        <select className="instrument-select" aria-label="选择期货品种" value={instrument} onChange={(event) => setInstrument(event.target.value as InstrumentCode)}><option value="BU">石油沥青 · BU</option><option value="LC">碳酸锂 · LC</option></select>
        <div className="nav-caption">工作空间</div>
        <nav>
          {navItems.map(({ label, icon: Icon }) => (
            <button key={label} className={`nav-item ${active === label ? 'active' : ''}`} onClick={() => setActive(label)}>
              <Icon size={17} strokeWidth={1.8} /><span>{label}</span>
              {label === '预测中心' && <span className="nav-tag">5</span>}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="source-card"><div className="source-title"><span className={`status-dot ${apiStatus}`} />API 服务</div><span>{apiStatus === 'connected' ? '已连接' : apiStatus === 'loading' ? '连接中' : '未连接'}</span></div>
          <button className="nav-item"><Settings2 size={17} /><span>设置</span></button>
          <button className="nav-item"><CircleHelp size={17} /><span>帮助与文档</span></button>
          <div className="user-card"><div className="avatar">研</div><div><strong>研究工作区</strong><span>本地开发环境</span></div><ChevronDown size={14} /></div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumb">工作空间 <span>/</span> <strong>{active}</strong></div>
          <div className="top-actions"><span className="env-pill">开发环境</span><select className="top-instrument-select" aria-label="选择期货品种" value={instrument} onChange={(event) => setInstrument(event.target.value as InstrumentCode)}><option value="BU">BU</option><option value="LC">LC</option></select><button className="icon-button" aria-label="通知"><Bell size={18} /><i /></button><div className="top-divider" /><span className="date-label">{instrument} · {instruments[instrument].exchange}</span></div>
        </header>
        <div className="page-content">
          <div className="page-heading">
            <div><div className="eyebrow">FUTURES · RESEARCH PLATFORM</div><h1>{active}</h1><p>{pageDetails[active].intro}</p></div>
            <div className="heading-actions"><button className="secondary-button"><span className="live-dot" />研究品种 <strong>{instrument} · {instruments[instrument].name}</strong><ChevronDown size={15} /></button><button className="refresh-button" title="数据源接入后启用"><Activity size={16} /> 数据更新</button></div>
          </div>

          {active === '数据整理' ? <DataWorkbench instrument={instrument} /> : active === '预测中心' ? <ForecastWorkbench instrument={instrument} /> : active === '市场总览' ? <OverviewWorkbench instrument={instrument} onOpenData={() => setActive('数据整理')} onOpenForecast={() => setActive('预测中心')} /> : <>
            <section className="notice-banner"><div className="notice-icon"><Database size={17} /></div><div><strong>该模块已建立，数据源尚未接入</strong><span>{dataMessage}。当前页面不展示模拟市场数据。</span></div><span className="notice-badge">等待配置</span></section>
            <section className="module-grid">
              {pageDetails[active].sections.map((section) => <article className="panel module-card" key={section}><div className="panel-heading"><div><h2>{section}</h2><p>{instrument} {instruments[instrument].name} · 数据接入后展示</p></div><span className="unavailable-label">数据暂缺</span></div><EmptyStrip icon={<Database size={19} />} label="等待可验证数据" detail="接入数据来源并完成口径、时间戳与质量校验后启用。" /></article>)}
            </section>
          </>}

          <footer className="page-footer"><span><span className={`status-dot ${apiStatus === 'connected' ? 'connected' : 'disconnected'}`} />{apiStatus === 'connected' ? 'API 服务已连接' : 'API 服务未连接'}</span><span>{instrument} {instruments[instrument].name} · 本地数据库</span><span>演示环境不会显示模拟市场数值</span></footer>
        </div>
      </main>
    </div>
  )
}

function EmptyStrip({ icon, label, detail }: { icon: React.ReactNode; label: string; detail: string }) {
  return <div className="empty-strip"><div className="strip-icon">{icon}</div><div><strong>{label}</strong><span>{detail}</span></div></div>
}

export default App
