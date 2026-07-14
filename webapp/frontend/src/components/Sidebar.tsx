import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, TrendingUp, Brain, Terminal, Settings as Cog, Activity,
  BarChart3,
} from "lucide-react";
import { cn } from "../lib/utils";
import { useTradeStore } from "../store/tradeStore";

const items = [
  { to: "/",          label: "总览",    icon: LayoutDashboard },
  { to: "/trading",   label: "交易",    icon: TrendingUp },
  { to: "/analysis",  label: "分析",    icon: BarChart3 },
  { to: "/strategy",  label: "策略",    icon: Brain },
  { to: "/logs",      label: "日志",    icon: Terminal },
  { to: "/settings",  label: "设置",    icon: Cog },
];

export function Sidebar() {
  const ws = useTradeStore((s) => s.wsStatus);
  return (
    <aside className="w-56 shrink-0 bg-bg-panel border-r border-line flex flex-col">
      <div className="px-5 py-5 flex items-center gap-3">
        <div className="h-8 w-8 rounded-lg bg-emerald-500 grid place-items-center text-bg font-bold">
          <Activity className="h-4 w-4" />
        </div>
        <div>
          <div className="text-fg font-semibold leading-none">Trader</div>
          <div className="text-fg-muted text-[11px] mt-1 tracking-wider uppercase">NdXinfo</div>
        </div>
      </div>

      <nav className="flex-1 px-3 py-2 space-y-1">
        {items.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition",
                "hover:bg-bg-hover",
                isActive
                  ? "bg-bg-hover text-fg shadow-[inset_2px_0_0_0_#10B981]"
                  : "text-fg-muted"
              )
            }
          >
            <Icon className="h-4 w-4" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="px-5 py-4 border-t border-line">
        <div className="text-[11px] uppercase tracking-wider text-fg-muted">
          WebSocket
        </div>
        <div className="mt-1 flex items-center gap-2 text-sm">
          <span className={cn(
            "h-2 w-2 rounded-full",
            ws === "open" ? "bg-emerald-500" :
            ws === "closed" ? "bg-rose-500" :
            "bg-amber-500"
          )} />
          <span className="tabular lowercase">
            {ws === "open" ? "已连接" : ws === "closed" ? "已断开" : "连接中…"}
          </span>
        </div>
      </div>
    </aside>
  );
}
