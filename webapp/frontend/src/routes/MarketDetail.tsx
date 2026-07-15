/**
 * MarketDetail.tsx — 市场详情占位页
 *
 * Phase 3 会扩展为完整的市场页面，包含交易所、指数、代表公司等。
 */
import { useParams, Link } from "react-router-dom";

const MARKET_INFO: Record<string, {
  name: string; flag: string; exchanges: string[]; index: string; currency: string; hours: string;
}> = {
  us: { name: "美国", flag: "🇺🇸", exchanges: ["NYSE", "NASDAQ"], index: "S&P 500 · 纳斯达克100", currency: "美元 (USD)", hours: "美东 9:30-16:00" },
  cn: { name: "中国大陆", flag: "🇨🇳", exchanges: ["上海证券交易所", "深圳证券交易所"], index: "上证指数 · 沪深300", currency: "人民币 (CNY)", hours: "北京时间 9:30-15:00" },
  hk: { name: "中国香港", flag: "🇭🇰", exchanges: ["香港交易所 (HKEX)"], index: "恒生指数", currency: "港元 (HKD)", hours: "香港时间 9:30-16:00" },
  jp: { name: "日本", flag: "🇯🇵", exchanges: ["东京证券交易所 (TSE)"], index: "日经225 · TOPIX", currency: "日元 (JPY)", hours: "东京时间 9:00-15:00" },
  eu: { name: "欧洲", flag: "🇪🇺", exchanges: ["伦敦证券交易所", "法兰克福证券交易所"], index: "FTSE 100 · DAX", currency: "英镑 (GBP) · 欧元 (EUR)", hours: "当地时间 8:00-16:30" },
};

export function MarketDetail() {
  const { marketId } = useParams<{ marketId: string }>();
  const m = MARKET_INFO[marketId || "us"] || MARKET_INFO.us;

  return (
    <div className="max-w-2xl mx-auto py-8 px-4 space-y-8">
      <Link to="/explore" className="text-xs text-fg-dim hover:text-fg transition">← 返回世界市场</Link>

      <div className="flex items-center gap-4">
        <span className="text-4xl">{m.flag}</span>
        <div>
          <h1 className="text-2xl font-bold text-fg">{m.name}股票市场</h1>
          <p className="text-sm text-fg-muted">{m.exchanges.join(" · ")}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="rounded-xl bg-bg-panel border border-line p-4">
          <p className="text-xs text-fg-muted uppercase tracking-wider">代表指数</p>
          <p className="text-sm font-semibold text-fg mt-1">{m.index}</p>
        </div>
        <div className="rounded-xl bg-bg-panel border border-line p-4">
          <p className="text-xs text-fg-muted uppercase tracking-wider">交易货币</p>
          <p className="text-sm font-semibold text-fg mt-1">{m.currency}</p>
        </div>
        <div className="rounded-xl bg-bg-panel border border-line p-4">
          <p className="text-xs text-fg-muted uppercase tracking-wider">交易时间</p>
          <p className="text-sm font-semibold text-fg mt-1">{m.hours}</p>
        </div>
        <div className="rounded-xl bg-bg-panel border border-line p-4">
          <p className="text-xs text-fg-muted uppercase tracking-wider">交易所数量</p>
          <p className="text-sm font-semibold text-fg mt-1">{m.exchanges.length} 个主要交易所</p>
        </div>
      </div>

      <div className="p-4 rounded-xl bg-bg-subtle border border-line text-xs text-fg-muted leading-relaxed">
        Phase 3 将在此展示：主要行业、代表公司、跨市场上市关系、汇率基础等信息。
      </div>
    </div>
  );
}
