/**
 * MobileTabBar.tsx — 移动端底部导航栏 (v2.4 Phase 8)
 *
 * Liquid Glass 风格，5 项主导航，安全区适配
 */
import { NavLink } from "react-router-dom";
import { primaryNavItems } from "./navItems";
import { cn } from "../lib/utils";

export function MobileTabBar() {
  return (
    <nav className="fixed bottom-0 inset-x-0 z-40 lg:hidden">
      {/* 玻璃背景 */}
      <div className="glass border-t border-white/[0.08] rounded-t-[20px]
                      pb-[env(safe-area-inset-bottom)]">
        <div className="flex items-center justify-around px-2 pt-1.5 pb-1">
          {primaryNavItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  "flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-[12px] min-w-[56px]",
                  "transition-all duration-300",
                  isActive
                    ? "text-emerald-400"
                    : "text-fg-dim hover:text-fg-muted"
                )
              }
            >
              {({ isActive }) => (
                <>
                  <div className={cn(
                    "w-8 h-8 rounded-[10px] flex items-center justify-center transition-all",
                    isActive && "bg-emerald-500/15 shadow-[0_0_12px_rgba(52,211,153,0.2)]"
                  )}>
                    <Icon className="w-[18px] h-[18px]" strokeWidth={isActive ? 2.2 : 1.8} />
                  </div>
                  <span className="text-[10px] font-medium">{label}</span>
                </>
              )}
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  );
}
