"""
市场分析功能模拟测试脚本

使用 Mock 数据源和 Mock LLM 客户端，无需真实 API Key 即可运行。
测试完整的市场分析流程：数据获取 → Prompt 组装 → LLM 调用 → 结果解析

运行方式：python3 test_market_mock.py
"""
from __future__ import annotations

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.analyzer.market import MarketAnalyzer
from src.analyzer.prompts import MARKET_ANALYSIS_SYSTEM_PROMPT, MARKET_ANALYSIS_USER_PROMPT
from src.config import SkillConfig
from src.data.provider import MarketDataProvider
from src.llm.client import LLMClient
from src.models import (
    IndexData,
    MarketAnalysisResult,
    MarketOverview,
    MarketStatistics,
    SectorData,
)


class MockDataProvider(MarketDataProvider):
    """模拟数据源，返回构造的 A 股市场数据"""

    async def get_stock_info(self, code: str):
        pass

    async def get_daily_data(self, code: str, days: int = 120):
        pass

    async def get_realtime_quote(self, code: str):
        pass

    async def get_chip_distribution(self, code: str):
        pass

    async def get_market_overview(self) -> MarketOverview:
        indices = [
            IndexData(name="上证指数", code="000001.SH", close=3387.57, change_pct=0.76, change_amt=25.63),
            IndexData(name="深证成指", code="399001.SZ", close=10245.32, change_pct=1.12, change_amt=113.48),
            IndexData(name="创业板指", code="399006.SZ", close=2089.15, change_pct=1.58, change_amt=32.47),
        ]
        statistics = MarketStatistics(
            up_count=3456,
            down_count=1523,
            flat_count=287,
            limit_up_count=68,
            limit_down_count=12,
        )
        top_sectors = [
            SectorData(name="半导体", change_pct=4.32, lead_stock="中芯国际"),
            SectorData(name="人工智能", change_pct=3.87, lead_stock="科大讯飞"),
            SectorData(name="新能源车", change_pct=3.21, lead_stock="比亚迪"),
            SectorData(name="光伏", change_pct=2.95, lead_stock="隆基绿能"),
            SectorData(name="消费电子", change_pct=2.68, lead_stock="立讯精密"),
        ]
        bottom_sectors = [
            SectorData(name="房地产", change_pct=-2.15, lead_stock="万科A"),
            SectorData(name="银行", change_pct=-1.32, lead_stock="招商银行"),
            SectorData(name="煤炭", change_pct=-0.98, lead_stock="中国神华"),
            SectorData(name="钢铁", change_pct=-0.76, lead_stock="宝钢股份"),
            SectorData(name="石油石化", change_pct=-0.54, lead_stock="中国石油"),
        ]
        return MarketOverview(
            indices=indices,
            statistics=statistics,
            top_sectors=top_sectors,
            bottom_sectors=bottom_sectors,
        )

    async def get_sector_rankings(self):
        overview = await self.get_market_overview()
        return overview.top_sectors, overview.bottom_sectors

    async def get_market_statistics(self) -> MarketStatistics:
        overview = await self.get_market_overview()
        return overview.statistics

    async def get_indices(self):
        overview = await self.get_market_overview()
        return overview.indices


