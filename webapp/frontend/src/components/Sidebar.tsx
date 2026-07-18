import { NavLink } from "react-router-dom";
import {
  Activity,
  BookOpen, Sparkles, Settings,
} from "lucide-react";
import { cn } from "../lib/utils";
import { primaryNavItems } from "./navItems";

/**
 * Sidebar.tsx — Liquid Glass 浮动玻璃侧边栏
 *
 * macOS 27 风格：
 * - 浮动玻璃面板，与背景氛围光折射
 * - 大圆角 + 光谱高光边缘
 * - 选中态：翡翠玻璃胶囊
 * - 移动端隐藏（由 MobileTabBar 替代）
 */

const primaryItems = primaryNavItems;

const toolItems = [
  { to: "/glossary", label: "术语表",  icon: BookOpen },
  { to: "/advisor",  label: "AI 推荐", icon: Sparkles },
  { to: "/settings", label: "设置",    icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="relative z-10 shrink-0 p-3 pr-0 hidden lg:flex flex-col">
      {/* 浮动玻璃面板 */}
      <div className="glass specular-edge rounded-[22px] w-56 flex-1 flex flex-col overflow-hidden">
        {/* Logo */}
        <div className="px-5 pt-5 pb-4 flex items-center gap-3">
          <div className="h-9 w-9 rounded-[12px] grid place-items-center text-white font-bold
                          bg-gradient-to-br from-emerald-400 to-emerald-600
                          shadow-[0_4px_16px_rgba(16,185,129,0.4),inset_0_1px_0_rgba(255,255,255,0.3)]">
            <Activity className="h-4.5 w-4.5" strokeWidth={2.5} />
          </div>
          <div>
            <div className="text-fg font-semibold leading-none tracking-tight">TradeCamp</div>
            <div className="text-fg-dim text-[10px] mt-1 tracking-widest uppercase">学堂</div>
          </div>
        </div>

        <div className="glass-divider mx-4" />

        {/* 主导航 */}
        <nav className="flex-1 px-3 py-3 space-y-1 overflow-y-auto">
          {primaryItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to !== "/"}
              className={({ isActive }) =>
                cn(
                  "group flex items-center gap-3 px-3.5 py-2.5 rounded-[14px] text-sm font-medium",
                  "transition-all duration-300 ease-[cubic-bezier(.22,1,.36,1)]",
                  isActive
                    ? "text-white bg-gradient-to-r from-emerald-500/80 to-emerald-600/70 " +
                      "shadow-[0_4px_16px_rgba(16,185,129,0.35),inset_0_1px_0_rgba(255,255,255,0.25)] " +
                      "border border-emerald-400/30"
                    : "text-fg-muted hover:text-fg hover:bg-white/[0.06] border border-transparent"
                )
              }
            >
              <Icon className="h-[18px] w-[18px] shrink-0" strokeWidth={2} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        {/* 底部：更多工具 */}
        <div className="px-3 pb-4">
          <div className="glass-divider mx-1 mb-3" />
          <p className="text-[10px] uppercase tracking-widest text-fg-dim px-3.5 pb-2">
            更多工具
          </p>
          <div className="space-y-1">
            {toolItems.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 px-3.5 py-2 rounded-[12px] text-[13px]",
                    "transition-all duration-300 ease-[cubic-bezier(.22,1,.36,1)]",
                    isActive
                      ? "text-fg bg-white/[0.08] border border-white/[0.1]"
                      : "text-fg-muted hover:text-fg hover:bg-white/[0.05] border border-transparent"
                  )
                }
              >
                <Icon className="h-4 w-4 shrink-0" strokeWidth={2} />
                <span>{label}</span>
              </NavLink>
            ))}
          </div>
        </div>
      </div>
    </aside>
  );
}
