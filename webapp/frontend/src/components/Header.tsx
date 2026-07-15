/**
 * Header.tsx — v2.2 教学化顶部栏
 *
 * 不再展示账户数字和真实账户切换器。
 * 仅保留当前学习阶段的简短提示。
 */
import { useSandboxStore } from "../store/sandboxStore";

export function Header() {
  const sandboxCash = useSandboxStore((s) => s.sandboxCash);
  const sandboxPositions = useSandboxStore((s) => s.sandboxPositions);
  const marketValue = sandboxPositions.reduce((s, p) => s + p.quantity * p.avgCost, 0);

  return (
    <header className="h-16 shrink-0 bg-bg-panel border-b border-line flex items-center px-6">
      <div className="flex-1" />
      <div className="flex items-center gap-6">
        <span className="text-xs text-fg-muted">
          模拟账户余额 <span className="text-fg font-semibold tabular ml-1">
            ${(sandboxCash + marketValue).toLocaleString()}
          </span>
        </span>
      </div>
    </header>
  );
}
