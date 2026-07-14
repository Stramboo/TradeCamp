/**
 * api.ts — 简单 fetch 客户端（与 Vite proxy 配合，自动转发 /api 到 FastAPI）
 */

const BASE = "";  // 用 Vite proxy 转发

class ApiError extends Error {
  constructor(public status: number, public body: unknown) {
    super(`HTTP ${status}: ${JSON.stringify(body)}`);
  }
}

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    let body: unknown;
    try { body = await res.json(); } catch { body = await res.text(); }
    throw new ApiError(res.status, body);
  }
  return res.json();
}

// ---------- 类型 ----------

export type Account = {
  cash: number;
  equity: number;
  settled_cash: number;
  market_value: number;
  total_return_pct: number;
  daily_pnl: number;
  positions: number;
};

export type Position = {
  symbol: string;
  quantity: number;
  avg_cost: number;
  last_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
};

export type Order = {
  order_id: string;
  symbol: string;
  side: "BUY" | "SELL";
  quantity: number;
  avg_fill_price: number;
  commission: number;
  status: "filled" | "rejected" | "pending";
  note: string;
  rejection_code: number;
  ts: number;
};

export type OHLC = {
  t: number; o: number; h: number; l: number; c: number; v: number;
};

export type Signal = {
  symbol: string;
  action: "BUY" | "SELL" | "HOLD";
  strength: number;
  reason: string;
  ts: number;
};

export type EquityPoint = {
  ts: number; equity: number; cash: number; market_value: number; daily_pnl: number;
};

// ---- 分析相关类型 ----
export type NdxStatusData = {
  symbol: string;
  last_close: number;
  change_pct: number;
  ma50: number;
  ma200: number;
  above_ma200: boolean;
  rsi14: number;
  sentiment: "bull" | "bear" | "neutral";
  sentiment_label: string;
  summary: string;
  source: string;
  ts: number;
  ndx_analysis_report_path: string;
};

export type StockAnalysisData = {
  symbol: string;
  name: string;
  sector: string;
  close: number;
  change_pct: number;
  ma5: number;
  ma20: number;
  ma60: number;
  rsi14: number;
  macd_signal: "bull" | "bear" | "neutral";
  trend: string;
  recommendation: string;
};

export type SectorAnalysisData = {
  name: string;
  etf: string;
  close: number;
  change_pct: number;
  ma20: number;
  rsi14: number;
  rank: number;
};

export type FullAnalysisData = {
  ndx: NdxStatusData;
  stocks: StockAnalysisData[];
  sectors: SectorAnalysisData[];
  market_breadth: {
    advancing: number; declining: number; total: number;
    adv_volume: number; dec_volume: number;
    new_highs: number; new_lows: number; breadth_ratio: number;
  };
  sentiment_data: {
    vix: number; vix_change: number;
    fear_greed_index: number; fear_greed_label: string;
    put_call_ratio: number; summary: string;
  };
  source: string;
  ts: number;
  ndx_analysis_report_path: string;
};

// ---------- 接口 ----------

export const api = {
  health:        ()                 => http<{status:string; backend:string; uptime_s:number}>(`/api/health`),
  account:       ()                 => http<Account>(`/api/account`),
  positions:     ()                 => http<Position[]>(`/api/positions`),
  orders:        (limit = 50)       => http<Order[]>(`/api/orders?limit=${limit}`),
  symbols:       ()                 => http<string[]>(`/api/market/symbols`),
  quote:         (sym: string)      => http<{symbol:string; price:number; ts:number}>(`/api/market/${sym}`),
  ohlc:          (sym: string, lim = 200) => http<OHLC[]>(`/api/market/${sym}/ohlc?limit=${lim}`),
  signals:       (limit = 50)       => http<Signal[]>(`/api/signals?limit=${limit}`),
  equity:        (limit = 300)      => http<EquityPoint[]>(`/api/equity-history?limit=${limit}`),
  strategy:      ()                 => http<{name:string; weights:Record<string,number>; available:string[]}>(`/api/strategy`),
  limits:        ()                 => http<Record<string, number | boolean | string>>(`/api/limits`),
  fullAnalysis:  ()                 => http<FullAnalysisData>(`/api/analysis/full`),
  placeOrder:    (req: {symbol:string; side:"BUY"|"SELL"; quantity:number; order_type?:string; limit_price?:number|null}) =>
                   http<Order>(`/api/orders`, {
                     method: "POST",
                     body: JSON.stringify(req),
                   }),
};

export { ApiError };
