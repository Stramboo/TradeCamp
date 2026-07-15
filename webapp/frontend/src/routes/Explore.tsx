/**
 * Explore.tsx — 世界市场探索入口
 *
 * Phase 3 会扩展为完整的全球市场模块。
 * 当前为占位页面，展示市场时间轴和地区入口。
 */
import { Link } from "react-router-dom";

const MARKETS = [
  { id: "us", name: "美国", exchanges: "NYSE · NASDAQ", index: "S&P 500 · NDX", flag: "🇺🇸", timezone: "美东时间" },
  { id: "cn", name: "中国大陆", exchanges: "上交所 · 深交所", index: "上证指数 · 沪深300", flag: "🇨🇳", timezone: "北京时间" },
  { id: "hk", name: "中国香港", exchanges: "港交所", index: "恒生指数", flag: "🇭🇰", timezone: "香港时间" },
  { id: "jp", name: "日本", exchanges: "东京证券交易所", index: "日经225", flag: "🇯🇵", timezone: "东京时间" },
  { id: "eu", name: "欧洲", exchanges: "伦交所 · 法兰克福", index: "FTSE 100 · DAX", flag: "🇪🇺", timezone: "欧洲时间" },
];

export function Explore() {
  return (
    <div className="max-w-3xl mx-auto py-8 px-4 space-y-8">
      <div className="space-y-2">
        <p className="text-xs text-fg-muted uppercase tracking-wider">世界市场</p>
        <h1 className="text-2xl font-bold text-fg">全球股票市场</h1>
        <p className="text-sm text-fg-muted leading-relaxed">
          了解世界各地的股票市场。每家上市公司都在某个交易所挂牌交易，而每个市场都有自己的规则和节奏。
        </p>
      </div>

      {/* 简易市场时间轴 */}
      <div className="rounded-xl bg-bg-panel border border-line p-5 space-y-2">
        <p className="text-xs text-fg-muted uppercase tracking-wider">今日交易时段</p>
        <div className="flex items-center gap-2 text-sm">
          {[
            { label: "上海", status: "已收盘" },
            { label: "东京", status: "已收盘" },
            { label: "伦敦", status: "交易中" },
            { label: "纽约", status: "即将开盘" },
          ].map((m) => (
            <span key={m.label} className="px-3 py-1.5 rounded-lg bg-bg-subtle text-fg-muted text-xs">
              {m.label} · {m.status}
            </span>
          ))}
        </div>
      </div>

      {/* 市场列表 */}
      <div className="space-y-3">
        {MARKETS.map((m) => (
          <Link
            key={m.id}
            to={`/explore/markets/${m.id}`}
            className="block rounded-xl bg-bg-panel border border-line p-4
                       hover:border-emerald-500/30 transition group"
          >
            <div className="flex items-center gap-4">
              <span className="text-2xl">{m.flag}</span>
              <div className="flex-1">
                <p className="text-sm font-semibold text-fg group-hover:text-emerald-400 transition">
                  {m.name}
                </p>
                <p className="text-xs text-fg-dim mt-0.5">
                  {m.exchanges} · {m.index}
                </p>
              </div>
              <span className="text-xs text-fg-dim">{m.timezone}</span>
            </div>
          </Link>
        ))}
      </div>

      {/* 探索方式提示 */}
      <div className="p-4 rounded-xl bg-bg-subtle border border-line space-y-2">
        <p className="text-xs text-fg-muted uppercase tracking-wider">你还可这样探索</p>
        <div className="grid grid-cols-3 gap-3 text-xs text-fg-dim">
          <span>📱 按产品 → 手机 / 汽车 / 游戏</span>
          <span>🏢 按行业 → 科技 / 金融 / 医疗</span>
          <span>🌍 按国家 → 美国 / 中国 / 日本</span>
        </div>
      </div>
    </div>
  );
}
