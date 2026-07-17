/**
 * ReviewToast.tsx — 卖出后复盘卡片 (v2.4 Phase 2)
 *
 * 右下角浮动玻璃卡片：评分 + 盈亏 + 错误模式 + 查看详情
 */
import { Link } from "react-router-dom";
import { X, TrendingUp, TrendingDown } from "lucide-react";

interface Review {
  trade_id: string;
  symbol: string;
  pnl: number;
  pnl_pct: number;
  score: number;
  mistakes: { pattern: string; detail: string }[];
  summary: string;
}

export function ReviewToast({ review, onClose }: { review: Review; onClose: () => void }) {
  const isProfit = review.pnl >= 0;
  const scoreColor = review.score >= 70 ? "text-emerald-400" : review.score >= 50 ? "text-amber-400" : "text-rose-400";

  return (
    <div className="fixed bottom-6 right-6 z-50 w-80 glass-card specular-edge p-4 space-y-3
                    animate-[slideUp_0.4s_cubic-bezier(.22,1,.36,1)]">
      {/* 头部 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {isProfit
            ? <TrendingUp className="w-4 h-4 text-emerald-400" />
            : <TrendingDown className="w-4 h-4 text-rose-400" />}
          <span className="text-sm font-semibold text-fg">复盘已生成</span>
        </div>
        <button onClick={onClose} className="p-1 rounded-lg hover:bg-white/[0.06] text-fg-dim transition">
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* 核心数据 */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-fg-dim">{review.symbol}</p>
          <p className={`text-lg font-bold ${isProfit ? "text-emerald-400" : "text-rose-400"}`}>
            {isProfit ? "+" : ""}{review.pnl_pct.toFixed(1)}%
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs text-fg-dim">评分</p>
          <p className={`text-lg font-bold ${scoreColor}`}>{review.score.toFixed(0)}</p>
        </div>
      </div>

      {/* 错误模式提示 */}
      {review.mistakes.length > 0 && (
        <div className="glass-light rounded-[10px] px-3 py-2">
          <p className="text-xs text-amber-400">
            ⚠️ 发现 {review.mistakes.length} 个可改进点
          </p>
        </div>
      )}

      {/* 查看详情 */}
      <Link
        to="/me/reviews"
        className="glass-btn-primary block text-center py-2 rounded-[10px] text-xs font-semibold"
        onClick={onClose}
      >
        查看完整复盘
      </Link>
    </div>
  );
}
