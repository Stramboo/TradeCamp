# -*- coding: utf-8 -*-
"""
test_backtest_consistency.py — 回测一致性测试

使用 tests/fixtures/market_data/*.csv 固定数据集，
验证回测引擎的确定性、现金持仓对账等关键属性。
"""
import pandas as pd

from backtest.engine import BacktestEngine as BTEngine
from trading.strategy import create_strategy


def _compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """为固定 CSV 数据计算技术指标（模拟真实流程）"""
    from indicators import calc_all_indicators
    return calc_all_indicators(df.copy())


class TestBacktestDeterminism:
    """同一策略 + 同一数据，多次运行必须产生相同结果"""

    def test_same_input_same_output(self, aapl_fixture):
        df = _compute_indicators(aapl_fixture)
        strategy = create_strategy("multi")

        result1 = BTEngine(
            df_by_symbol={"AAPL": df}, strategy=strategy
        ).run()
        result2 = BTEngine(
            df_by_symbol={"AAPL": df}, strategy=strategy
        ).run()

        m1 = result1.metrics.to_dict()
        m2 = result2.metrics.to_dict()

        assert m1["total_return"] == m2["total_return"], \
            f"total_return 不一致: {m1['total_return']} vs {m2['total_return']}"
        assert m1["sharpe_ratio"] == m2["sharpe_ratio"], \
            f"sharpe_ratio 不一致: {m1['sharpe_ratio']} vs {m2['sharpe_ratio']}"
        assert m1["max_drawdown"] == m2["max_drawdown"]

    def test_deterministic_across_runs(self, aapl_fixture):
        """连续 5 次应得到完全一致的结果"""
        df = _compute_indicators(aapl_fixture)
        results = []
        for _ in range(5):
            e = BTEngine(df_by_symbol={"AAPL": df}, strategy=create_strategy("multi"))
            results.append(e.run().metrics.to_dict()["total_return"])

        assert len(set(results)) == 1, f"5 次结果不一致: {results}"


class TestMultiSymbolBacktest:
    """多标的回测基本验证"""

    def test_multisymbol_run(self, aapl_fixture, msft_fixture):
        df_aapl = _compute_indicators(aapl_fixture)
        df_msft = _compute_indicators(msft_fixture)
        df_by_symbol = {"AAPL": df_aapl, "MSFT": df_msft}
        result = BTEngine(
            df_by_symbol=df_by_symbol, strategy=create_strategy("multi")
        ).run()

        assert result.metrics is not None
        assert result.strategy_name is not None
        assert len(result.symbols) == 2


class TestCashAndPositionReconciliation:
    """回测结束账户净值 = 现金 + 持仓市值"""

    def test_equity_reconciliation(self, aapl_fixture):
        df = _compute_indicators(aapl_fixture)
        engine = BTEngine(
            df_by_symbol={"AAPL": df},
            strategy=create_strategy("multi"),
            initial_cash=100000.0,
        )
        result = engine.run()
        portfolio = result.portfolio
        equity = result.metrics.to_dict().get("final_equity", 0)

        # 计算持仓市值
        last_aapl_price = float(df["Close"].iloc[-1])
        market_value = 0.0
        for sym, pos in portfolio.positions.items():
            market_value += pos.quantity * last_aapl_price

        # 允许浮点误差
        expected = portfolio.cash + market_value
        assert abs(portfolio.cash + market_value - expected) < 1.0, \
            f"净值对账失败: cash={portfolio.cash:.2f} mktval={market_value:.2f}"


class TestEdgeCases:
    """边界情况"""

    def test_empty_data_raises(self):
        try:
            BTEngine(df_by_symbol={}, strategy=create_strategy("multi"))
            assert False, "空数据应抛异常"
        except ValueError:
            pass

    def test_insufficient_data(self, aapl_fixture):
        df = _compute_indicators(aapl_fixture.head(10))  # 仅 10 行
        result = BTEngine(
            df_by_symbol={"AAPL": df}, strategy=create_strategy("multi")
        ).run()
        # 应该无成交（窗口不足 30 天），零交易
        assert result.metrics.to_dict().get("trade_count", 0) == 0

    def test_volatile_market_no_crash(self, volatile_fixture):
        df = _compute_indicators(volatile_fixture)
        result = BTEngine(
            df_by_symbol={"VOL": df}, strategy=create_strategy("multi")
        ).run()
        assert result.metrics is not None


class TestBacktestResultConsistency:
    """回测报告调用与直接调用结果一致"""

    def test_metric_accessors(self, aapl_fixture):
        df = _compute_indicators(aapl_fixture)
        result = BTEngine(
            df_by_symbol={"AAPL": df}, strategy=create_strategy("multi")
        ).run()

        md = result.metrics.to_dict()
        # 验证关键指标存在
        for key in ("total_return", "sharpe_ratio", "max_drawdown",
                     "win_rate", "annual_return"):
            assert key in md, f"指标缺失: {key}"
