/**
 * navItems.ts — 共享导航常量 (v2.4 Phase 8)
 *
 * Sidebar 和 MobileTabBar 共用，避免两处维护
 */
import { Compass, GraduationCap, Globe, Gamepad2, User } from "lucide-react";

export const primaryNavItems = [
  { to: "/today",     label: "今日",     icon: Compass },
  { to: "/learning",  label: "学习",     icon: GraduationCap },
  { to: "/explore",   label: "世界市场", icon: Globe },
  { to: "/practice",  label: "模拟练习", icon: Gamepad2 },
  { to: "/me",        label: "我的成长", icon: User },
];
