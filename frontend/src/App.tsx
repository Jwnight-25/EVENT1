import { useEffect, useState } from 'react'
import {
  Activity, BarChart3, Bell, ChevronDown, CircleHelp, Database,
  FileChartColumnIncreasing, Gauge, LayoutDashboard, Newspaper,
  Settings2, Waves,
} from 'lucide-react'

const navItems = [
  { label: '市场总览', icon: LayoutDashboard },
  { label: '行情分析', icon: Activity },
  { label: '基本面 Profile', icon: Database },
  { label: '预测中心', icon: Waves },
  { label: '模型详情', icon: FileChartColumnIncreasing },
  { label: '新闻与事件', icon: Newspaper },
]

const pageDetails: Record<string, { endpoint: string; intro: string; sections: string[] }> = {
  '市场总览': { endpoint: 'overview', intro: '聚焦沥青期货市场、产业基本面与多周期模型研究。', sections: ['主力合约行情', '多周期预测', '库存概览', '近期资讯'] },
  '行情分析': { endpoint: 'market', intro: '查看 BU 主力及近月合约行情、成交与期限结构。', sections: ['分时与K线', '成交量与持仓', '技术指标', '多合约对比'] },
  '基本面 Profile': { endpoint: 'fundamentals', intro: '追踪库存、供应、生产、贸易、需求与成本数据。', sections: ['总量及地区库存', '产量与开工率', '进出口与需求', '原油及季节性'] },
  '预测中心': { endpoint: 'forecasts', intro: '按五个时间周期查看经验证的模型结果与历史表现。', sections: ['短期预测 · 5m / 30m / 1D', '中长期预测 · 1M / 3M', '模型选择与主要驱动', '历史验证与不确定性'] },
  '模型详情': { endpoint: 'models', intro: '集中查看模型版本、训练过程、诊断和样本外评估。', sections: ['模型与数据窗口', '真实值与预测值 / Loss', '残差及时域 / 频域诊断', '特征重要性与评估'] },
  '新闻与事件': { endpoint: 'news', intro: '汇总沥青、原油、炼厂、供需、施工与政策资讯。', sections: ['最新资讯', '类别与关联主题', '事件时间线', '来源与更新时间'] },
}

type ApiStatus = 'loading' | 'connected' | 'unavailable'

