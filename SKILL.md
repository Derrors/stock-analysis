---
name: stock-analysis
description: |
  A股市场分析与个股深度分析技能。支持技术面（均线/乖离率/量比）、筹码分布、舆情情报等多维度分析，输出结构化评分与操作建议。

  Triggers: "分析股票", "个股分析", "市场分析", "A股分析", "stock analysis", "analyze stock", "market analysis", "股票评分", "买卖建议", "涨停分析"

  Does NOT trigger:
  - 简单的股价查询（无需深度分析）
  - 港股/美股/非A股市场分析
  - 基金/债券/期货分析

  Output: 结构化分析报告（评分0-100、操作方向、买卖点位、风险提示、检查清单）
version: 1.0.0
metadata:
  openclaw:
    requires:
      env:
        - LLM_API_KEY
        - LLM_BASE_URL
        - LLM_MODEL
      bins:
        - python3
    primaryEnv: LLM_API_KEY
    emoji: "📈"
    install:
      - kind: uv
        command: pip install -r requirements.txt
---

# A股股票市场分析 Skill

## 功能

### 个股分析
输入股票代码，输出结构化分析结果：
- 技术面：MA5/MA10/MA20/MA60 均线、多头排列、乖离率、量比
- 筹码分布：获利比例、平均成本、集中度
- 舆情情报：多引擎新闻搜索
- 实时行情：当前价、涨跌幅、成交量、换手率
- 分析结论：评分 + 操作方向 + 买卖点位 + 检查清单 + 风险提示

### 市场分析
每日 A 股市场复盘：
- 主要指数（上证/深证/创业板）
- 涨跌统计（涨跌家数、涨停跌停数）
- 板块排名（领涨/领跌 Top5）
- 市场情绪判断 + 操作建议

## 使用方式

### 生成分析报告（推荐）

```bash
# 个股分析报告 → 保存到 reports/{代码}_{日期}.md
python3 {baseDir}/scripts/report.py stock 600519

# 市场分析报告 → 保存到 reports/market_{日期}.md
python3 {baseDir}/scripts/report.py market

# 同时输出 JSON
python3 {baseDir}/scripts/report.py stock 600519 --json

# 自定义输出目录
python3 {baseDir}/scripts/report.py stock 600519 -o ./my-reports
```

### JSON 输出

```bash
python3 {baseDir}/scripts/analyze_stock.py 600519
python3 {baseDir}/scripts/analyze_market.py
```

### Handler 调用

```python
from src.index import handler
result = await handler({"mode": "stock", "code": "600519"})
result = await handler({"mode": "market"})
result = await handler({"mode": "stock", "code": "600519", "save": True})
```

## 输入格式

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| mode | string | 是 | "stock" 或 "market" |
| code | string | mode=stock时必填 | A股股票代码，如 "600519" |

## 输出格式

### 个股分析结果

```json
{
  "stock_code": "600519",
  "stock_name": "贵州茅台",
  "core_conclusion": "一句话核心结论",
  "score": 75,
  "action": "买入/观望/卖出",
  "trend": "看多/震荡/看空",
  "buy_price": 1800.0,
  "stop_loss_price": 1700.0,
  "target_price": 2000.0,
  "checklist": [{"condition": "...", "status": "✅/❌", "detail": "..."}],
  "risk_alerts": ["风险1", "风险2"],
  "positive_catalysts": ["利好1"],
  "strategy": "买卖策略建议",
  "raw_report": "LLM完整分析报告(Markdown)",
  "disclaimer": "仅供参考，不构成投资建议"
}
```

### 市场分析结果

```json
{
  "date": "2025-01-15",
  "core_conclusion": "一句话核心结论",
  "indices": [{"name": "上证指数", "close": 3200.0, "change_pct": 0.5}],
  "statistics": {"up_count": 3000, "down_count": 1500, "limit_up_count": 50},
  "top_sectors": [{"name": "半导体", "change_pct": 3.2}],
  "bottom_sectors": [{"name": "房地产", "change_pct": -1.5}],
  "sentiment": "偏多/中性/偏空",
  "strategy": "操作建议",
  "raw_report": "LLM完整复盘报告(Markdown)"
}
```

## 数据源

行情数据采用三级自动容灾：Efinance（优先）→ AkShare（备选）→ Pytdx（兜底），均为免费接口无需 Token。详见 references/data-sources.md。

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| LLM_API_KEY | 是 | LLM API Key |
| LLM_BASE_URL | 是 | OpenAI 兼容 API 地址 |
| LLM_MODEL | 是 | 模型名称 |
| SERPAPI_KEY | 否 | SerpAPI 搜索 Key |
| TAVILY_KEY | 否 | Tavily 搜索 Key |
| BRAVE_KEY | 否 | Brave 搜索 Key |
| BOCHA_KEY | 否 | 博查搜索 Key |

## 注意事项

- 行情数据源免费，无需注册或配置 Token
- 任一数据源异常时自动切换至下一级
- 分析结果仅供参考，不构成投资建议
