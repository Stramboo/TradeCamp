# -*- coding: utf-8 -*-
"""
NASDAQ 每日分析报告 - 报告生成模块
使用 Jinja2 渲染 HTML 模板，将 DataFrame 转换为 ECharts JSON 数据格式
支持回测、情绪、板块、对比等新增数据模块
"""

import json
import os
import shutil
import math
import logging
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from config import (
    OUTPUT_DIR, TEMPLATE_DIR, CHART_DISPLAY_DAYS, MA_PERIODS, BASE_DIR,
    REPORTS_ARCHIVE_DIR
)

logger = logging.getLogger(__name__)


class ReportGenerator:
    """HTML 报告生成器"""

    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(TEMPLATE_DIR),
            autoescape=False  # HTML 模板不转义，允许注入 JSON
        )

    def _safe_float(self, value):
        """安全转换浮点数，NaN/Inf 返回 None"""
        if value is None:
            return None
        try:
            f = float(value)
            if math.isnan(f) or math.isinf(f):
                return None
            return round(f, 2)
        except (ValueError, TypeError):
            return None

    def _prepare_chart_data(self, df, display_days=CHART_DISPLAY_DAYS):
        """将 DataFrame 转换为 ECharts 所需的数据格式"""
        if df is None or df.empty:
            return {
                "dates": [], "candlestick": [], "ma_lines": {f"MA{p}": [] for p in MA_PERIODS},
                "volume": [], "boll_upper": [], "boll_lower": [],
                "macd_dif": [], "macd_dea": [], "macd_hist": [],
                "rsi": [], "k": [], "d": [], "j": [],
                "atr": [], "obv": [], "wr": [], "cci": [], "vwap": []
            }

        # 取最近 display_days 天数据
        recent = df.tail(display_days)

        # 日期
        dates = recent.index.strftime("%Y-%m-%d").tolist()

        # K线数据: [open, close, low, high]
        candlestick = []
        for _, row in recent.iterrows():
            candlestick.append([
                self._safe_float(row.get("Open")),
                self._safe_float(row.get("Close")),
                self._safe_float(row.get("Low")),
                self._safe_float(row.get("High")),
            ])

        # MA 线数据
        ma_lines = {}
        for p in MA_PERIODS:
            col = f"MA{p}"
            ma_lines[col] = [self._safe_float(v) for v in recent[col].tolist()] if col in recent.columns else []

        # 成交量数据（带涨跌标记）
        volume = []
        if "Volume" in recent.columns:
            closes = recent["Close"].tolist()
            opens = recent["Open"].tolist()
            volumes = recent["Volume"].tolist()
            for i in range(len(volumes)):
                vol = volumes[i]
                if hasattr(vol, 'item'):
                    vol = vol.item()
                volume.append({
                    "value": int(vol) if not math.isnan(float(vol)) else 0,
                    "isup": float(closes[i]) >= float(opens[i]) if not math.isnan(float(closes[i])) and not math.isnan(float(opens[i])) else True
                })

        # 布林带数据
        boll_upper = [self._safe_float(v) for v in recent["BOLL_UPPER"].tolist()] if "BOLL_UPPER" in recent.columns else []
        boll_lower = [self._safe_float(v) for v in recent["BOLL_LOWER"].tolist()] if "BOLL_LOWER" in recent.columns else []

        # MACD 数据
        macd_dif = [self._safe_float(v) for v in recent["DIF"].tolist()] if "DIF" in recent.columns else []
        macd_dea = [self._safe_float(v) for v in recent["DEA"].tolist()] if "DEA" in recent.columns else []
        macd_hist = [self._safe_float(v) for v in recent["MACD_HIST"].tolist()] if "MACD_HIST" in recent.columns else []

        # RSI 数据
        rsi = [self._safe_float(v) for v in recent["RSI"].tolist()] if "RSI" in recent.columns else []

        # KDJ 数据
        k = [self._safe_float(v) for v in recent["K"].tolist()] if "K" in recent.columns else []
        d = [self._safe_float(v) for v in recent["D"].tolist()] if "D" in recent.columns else []
        j = [self._safe_float(v) for v in recent["J"].tolist()] if "J" in recent.columns else []

        # 新增指标数据
        atr = [self._safe_float(v) for v in recent["ATR"].tolist()] if "ATR" in recent.columns else []
        obv = [self._safe_float(v) for v in recent["OBV"].tolist()] if "OBV" in recent.columns else []
        wr = [self._safe_float(v) for v in recent["WR"].tolist()] if "WR" in recent.columns else []
        cci = [self._safe_float(v) for v in recent["CCI"].tolist()] if "CCI" in recent.columns else []
        vwap = [self._safe_float(v) for v in recent["VWAP"].tolist()] if "VWAP" in recent.columns else []

        return {
            "dates": dates,
            "candlestick": candlestick,
            "ma_lines": ma_lines,
            "volume": volume,
            "boll_upper": boll_upper,
            "boll_lower": boll_lower,
            "macd_dif": macd_dif,
            "macd_dea": macd_dea,
            "macd_hist": macd_hist,
            "rsi": rsi,
            "k": k,
            "d": d,
            "j": j,
            "atr": atr,
            "obv": obv,
            "wr": wr,
            "cci": cci,
            "vwap": vwap,
        }

    def _prepare_backtest_chart(self, backtest_result):
        """准备回测净值曲线图表数据"""
        if not backtest_result:
            return None

        equity_curve = backtest_result.get("equity_curve", [])
        if not equity_curve:
            return None

        # 兼容两种 equity_curve 格式：
        # 1. list[dict]（旧版本，含 date/equity/close 字段）
        # 2. list[tuple[str, float]]（新 BacktestEngine 输出 (timestamp, equity)）
        dates = []
        equity_values = []
        benchmark_values = []
        for e in equity_curve:
            if isinstance(e, tuple):
                # 新格式：(timestamp, equity)
                ts, eq = e
                dates.append(str(ts))
                equity_values.append(float(eq) if eq is not None else 0.0)
                benchmark_values.append(0.0)  # 新格式无基准，填 0
            elif isinstance(e, dict):
                dates.append(e.get("date", ""))
                equity_values.append(e.get("equity", 0))
                benchmark_values.append(e.get("close", 0))

        return {
            "dates": dates,
            "equity": equity_values,
            "benchmark": benchmark_values,
            "metrics": backtest_result.get("metrics", {}),
            "trades": backtest_result.get("trades", []),
        }

    def _prepare_sector_chart(self, sector_data):
        """准备板块轮动图表数据"""
        if not sector_data:
            return None

        sector_analysis = sector_data.get("sector_analysis", [])
        broad_analysis = sector_data.get("broad_analysis", [])

        if not sector_analysis:
            return None

        return {
            "sectors": [item["sector"] for item in sector_analysis],
            "tickers": [item["ticker"] for item in sector_analysis],
            "ret_5d": [item["ret_5d"] for item in sector_analysis],
            "ret_20d": [item["ret_20d"] for item in sector_analysis],
            "momentum_scores": [item["momentum_score"] for item in sector_analysis],
            "labels": [item["label"] for item in sector_analysis],
            "ranks": [item["rank"] for item in sector_analysis],
            "broad_indices": broad_analysis,
        }

    def _prepare_sentiment_data(self, sentiment_data):
        """准备情绪分析数据"""
        if not sentiment_data:
            return None

        return {
            "overall_score": sentiment_data.get("overall_score", 0),
            "overall_label": sentiment_data.get("overall_label", "无数据"),
            "news_items": sentiment_data.get("news_items", [])[:10],
            "news_count": len(sentiment_data.get("news_items", [])),
        }

    def _prepare_comparison_data(self, comparison_data):
        """准备历史对比数据"""
        if not comparison_data or not comparison_data.get("has_previous"):
            return None

        return {
            "has_previous": True,
            "previous_date": comparison_data.get("previous_date", ""),
            "changes": comparison_data.get("changes", []),
        }

    def generate(self, report_data):
        """
        生成完整 HTML 报告
        report_data: dict 包含所有报告数据
        返回: 输出文件路径
        """
        logger.info("开始生成 HTML 报告...")

        # 准备图表数据
        ixic_df = report_data.get("ixic_df")
        ndx_df = report_data.get("ndx_df")

        chart_json = {
            "ixic": self._prepare_chart_data(ixic_df),
            "ndx": self._prepare_chart_data(ndx_df),
            "dynamic_gainers": report_data.get("dynamic_gainers", []),
            "backtest": self._prepare_backtest_chart(report_data.get("backtest_result")),
            "sector": self._prepare_sector_chart(report_data.get("sector_data")),
        }

        # 准备新增模块数据
        sentiment_data = self._prepare_sentiment_data(report_data.get("sentiment_data"))
        comparison_data = self._prepare_comparison_data(report_data.get("comparison_data"))

        # 渲染模板
        template = self.env.get_template("report_template.html")
        html = template.render(
            report_date=datetime.now().strftime("%Y-%m-%d"),
            report_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            market_summary=report_data.get("market_summary", {}),
            ixic_latest=report_data.get("ixic_latest"),
            ndx_latest=report_data.get("ndx_latest"),
            vix_data=report_data.get("vix_data", {"value": 20, "level": "中性", "color": "#d29922", "desc": "数据不可用"}),
            trend=report_data.get("trend", {"direction": "数据不足", "level": "sideways", "score": 2.5}),
            support_resistance=report_data.get("support_resistance", {"support1": 0, "support2": 0, "resistance1": 0, "resistance2": 0}),
            signals=report_data.get("signals", []),
            market_breadth=report_data.get("market_breadth", {"up": 0, "down": 0, "flat": 0, "breadth_ratio": 0}),
            stock_recommendations=report_data.get("stock_recommendations", {}),
            dynamic_gainers=report_data.get("dynamic_gainers", []),
            chart_data=json.dumps(chart_json, ensure_ascii=False, default=str),
            # 新增模块数据
            backtest_result=report_data.get("backtest_result"),
            sentiment_data=sentiment_data,
            sector_data=report_data.get("sector_data"),
            comparison_data=comparison_data,
        )

        # 保存到输出目录
        filename = f"nasdaq_report_{datetime.now().strftime('%Y-%m-%d')}.html"
        output_path = os.path.join(OUTPUT_DIR, filename)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        # 确保 echarts.min.js 存在于输出目录
        echarts_src = os.path.join(BASE_DIR, "echarts.min.js")
        echarts_dst = os.path.join(OUTPUT_DIR, "echarts.min.js")
        if os.path.exists(echarts_src) and echarts_src != echarts_dst:
            shutil.copy2(echarts_src, echarts_dst)
            logger.info(f"已复制 echarts.min.js 到输出目录")

        # 报告归档
        self._archive_report(output_path, report_data)

        logger.info(f"HTML 报告已生成: {output_path}")
        return output_path

    def _archive_report(self, output_path, report_data):
        """将报告归档到 reports/ 目录并写入数据库"""
        try:
            # 复制到归档目录
            if REPORTS_ARCHIVE_DIR != OUTPUT_DIR:
                os.makedirs(REPORTS_ARCHIVE_DIR, exist_ok=True)
                archive_path = os.path.join(REPORTS_ARCHIVE_DIR, os.path.basename(output_path))
                shutil.copy2(output_path, archive_path)
                logger.info(f"报告已归档: {archive_path}")

            # 写入数据库
            self._save_to_db(output_path, report_data)
        except Exception as e:
            logger.warning(f"报告归档失败（不影响主流程）: {e}")

    def _save_to_db(self, output_path, report_data):
        """将报告元数据写入 SQLite 数据库"""
        try:
            from db import DbManager
            db = DbManager()
            today = datetime.now().strftime("%Y-%m-%d")

            ixic_close = None
            if report_data.get("ixic_latest"):
                ixic_close = report_data["ixic_latest"].get("close")

            vix_val = report_data.get("vix_data", {}).get("value")
            trend_dir = report_data.get("trend", {}).get("direction", "")
            breadth = report_data.get("market_breadth", {}).get("breadth_ratio")
            sentiment = None
            if report_data.get("sentiment_data"):
                sentiment = report_data["sentiment_data"].get("overall_label")

            db.upsert_report(today, output_path, ixic_close, vix_val, trend_dir, breadth, sentiment)

            # 写入个股指标快照
            for sector_stocks in report_data.get("stock_recommendations", {}).values():
                for stock in sector_stocks:
                    ticker = stock.get("ticker", "")
                    rsi_val = stock.get("rsi")
                    rec = stock.get("recommendation", "")
                    db.upsert_indicator_snapshot(
                        ticker=ticker, date=today,
                        rsi=rsi_val, macd_hist=None, atr=None,
                        trend=stock.get("trend", ""), recommendation=rec,
                        vix=vix_val, breadth_ratio=breadth
                    )

            # 写入回测结果
            if report_data.get("backtest_result"):
                metrics = report_data["backtest_result"].get("metrics", {})
                if metrics:
                    db.upsert_backtest_result(today, "MACD_RSI_WR", metrics)

            logger.info(f"报告数据已写入数据库")
        except Exception as e:
            logger.warning(f"数据库写入失败: {e}")
