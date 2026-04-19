from __future__ import annotations

import asyncio
import logging
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Generator, Optional

import pandas as pd

from src.data.provider import MarketDataProvider
from src.models import (
    ChipDistribution,
    IndexData,
    MarketOverview,
    MarketStatistics,
    RealtimeQuote,
    SectorData,
    StockInfo,
)

logger = logging.getLogger(__name__)

DEFAULT_HOSTS = [
    ("119.147.212.81", 7709),
    ("112.74.214.43", 7727),
    ("221.231.141.60", 7709),
    ("101.227.73.20", 7709),
    ("101.227.77.254", 7709),
    ("14.215.128.18", 7709),
    ("59.173.18.140", 7709),
    ("180.153.39.51", 7709),
]


def _get_market_code(stock_code: str) -> tuple[int, str]:
    code = stock_code.strip()
    if code.startswith(("60", "68")):
        return 1, code
    return 0, code


class _TdxSession:

    def __init__(self, hosts: list[tuple[str, int]]):
        self._hosts = hosts
        self._host_idx = 0

    @contextmanager
    def connect(self) -> Generator:
        from pytdx.hq import TdxHq_API

        api = TdxHq_API()
        connected = False
        try:
            for i in range(len(self._hosts)):
                idx = (self._host_idx + i) % len(self._hosts)
                host, port = self._hosts[idx]
                try:
                    if api.connect(host, port, time_out=5):
                        connected = True
                        self._host_idx = idx
                        logger.info("Pytdx 连接成功: %s:%d", host, port)
                        break
                except Exception as e:
                    logger.warning("Pytdx 连接 %s:%d 失败: %s", host, port, e)
                    continue
            if not connected:
                logger.debug("Pytdx 已尝试全部 %d 台服务器，均连接失败", len(self._hosts))
                raise ConnectionError("Pytdx 无法连接任何通达信服务器")
            yield api
        finally:
            try:
                api.disconnect()
            except Exception:
                pass


