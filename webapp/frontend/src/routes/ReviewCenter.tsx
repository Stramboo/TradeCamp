/**
 * ReviewCenter.tsx — 交易复盘中心 (v2.3 Phase 3)
 *
 * 展示交易复盘报告、错误模式统计、评分趋势
 */
import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";

interface Review {
  trade_id: string;
  symbol: string;
  side: string;
  quantity: number;
  price: number;
  pnl: number;
  pnl_pct: number;
  holding_days: number;
  score: number;
  mistakes: { pattern: string; confidence: number; detail: string }[];
  summary: string;
  created_at: number;
}

interface MistakePattern {
  name: string;
  description: string;
  suggestion: string;
}

export function ReviewCenter() {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [patterns, setPatterns] = useState<Record<string, MistakePattern>>({});
  const [stats, setStats] = useState<{ avg_score: number; win_rate: number; score_trend: { date: number; score: number }[] } | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedReview, setSelectedReview] = useState<Review | null>(null);

  useEffect(() => {
    Promise.all([
      fetch("/api/reviews").then((r) => r.json()).catch(() => []),
      fetch("/api/reviews/patterns").then((r) => r.json()).catch(() => ({})),
      fetch("/api/reviews/stats").then((r) => r.json()).catch(() => null),
    ]).then(([revs, pats, sts]) => {
      setReviews(revs);
      setPatterns(pats);
      setStats(sts);
      setLoading(false);
    });
  }, []);

  // 统计错误模式频率
  const mistakeStats = reviews.reduce<Record<string, number>>((acc, r) => {
    for (const m of r.mistakes) {
      acc[m.pattern] = (acc[m.pattern] || 0) + 1;
    }
    return acc;
  }, {});

  const avgScore = reviews.length > 0
    ? reviews.reduce((sum, r) => sum + r.score, 0) / reviews.length
    : 0;

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto py-8 px-4 space-y-4">
        <div className="h-6 w-32 rounded bg-bg-subtle animate-pulse" />
        <div className="h-8 w-48 rounded bg-bg-subtle animate-pulse" />
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 rounded-xl bg-bg-panel animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 space-y-6">
      {/* 头部 */}
      <div className="flex items-center justify-between">
        <div>
          <Link to="/me" className="text-xs text-fg-dim hover:text-fg transition">
            ← 返回我的成长
          </Link>
          <h1 className="text-xl font-bold text-fg mt-1">交易复盘中心</h1>
        </div>
        <div className="text-right">
          <p className="text-xs text-fg-dim">平均评分</p>
          <p className={`text-2xl font-bold ${avgScore >= 70 ? "text-emerald-400" : avgScore >= 50 ? "text-amber-400" : "text-rose-400"}`}>
            {avgScore.toFixed(1)}
          </p>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-card p-4 text-center">
          <p className="text-2xl font-bold text-fg">{reviews.length}</p>
          <p className="text-xs text-fg-dim mt-1">复盘交易数</p>
        </div>
        <div className="glass-card p-4 text-center">
          <p className="text-2xl font-bold text-emerald-400">
            {reviews.filter((r) => r.pnl > 0).length}
          </p>
          <p className="text-xs text-fg-dim mt-1">盈利交易</p>
        </div>
        <div className="glass-card p-4 text-center">
          <p className="text-2xl font-bold text-rose-400">
            {reviews.filter((r) => r.pnl < 0).length}
          </p>
          <p className="text-xs text-fg-dim mt-1">亏损交易</p>
        </div>
        <div className="glass-card p-4 text-center">
          <p className="text-2xl font-bold text-blue-400">
            {stats ? `${stats.win_rate}%` : "—"}
          </p>
          <p className="text-xs text-fg-dim mt-1">胜率</p>
        </div>
      </div>

      {/* 评分趋势迷你图 */}
      {stats && stats.score_trend.length >= 3 && (
        <div className="glass-card p-4 space-y-2">
          <p className="text-xs text-fg-muted uppercase tracking-wider">评分趋势</p>
          <div className="flex items-end gap-1 h-16">
            {stats.score_trend.map((t, i) => (
              <div
                key={i}
                title={`${t.score} 分`}
                className={`flex-1 rounded-t transition-all ${
                  t.score >= 70 ? "bg-emerald-500/60" : t.score >= 50 ? "bg-amber-500/60" : "bg-rose-500/60"
                }`}
                style={{ height: `${Math.max(8, t.score)}%` }}
              />
            ))}
          </div>
        </div>
      )}

      {/* 错误模式统计 */}
      {Object.keys(mistakeStats).length > 0 && (
        <div className="glass-card p-5 space-y-3">
          <p className="text-xs text-fg-muted uppercase tracking-wider">常见错误模式</p>
          <div className="space-y-2">
            {Object.entries(mistakeStats)
              .sort((a, b) => b[1] - a[1])
              .map(([pattern, count]) => {
                const info = patterns[pattern];
                return (
                  <div key={pattern} className="flex items-center gap-3">
                    <div className="flex-1">
                      <p className="text-sm text-fg">{info?.name || pattern}</p>
                      <p className="text-xs text-fg-dim">{info?.description}</p>
                    </div>
                    <span className="text-sm font-semibold text-amber-400">{count} 次</span>
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* 复盘列表 */}
      <div className="space-y-3">
        <p className="text-xs text-fg-muted uppercase tracking-wider">复盘记录</p>
        {reviews.length === 0 ? (
          <div className="glass-card p-8 text-center">
            <p className="text-sm text-fg-dim">暂无复盘记录</p>
            <p className="text-xs text-fg-muted mt-2">
              完成一笔沙盒交易后，系统会自动生成复盘报告
            </p>
            <Link
              to="/practice/free"
              className="inline-block mt-4 px-4 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-sm text-emerald-400 hover:bg-emerald-500/20 transition"
            >
              去交易 →
            </Link>
          </div>
        ) : (
          <div className="space-y-2">
            {reviews.map((r) => (
              <button
                key={r.trade_id}
                onClick={() => setSelectedReview(selectedReview?.trade_id === r.trade_id ? null : r)}
                className="w-full text-left glass-card p-4 hover:border-emerald-500/30 transition"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className={`text-lg font-bold ${r.pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                      {r.pnl >= 0 ? "+" : ""}{r.pnl_pct.toFixed(1)}%
                    </span>
                    <div>
                      <p className="text-sm font-semibold text-fg">{r.symbol}</p>
                      <p className="text-xs text-fg-dim">
                        {r.side === "BUY" ? "买入" : "卖出"} {r.quantity} 股 @ ${r.price.toFixed(2)}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`text-sm font-semibold ${r.score >= 70 ? "text-emerald-400" : r.score >= 50 ? "text-amber-400" : "text-rose-400"}`}>
                      {r.score.toFixed(0)} 分
                    </p>
                    <p className="text-xs text-fg-dim">
                      {new Date(r.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                {/* 展开的详细内容 */}
                {selectedReview?.trade_id === r.trade_id && (
                  <div className="mt-4 pt-4 border-t border-line space-y-3">
                    <div className="text-sm text-fg-muted leading-relaxed whitespace-pre-line">
                      {r.summary}
                    </div>
                    {r.mistakes.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-xs text-fg-muted uppercase tracking-wider">需要改进</p>
                        {r.mistakes.map((m, i) => {
                          const info = patterns[m.pattern];
                          return (
                            <div key={i} className="rounded-lg bg-amber-500/5 border border-amber-500/20 p-3">
                              <p className="text-sm font-medium text-amber-400">{info?.name || m.pattern}</p>
                              <p className="text-xs text-fg-muted mt-1">{m.detail}</p>
                              <p className="text-xs text-fg-dim mt-2">💡 {info?.suggestion}</p>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                )}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
