from __future__ import annotations

import logging
import time
from typing import Optional

import pandas as pd

from data.provider import MarketDataProvider
from data.utils import calculate_chip_from_daily
from models import (
    ChipDistribution,
    IndexData,
    MarketOverview,
    MarketStatistics,
    RealtimeQuote,
    SectorData,
    StockInfo,
)

logger = logging.getLogger(__name__)


class DataProviderManager(MarketDataProvider):

    def __init__(self, providers: list[MarketDataProvider]):
        self.providers = providers
        provider_names = [p.__class__.__name__ for p in providers]
        logger.info("DataProviderManager 初始化: %s", " → ".join(provider_names))

    async def get_stock_info(self, code: str) -> StockInfo:
        code = self.normalize_code(code)
        start = time.monotonic()
        for i, provider in enumerate(self.providers):
            try:
                result = await provider.get_stock_info(code)
                if result and result.name and result.name != code:
                    logger.info("[数据源 %d/%d] %s 获取股票信息成功: %s", i + 1, len(self.providers), provider.__class__.__name__, result.name)
                    logger.debug("get_stock_info(%s) 完成 耗时%.2fs", code, time.monotonic() - start)
                    return result
                logger.warning("[数据源 %d/%d] %s 返回无效结果", i + 1, len(self.providers), provider.__class__.__name__)
            except Exception as e:
                logger.warning("[数据源切换] %s get_stock_info 失败: %s", provider.__class__.__name__, e)
                continue
        logger.warning("get_stock_info(%s) 所有数据源均失败", code)
        return StockInfo(code=code, name=code)

    async def get_daily_data(self, code: str, days: int = 120) -> pd.DataFrame:
        code = self.normalize_code(code)
        start = time.monotonic()
        for i, provider in enumerate(self.providers):
            try:
                result = await provider.get_daily_data(code, days)
                if result is not None and not result.empty:
                    logger.info("[数据源 %d/%d] %s 获取日K线成功: %d 条", i + 1, len(self.providers), provider.__class__.__name__, len(result))
                    logger.debug("get_daily_data(%s) 完成 耗时%.2fs", code, time.monotonic() - start)
                    return result
                logger.warning("[数据源 %d/%d] %s 日K线数据为空", i + 1, len(self.providers), provider.__class__.__name__)
            except Exception as e:
                logger.warning("[数据源切换] %s get_daily_data 失败: %s", provider.__class__.__name__, e)
                continue
        logger.warning("get_daily_data(%s) 所有数据源均失败", code)
        return pd.DataFrame()

    async def get_realtime_quote(self, code: str) -> RealtimeQuote:
        code = self.normalize_code(code)
        start = time.monotonic()
        for i, provider in enumerate(self.providers):
            try:
                result = await provider.get_realtime_quote(code)
                if result and result.price > 0:
                    logger.info("[数据源 %d/%d] %s 获取实时行情成功: %.2f", i + 1, len(self.providers), provider.__class__.__name__, result.price)
                    logger.debug("get_realtime_quote(%s) 完成 耗时%.2fs", code, time.monotonic() - start)
                    return result
                logger.warning("[数据源 %d/%d] %s 实时行情无效", i + 1, len(self.providers), provider.__class__.__name__)
            except Exception as e:
                logger.warning("[数据源切换] %s get_realtime_quote 失败: %s", provider.__class__.__name__, e)
                continue
        logger.warning("get_realtime_quote(%s) 所有数据源均失败", code)
        return RealtimeQuote()

    async def get_chip_distribution(self, code: str) -> Optional[ChipDistribution]:
        code = self.normalize_code(code)
        start = time.monotonic()
        for i, provider in enumerate(self.providers):
            try:
                result = await provider.get_chip_distribution(code)
                if result is not None:
                    logger.info("[数据源 %d/%d] %s 获取筹码分布成功", i + 1, len(self.providers), provider.__class__.__name__)
                    logger.debug("get_chip_distribution(%s) 完成 耗时%.2fs", code, time.monotonic() - start)
                    return result
            except Exception as e:
                logger.warning("[数据源切换] %s get_chip_distribution 失败: %s", provider.__class__.__name__, e)
                continue

        logger.info("[筹码兜底] 所有数据源筹码接口未返回，尝试K线估算")
        try:
            df = await self.get_daily_data(code, 90)
        except Exception:
            logger.warning("[筹码兜底] K线数据获取失败，筹码分布不可用")
            return None
        result = calculate_chip_from_daily(df)
        if result:
            logger.info("[筹码兜底] K线估算筹码分布成功: 获利比例=%.1f%%, 平均成本=%.2f",
                        result.profit_ratio, result.avg_cost)
        else:
            logger.warning("[筹码兜底] K线估算筹码分布失败: 数据不足")
        logger.debug("get_chip_distribution(%s) 完成 耗时%.2fs", code, time.monotonic() - start)
        return result

    async def get_market_overview(self) -> MarketOverview:
        start = time.monotonic()
        logger.info("开始获取市场概览...")

        indices = await self.get_indices()
        statistics = await self.get_market_statistics()
        top_sectors, bottom_sectors = await self.get_sector_rankings()

        overview = MarketOverview(
            indices=indices,
            statistics=statistics,
            top_sectors=top_sectors,
            bottom_sectors=bottom_sectors,
        )

        logger.info("市场概览获取完成: 指数%d个, 涨%d/跌%d/平%d, 领涨板块%d个, 领跌板块%d个, 耗时%.2fs",
                    len(indices), statistics.up_count, statistics.down_count,
                    statistics.flat_count, len(top_sectors), len(bottom_sectors),
                    time.monotonic() - start)
        return overview

    async def get_indices(self) -> list[IndexData]:
        start = time.monotonic()
        for i, provider in enumerate(self.providers):
            try:
                result = await provider.get_indices()
                if result:
                    logger.info("[数据源 %d/%d] %s 获取指数数据成功: %d个",
                                i + 1, len(self.providers), provider.__class__.__name__, len(result))
                    logger.debug("get_indices() 完成 耗时%.2fs", time.monotonic() - start)
                    return result
            except Exception as e:
                logger.warning("[数据源切换] %s get_indices 失败: %s", provider.__class__.__name__, e)
                continue
        logger.warning("get_indices() 所有数据源均失败")
        return []

    async def get_sector_rankings(self) -> tuple[list[SectorData], list[SectorData]]:
        start = time.monotonic()
        for i, provider in enumerate(self.providers):
            try:
                top, bottom = await provider.get_sector_rankings()
                if top or bottom:
                    logger.info("[数据源 %d/%d] %s 获取板块排名成功: 领涨%d 领跌%d",
                                i + 1, len(self.providers), provider.__class__.__name__, len(top), len(bottom))
                    logger.debug("get_sector_rankings() 完成 耗时%.2fs", time.monotonic() - start)
                    return top, bottom
            except Exception as e:
                logger.warning("[数据源切换] %s get_sector_rankings 失败: %s", provider.__class__.__name__, e)
                continue
        logger.warning("get_sector_rankings() 所有数据源均失败")
        return [], []

    async def get_market_statistics(self) -> MarketStatistics:
        start = time.monotonic()
        for i, provider in enumerate(self.providers):
            try:
                result = await provider.get_market_statistics()
                if result and (result.up_count > 0 or result.down_count > 0):
                    logger.info("[数据源 %d/%d] %s 获取市场统计成功: 涨%d 跌%d 涨停%d 跌停%d",
                                i + 1, len(self.providers), provider.__class__.__name__,
                                result.up_count, result.down_count,
                                result.limit_up_count, result.limit_down_count)
                    logger.debug("get_market_statistics() 完成 耗时%.2fs", time.monotonic() - start)
                    return result
            except Exception as e:
                logger.warning("[数据源切换] %s get_market_statistics 失败: %s", provider.__class__.__name__, e)
                continue
        logger.warning("get_market_statistics() 所有数据源均失败")
        return MarketStatistics()
