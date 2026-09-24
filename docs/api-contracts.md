# API 与服务边界

Base URL：`http://localhost:8000/api/v1`。所有返回使用 JSON，时间戳以带时区的 ISO 8601 表示。当前 API 仅供本机单用户使用，没有登录、推送或自动交易。

## 数据集与图表

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | `/datasets` | 列出已导入时间序列 |
| POST | `/datasets/import` | 导入 CSV；调用方指定日期/时间列、数值列、单位、频率、来源及时区 |
| GET | `/datasets/{id}` | 读取数据集口径和来源元信息 |
| GET | `/datasets/{id}/summary` | 返回数量、首末时间和数值范围 |
| GET | `/datasets/{id}/observations` | 查询原始时间和值，支持起止时间及分页 |
| GET | `/datasets/{id}/chart` | 返回前端折线图所需的 x/y 字段和点集 |

CSV首版要求包含标题行和可指定的两列，编码支持 UTF-8 与 GB18030。日期没有时区时按 `Asia/Shanghai` 解释并转为带时区时间存储。数值保留原始文本与解析后的数值。相同数据集的重复时间点不会重复写入。

## 预测与 AI

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | `/forecasts` | 读取已保存的预测运行 |
| POST | `/forecasts/run` | 运行最后观测值延续基线，保存预测点与时间顺序滚动验证摘要 |
| GET | `/forecasts/{id}` | 读取单次预测运行及验证摘要 |
| GET | `/forecasts/{id}/points` | 读取该次运行的预测点和实际值 |
| GET | `/ai/capabilities` | 检查 provider、模型、密钥配置状态及联网搜索配置 |
| POST | `/ai/explanations` | 用云端 LLM 解释服务端读取的已验证结果，并可联网搜索补充背景 |
| GET | `/ai/explanations/{id}` | 读取保存的解释和来源 |

OpenAI GPT-6 Luna 是默认解释 provider。网页搜索可关闭，启用后会有单独搜索工具费用和搜索内容 token 费用。解释请求只提交已验证的 `forecast_run_id`，服务端从数据库取模型、验证指标和预测点，不接受浏览器直接注入预测数字。AI解释接口不会创建或改写价格、方向、概率、区间、指标等量化预测；数值预测由时间序列基线或后续模型提供。

首版基线为 `naive_baseline`（最后观测值延续）。预测步数按请求周期与数据中位采样间隔估算；运行前检查样本量，并用滚动起点回测计算 MAE、RMSE、MAPE 和经验绝对误差 P90 区间。周末、节假日和非规则时间戳的处理仍需针对具体数据源完善，结果会保留验证状态。

Gemini 和 Claude 仅作为 provider 替换位预留；当前切换到它们会明确提示 adapter 尚未实现。Provider 密钥只从后端环境读取。

## 后续路由组

- `/market`：行情及合约序列
- `/fundamentals`：库存、产量、开工、贸易、需求和成本序列
- `/contracts`：合约主数据及换月
- `/news`：新闻/事件聚合
- `/models`：模型注册和训练诊断
- `/health`、`/overview`：服务状态和总览

这些路由在数据源和模型明确前返回结构化空状态，不伪造数据。
