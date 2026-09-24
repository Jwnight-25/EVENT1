# 沥青期货智能分析平台

面向 BU（上海期货交易所石油沥青）的本机项目。当前已提供可导航前端、版本化 FastAPI 接口、PostgreSQL 数据层、CSV 时间序列导入与图表、最后观测值基线预测和滚动验证，以及 AI 解释接口。尚未接入自动免费数据源；预测结果明确标注基线模型及验证状态。

## 技术结构

- `frontend/`：React + TypeScript + Vite 单页应用
- `backend/`：FastAPI 服务及版本化 API 路由
- `backend/app/connectors/`：按数据源隔离的接入适配器
- `backend/app/domain/`：品种、合约、序列和预测规则
- `backend/app/repositories/`：持久化访问边界
- `backend/app/services/`：用例/业务编排
- `backend/app/schemas/`：API 与数据契约
- `backend/app/models/`：模型注册、验证与预测接口
- `backend/app/ai/providers/`：解释服务 provider（默认 GPT-6 Luna）
- `backend/migrations/`：Alembic 数据库迁移
- `data/`：原始数据、清洗数据与数据字典的本地占位目录
- `models/`：训练、验证与模型产物的占位目录
- `docs/`：需求记录与后续数据/API设计文档

## 本地启动

需要 Node.js 20.19+ 或 22.12+、Python 3.11+，以及本机 PostgreSQL 服务。当前不依赖 Docker。

### 后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
cp .env.example .env
# 编辑 .env：设置本地 DATABASE_URL；如需 AI 解释，再设置 OPENAI_API_KEY
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

先在本机 PostgreSQL 中创建 `bitumen_research` 数据库，并在 `.env` 中填入实际用户名和密码。`.env` 不会提交到 Git。数据库尚未配置时，健康检查仍可访问，数据导入和预测记录接口会返回清楚的配置错误。

API 文档：`http://localhost:8000/docs`。接口清单和 CSV 导入口径见 [`docs/api-contracts.md`](docs/api-contracts.md)。基础接口：

- `GET /api/v1/health`：服务健康状态
- `GET /api/v1/overview`：总览空状态
- `GET /api/v1/market`：行情
- `GET /api/v1/fundamentals`：基本面
- `GET /api/v1/forecasts`：预测
- `GET /api/v1/contracts`：合约
- `GET /api/v1/news`：资讯
- `GET /api/v1/models`：模型
- `GET /api/v1/datasets`、`POST /api/v1/datasets/import`：数据集与 CSV 时间序列导入
- `GET /api/v1/datasets/{id}/observations`、`/summary`、`/chart`：数据点查询与图表序列
- `GET /api/v1/ai/capabilities`、`POST /api/v1/ai/explanations`：AI配置与已验证预测结果解释
- `POST /api/v1/forecasts/run`：运行最后观测值延续基线并进行时间顺序滚动验证

市场、基本面、资讯与模型目录接口在真实来源或模型接入前返回明确空状态。CSV 导入支持 UTF-8/GB18030；时间列、数值列、单位、频率、来源及时间区均由导入请求声明。

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
- OpenAI API 是单独计费的云服务，不包含在 ChatGPT 订阅内；配置密钥后，AI 解释和可选网页搜索按实际使用量计费。默认模型为 `gpt-6-luna`。
- 项目需求基线见 [`docs/requirements.md`](docs/requirements.md)。
- 本次基础底座变更记录见 [`docs/CHANGELOG.md`](docs/CHANGELOG.md)。

## 下一步建议

下一步按需求基线调查免费 BU 数据源，完善数据清洗、质量规则和多频率验证；之后可接入移动平均等候选基线及更复杂模型、新闻源和实时推送。
