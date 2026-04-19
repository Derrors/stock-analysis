# A 股股票市场分析 Skill

专为 OpenClaw 等智能体设计的 A 股股票分析技能，提供个股分析和市场分析两大核心能力。

基于 [daily\_stock\_analysis](https://github.com/ZhuLinsen/daily_stock_analysis) 项目精简重写，去除 WebUI、通知推送、Agent 问股等非核心功能，聚焦分析能力本身。

## 功能特性

### 个股分析

输入股票代码，输出结构化分析结果：

- **技术面分析**：MA5/MA10/MA20/MA60 均线、多头排列判断、乖离率、量比
- **筹码分布**：获利比例、平均成本、集中度
- **舆情情报**：多引擎新闻搜索（SerpAPI / Tavily / Brave / Bocha）
- **实时行情**：当前价、涨跌幅、成交量、换手率等
- **分析结论**：一句话核心结论 + 评分 + 操作方向 + 精确买卖点位 + 操作检查清单 + 买卖策略

### 市场分析

每日 A 股市场复盘：

- **主要指数**：上证指数、深证成指、创业板指
- **市场统计**：涨跌家数、涨停跌停数
- **板块排名**：领涨 / 领跌板块 Top5
- **分析结论**：市场情绪判断 + 操作建议 + 完整复盘报告

### 多源数据架构

行情数据采用三级自动容灾策略，所有数据源均免费、无需 API Token：

| 优先级 | 数据源 | 说明 |
| --- | --- | --- |
| 0（最优先） | **Efinance** | 基于东财接口，覆盖日 K、实时行情、板块排名、市场统计 |
| 1（备选） | **AkShare** | 东财 + 新浪双通道，额外支持筹码分布 |
| 2（兜底） | **Pytdx** | 直连通达信行情服务器，支持日 K、实时行情、指数数据 |

任意数据源异常时自动切换到下一级，无需人工干预。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 API Key：

```env
# LLM 配置（必填）— 支持 DeepSeek 和 OpenAI 兼容模型
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=your-api-key-here
LLM_MODEL=deepseek-chat

# 新闻搜索（至少配置一个，可选）
SERPAPI_KEY=
TAVILY_KEY=
BRAVE_KEY=
BOCHA_KEY=
```

> 行情数据源（Efinance / AkShare / Pytdx）均为免费接口，无需配置任何 Token。

### 3. 调用分析

#### 方式一：CLI 脚本

```bash
# 个股分析
python3 scripts/analyze_stock.py 600519

# 市场分析
python3 scripts/analyze_market.py
```

#### 方式二：Python API

```python
import asyncio
from src.index import analyze_stock, analyze_market

# 个股分析 — 输入 A 股代码
result = asyncio.run(analyze_stock("600519"))
print(result.core_conclusion)   # 一句话核心结论
print(result.action)            # 买入/观望/卖出
print(result.buy_price)         # 买入价
print(result.stop_loss_price)   # 止损价
print(result.target_price)      # 目标价
print(result.raw_report)        # 完整分析报告

# 市场分析
result = asyncio.run(analyze_market())
print(result.core_conclusion)   # 市场核心结论
print(result.sentiment)         # 偏多/中性/偏空
print(result.raw_report)        # 完整复盘报告
```

#### 方式三：OpenClaw Handler

```python
from src.index import handler

# 个股分析
result = await handler({"mode": "stock", "code": "600519"})

# 市场分析
result = await handler({"mode": "market"})
```

也可以传入自定义配置：

```python
from src.config import SkillConfig

config = SkillConfig(
    llm_base_url="https://api.openai.com/v1",
    llm_api_key="sk-xxx",
    llm_model="gpt-4o",
)

result = asyncio.run(analyze_stock("000001", config=config))
```

## 项目结构

```
stock-analysis/
├── SKILL.md                    # ★ Skill 定义（OpenClaw 标准入口）
├── manifest.yaml               # 机器可读元数据 + 输入输出 Schema
├── src/                        # 源代码
│   ├── index.py                # ★ Skill 入口（handler + analyze_stock/market）
│   ├── config.py               # 配置管理（环境变量 + .env）
│   ├── models.py               # 数据模型定义
│   ├── analyzer/
│   │   ├── stock.py            # 个股分析引擎
│   │   ├── market.py           # 市场分析引擎
│   │   └── prompts.py          # Prompt 模板
│   ├── data/
│   │   ├── provider.py         # 数据源抽象基类（MarketDataProvider）
│   │   ├── efinance_provider.py # Efinance 数据源（优先级 0）
│   │   ├── akshare_provider.py  # AkShare 数据源（优先级 1）
│   │   ├── pytdx_provider.py    # Pytdx 数据源（优先级 2）
│   │   ├── manager.py          # 数据源管理器（多源自动容灾）
│   │   └── utils.py            # 公共工具（缓存/统计/限流）
│   ├── search/
│   │   ├── base.py             # 搜索引擎抽象基类
│   │   ├── serpapi.py          # SerpAPI 搜索
│   │   ├── tavily.py           # Tavily 搜索
│   │   ├── brave.py            # Brave 搜索
│   │   └── bocha.py            # Bocha 搜索
│   └── llm/
│       └── client.py           # LLM 客户端（OpenAI 兼容接口）
├── scripts/                    # CLI 入口脚本
│   ├── analyze_stock.py        # 个股分析 CLI
│   └── analyze_market.py       # 市场分析 CLI
├── references/                 # 按需加载的详细文档
│   └── data-sources.md         # 数据源架构详细说明
├── test/
│   ├── test.py                 # 集成测试
│   └── test_market_mock.py     # Mock 测试
├── requirements.txt
├── config.example.yaml         # YAML 格式示例配置
├── .env.example
├── .gitignore
└── README.md
```

## 架构设计

```
┌──────────────────────────────────────────┐
│         SKILL.md / manifest.yaml          │
│         OpenClaw Skill 定义层             │
└──────────────────┬───────────────────────┘
                   │
┌──────────────────▼───────────────────────┐
│         src/index.py（接口层）              │
│  handler()  analyze_stock()  analyze_market() │
└──────────────────┬───────────────────────┘
                   │
┌──────────────────▼───────────────────────┐
│        src/analyzer/（分析层）              │
│     组装数据 + 构建 Prompt + 调用 LLM       │
└──┬───────────────┬───────────┬───────────┘
   │               │           │
   ▼               ▼           ▼
┌────────────┐ ┌──────┐ ┌──────────┐
│  src/data/ │ │search│ │   llm/   │
│   数据层    │ │搜索层 │ │  模型层   │
│ 三级自动容灾 │ │4 引擎 │ │DeepSeek  │
│            │ │(可扩展)│ │(OpenAI兼容)│
│ Efinance   │ └──────┘ └──────────┘
│  ↓ 失败     │
│ AkShare    │
│  ↓ 失败     │
│ Pytdx      │
└────────────┘
```

每层均通过抽象基类解耦，可独立扩展：

- **数据层**：实现 `MarketDataProvider` 抽象基类即可接入新数据源，通过 `DataProviderManager` 自动管理容灾切换
- **搜索层**：实现 `NewsSearchEngine` 即可接入新搜索引擎
- **模型层**：所有 OpenAI 兼容 API 均可直接使用

### 数据源能力矩阵

| 能力 | Efinance | AkShare | Pytdx |
| --- | :---: | :---: | :---: |
| 股票基本信息 | ✅ | ✅ | ✅ |
| 日 K 线数据 | ✅ | ✅ | ✅ |
| 实时行情 | ✅ | ✅ | ✅ |
| 筹码分布 | ❌ | ✅ | ❌ |
| 板块排名 | ✅ | ✅ | ❌ |
| 市场统计 | ✅ | ✅ | ❌ |
| 指数数据 | ✅ | ✅ | ✅ |

### 反封禁策略

参照原项目实现，内置多项反封禁措施：

- 随机 User-Agent 轮换（5 组 UA）
- 请求间随机 Sleep（1.5 ~ 3.0 秒抖动）
- 全市场实时行情缓存（TTL 600 秒）
- 涨停 / 跌停精确计算（科创板 / 创业板 20%、北交所 30%、ST 5%、普通 10%）

## 配置说明

| 环境变量 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `LLM_BASE_URL` | 是 | `https://api.deepseek.com/v1` | OpenAI 兼容 API 地址 |
| `LLM_API_KEY` | 是 | — | API Key |
| `LLM_MODEL` | 是 | `deepseek-chat` | 模型名称 |
| `SERPAPI_KEY` | 否 | — | SerpAPI Key |
| `TAVILY_KEY` | 否 | — | Tavily Key |
| `BRAVE_KEY` | 否 | — | Brave Search Key |
| `BOCHA_KEY` | 否 | — | 博查搜索 Key |
| `BIAS_THRESHOLD` | 否 | `5.0` | 乖离率阈值（%） |
| `NEWS_MAX_AGE_DAYS` | 否 | `3` | 新闻最大时效（天） |
| `ENABLE_CHIP` | 否 | `true` | 是否启用筹码分布 |
| `LOG_LEVEL` | 否 | `INFO` | 日志级别：DEBUG/INFO/WARNING/ERROR |

## 分析结果结构

### 个股分析 — `StockAnalysisResult`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `stock_code` | str | 股票代码 |
| `stock_name` | str | 股票名称 |
| `core_conclusion` | str | 一句话核心结论 |
| `score` | int | 评分 0-100 |
| `action` | str | 操作方向：买入/观望/卖出 |
| `trend` | str | 趋势判断：看多/震荡/看空 |
| `buy_price` | float | 建议买入价 |
| `stop_loss_price` | float | 止损价 |
| `target_price` | float | 目标价 |
| `checklist` | list\[CheckItem] | 操作检查清单 |
| `risk_alerts` | list\[str] | 风险警报 |
| `positive_catalysts` | list\[str] | 利好催化 |
| `strategy` | str | 买卖策略建议 |
| `raw_report` | str | LLM 完整分析报告（Markdown） |
| `disclaimer` | str | 免责声明 |

### 市场分析 — `MarketAnalysisResult`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `date` | str | 分析日期 |
| `core_conclusion` | str | 一句话核心结论 |
| `indices` | list\[IndexData] | 主要指数数据 |
| `statistics` | MarketStatistics | 涨跌统计 |
| `top_sectors` | list\[SectorData] | 领涨板块 |
| `bottom_sectors` | list\[SectorData] | 领跌板块 |
| `sentiment` | str | 市场情绪：偏多/中性/偏空 |
| `strategy` | str | 操作建议 |
| `raw_report` | str | LLM 完整复盘报告（Markdown） |
| `disclaimer` | str | 免责声明 |

## 注意事项

- **免 Token 数据源**：三级数据源（Efinance / AkShare / Pytdx）均为免费接口，无需注册或配置 Token
- **自动容灾**：任一数据源因网络、限流等原因异常时，自动切换至下一级数据源，日志会输出 `[数据源切换]` 提示
- **网络环境**：部分数据源依赖东方财富（eastmoney）接口，在特定网络环境（如企业内网 / 代理）下可能受限，此时系统会自动回退至新浪或通达信通道
- **API 限流**：搜索 API 有调用频率限制，频繁调用可能触发限流
- **数据时效**：实时行情基于最新日线数据，盘中数据可能有延迟
- **无状态设计**：Skill 不保存任何分析结果，每次调用独立执行

## 免责声明

本项目所有分析结果仅供参考，不构成投资建议。股市有风险，投资需谨慎。
