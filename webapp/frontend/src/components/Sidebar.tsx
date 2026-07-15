import { NavLink } from "react-router-dom";
import {
  Compass, GraduationCap, Globe, Gamepad2, User, Activity,
} from "lucide-react";
import { cn } from "../lib/utils";

/**
 * Sidebar.tsx — v2.2 教学化一级导航
 *
 * 从 13 个入口缩减为 5 个核心入口：
 *   今日 · 学习 · 世界市场 · 模拟练习 · 我的成长
 *
 * 旧交易终端入口保留在底部"工具"区，默认收起。
 */

const primaryItems = [
  { to: "/today",     label: "今日",     icon: Compass },
  { to: "/learning",  label: "学习",     icon: GraduationCap },
  { to: "/explore",   label: "世界市场", icon: Globe },
  { to: "/practice",  label: "模拟练习", icon: Gamepad2 },
  { to: "/me",        label: "我的成长", icon: User },
];

export function Sidebar() {
  return (
    <aside className="w-56 shrink-0 bg-bg-panel border-r border-line flex flex-col">
      {/* Logo */}
      <div className="px-5 py-5 flex items-center gap-3">
        <div className="h-8 w-8 rounded-lg bg-emerald-500 grid place-items-center text-bg font-bold">
          <Activity className="h-4 w-4" />
        </div>
        <div>
          <div className="text-fg font-semibold leading-none">TradeCamp</div>
          <div className="text-fg-muted text-[11px] mt-1 tracking-wider uppercase">学堂</div>
        </div>
      </div>

      {/* 主导航 — 5 项 */}
      <nav className="flex-1 px-3 py-2 space-y-0.5">
        {primaryItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to !== "/"}
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

      {/* 底部：旧入口（默认收起） */}
      <details className="px-3 pb-2 group">
        <summary className="text-[10px] uppercase tracking-wider text-fg-dim cursor-pointer
                            pl-3 py-1 hover:text-fg-muted transition select-none">
          更多工具 ▾
        </summary>
        <div className="mt-1 space-y-0.5">
          {[
            { to: "/glossary",   label: "术语表" },
            { to: "/advisor",    label: "AI推荐" },
            { to: "/settings",   label: "设置" },
          ].map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 pl-6 pr-3 py-1.5 rounded text-xs transition",
                  "hover:bg-bg-hover",
                  isActive ? "text-fg" : "text-fg-dim"
                )
              }
            >
              <span>{label}</span>
            </NavLink>
          ))}
        </div>
      </details>
    </aside>
  );
}