class MockLLMClient(LLMClient):
    """模拟 LLM 客户端，返回预设的分析结果"""

    def __init__(self):
        pass

    async def analyze(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        mock_response = {
            "core_conclusion": "A股三大指数集体收涨，市场情绪偏多，半导体和AI板块领涨，地产银行拖累",
            "sentiment": "偏多",
            "strategy": "当前市场做多情绪较浓，建议关注半导体、AI等科技主线，逢低布局；规避地产、银行等弱势板块。仓位控制在6-7成，注意板块轮动节奏。",
            "report": """## A股市场复盘报告

### 一、指数表现
今日A股三大指数集体收涨，市场呈现普涨格局：
- 🟢 **上证指数** 收于3387.57点，上涨0.76%，成交额较昨日有所放大
- 🟢 **深证成指** 收于10245.32点，上涨1.12%，科技股带动明显
- 🟢 **创业板指** 收于2089.15点，上涨1.58%，领涨三大指数

### 二、市场统计
- 上涨家数3456家，下跌家数1523家，涨跌比约2.3:1
- 涨停68家，跌停仅12家，赚钱效应较好
- 市场成交活跃，资金做多意愿较强

### 三、板块表现
**领涨板块：**
1. 半导体 +4.32%：受国产替代利好催化，中芯国际领涨
2. 人工智能 +3.87%：大模型应用落地加速，科大讯飞涨停
3. 新能源车 +3.21%：销量数据超预期，比亚迪大涨
4. 光伏 +2.95%：海外需求回暖，隆基绿能领涨
5. 消费电子 +2.68%：苹果新品催化，立讯精密走强

**领跌板块：**
1. 房地产 -2.15%：政策预期落空，万科A领跌
2. 银行 -1.32%：净息差收窄担忧，招商银行走弱
3. 煤炭 -0.98%：煤价下行，中国神华调整
4. 钢铁 -0.76%：需求疲软，宝钢股份小跌
5. 石油石化 -0.54%：油价震荡，中国石油微跌

### 四、市场情绪与展望
今日市场情绪明显偏多，科技成长风格占优。半导体和AI板块资金流入明显，短期有望延续强势。但需注意：
1. 地产板块持续走弱，需警惕信用风险蔓延
2. 涨停家数较多，但部分个股存在追高风险
3. 北向资金动向需持续关注

### 五、操作建议
- 仓位：6-7成，偏积极但留有余地
- 主线：半导体、AI、新能源车等科技成长方向
- 规避：地产、银行等低估值但基本面承压板块
- 策略：逢低布局，不追高，关注板块轮动节奏

⚠️ 仅供参考，不构成投资建议。股市有风险，投资需谨慎。""",
        }
        return json.dumps(mock_response, ensure_ascii=False)


def print_separator(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_market_overview(overview: MarketOverview):
    print_separator("模拟市场数据")
    print("\n📊 主要指数：")
    for idx in overview.indices:
        emoji = "🟢" if idx.change_pct > 0 else "🔴" if idx.change_pct < 0 else "⚪"
        print(f"  {emoji} {idx.name}: {idx.close:.2f} ({'+' if idx.change_pct > 0 else ''}{idx.change_pct:.2f}%)")

    print(f"\n📈 市场统计：")
    print(f"  上涨: {overview.statistics.up_count}家 | 下跌: {overview.statistics.down_count}家 | 平盘: {overview.statistics.flat_count}家")
    print(f"  涨停: {overview.statistics.limit_up_count}家 | 跌停: {overview.statistics.limit_down_count}家")

    print(f"\n🔥 领涨板块：")
    for s in overview.top_sectors:
        print(f"  - {s.name}: +{s.change_pct:.2f}% (领涨股: {s.lead_stock})")

    print(f"\n❄️ 领跌板块：")
    for s in overview.bottom_sectors:
        print(f"  - {s.name}: {s.change_pct:.2f}% (领跌股: {s.lead_stock})")


def print_prompt(system_prompt: str, user_prompt: str):
    print_separator("组装后的 Prompt")
    print("\n🤖 System Prompt:")
    print(f"  {system_prompt[:200]}...")
    print(f"\n👤 User Prompt:")
    print(user_prompt)


def print_result(result: MarketAnalysisResult):
    print_separator("市场分析结果")
    print(f"\n📅 日期: {result.date}")
    print(f"🎯 核心结论: {result.core_conclusion}")
    print(f"💭 市场情绪: {result.sentiment}")
    print(f"📋 操作建议: {result.strategy}")
    print(f"\n⚠️ 免责声明: {result.disclaimer}")

    print(f"\n📊 指数数据: ")
    for idx in result.indices:
        emoji = "🟢" if idx.change_pct > 0 else "🔴"
        print(f"  {emoji} {idx.name}: {idx.close:.2f} ({'+' if idx.change_pct > 0 else ''}{idx.change_pct:.2f}%)")

    print(f"\n📈 市场统计: 上涨{result.statistics.up_count}家 | 下跌{result.statistics.down_count}家 | 涨停{result.statistics.limit_up_count}家 | 跌停{result.statistics.limit_down_count}家")

    print_separator("LLM 原始报告")
    print(result.raw_report)


async def run_test():
    print("🚀 A股市场分析功能 - 模拟测试")
    print("=" * 60)

    config = SkillConfig(
        llm_base_url="https://mock.local",
        llm_api_key="mock-key",
        llm_model="mock-model",
    )

    data_provider = MockDataProvider()
    llm_client = MockLLMClient()

    analyzer = MarketAnalyzer(
        data_provider=data_provider,
        llm_client=llm_client,
        config=config,
    )

    # 步骤1：获取市场数据
    print("\n[1/4] 获取市场数据...")
    overview = await data_provider.get_market_overview()
    print_market_overview(overview)

    # 步骤2：组装 Prompt
    print("\n[2/4] 组装 Prompt...")
    system_prompt = MARKET_ANALYSIS_SYSTEM_PROMPT
    user_prompt = analyzer._build_user_prompt(overview)
    print_prompt(system_prompt, user_prompt)

    # 步骤3：执行完整分析
    print("\n[3/4] 执行市场分析（Mock LLM）...")
    result = await analyzer.analyze()

    # 步骤4：输出结果
    print("\n[4/4] 输出分析结果...")
    print_result(result)

    # 验证结果完整性
    print_separator("结果完整性验证")
    checks = [
        ("core_conclusion 非空", bool(result.core_conclusion)),
        ("sentiment 非空", bool(result.sentiment)),
        ("strategy 非空", bool(result.strategy)),
        ("raw_report 非空", bool(result.raw_report)),
        ("indices 有数据", len(result.indices) > 0),
        ("top_sectors 有数据", len(result.top_sectors) > 0),
        ("bottom_sectors 有数据", len(result.bottom_sectors) > 0),
        ("statistics.up_count > 0", result.statistics.up_count > 0),
        ("disclaimer 存在", bool(result.disclaimer)),
    ]
    all_pass = True
    for name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}")
        if not passed:
            all_pass = False

    print(f"\n{'🎉 所有验证通过！市场分析功能正常！' if all_pass else '⚠️ 部分验证未通过，请检查！'}")
    return all_pass


if __name__ == "__main__":
    success = asyncio.run(run_test())
    sys.exit(0 if success else 1)
