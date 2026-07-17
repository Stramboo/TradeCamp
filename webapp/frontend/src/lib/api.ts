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
  health:        ()                 => http<{status:string; backend:string; uptime_s:number; real_data?:boolean}>(`/api/health`),
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

  // ---- 用户个性化 API ----

  // 自选列表
  watchlists:    ()                              => http<Watchlist[]>(`/api/watchlists`),
  createWatchlist: (req: {name:string; symbols:string[]}) =>
                   http<Watchlist>(`/api/watchlists`, { method: "POST", body: JSON.stringify(req) }),
  updateWatchlist: (id: number, req: {name:string; symbols:string[]}) =>
                   http<Watchlist>(`/api/watchlists/${id}`, { method: "PUT", body: JSON.stringify(req) }),
  deleteWatchlist: (id: number) =>
                   http<{deleted:boolean}>(`/api/watchlists/${id}`, { method: "DELETE" }),

  // 价格告警
  alerts:        ()                              => http<PriceAlert[]>(`/api/alerts`),
  createAlert:   (req: {symbol:string; condition:string; target_value:number; note?:string}) =>
                   http<PriceAlert>(`/api/alerts`, { method: "POST", body: JSON.stringify(req) }),
  deleteAlert:   (id: number) =>
                   http<{deleted:boolean}>(`/api/alerts/${id}`, { method: "DELETE" }),
  ackAlert:      (id: number) =>
                   http<{acknowledged:boolean}>(`/api/alerts/${id}/ack`, { method: "POST" }),

  // 自动操盘
  tradeStatus:   ()                              => http<TradeStatus>(`/api/trade/status`),
  tradeControl:  (action: string, interval = 60) =>
                   http<{action:string; status:string}>(`/api/trade/control`, {
                     method: "POST", body: JSON.stringify({ action, interval }),
                   }),

  // 持仓组合（投资组合管理）
  portfolio:     ()                              => http<PortfolioHolding[]>(`/api/portfolio`),
  createHolding: (req: {symbol:string; name:string; quantity:number; avg_cost:number; notes?:string}) =>
                   http<PortfolioHolding>(`/api/portfolio`, { method: "POST", body: JSON.stringify(req) }),
  updateHolding: (id: number, req: {symbol?:string; name?:string; quantity?:number; avg_cost?:number; notes?:string}) =>
                   http<PortfolioHolding>(`/api/portfolio/${id}`, { method: "PUT", body: JSON.stringify(req) }),
  deleteHolding: (id: number) =>
                   http<{deleted:boolean}>(`/api/portfolio/${id}`, { method: "DELETE" }),
  portfolioSnapshots: ()                              => http<PortfolioSnapshot[]>(`/api/portfolio/snapshots`),
  createPortfolioSnapshot: (req: { total_value: number }) =>
                   http<PortfolioSnapshot>(`/api/portfolio/snapshots`, { method: "POST", body: JSON.stringify(req) }),

  // 交易日志（交易日记）
  journal:       ()                              => http<JournalEntry[]>(`/api/journal`),
  createJournalEntry: (req: {symbol:string; direction:string; entry_date:string; exit_date?:string; entry_price:number; exit_price?:number; quantity:number; pnl?:number; rating?:number; tags?:string[]; notes?:string}) =>
                   http<JournalEntry>(`/api/journal`, { method: "POST", body: JSON.stringify(req) }),
  updateJournalEntry: (id: number, req: Partial<JournalEntry>) =>
                   http<JournalEntry>(`/api/journal/${id}`, { method: "PUT", body: JSON.stringify(req) }),
  deleteJournalEntry: (id: number) =>
                   http<{deleted:boolean}>(`/api/journal/${id}`, { method: "DELETE" }),
  journalStats:  ()                              => http<JournalStats>(`/api/journal/stats`),

  // 策略参数
  strategyParams: (name: string) =>
                   http<Record<string, number | string | boolean>>(`/api/strategy/${name}/params`),
  updateStrategyParams: (name: string, params: Record<string, number | string | boolean>) =>
                   http<Record<string, number | string | boolean>>(`/api/strategy/${name}/params`, { method: "PUT", body: JSON.stringify(params) }),

  // ---- 沙盒交易 API (v2.3) ----
  sandboxAccount: () => http<{cash:number; initial_cash:number; positions:{symbol:string; quantity:number; avg_cost:number}[]}>(`/api/sandbox/account`),
  sandboxOrder: (req: {symbol:string; side:"BUY"|"SELL"; quantity:number; price:number}) =>
                   http<{order_id:string; status:string; ts:number; review?:any}>(`/api/sandbox/order`, { method: "POST", body: JSON.stringify(req) }),
  sandboxOrders: (limit = 50) => http<{order_id:string; symbol:string; side:string; quantity:number; price:number; ts:number}[]>(`/api/sandbox/orders?limit=${limit}`),
  sandboxReset: () => http<{ok:boolean}>(`/api/sandbox/reset`, { method: "POST" }),
};

// ---- 用户个性化类型 ----

export type Watchlist = {
  id: number;
  name: string;
  symbols: string[];
  created_at: string;
  updated_at: string;
};

export type TradeStatus = {
  running: boolean; mode: string; strategy: string;
  tick_count: number; success: number; errors: number; interval_s: number;
  account?: Account; positions_count?: number; last_error?: string; error?: string;
};

export type PriceAlert = {
  id: number;
  symbol: string;
  condition: "above" | "below" | "pct_change";
  target_value: number;
  enabled: number;
  triggered: number;
  triggered_at: string | null;
  created_at: string;
  note: string;
};

export type PortfolioHolding = {
  id: number;
  symbol: string;
  name: string;
  quantity: number;
  avg_cost: number;
  notes: string;
  created_at: string;
  updated_at: string;
};

export type PortfolioSnapshot = {
  id: number;
  total_value: number;
  recorded_at: string;
};

export type JournalEntry = {
  id: number;
  symbol: string;
  direction: string;
  entry_date: string;
  exit_date: string | null;
  entry_price: number;
  exit_price: number | null;
  quantity: number;
  pnl: number | null;
  rating: number | null;
  tags: string[];
  notes: string;
  created_at: string;
  updated_at: string;
};

export type JournalStats = {
  total_trades: number;
  win_rate: number;
  avg_pnl: number;
  avg_rating: number;
  total_pnl: number;
  profitable_count: number;
  unprofitable_count: number;
};

export { ApiError };