class PytdxProvider(MarketDataProvider):

    def __init__(self, hosts: list[tuple[str, int]] | None = None):
        self._session = _TdxSession(hosts or DEFAULT_HOSTS)
        self._stock_name_cache: dict[str, str] = {}

    def _run_sync(self, func, *args, **kwargs):
        return asyncio.to_thread(func, *args, **kwargs)

    def _get_stock_name_sync(self, market: int, code: str, api) -> str:
        if code in self._stock_name_cache:
            return self._stock_name_cache[code]
        try:
            stocks = api.get_security_list(market, 0)
            if stocks:
                for s in stocks:
                    if s.get("code") == code:
                        name = s.get("name", code)
                        self._stock_name_cache[code] = name
                        return name
        except Exception:
            pass
        return code

    async def get_stock_info(self, code: str) -> StockInfo:
        start = time.monotonic()
        code = self.normalize_code(code)
        try:
            def _fetch():
                market, pure_code = _get_market_code(code)
                logger.debug("Pytdx 获取股票信息: code=%s, market=%d", code, market)
                with self._session.connect() as api:
                    name = self._get_stock_name_sync(market, pure_code, api)
                    return name

            name = await self._run_sync(_fetch)
            logger.debug("Pytdx 股票信息: name=%s", name)
            logger.debug("Pytdx get_stock_info 完成 耗时%.2fs", time.monotonic() - start)
            return StockInfo(code=code, name=name)
        except Exception as e:
            logger.warning("PytdxProvider 获取股票信息失败 %s: %s", code, e)
            return StockInfo(code=code, name=code)

    async def get_daily_data(self, code: str, days: int = 120) -> pd.DataFrame:
        start = time.monotonic()
        code = self.normalize_code(code)
        try:
            def _fetch():
                market, pure_code = _get_market_code(code)
                logger.debug("Pytdx 获取日K线: code=%s, days=%d, market=%d", code, days, market)
                count = min(days + 30, 800)
                with self._session.connect() as api:
                    data = api.get_security_bars(
                        category=9,
                        market=market,
                        code=pure_code,
                        start=0,
                        count=count,
                    )
                    if not data:
                        logger.debug("Pytdx 日K线无数据: code=%s", code)
                        return pd.DataFrame()
                    logger.debug("Pytdx 日K线原始数据: %d条", len(data))
                    df = api.to_df(data)
                    return df

            df = await self._run_sync(_fetch)
            if df is None or df.empty:
                return pd.DataFrame()

            column_mapping = {
                "datetime": "trade_date",
                "vol": "volume",
            }
            df = df.rename(columns=column_mapping)
            df["trade_date"] = pd.to_datetime(df["trade_date"])

            if "close" in df.columns:
                df["change_pct"] = df["close"].pct_change() * 100
                df["change_pct"] = df["change_pct"].fillna(0).round(2)

            df = df.sort_values("trade_date").reset_index(drop=True)
            result = df.tail(days).reset_index(drop=True)
            logger.debug("Pytdx 日K线处理完成: %d条最终数据", len(result))
            logger.debug("Pytdx get_daily_data 完成 耗时%.2fs", time.monotonic() - start)
            return result
        except Exception as e:
            logger.error("PytdxProvider 获取日K线数据失败 %s: %s", code, e)
            return pd.DataFrame()

    async def get_realtime_quote(self, code: str) -> RealtimeQuote:
        start = time.monotonic()
        code = self.normalize_code(code)
        try:
            def _fetch():
                market, pure_code = _get_market_code(code)
                logger.debug("Pytdx 获取实时行情: code=%s, market=%d", code, market)
                with self._session.connect() as api:
                    data = api.get_security_quotes([(market, pure_code)])
                    if data and len(data) > 0:
                        return data[0]
                    return None

            quote = await self._run_sync(_fetch)
            if quote is None:
                logger.debug("Pytdx 实时行情无数据: code=%s", code)
                return RealtimeQuote()

            price = float(quote.get("price", 0))
            pre_close = float(quote.get("last_close", 0))
            change_amt = price - pre_close if price and pre_close else 0.0
            change_pct = (change_amt / pre_close * 100) if pre_close else 0.0
            high = float(quote.get("high", 0))
            low = float(quote.get("low", 0))
            amplitude = ((high - low) / pre_close * 100) if pre_close else 0.0

            logger.debug("Pytdx 实时行情: price=%.2f, change_pct=%.2f%%", price, change_pct)
            logger.debug("Pytdx get_realtime_quote 完成 耗时%.2fs", time.monotonic() - start)
            return RealtimeQuote(
                price=price,
                change_pct=round(change_pct, 2),
                change_amt=round(change_amt, 2),
                volume=float(quote.get("vol", 0)),
                turnover=float(quote.get("amount", 0)),
                high=high,
                low=low,
                open=float(quote.get("open", 0)),
                prev_close=pre_close,
                amplitude=round(amplitude, 2),
            )
        except Exception as e:
            logger.error("PytdxProvider 获取实时行情失败 %s: %s", code, e)
            return RealtimeQuote()

    async def get_chip_distribution(self, code: str) -> Optional[ChipDistribution]:
        logger.debug("Pytdx 不支持筹码分布，返回 None")
        return None

    async def get_market_overview(self) -> MarketOverview:
        logger.debug("Pytdx 市场概览: 仅支持指数数据")
        indices = await self.get_indices()
        return MarketOverview(indices=indices)

    async def get_sector_rankings(self) -> tuple[list[SectorData], list[SectorData]]:
        logger.debug("Pytdx 不支持板块排名")
        return [], []

    async def get_market_statistics(self) -> MarketStatistics:
        logger.debug("Pytdx 不支持市场统计")
        return MarketStatistics()

    async def get_indices(self) -> list[IndexData]:
        start = time.monotonic()
        indices_config = [
            (1, "000001", "上证指数"),
            (0, "399001", "深证成指"),
            (0, "399006", "创业板指"),
        ]
        try:
            def _fetch():
                logger.debug("Pytdx 获取指数数据...")
                results = []
                with self._session.connect() as api:
                    for market, idx_code, idx_name in indices_config:
                        data = api.get_index_bars(
                            category=9,
                            market=market,
                            code=idx_code,
                            start=0,
                            count=2,
                        )
                        if data and len(data) >= 1:
                            df = api.to_df(data)
                            latest = df.iloc[-1]
                            close_val = float(latest.get("close", 0))
                            if len(df) >= 2:
                                prev = float(df.iloc[-2]["close"])
                                change_amt = close_val - prev
                                change_pct = (change_amt / prev * 100) if prev else 0.0
                            else:
                                change_amt = 0.0
                                change_pct = 0.0
                            logger.debug("Pytdx 指数 %s: close=%.2f, change_pct=%.2f%%", idx_name, close_val, change_pct)
                            results.append(IndexData(
                                name=idx_name,
                                code=idx_code,
                                close=close_val,
                                change_pct=round(change_pct, 2),
                                change_amt=round(change_amt, 2),
                            ))
                return results

            result = await self._run_sync(_fetch)
            logger.debug("Pytdx 指数数据: %d个", len(result))
            logger.debug("Pytdx get_indices 完成 耗时%.2fs", time.monotonic() - start)
            return result
        except Exception as e:
            logger.warning("PytdxProvider 获取指数数据失败: %s", e)
            return []
