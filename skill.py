from __future__ import annotations

import logging
import time
from typing import Optional

from analyzer.market import MarketAnalyzer
from analyzer.stock import StockAnalyzer
from config import SkillConfig, setup_logging
from data.akshare_provider import AkShareProvider
from data.efinance_provider import EfinanceProvider
from data.manager import DataProviderManager
from data.pytdx_provider import PytdxProvider
from llm.client import LLMClient
from models import MarketAnalysisResult, StockAnalysisResult
from search.base import NewsSearchEngine
from search.bocha import BochaSearch
from search.brave import BraveSearch
from search.serpapi import SerpAPISearch
from search.tavily import TavilySearch

logger = logging.getLogger(__name__)


def _build_data_provider(config: SkillConfig) -> DataProviderManager:
    """构建数据源（Efinance 最优先 → AkShare 备选 → Pytdx 兜底）"""
    return DataProviderManager([EfinanceProvider(), AkShareProvider(), PytdxProvider()])


def _build_search_engines(config: SkillConfig) -> list[NewsSearchEngine]:
    """构建搜索引擎列表，按配置顺序"""
    engines: list[NewsSearchEngine] = []
    if config.serpapi_key:
        engines.append(SerpAPISearch(config.serpapi_key))
    if config.tavily_key:
        engines.append(TavilySearch(config.tavily_key))
    if config.brave_key:
        engines.append(BraveSearch(config.brave_key))
    if config.bocha_key:
        engines.append(BochaSearch(config.bocha_key))
    return engines


def _build_llm_client(config: SkillConfig) -> LLMClient:
    """构建 LLM 客户端"""
    return LLMClient(
        base_url=config.llm_base_url,
        api_key=config.llm_api_key,
        model=config.llm_model,
    )


async def analyze_stock(code: str, config: Optional[SkillConfig] = None) -> StockAnalysisResult:
    """个股分析 - 供智能体调用的主入口

    Args:
        code: A股股票代码，如 "600519"、"000001"
        config: 配置对象，为 None 时从环境变量加载

    Returns:
        StockAnalysisResult 个股分析结果
    """
    if config is None:
        config = SkillConfig()

    setup_logging()

    errors = config.validate()
    if errors:
        logger.error("配置校验失败: %s", "; ".join(errors))
        return StockAnalysisResult(
            stock_code=code,
            core_conclusion=f"配置错误: {'; '.join(errors)}",
        )

    logger.info("========== 个股分析开始 [%s] ==========", code)
    logger.info("配置: model=%s, base_url=%s, 搜索引擎=%d个, 筹码=%s",
                config.llm_model, config.llm_base_url,
                sum(1 for k in ["serpapi_key", "tavily_key", "brave_key", "bocha_key"]
                    if getattr(config, k, "")),
                "启用" if config.enable_chip else "禁用")

    start = time.monotonic()
    data_provider = _build_data_provider(config)
    llm_client = _build_llm_client(config)
    search_engines = _build_search_engines(config)

    analyzer = StockAnalyzer(
        data_provider=data_provider,
        llm_client=llm_client,
        search_engines=search_engines,
        config=config,
    )

    result = await analyzer.analyze(code)
    elapsed = time.monotonic() - start
    logger.info("========== 个股分析完成 [%s] 耗时%.2fs: %s ==========",
                code, elapsed, result.core_conclusion[:50] if result.core_conclusion else "无结论")
    return result


async def analyze_market(config: Optional[SkillConfig] = None) -> MarketAnalysisResult:
    """市场分析 - 供智能体调用的主入口

    Args:
        config: 配置对象，为 None 时从环境变量加载

    Returns:
        MarketAnalysisResult 市场分析结果
    """
    if config is None:
        config = SkillConfig()

    setup_logging()

    errors = config.validate()
    if errors:
        logger.error("配置校验失败: %s", "; ".join(errors))
        return MarketAnalysisResult(
            core_conclusion=f"配置错误: {'; '.join(errors)}",
        )

    logger.info("========== 市场分析开始 ==========")
    logger.info("配置: model=%s, base_url=%s", config.llm_model, config.llm_base_url)

    start = time.monotonic()
    data_provider = _build_data_provider(config)
    llm_client = _build_llm_client(config)

    analyzer = MarketAnalyzer(
        data_provider=data_provider,
        llm_client=llm_client,
        config=config,
    )

    result = await analyzer.analyze()
    elapsed = time.monotonic() - start
    logger.info("========== 市场分析完成 耗时%.2fs: %s ==========",
                elapsed, result.core_conclusion[:50] if result.core_conclusion else "无结论")
    return result
