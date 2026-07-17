/**
 * PortfolioAnalytics.tsx — 组合分析仪表盘 (v2.3 Phase 6)
 *
 * 持仓分布 + 盈亏统计 + 风险指标
 */
import { useMemo } from "react";

interface Position {
  symbol: string;
  quantity: number;
  avg_cost: number;
}

interface PortfolioAnalyticsProps {
  positions: Position[];
  quotes: Record<string, { price: number }>;
  cash: number;
}

const COLORS = [
  "bg-emerald-500", "bg-blue-500", "bg-amber-500",
  "bg-rose-500", "bg-purple-500", "bg-cyan-500",
];

export function PortfolioAnalytics({ positions, quotes, cash }: PortfolioAnalyticsProps) {
  const analytics = useMemo(() => {
    const totalValue = positions.reduce((sum, p) => {
      const price = quotes[p.symbol]?.price || p.avg_cost;
      return sum + price * p.quantity;
    }, 0) + cash;

    const positionData = positions.map((p, i) => {
      const price = quotes[p.symbol]?.price || p.avg_cost;
      const value = price * p.quantity;
      const pct = totalValue > 0 ? (value / totalValue) * 100 : 0;
      const pnl = (price - p.avg_cost) * p.quantity;
      const pnlPct = p.avg_cost > 0 ? ((price / p.avg_cost) - 1) * 100 : 0;
      return {
        symbol: p.symbol,
        value,
        pct,
        pnl,
        pnlPct,
        color: COLORS[i % COLORS.length],
      };
    });

    const cashPct = totalValue > 0 ? (cash / totalValue) * 100 : 0;
    const totalPnl = positionData.reduce((sum, p) => sum + p.pnl, 0);

    return { totalValue, positionData, cashPct, totalPnl };
  }, [positions, quotes, cash]);

  if (positions.length === 0) {
    return (
      <div className="rounded-xl bg-bg-panel border border-line p-6 text-center">
        <p className="text-sm text-fg-dim">暂无持仓数据</p>
        <p className="text-xs text-fg-muted mt-1">完成一笔交易后，这里会显示组合分析</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 持仓分布 */}
      <div className="rounded-xl bg-bg-panel border border-line p-4 space-y-3">
        <p className="text-xs text-fg-muted uppercase tracking-wider">持仓分布</p>
        <div className="space-y-2">
          {analytics.positionData.map((p) => (
            <div key={p.symbol} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-fg font-medium">{p.symbol}</span>
                <span className="text-fg-muted">{p.pct.toFixed(1)}%</span>
              </div>
              <div className="h-2 rounded-full bg-bg-subtle overflow-hidden">
                <div
                  className={`h-full rounded-full ${p.color}`}
                  style={{ width: `${p.pct}%` }}
                />
              </div>
              <div className="flex items-center justify-between text-[10px]">
                <span className="text-fg-dim">${p.value.toFixed(0)}</span>
                <span className={p.pnl >= 0 ? "text-emerald-400" : "text-rose-400"}>
                  {p.pnl >= 0 ? "+" : ""}{p.pnlPct.toFixed(1)}%
                </span>
              </div>
            </div>
          ))}
          {/* 现金 */}
          <div className="space-y-1 pt-2 border-t border-line">
            <div className="flex items-center justify-between text-xs">
              <span className="text-fg-muted">现金</span>
              <span className="text-fg-muted">{analytics.cashPct.toFixed(1)}%</span>
            </div>
            <div className="h-2 rounded-full bg-bg-subtle overflow-hidden">
              <div
                className="h-full rounded-full bg-slate-500"
                style={{ width: `${analytics.cashPct}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* 盈亏统计 */}
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-xl bg-bg-panel border border-line p-4 text-center">
          <p className="text-xs text-fg-muted">总盈亏</p>
          <p className={`text-lg font-bold ${analytics.totalPnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
            {analytics.totalPnl >= 0 ? "+" : ""}${analytics.totalPnl.toFixed(0)}
          </p>
        </div>
        <div className="rounded-xl bg-bg-panel border border-line p-4 text-center">
          <p className="text-xs text-fg-muted">持仓数量</p>
          <p className="text-lg font-bold text-fg">{positions.length}</p>
        </div>
      </div>
    </div>
  );
}
