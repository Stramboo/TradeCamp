/**
 * Analysis.tsx — "分析"页面
 *
 * 整合 NDX 每日分析报告的核心数据：
 * 1. NDX 大盘概览（价格/均线/RSI/情绪）
 * 2. 关键股票分析（按板块分组，含技术指标+推荐）
 * 3. 板块轮动排行
 * 4. 市场宽度 & 情绪面板
 *
 * 数据来源：后端 /api/analysis/full（缓存 5 分钟，失败降级到 mock）
 */

import { useEffect, useState, useMemo } from "react";
import {
  TrendingUp, TrendingDown, Minus, BarChart3, PieChart, Gauge,
  FileText, AlertCircle, RefreshCw, Layers, Target, Activity,
} from "lucide-react";
import { api, type FullAnalysisData, type StockAnalysisData, type SectorAnalysisData } from "../lib/api";

/* ================================================================
 * 格式化工具
 * ================================================================ */

const fmt = (v: number, frac = 2) =>
  v.toLocaleString("en-US", { minimumFractionDigits: frac, maximumFractionDigits: frac });
const pct = (v: number, withSign = true) =>
  `${v >= 0 && withSign ? "+" : ""}${v.toFixed(2)}%`;
const fmtVol = (v: number) => {
  if (v >= 1e9) return `${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `${(v / 1e6).toFixed(1)}M`;
  return v.toLocaleString();
};

/* ================================================================
 * 子组件
 * ================================================================ */

/** 大盘概览卡片 */
function NdxOverview({ data }: { data: FullAnalysisData["ndx"] }) {
  const pos = data.change_pct >= 0;
  const Arrow = pos ? TrendingUp : data.change_pct < 0 ? TrendingDown : Minus;
  const color = pos ? "text-emerald-400" : "text-rose-400";

  return (
    <div className="panel-card p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="flex items-center gap-2 text-fg text-lg font-semibold">
          <Activity className="h-5 w-5 text-emerald-400" />
          NDX 大盘概览
        </h2>
        {data.source === "mock" && (
          <span className="flex items-center gap-1 text-[10px] text-amber-400 bg-bg-subtle px-2 py-1 rounded">
            <AlertCircle className="h-3 w-3" /> mock 数据
          </span>
        )}
      </div>

      <div className="flex items-end gap-4 mb-5">
        <div>
          <div className="text-[11px] uppercase tracking-wider text-fg-muted mb-1">
            最新价
          </div>
          <div className="flex items-baseline gap-2">
            <span className="tabular text-3xl font-bold text-fg">
              ${fmt(data.last_close, 0)}
            </span>
            <span className={`tabular text-lg font-semibold ${color}`}>
              <Arrow className="inline h-4 w-4 mr-0.5 -mt-0.5" />
              {pct(data.change_pct)}
            </span>
          </div>
        </div>
        <div className={`ml-auto px-3 py-1.5 rounded-lg text-sm font-semibold ${
          data.sentiment === "bull" ? "bg-pos text-emerald-400" :
          data.sentiment === "bear" ? "bg-neg text-rose-400" :
          "bg-bg-subtle text-fg-muted"
        }`}>
          {data.sentiment_label}
        </div>
      </div>

      {/* 关键指标条 */}
      <div className="grid grid-cols-4 gap-3">
        <IndicatorChip label="MA50" value={`$${fmt(data.ma50, 0)}`}
                       above={data.last_close > data.ma50} />
        <IndicatorChip label="MA200" value={`$${fmt(data.ma200, 0)}`}
                       above={data.above_ma200} />
        <IndicatorChip label="RSI(14)" value={data.rsi14.toFixed(1)}
                       above={data.rsi14 < 70 && data.rsi14 > 30}
                       neutral={data.rsi14 >= 70 || data.rsi14 <= 30} />
        <IndicatorChip label="MA200位" value={data.above_ma200 ? "上方 ✓" : "下方 ✗"}
                       above={data.above_ma200} />
      </div>

      <p className="mt-3 text-xs text-fg-muted">{data.summary}</p>
    </div>
  );
}

function IndicatorChip({ label, value, above, neutral }: {
  label: string; value: string; above: boolean; neutral?: boolean;
}) {
  const cls = neutral ? "text-amber-400" : above ? "text-emerald-400" : "text-rose-400";
  return (
    <div className="bg-bg-subtle rounded-lg px-3 py-2.5">
      <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-0.5">
        {label}
      </div>
      <div className={`tabular text-sm font-semibold ${cls}`}>{value}</div>
    </div>
  );
}

/** 关键股票分析表 */
function StocksTable({ stocks }: { stocks: StockAnalysisData[] }) {
  // 按板块分组
  const grouped = useMemo(() => {
    const map = new Map<string, StockAnalysisData[]>();
    for (const s of stocks) {
      if (!map.has(s.sector)) map.set(s.sector, []);
      map.get(s.sector)!.push(s);
    }
    return Array.from(map.entries());
  }, [stocks]);

  return (
    <div className="space-y-4">
      {grouped.map(([sector, sectorStocks]) => (
        <section key={sector} className="panel-card overflow-hidden">
          <div className="px-5 py-3 bg-bg-subtle flex items-center gap-2">
            <Layers className="h-4 w-4 text-fg-muted" />
            <span className="text-sm font-semibold text-fg">{sector}</span>
            <span className="text-xs text-fg-muted">({sectorStocks.length} 只)</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line text-fg-muted text-[11px] uppercase tracking-wider">
                  <th className="text-left px-4 py-2.5 font-medium">股票</th>
                  <th className="text-right px-3 py-2.5 font-medium">最新价</th>
                  <th className="text-right px-3 py-2.5 font-medium">涨跌</th>
                  <th className="text-right px-3 py-2.5 font-medium">MA5</th>
                  <th className="text-right px-3 py-2.5 font-medium">MA20</th>
                  <th className="text-right px-3 py-2.5 font-medium">RSI</th>
                  <th className="text-center px-3 py-2.5 font-medium">MACD</th>
                  <th className="text-center px-3 py-2.5 font-medium">趋势</th>
                  <th className="text-center px-3 py-2.5 font-medium">推荐</th>
                </tr>
              </thead>
              <tbody>
                {sectorStocks.map((s) => (
                  <tr key={s.symbol}
                      className="border-b border-line last:border-b-0 hover:bg-bg-hover transition">
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-2">
                        <span className="tabular font-semibold text-fg">{s.symbol}</span>
                        <span className="text-xs text-fg-muted">{s.name}</span>
                      </div>
                    </td>
                    <td className="px-3 py-2.5 tabular text-right text-fg">
                      ${fmt(s.close || 0, 2)}
                    </td>
                    <td className={`px-3 py-2.5 tabular text-right font-medium ${
                      s.change_pct >= 0 ? "text-emerald-400" : "text-rose-400"
                    }`}>
                      {pct(s.change_pct || 0)}
                    </td>
                    <td className={`px-3 py-2.5 tabular text-right ${
                      s.close > s.ma5 ? "text-emerald-400" : "text-rose-400"
                    }`}>
                      ${fmt(s.ma5 || 0, 2)}
                    </td>
                    <td className={`px-3 py-2.5 tabular text-right ${
                      s.close > s.ma20 ? "text-emerald-400" : "text-rose-400"
                    }`}>
                      ${fmt(s.ma20 || 0, 2)}
                    </td>
                    <td className="px-3 py-2.5 tabular text-right">
                      <RSIBadge value={s.rsi14 || 50} />
                    </td>
                    <td className="px-3 py-2.5 text-center">
                      <SignalBadge signal={s.macd_signal} />
                    </td>
                    <td className="px-3 py-2.5 text-center">
                      <TrendBadge trend={s.trend} />
                    </td>
                    <td className="px-3 py-2.5 text-center">
                      <RecBadge rec={s.recommendation} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ))}
    </div>
  );
}

function RSIBadge({ value }: { value: number }) {
  const cls = value >= 70 ? "text-rose-400 bg-neg" :
              value <= 30 ? "text-emerald-400 bg-pos" :
              "text-fg-muted bg-bg-subtle";
  return <span className={`tabular text-xs px-1.5 py-0.5 rounded ${cls}`}>{value.toFixed(1)}</span>;
}

function SignalBadge({ signal }: { signal: string }) {
  if (signal === "bull") return <span className="text-xs px-1.5 py-0.5 rounded bg-pos text-emerald-400">金叉</span>;
  if (signal === "bear") return <span className="text-xs px-1.5 py-0.5 rounded bg-neg text-rose-400">死叉</span>;
  return <span className="text-xs px-1.5 py-0.5 rounded bg-bg-subtle text-fg-muted">—</span>;
}

function TrendBadge({ trend }: { trend: string }) {
  const cls = trend.includes("上涨") ? "bg-pos text-emerald-400" :
              trend.includes("下跌") ? "bg-neg text-rose-400" :
              "bg-bg-subtle text-fg-muted";
  return <span className={`text-xs px-1.5 py-0.5 rounded ${cls}`}>{trend}</span>;
}

function RecBadge({ rec }: { rec: string }) {
  const cls = rec.includes("加仓") ? "bg-pos text-emerald-400" :
              rec.includes("减仓") ? "bg-neg text-rose-400" :
              rec.includes("超买") ? "bg-neg text-amber-400" :
              rec.includes("超卖") ? "bg-pos text-amber-400" :
              "bg-bg-subtle text-fg-muted";
  return <span className={`text-xs px-1.5 py-0.5 rounded whitespace-nowrap ${cls}`}>{rec}</span>;
}

/** 板块轮动排行 */
function SectorRanking({ sectors }: { sectors: SectorAnalysisData[] }) {
  const maxChg = Math.max(...sectors.map(s => Math.abs(s.change_pct || 0)), 0.01);

  return (
    <div className="panel-card p-5">
      <h2 className="flex items-center gap-2 text-fg text-lg font-semibold mb-4">
        <PieChart className="h-5 w-5 text-amber-400" />
        板块轮动排行
      </h2>
      <div className="space-y-2">
        {sectors.map((s) => (
          <div key={s.name}
               className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-bg-hover transition">
            <span className="w-6 text-center text-xs font-mono text-fg-muted tabular">
              #{s.rank}
            </span>
            <span className="w-20 text-sm font-medium text-fg">{s.name}</span>
            <span className="w-12 text-xs text-fg-muted tabular">{s.etf}</span>
            {/* 涨跌条 */}
            <div className="flex-1 flex items-center gap-2">
              <div className="flex-1 h-1.5 bg-bg-subtle rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${
                    s.change_pct >= 0 ? "bg-emerald-500" : "bg-rose-500"
                  }`}
                  style={{ width: `${Math.min((Math.abs(s.change_pct) / maxChg) * 100, 100)}%` }}
                />
              </div>
              <span className={`tabular text-sm font-semibold w-16 text-right ${
                s.change_pct >= 0 ? "text-emerald-400" : "text-rose-400"
              }`}>
                {pct(s.change_pct || 0)}
              </span>
            </div>
            <span className={`tabular text-xs w-14 text-right ${
              s.rsi14 >= 60 ? "text-rose-400" : s.rsi14 <= 40 ? "text-emerald-400" : "text-fg-muted"
            }`}>
              RSI {s.rsi14.toFixed(1)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/** 市场宽度面板 */
function MarketBreadth({ breadth }: { breadth: FullAnalysisData["market_breadth"] }) {
  const advPct = breadth.total > 0 ? (breadth.advancing / breadth.total * 100) : 50;
  return (
    <div className="panel-card p-5">
      <h2 className="flex items-center gap-2 text-fg text-lg font-semibold mb-4">
        <BarChart3 className="h-5 w-5 text-fg-muted" />
        市场宽度
      </h2>
      <div className="grid grid-cols-2 gap-4">
        {/* 涨跌比 */}
        <div>
          <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-2">
            涨跌分布
          </div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs text-emerald-400 tabular">{breadth.advancing} 涨</span>
            <div className="flex-1 h-2 bg-bg-subtle rounded-full overflow-hidden flex">
              <div className="h-full bg-emerald-500 transition-all"
                   style={{ width: `${advPct}%` }} />
              <div className="h-full bg-rose-500 transition-all"
                   style={{ width: `${100 - advPct}%` }} />
            </div>
            <span className="text-xs text-rose-400 tabular">{breadth.declining} 跌</span>
          </div>
          <div className="text-xs text-fg-muted tabular">
            腾落比: {breadth.breadth_ratio?.toFixed(2) || "—"}
          </div>
        </div>

        {/* 成交量 */}
        <div>
          <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-2">
            成交量
          </div>
          <div className="flex items-center gap-3">
            <div>
              <div className="text-xs text-fg-muted">涨方</div>
              <div className="text-sm text-emerald-400 tabular font-semibold">
                {fmtVol(breadth.adv_volume || 0)}
              </div>
            </div>
            <div>
              <div className="text-xs text-fg-muted">跌方</div>
              <div className="text-sm text-rose-400 tabular font-semibold">
                {fmtVol(breadth.dec_volume || 0)}
              </div>
            </div>
          </div>
        </div>

        {/* 新高新低 */}
        <div>
          <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-2">
            52周新高/新低
          </div>
          <div className="flex items-center gap-4">
            <div>
              <div className="text-xs text-fg-muted">新高</div>
              <div className="text-lg tabular font-bold text-emerald-400">
                {breadth.new_highs || 0}
              </div>
            </div>
            <div className="text-fg-dim">/</div>
            <div>
              <div className="text-xs text-fg-muted">新低</div>
              <div className="text-lg tabular font-bold text-rose-400">
                {breadth.new_lows || 0}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/** 市场情绪面板 */
function SentimentPanel({ sentiment }: { sentiment: FullAnalysisData["sentiment_data"] }) {
  const vixPos = (sentiment.vix_change || 0) <= 0;
  return (
    <div className="panel-card p-5">
      <h2 className="flex items-center gap-2 text-fg text-lg font-semibold mb-4">
        <Gauge className="h-5 w-5 text-fg-muted" />
        市场情绪
      </h2>

      <div className="grid grid-cols-2 gap-4">
        {/* VIX */}
        <div>
          <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-1">
            VIX 恐慌指数
          </div>
          <div className="flex items-baseline gap-2">
            <span className="tabular text-2xl font-bold text-fg">
              {sentiment.vix?.toFixed(1) || "—"}
            </span>
            <span className={`tabular text-sm ${vixPos ? "text-emerald-400" : "text-rose-400"}`}>
              {pct(sentiment.vix_change || 0)}
            </span>
          </div>
          <div className="mt-2 h-1.5 bg-bg-subtle rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${
                (sentiment.vix || 0) < 15 ? "bg-emerald-500" :
                (sentiment.vix || 0) < 25 ? "bg-amber-500" : "bg-rose-500"
              }`}
              style={{ width: `${Math.min(((sentiment.vix || 0) / 40) * 100, 100)}%` }}
            />
          </div>
          <div className="flex justify-between text-[10px] text-fg-dim mt-1">
            <span>0</span><span>20</span><span>40</span>
          </div>
        </div>

        {/* 恐慌贪婪指数 */}
        <div>
          <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-1">
            恐慌贪婪指数
          </div>
          <div className="flex items-baseline gap-2">
            <span className="tabular text-2xl font-bold text-fg">
              {sentiment.fear_greed_index || "—"}
            </span>
            <span className={`text-xs px-2 py-0.5 rounded ${
              (sentiment.fear_greed_index || 50) > 55 ? "bg-pos text-emerald-400" :
              (sentiment.fear_greed_index || 50) < 45 ? "bg-neg text-rose-400" :
              "bg-bg-subtle text-fg-muted"
            }`}>
              {sentiment.fear_greed_label || "—"}
            </span>
          </div>
          {/* 指数条 */}
          <div className="mt-2 h-1.5 bg-bg-subtle rounded-full overflow-hidden flex">
            <div className="h-full bg-rose-500" style={{ width: "25%" }} />
            <div className="h-full bg-amber-500" style={{ width: "25%" }} />
            <div className="h-full bg-emerald-500" style={{ width: "25%" }} />
            <div className="h-full bg-emerald-400" style={{ width: "25%" }} />
          </div>
          <div className="flex justify-between text-[10px] text-fg-dim mt-1">
            <span>恐慌</span><span>中性</span><span>贪婪</span>
          </div>
        </div>

        {/* Put/Call Ratio */}
        <div>
          <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-1">
            Put/Call 比率
          </div>
          <div className="tabular text-lg font-semibold text-fg">
            {sentiment.put_call_ratio?.toFixed(2) || "—"}
          </div>
          <div className="text-xs text-fg-muted mt-0.5">
            {(sentiment.put_call_ratio || 0) > 1 ? "偏空信号" : "偏多信号"}
          </div>
        </div>
      </div>

      {sentiment.summary && (
        <p className="mt-4 text-xs text-fg-muted border-t border-line pt-3">
          {sentiment.summary}
        </p>
      )}
    </div>
  );
}

/* ================================================================
 * 主页面
 * ================================================================ */

export function Analysis() {
  const [data, setData] = useState<FullAnalysisData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.fullAnalysis();
      setData(result);
    } catch (e: any) {
      setError(e?.message || "加载分析数据失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // 加载状态
  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center space-y-3">
          <RefreshCw className="h-8 w-8 text-emerald-400 animate-spin mx-auto" />
          <p className="text-fg-muted text-sm">正在加载分析数据…</p>
        </div>
      </div>
    );
  }

  // 错误但无降级数据
  if (error && !data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center space-y-3">
          <AlertCircle className="h-8 w-8 text-rose-400 mx-auto" />
          <p className="text-fg-muted text-sm">{error}</p>
          <button onClick={fetchData}
                  className="text-sm text-emerald-400 hover:text-emerald-300 transition">
            重试
          </button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-6">
      {/* 页面标题栏 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-fg flex items-center gap-2">
            <Target className="h-5 w-5 text-emerald-400" />
            每日分析
          </h1>
          <p className="text-xs text-fg-muted mt-1">
            NDX 大盘 · 关键个股 · 板块轮动 · 市场情绪
            {data.source === "mock" && (
              <span className="ml-2 text-amber-400">（mock 数据 — 实时行情暂不可用）</span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {data.ndx_analysis_report_path && (
            <a href={`/${data.ndx_analysis_report_path}`}
               target="_blank" rel="noreferrer"
               className="flex items-center gap-1.5 text-xs text-emerald-400 hover:text-emerald-300
                          bg-bg-subtle hover:bg-bg-hover px-3 py-1.5 rounded-lg transition">
              <FileText className="h-3.5 w-3.5" />
              查看完整报告
            </a>
          )}
          <button onClick={fetchData}
                  className="flex items-center gap-1.5 text-xs text-fg-muted hover:text-fg
                             bg-bg-subtle hover:bg-bg-hover px-3 py-1.5 rounded-lg transition">
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            刷新
          </button>
        </div>
      </div>

      {/* 1. NDX 大盘概览 */}
      <NdxOverview data={data.ndx} />

      {/* 2. 板块轮动 + 市场宽度 + 情绪（三栏） */}
      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-1">
          <SectorRanking sectors={data.sectors} />
        </div>
        <div className="col-span-2 space-y-4">
          <MarketBreadth breadth={data.market_breadth} />
          <SentimentPanel sentiment={data.sentiment_data} />
        </div>
      </div>

      {/* 3. 关键股票分析 */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 className="h-5 w-5 text-fg-muted" />
          <h2 className="text-lg font-semibold text-fg">关键股票分析</h2>
        </div>
        <StocksTable stocks={data.stocks} />
      </div>
    </div>
  );
}
