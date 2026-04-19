import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.index import analyze_stock, analyze_market


def print_separator(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


async def test_stock_analysis():
    print_separator("个股分析 — 贵州茅台(600519)")
    result = await analyze_stock("600519")

    print(f"  股票: {result.stock_name}({result.stock_code})")
    print(f"  核心结论: {result.core_conclusion}")
    print(f"  评分: {result.score}")
    print(f"  操作方向: {result.action}")
    print(f"  趋势: {result.trend}")
    print(f"  买入价: {result.buy_price}")
    print(f"  止损价: {result.stop_loss_price}")
    print(f"  目标价: {result.target_price}")

    if result.checklist:
        print(f"\n  操作检查清单:")
        for item in result.checklist:
            status_icon = {"满足": "✅", "注意": "⚠️", "不满足": "❌"}.get(item.status, "❓")
            print(f"    {status_icon} {item.condition}: {item.detail}")

    if result.risk_alerts:
        print(f"\n  风险警报:")
        for alert in result.risk_alerts:
            print(f"    🔴 {alert}")

    if result.positive_catalysts:
        print(f"\n  利好催化:")
        for catalyst in result.positive_catalysts:
            print(f"    🟢 {catalyst}")

    print(f"\n  买卖策略: {result.strategy}")
    print(f"\n  ⚠️ {result.disclaimer}")

    if result.raw_report:
        print_separator("完整分析报告")
        print(result.raw_report)

    return result


async def test_market_analysis():
    print_separator("市场分析 — A股大盘复盘")
    result = await analyze_market()

    print(f"  日期: {result.date}")
    print(f"  核心结论: {result.core_conclusion}")
    print(f"  市场情绪: {result.sentiment}")

    if result.indices:
        print(f"\n  主要指数:")
        for idx in result.indices:
            emoji = "🟢" if idx.change_pct > 0 else "🔴" if idx.change_pct < 0 else "⚪"
            print(f"    {emoji} {idx.name}: {idx.close:.2f} ({'+' if idx.change_pct > 0 else ''}{idx.change_pct:.2f}%)")

    print(f"\n  市场统计: 上涨{result.statistics.up_count}家 | 下跌{result.statistics.down_count}家 | 平盘{result.statistics.flat_count}家")
    print(f"  涨停{result.statistics.limit_up_count}家 | 跌停{result.statistics.limit_down_count}家")

    if result.top_sectors:
        print(f"\n  领涨板块:")
        for s in result.top_sectors:
            print(f"    🔥 {s.name}: +{s.change_pct:.2f}%")

    if result.bottom_sectors:
        print(f"\n  领跌板块:")
        for s in result.bottom_sectors:
            print(f"    ❄️ {s.name}: {s.change_pct:.2f}%")

    print(f"\n  操作建议: {result.strategy}")
    print(f"\n  ⚠️ {result.disclaimer}")

    if result.raw_report:
        print_separator("完整复盘报告")
        print(result.raw_report)

    return result


async def main():
    print("🚀 A股股票分析 Skill — 真实数据测试")
    print("=" * 60)

    print_separator("个股分析测试")
    try:
        stock_result = await test_stock_analysis()
        stock_ok = bool(stock_result.core_conclusion)
    except Exception as e:
        print(f"  ❌ 个股分析失败: {e}")
        stock_ok = False

    print_separator("市场分析测试")
    try:
        market_result = await test_market_analysis()
        market_ok = bool(market_result.core_conclusion)
    except Exception as e:
        print(f"  ❌ 市场分析失败: {e}")
        market_ok = False

    print_separator("测试结果汇总")
    print(f"  {'✅' if stock_ok else '❌'} 个股分析")
    print(f"  {'✅' if market_ok else '❌'} 市场分析")

    if stock_ok and market_ok:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️ 部分测试未通过，请检查配置和网络连接")


if __name__ == "__main__":
    asyncio.run(main())