function App() {
  const [active, setActive] = useState('市场总览')
  const [apiStatus, setApiStatus] = useState<ApiStatus>('loading')
  const [dataMessage, setDataMessage] = useState('尚无已验证数据')

  useEffect(() => {
    const base = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
    fetch(`${base}/api/v1/${pageDetails[active].endpoint}`)
      .then((response) => {
        if (!response.ok) throw new Error('API unavailable')
        return response.json()
      })
      .then((payload) => {
        setApiStatus('connected')
        setDataMessage(payload.message ?? '尚无已验证数据')
      })
      .catch(() => setApiStatus('unavailable'))
  }, [active])

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-lockup">
          <div className="brand-mark"><BarChart3 size={19} /></div>
          <div><strong>沥青研究终端</strong><span>BITUMEN INTELLIGENCE</span></div>
        </div>
        <div className="workspace-label">研究工作台</div>
        <button className="instrument-select"><span className="instrument-dot" />石油沥青 <b>BU</b><ChevronDown size={15} /></button>
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
          <div className="top-actions"><span className="env-pill">开发环境</span><button className="icon-button" aria-label="通知"><Bell size={18} /><i /></button><div className="top-divider" /><span className="date-label">BU · 上海期货交易所</span></div>
        </header>
        <div className="page-content">
          <div className="page-heading">
            <div><div className="eyebrow">BITUMEN FUTURES · RESEARCH PLATFORM</div><h1>{active}</h1><p>{pageDetails[active].intro}</p></div>
            <div className="heading-actions"><button className="secondary-button"><span className="live-dot" />主力合约 <strong>BU — 暂无数据</strong><ChevronDown size={15} /></button><button className="refresh-button" title="数据源接入后启用"><Activity size={16} /> 数据更新</button></div>
          </div>

          {active === '市场总览' ? <>

          <section className="notice-banner"><div className="notice-icon"><Database size={17} /></div><div><strong>数据源尚未接入</strong><span>当前为项目基础骨架。接入并验证行情、库存及模型数据后，此处将展示实时研究结果。</span></div><span className="notice-badge">等待配置</span></section>

          <section className="metric-grid">
            <Metric label="主力合约价格" unit="BU" icon={<Gauge size={17} />} />
            <Metric label="现货与基差" unit="现货 − 期货" icon={<Activity size={17} />} />
            <Metric label="总库存" unit="最新发布值" icon={<Database size={17} />} />
            <Metric label="预测信号" unit="5 个周期" icon={<Waves size={17} />} />
          </section>

          <section className="content-grid">
            <article className="panel chart-panel">
              <div className="panel-heading"><div><h2>主力合约行情</h2><p>价格走势 · 日线</p></div><button className="period-select">日线 <ChevronDown size={14} /></button></div>
              <EmptyChart />
              <div className="chart-legend"><span><i className="legend-line" />BU 主力</span><span className="muted">数据源接入后展示</span></div>
            </article>
            <article className="panel forecast-panel">
              <div className="panel-heading"><div><h2>多周期预测</h2><p>模型结果与历史验证表现</p></div><button className="text-button" onClick={() => setActive('预测中心')}>查看详情 <span>→</span></button></div>
              <div className="forecast-list">{['5 分钟', '30 分钟', '1 天', '1 个月', '3 个月'].map((period) => <div className="forecast-row" key={period}><span className="period-name">{period}</span><span className="forecast-empty">等待模型数据</span><span className="signal-chip">—</span></div>)}</div>
              <div className="panel-footnote">预测方向、价格区间与置信信息仅在模型输出可验证时展示。</div>
            </article>
          </section>

          <section className="lower-grid">
            <article className="panel lower-panel"><div className="panel-heading"><div><h2>库存概览</h2><p>全国与区域库存 · 按数据源发布频率更新</p></div><button className="text-button" onClick={() => setActive('基本面 Profile')}>基本面 <span>→</span></button></div><EmptyStrip icon={<Database size={19} />} label="尚无库存数据" detail="接入库存来源后展示总量、区域分布与周度变化。" /></article>
            <article className="panel lower-panel"><div className="panel-heading"><div><h2>近期资讯</h2><p>沥青 · 原油 · 炼厂 · 供需与政策</p></div><button className="text-button" onClick={() => setActive('新闻与事件')}>更多资讯 <span>→</span></button></div><EmptyStrip icon={<Newspaper size={19} />} label="尚无资讯数据" detail="接入资讯来源后按发布时间倒序展示。" /></article>
          </section>

          </> : <>
            <section className="notice-banner"><div className="notice-icon"><Database size={17} /></div><div><strong>该模块已建立，数据源尚未接入</strong><span>{dataMessage}。当前页面不展示模拟市场数据。</span></div><span className="notice-badge">等待配置</span></section>
            <section className="module-grid">
              {pageDetails[active].sections.map((section) => <article className="panel module-card" key={section}><div className="panel-heading"><div><h2>{section}</h2><p>BU 石油沥青 · 数据接入后展示</p></div><span className="unavailable-label">数据暂缺</span></div><EmptyStrip icon={<Database size={19} />} label="等待可验证数据" detail="接入数据来源并完成口径、时间戳与质量校验后启用。" /></article>)}
            </section>
          </>}

          <footer className="page-footer"><span><span className={`status-dot ${apiStatus === 'connected' ? 'connected' : 'disconnected'}`} />{apiStatus === 'connected' ? 'API 服务已连接' : 'API 服务未连接'}</span><span>BU 石油沥青 · 数据更新时间：—</span><span>演示环境不会显示模拟市场数值</span></footer>
        </div>
      </main>
    </div>
  )
}

function Metric({ label, unit, icon }: { label: string; unit: string; icon: React.ReactNode }) {
  return <article className="metric-card"><div className="metric-top"><span>{label}</span><span className="metric-icon">{icon}</span></div><div className="metric-value">—</div><div className="metric-bottom"><span>{unit}</span><span className="unavailable-label">数据暂缺</span></div></article>
}

function EmptyChart() {
  return <div className="empty-chart"><div className="chart-grid-lines"><i /><i /><i /><i /></div><div className="chart-empty-message"><div className="chart-empty-icon"><BarChart3 size={20} /></div><strong>等待接入行情数据</strong><span>此图表将在可验证的 BU 行情数据接入后生成</span></div><div className="axis-labels"><span>—</span><span>—</span><span>—</span><span>—</span><span>—</span></div></div>
}

function EmptyStrip({ icon, label, detail }: { icon: React.ReactNode; label: string; detail: string }) {
  return <div className="empty-strip"><div className="strip-icon">{icon}</div><div><strong>{label}</strong><span>{detail}</span></div></div>
}

export default App
