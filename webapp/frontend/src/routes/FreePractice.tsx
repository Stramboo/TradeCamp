/**
 * FreePractice.tsx — 自由模拟交易 (v2.3 Phase 2)
 *
 * 完整的自由交易环境：股票列表 + K线图 + 下单面板 + 持仓 + 交易历史
 */
import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { fmtMoney } from "../lib/utils";
import { PortfolioAnalytics } from "../features/PortfolioAnalytics";
import { ReviewToast } from "../features/ReviewToast";
import { SandboxEquityCurve } from "../features/SandboxEquityCurve";

interface SandboxAccount {
  cash: number;
  initial_cash: number;
  positions: { symbol: string; quantity: number; avg_cost: number }[];
}

interface Quote {
  symbol: string;
  price: number;
  change?: number;
  change_pct?: number;
  source?: string;
}

interface Order {
  order_id: string;
  symbol: string;
  side: string;
  quantity: number;
  price: number;
  ts: number;
}

const TRADE_SYMBOLS = ["NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"];

export function FreePractice() {
  const [account, setAccount] = useState<SandboxAccount | null>(null);
  const [quotes, setQuotes] = useState<Record<string, Quote>>({});
  const [orders, setOrders] = useState<Order[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState("NVDA");
  const [quantity, setQuantity] = useState(10);
  const [orderType, setOrderType] = useState<"BUY" | "SELL">("BUY");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [review, setReview] = useState<any>(null);

  // 加载账户数据
  const loadAccount = useCallback(async () => {
    try {
      const acc = await api.sandboxAccount();
      setAccount(acc);
    } catch (e) {
      console.error("Failed to load sandbox account", e);
    }
  }, []);

  // 加载报价
  const loadQuotes = useCallback(async () => {
    const out: Record<string, Quote> = {};
    for (const sym of TRADE_SYMBOLS) {
      try {
        const q = await api.quote(sym);
        out[sym] = q;
      } catch { /* ignore */ }
    }
    setQuotes(out);
  }, []);

  // 加载订单历史
  const loadOrders = useCallback(async () => {
    try {
      const ords = await api.sandboxOrders(20);
      setOrders(ords);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    loadAccount();
    loadQuotes();
    loadOrders();
    const timer = setInterval(() => {
      loadQuotes();
    }, 5000);
    return () => clearInterval(timer);
  }, [loadAccount, loadQuotes, loadOrders]);

  // 计算持仓市值
  const positionValue = account?.positions.reduce((sum, p) => {
    const price = quotes[p.symbol]?.price || p.avg_cost;
    return sum + price * p.quantity;
  }, 0) || 0;

  const equity = (account?.cash || 0) + positionValue;
  const totalReturn = account ? ((equity / account.initial_cash - 1) * 100) : 0;

  // 下单
  const handleOrder = async () => {
    if (!account || loading) return;
    const quote = quotes[selectedSymbol];
    if (!quote) {
      setMessage("无法获取报价");
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      const result = await api.sandboxOrder({
        symbol: selectedSymbol,
        side: orderType,
        quantity,
        price: quote.price,
      });
      setMessage(`${orderType === "BUY" ? "买入" : "卖出"} ${quantity} 股 ${selectedSymbol} 成功！`);
      // v2.4: 卖出后展示复盘卡片
      if (result?.review) {
        setReview(result.review);
      }
      await loadAccount();
      await loadOrders();
      // v2.4: 保存净值快照（fire-and-forget）
      const acc = await api.sandboxAccount();
      const mv = acc.positions.reduce((s, p) => {
        const q = quotes[p.symbol];
        return s + (q?.price || p.avg_cost) * p.quantity;
      }, 0);
      fetch("/api/sandbox/snapshot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ts: Date.now(),
          equity: acc.cash + mv,
          cash: acc.cash,
          market_value: mv,
        }),
      }).catch(() => {});
    } catch (e: any) {
      setMessage(`下单失败: ${e.message || "未知错误"}`);
    } finally {
      setLoading(false);
    }
  };

  const currentQuote = quotes[selectedSymbol];
  const currentPosition = account?.positions.find((p) => p.symbol === selectedSymbol);

  return (
    <div className="max-w-6xl mx-auto py-6 px-4 space-y-6">
      {/* 头部 */}
      <div className="flex items-center justify-between">
        <div>
          <Link to="/practice" className="text-xs text-fg-dim hover:text-fg transition">
            ← 返回练习
          </Link>
          <h1 className="text-xl font-bold text-fg mt-1">自由模拟交易</h1>
        </div>
        <div className="text-right">
          <p className="text-xs text-fg-dim">账户净值</p>
          <p className={`text-lg font-bold ${totalReturn >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
            ${fmtMoney(equity, 2)}
          </p>
          <p className={`text-xs ${totalReturn >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
            {totalReturn >= 0 ? "+" : ""}{totalReturn.toFixed(2)}%
          </p>
        </div>
      </div>

      {/* 净值曲线 */}
      <SandboxEquityCurve initialCash={account?.initial_cash || 100000} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 左侧：股票列表 */}
        <div className="space-y-3">
          <p className="text-xs text-fg-muted uppercase tracking-wider">可交易股票</p>
          <div className="space-y-2">
            {TRADE_SYMBOLS.map((sym) => {
              const q = quotes[sym];
              const pos = account?.positions.find((p) => p.symbol === sym);
              const isSelected = sym === selectedSymbol;
              return (
                <button
                  key={sym}
                  onClick={() => setSelectedSymbol(sym)}
                  className={`w-full text-left p-3 rounded-lg border transition ${
                    isSelected
                      ? "border-emerald-500 bg-emerald-500/10"
                      : "border-line bg-bg-panel hover:border-emerald-500/30"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-semibold text-fg">{sym}</p>
                      {pos && (
                        <p className="text-[10px] text-fg-dim">
                          持仓 {pos.quantity} 股 @ ${fmtMoney(pos.avg_cost, 2)}
                        </p>
                      )}
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold text-fg">
                        ${q ? fmtMoney(q.price, 2) : "—"}
                      </p>
                      {q?.change_pct !== undefined && (
                        <p className={`text-[10px] ${q.change_pct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                          {q.change_pct >= 0 ? "+" : ""}{q.change_pct.toFixed(2)}%
                        </p>
                      )}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* 账户概览 */}
          <div className="glass-card p-4 space-y-2">
            <p className="text-xs text-fg-muted uppercase tracking-wider">账户概览</p>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-fg-muted">可用现金</span>
                <span className="text-fg font-medium">${fmtMoney(account?.cash || 0, 2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-fg-muted">持仓市值</span>
                <span className="text-fg font-medium">${fmtMoney(positionValue, 2)}</span>
              </div>
              <div className="flex justify-between pt-1 border-t border-line">
                <span className="text-fg-muted">总净值</span>
                <span className="text-fg font-semibold">${fmtMoney(equity, 2)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* 中间：下单面板 */}
        <div className="space-y-4">
          <div className="glass-card p-5 space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold text-fg">{selectedSymbol}</p>
              <p className="text-lg font-bold text-fg">
                ${currentQuote ? fmtMoney(currentQuote.price, 2) : "—"}
              </p>
            </div>

            {/* 买卖切换 */}
            <div className="flex glass-light rounded-[12px] p-1">
              <button
                onClick={() => setOrderType("BUY")}
                className={`flex-1 py-2 rounded-md text-sm font-medium transition ${
                  orderType === "BUY"
                    ? "bg-emerald-500 text-white"
                    : "text-fg-muted hover:text-fg"
                }`}
              >
                买入
              </button>
              <button
                onClick={() => setOrderType("SELL")}
                className={`flex-1 py-2 rounded-md text-sm font-medium transition ${
                  orderType === "SELL"
                    ? "bg-rose-500 text-white"
                    : "text-fg-muted hover:text-fg"
                }`}
              >
                卖出
              </button>
            </div>

            {/* 数量 */}
            <div className="space-y-2">
              <label className="text-xs text-fg-muted">数量（股）</label>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setQuantity(Math.max(1, quantity - 10))}
                  className="w-8 h-8 rounded bg-bg-subtle text-fg hover:bg-bg-hover"
                >
                  -
                </button>
                <input
                  type="number"
                  value={quantity}
                  onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                  className="flex-1 h-8 px-3 rounded bg-bg-subtle text-fg text-center text-sm"
                />
                <button
                  onClick={() => setQuantity(quantity + 10)}
                  className="w-8 h-8 rounded bg-bg-subtle text-fg hover:bg-bg-hover"
                >
                  +
                </button>
              </div>
            </div>

            {/* 预估金额 */}
            <div className="glass-light rounded-[12px] p-3 space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-fg-muted">预估金额</span>
                <span className="text-fg font-medium">
                  ${currentQuote ? fmtMoney(currentQuote.price * quantity, 2) : "—"}
                </span>
              </div>
              {orderType === "SELL" && currentPosition && (
                <div className="flex justify-between text-xs">
                  <span className="text-fg-muted">当前持仓</span>
                  <span className="text-fg">{currentPosition.quantity} 股</span>
                </div>
              )}
            </div>

            {/* 下单按钮 */}
            <button
              onClick={handleOrder}
              disabled={loading || !currentQuote}
              className={`w-full py-3 rounded-lg text-sm font-semibold transition ${
                orderType === "BUY"
                  ? "bg-emerald-500 hover:bg-emerald-600 text-white"
                  : "bg-rose-500 hover:bg-rose-600 text-white"
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {loading ? "下单中..." : orderType === "BUY" ? "买入" : "卖出"}
            </button>

            {message && (
              <p className={`text-xs text-center ${message.includes("成功") ? "text-emerald-400" : "text-rose-400"}`}>
                {message}
              </p>
            )}
          </div>

          {/* 当前持仓 */}
          {currentPosition && (
            <div className="glass-card p-4">
              <p className="text-xs text-fg-muted uppercase tracking-wider mb-2">当前持仓</p>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-fg-muted">数量</span>
                  <span className="text-fg">{currentPosition.quantity} 股</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-fg-muted">成本价</span>
                  <span className="text-fg">${fmtMoney(currentPosition.avg_cost, 2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-fg-muted">浮动盈亏</span>
                  <span className={currentQuote && currentQuote.price >= currentPosition.avg_cost ? "text-emerald-400" : "text-rose-400"}>
                    {currentQuote
                      ? `${((currentQuote.price / currentPosition.avg_cost - 1) * 100).toFixed(2)}%`
                      : "—"}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 右侧：交易历史 + 组合分析 */}
        <div className="space-y-4">
          {/* 组合分析 */}
          {account && account.positions.length > 0 && (
            <PortfolioAnalytics
              positions={account.positions}
              quotes={quotes}
              cash={account.cash}
            />
          )}

          {/* 交易历史 */}
          <div className="space-y-3">
            <p className="text-xs text-fg-muted uppercase tracking-wider">最近交易</p>
            <div className="glass-card overflow-hidden">
              {orders.length === 0 ? (
                <p className="p-4 text-xs text-fg-dim text-center">暂无交易记录</p>
              ) : (
                <div className="divide-y divide-line max-h-96 overflow-y-auto">
                  {orders.map((o) => (
                    <div key={o.order_id} className="p-3 text-xs">
                      <div className="flex items-center justify-between">
                        <span className={`font-semibold ${o.side === "BUY" ? "text-emerald-400" : "text-rose-400"}`}>
                          {o.side === "BUY" ? "买入" : "卖出"}
                        </span>
                        <span className="text-fg-dim">
                          {new Date(o.ts).toLocaleTimeString()}
                        </span>
                      </div>
                      <div className="flex items-center justify-between mt-1">
                        <span className="text-fg">{o.symbol}</span>
                        <span className="text-fg-muted">
                          {o.quantity} 股 @ ${fmtMoney(o.price, 2)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* 重置按钮 */}
          <button
            onClick={async () => {
              if (confirm("确定要重置沙盒账户吗？所有持仓和交易记录将被清空。")) {
                await api.sandboxReset();
                await loadAccount();
                await loadOrders();
                setMessage("沙盒账户已重置");
              }
            }}
            className="w-full py-2 rounded-lg border border-line text-xs text-fg-muted hover:bg-bg-subtle transition"
          >
            重置沙盒账户
          </button>
        </div>
      </div>

      {/* 卖出复盘卡片 */}
      {review && <ReviewToast review={review} onClose={() => setReview(null)} />}
    </div>
  );
}
