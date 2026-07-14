#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NASDAQ 每日分析报告生成器
独立可运行脚本，供 SOLO Schedule 调用

用法: python nasdaq_analyzer.py
输出: nasdaq_report_YYYY-MM-DD.html

支持 Feature Flags 开关控制各功能模块：
  ENABLE_BACKTEST       - 策略回测分析
  ENABLE_NEWS_SENTIMENT - 新闻情绪分析
  ENABLE_SECTOR_ETF     - 板块轮动分析
  ENABLE_COMPARISON     - 历史报告对比
  ENABLE_HK_A_SHARE     - 港股/A股数据
"""

import sys
import os
import math
import logging
from datetime import datetime

# 将脚本所在目录加入 path（确保模块导入）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    INDEX_TICKERS, STOCK_UNIVERSE, OUTPUT_DIR,
    ENABLE_BACKTEST, ENABLE_NEWS_SENTIMENT, ENABLE_SECTOR_ETF,
    ENABLE_COMPARISON, ENABLE_HK_A_SHARE,
    HK_STOCK_UNIVERSE, A_SHARE_UNIVERSE,
)
from data_fetcher import DataFetcher
from indicators import calc_all_indicators
from analysis import (
    analyze_trend, find_support_resistance, generate_signals,
    analyze_market_breadth, vix_sentiment, generate_recommendation
)
from report_generator import ReportGenerator

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


def extract_latest(df):
    """提取最新行情数据"""
    if df is None or df.empty or len(df) < 2:
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2]

    try:
        close = float(last["Close"])
        prev_close = float(prev["Close"])
        change = close - prev_close
        change_pct = (change / prev_close) * 100 if prev_close != 0 else 0

        return {
            "close": round(close, 2),
            "open": round(float(last["Open"]), 2),
            "high": round(float(last["High"]), 2),
            "low": round(float(last["Low"]), 2),
            "volume": int(float(last["Volume"])),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
        }
    except (KeyError, ValueError, TypeError) as e:
        logger.warning(f"提取最新行情数据失败: {e}")
        return None


def analyze_stock(fetcher, ticker, stock_df):
    """分析单只股票，返回推荐信息"""
    if stock_df is None or stock_df.empty or len(stock_df) < 2:
        logger.warning(f"{ticker} 数据不足，跳过")
        return None

    # 计算技术指标
    stock_df = calc_all_indicators(stock_df)

    # 获取基本信息
    info = fetcher.fetch_stock_info(ticker)

    # 提取行情数据
    last = stock_df.iloc[-1]
    prev = stock_df.iloc[-2]

    try:
        close = float(last["Close"])
        prev_close = float(prev["Close"])
        change_pct = ((close - prev_close) / prev_close * 100) if prev_close != 0 else 0
    except (KeyError, ValueError, TypeError):
        close = 0
        change_pct = 0

    # 趋势和信号分析
    trend = analyze_trend(stock_df)
    signals = generate_signals(stock_df)
    rsi_val = last.get("RSI")
    rsi_val = float(rsi_val) if rsi_val is not None and not (isinstance(rsi_val, float) and math.isnan(rsi_val)) else None

    # 生成投资建议
    recommendation = generate_recommendation(trend, signals, rsi_val)

    return {
        "ticker": ticker,
        "name": info.get("name", ticker),
        "price": round(close, 2),
        "change_pct": round(change_pct, 2),
        "rsi": rsi_val,
        "trend": trend["direction"],
        "signals": ", ".join(s["type"] for s in signals) if signals else "无",
        "recommendation": recommendation,
    }


def main():
    """主执行流程"""
    logger.info("=" * 60)
    logger.info("NASDAQ 每日分析报告生成开始")
    logger.info(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"功能开关: 回测={ENABLE_BACKTEST} 情绪={ENABLE_NEWS_SENTIMENT} "
                f"板块={ENABLE_SECTOR_ETF} 对比={ENABLE_COMPARISON} 港股A股={ENABLE_HK_A_SHARE}")
    logger.info("=" * 60)

    fetcher = DataFetcher()
    generator = ReportGenerator()

    # 初始化数据库管理器（如果启用对比功能）
    db_manager = None
    if ENABLE_COMPARISON:
        try:
            from db import DbManager
            db_manager = DbManager()
            logger.info("数据库管理器初始化成功")
        except Exception as e:
            logger.warning(f"数据库初始化失败，对比功能将不可用: {e}")

    try:
        # ============================================================
        # Step 1: 获取指数数据
        # ============================================================
        logger.info(">>> Step 1: 获取指数数据")
        ixic_df = fetcher.fetch_index_history(INDEX_TICKERS["ixic"])
        ndx_df = fetcher.fetch_index_history(INDEX_TICKERS["ndx"])
        vix_df = fetcher.fetch_index_history(INDEX_TICKERS["vix"])

        # ============================================================
        # Step 2: 计算指数技术指标
        # ============================================================
        logger.info(">>> Step 2: 计算指数技术指标")
        ixic_df = calc_all_indicators(ixic_df)
        ndx_df = calc_all_indicators(ndx_df)

        # ============================================================
        # Step 3: 获取个股数据（批量）
        # ============================================================
        logger.info(">>> Step 3: 批量获取个股数据")
        all_tickers = []
        for group in STOCK_UNIVERSE.values():
            all_tickers.extend(group)

        # 如果启用港股/A股，添加相关股票
        if ENABLE_HK_A_SHARE:
            for group in HK_STOCK_UNIVERSE.values():
                all_tickers.extend(group)
            for group in A_SHARE_UNIVERSE.values():
                all_tickers.extend(group)
            logger.info(f"已添加港股/A股到股票池，当前共 {len(all_tickers)} 只")

        stocks_data = fetcher.fetch_stocks_batch(all_tickers)

        # ============================================================
        # Step 4: 计算个股指标并生成推荐
        # ============================================================
        logger.info(">>> Step 4: 分析个股并生成推荐")
        stock_recommendations = {}  # 按板块分组

        for sector_name, tickers in STOCK_UNIVERSE.items():
            stock_recommendations[sector_name] = []
            for ticker in tickers:
                stock_df = stocks_data.get(ticker)
                rec = analyze_stock(fetcher, ticker, stock_df)
                if rec:
                    stock_recommendations[sector_name].append(rec)

        # 港股/A股分析
        if ENABLE_HK_A_SHARE:
            for sector_name, tickers in HK_STOCK_UNIVERSE.items():
                stock_recommendations[f"港股-{sector_name}"] = []
                for ticker in tickers:
                    stock_df = stocks_data.get(ticker)
                    rec = analyze_stock(fetcher, ticker, stock_df)
                    if rec:
                        stock_recommendations[f"港股-{sector_name}"].append(rec)

            for sector_name, tickers in A_SHARE_UNIVERSE.items():
                stock_recommendations[f"A股-{sector_name}"] = []
                for ticker in tickers:
                    stock_df = stocks_data.get(ticker)
                    rec = analyze_stock(fetcher, ticker, stock_df)
                    if rec:
                        stock_recommendations[f"A股-{sector_name}"].append(rec)

        # ============================================================
        # Step 5: 动态筛选 NASDAQ 涨幅榜
        # ============================================================
        logger.info(">>> Step 5: 筛选 NASDAQ 涨幅榜")
        dynamic_gainers = fetcher.screen_top_nasdaq_gainers()
        logger.info(f"筛选到 {len(dynamic_gainers)} 只涨幅榜股票")

        # ============================================================
        # Step 6: 市场宽度分析
        # ============================================================
        logger.info(">>> Step 6: 市场宽度分析")
        all_stocks_flat = []
        for stocks in stock_recommendations.values():
            all_stocks_flat.extend(stocks)
        breadth = analyze_market_breadth(all_stocks_flat)

        # ============================================================
        # Step 7: VIX 情绪分析
        # ============================================================
        logger.info(">>> Step 7: VIX 情绪分析")
        vix_latest = 20.0  # 默认值
        if vix_df is not None and not vix_df.empty:
            try:
                vix_latest = float(vix_df.iloc[-1]["Close"])
                if math.isnan(vix_latest):
                    vix_latest = 20.0
            except (KeyError, ValueError, IndexError):
                vix_latest = 20.0

        vix_data = {
            "value": round(vix_latest, 2),
            **vix_sentiment(vix_latest)
        }

        # ============================================================
        # Step 8: 趋势与信号分析
        # ============================================================
        logger.info(">>> Step 8: 趋势与信号分析")
        ixic_trend = analyze_trend(ixic_df)
        sr = find_support_resistance(ixic_df)
        signals = generate_signals(ixic_df)

        # ============================================================
        # Step 9: 扩展模块分析（回测 / 板块 / 情绪 / 对比）
        # ============================================================
        logger.info(">>> Step 9: 扩展模块分析")

        # --- 9.1 策略回测 ---
        backtest_result = None
        if ENABLE_BACKTEST:
            try:
                logger.info("  [回测] 运行策略回测...")
                from backtest.engine import BacktestEngine
                from trading.strategy import create_strategy
                # 用 IXIC 指数做主时钟，叠加几只核心个股作为可交易池
                core_tickers = ["NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA"]
                df_by_symbol = {"IXIC": ixic_df}
                for tk in core_tickers:
                    if tk in stocks_data and not stocks_data[tk].empty:
                        df_by_symbol[tk] = stocks_data[tk]
                strategy = create_strategy("multi")
                engine = BacktestEngine(df_by_symbol=df_by_symbol, strategy=strategy)
                bt_result = engine.run()
                # 转成老格式，方便模板渲染
                metrics_dict = bt_result.metrics.to_dict()
                # 兼容旧模板字段名
                metrics_dict["num_trades"] = metrics_dict.get("trade_count", 0)
                metrics_dict["avg_holding_days"] = 0  # 新引擎暂未实现
                metrics_dict["benchmark_return"] = 0  # 新引擎暂未实现
                backtest_result = {
                    "metrics": metrics_dict,
                    "equity_curve": bt_result.portfolio.equity_curve,
                    "trades": getattr(bt_result, "trades", []),
                    "start_ts": str(bt_result.start_ts),
                    "end_ts": str(bt_result.end_ts),
                }
                metrics = backtest_result["metrics"]
                logger.info(f"  [回测] 总收益: {metrics.get('total_return', 0):.2f}% "
                            f"夏普: {metrics.get('sharpe_ratio', 0):.2f} "
                            f"胜率: {metrics.get('win_rate', 0):.1f}%")
            except Exception as e:
                logger.warning(f"  [回测] 回测分析失败: {e}")

        # --- 9.2 板块轮动 ---
        sector_data = None
        if ENABLE_SECTOR_ETF:
            try:
                from sector import fetch_sector_data, get_sector_chart_data
                logger.info("  [板块] 获取板块ETF数据...")
                sector_data = fetch_sector_data(fetcher)
                if sector_data:
                    sector_count = len(sector_data.get("sector_analysis", []))
                    logger.info(f"  [板块] 分析完成，共 {sector_count} 个行业板块")
            except Exception as e:
                logger.warning(f"  [板块] 板块轮动分析失败: {e}")

        # --- 9.3 新闻情绪 ---
        sentiment_data = None
        if ENABLE_NEWS_SENTIMENT:
            try:
                from sentiment import analyze_market_sentiment
                logger.info("  [情绪] 获取市场新闻情绪...")
                all_ticker_list = list(STOCK_UNIVERSE.get("科技", [])[:5])  # 取前5只科技股
                sentiment_data = analyze_market_sentiment(all_ticker_list)
                if sentiment_data:
                    logger.info(f"  [情绪] 整体情绪: {sentiment_data.get('overall_label', '未知')} "
                                f"得分: {sentiment_data.get('overall_score', 0):.2f} "
                                f"新闻数: {len(sentiment_data.get('news_items', []))}")
            except Exception as e:
                logger.warning(f"  [情绪] 新闻情绪分析失败: {e}")

        # --- 9.4 历史报告对比 ---
        comparison_data = None
        if ENABLE_COMPARISON and db_manager:
            try:
                from comparison import compare_with_previous
                logger.info("  [对比] 查询历史报告进行对比...")
                today = datetime.now().strftime("%Y-%m-%d")
                prev_report = db_manager.get_previous_report(today)
                if prev_report:
                    # 注意：ixic_latest 还没定义（它在 Step 10 才赋值），
                    # 这里改为用 ixic_df 最后一行直接提取 close
                    try:
                        _ixic_close = float(ixic_df["Close"].iloc[-1]) if not ixic_df.empty else 0
                    except Exception:
                        _ixic_close = 0
                    comparison_data = compare_with_previous({
                        "ixic_close": _ixic_close,
                        "vix": vix_latest,
                        "breadth": breadth,
                        "trend": ixic_trend,
                        "stock_recommendations": stock_recommendations,
                    }, db_manager)
                    if comparison_data and comparison_data.get("has_previous"):
                        logger.info(f"  [对比] 与 {comparison_data['previous_date']} 的报告对比完成")
                    else:
                        logger.info("  [对比] 无历史报告可对比（首次运行）")
                else:
                    logger.info("  [对比] 无历史报告可对比（首次运行）")
            except Exception as e:
                logger.warning(f"  [对比] 历史对比分析失败: {e}")

        # ============================================================
        # Step 10: 组装并生成报告
        # ============================================================
        logger.info(">>> Step 10: 组装并生成报告")
        ixic_latest = extract_latest(ixic_df)
        ndx_latest = extract_latest(ndx_df)

        report_data = {
            "ixic_df": ixic_df,
            "ndx_df": ndx_df,
            "ixic_latest": ixic_latest,
            "ndx_latest": ndx_latest,
            "vix_data": vix_data,
            "trend": ixic_trend,
            "support_resistance": sr,
            "signals": signals,
            "market_breadth": breadth,
            "stock_recommendations": stock_recommendations,
            "dynamic_gainers": dynamic_gainers,
            "market_summary": {
                "ixic_close": ixic_latest["close"] if ixic_latest else 0,
                "ndx_close": ndx_latest["close"] if ndx_latest else 0,
                "vix": vix_latest,
                "breadth": breadth,
            },
            # 新增模块数据
            "backtest_result": backtest_result,
            "sector_data": sector_data,
            "sentiment_data": sentiment_data,
            "comparison_data": comparison_data,
        }

        output_path = generator.generate(report_data)

        logger.info("=" * 60)
        logger.info(f"报告生成成功!")
        logger.info(f"输出路径: {output_path}")
        logger.info("=" * 60)

        # 标准输出文件路径（供 Schedule 工具识别）
        print(f"\nREPORT_OUTPUT:{output_path}")

        return output_path

    except Exception as e:
        logger.error(f"报告生成失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
