# 沥青期货智能分析平台

面向 BU（上海期货交易所石油沥青）的项目起始骨架。当前提供可导航的前端页面、版本化 API 空响应、数据/模型/连接器分层及数据字典模板；尚未接入真实行情、库存、资讯或预测模型。页面对尚无数据的区域明确显示“数据暂缺”，不会把演示数值显示成真实市场数据。

## 技术结构

- `frontend/`：React + TypeScript + Vite 单页应用
- `backend/`：FastAPI 服务及版本化 API 路由
- `backend/app/connectors/`：按数据源隔离的接入适配器
- `backend/app/domain/`：品种、合约、序列和预测规则
- `backend/app/repositories/`：持久化访问边界
- `backend/app/services/`：用例/业务编排
- `backend/app/schemas/`：API 与数据契约
- `backend/app/models/`：模型注册、验证与预测接口
- `data/`：原始数据、清洗数据与数据字典的本地占位目录
- `models/`：训练、验证与模型产物的占位目录
- `docs/`：需求记录与后续数据/API设计文档

## 本地启动

需要 Node.js 20.19+ 或 22.12+、Python 3.11+。

### 后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
uvicorn app.main:app --reload --port 8000
```

API 文档：`http://localhost:8000/docs`。基础接口：

- `GET /api/v1/health`：服务健康状态
- `GET /api/v1/overview`：总览空状态
- `GET /api/v1/market`：行情
- `GET /api/v1/fundamentals`：基本面
- `GET /api/v1/forecasts`：预测
- `GET /api/v1/contracts`：合约
- `GET /api/v1/news`：资讯
- `GET /api/v1/models`：模型

业务接口暂时返回明确的不可用状态与空列表。开始接入数据后，再为各模块增加服务、仓储和来源 Connector；避免把数据逻辑写在路由函数中。

### 前端

```bash
cd frontend
npm install
npm run dev
```

前端默认请求 `http://localhost:8000`，可通过 `VITE_API_BASE_URL` 覆盖。

## 当前页面骨架

- 市场总览
- 基本面 Profile
- 行情分析
- 预测中心（5m、30m、1D、1M、3M）
- 模型详情
- 新闻与事件

## 数据与模型约束

- 数据源接入前，缺失内容以“数据暂缺”呈现。
- 持久化层应区分原始数据、清洗数据、特征与预测；保留来源、单位、频率和时间戳。
- 时间序列验证需保持时间顺序，并保留独立测试区间；避免未来信息泄漏。
- 预测价格、概率、区间和模型指标必须来自可验证的模型结果。
- 使用 `data/data-dictionary-template.csv` 记录字段、单位、频率、来源、观测/发布时间、可用时间、转换规则、质量规则和授权备注。
- 需求基线：`docs/requirements.md`；完整需求记录：`outputs/期货智能分析平台_需求记录.md`。
- 项目需求基线见 [`docs/requirements.md`](docs/requirements.md)。

## 下一步建议

按需求基线先完成 BU 数据源调查与数据字典，再确定存储、采集频率和 API 字段；之后接入真实行情与基本面数据，再逐步实现特征、基线模型、时间序列验证与预测展示。数据库选型尚未冻结，当前没有绑定 PostgreSQL 或其他持久化产品。
