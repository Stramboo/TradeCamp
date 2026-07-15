import { Route, Routes, Navigate, useNavigate } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import { Header } from "./components/Header";
import { useWS } from "./lib/ws";
import { useBootstrapData } from "./lib/useBootstrapData";
import { Today } from "./routes/Today";
import { Explore } from "./routes/Explore";
import { MarketDetail } from "./routes/MarketDetail";
import { Practice } from "./routes/Practice";
import { GuidedPractice } from "./routes/GuidedPractice";
import { Me } from "./routes/Me";
// 旧路由 — 保留兼容
import { Trading } from "./routes/Trading";
import { TradingDesk } from "./routes/TradingDesk";
import { Analysis } from "./routes/Analysis";
import { AIAdvisor } from "./routes/AIAdvisor";
import { Strategy } from "./routes/Strategy";
import { Learning } from "./routes/Learning";
import { LearningChapter } from "./routes/LearningChapter";
import { LearningDashboard } from "./routes/LearningDashboard";
import { Glossary } from "./routes/Glossary";
import { Portfolio } from "./routes/Portfolio";
import { Journal } from "./routes/Journal";
import { Onboarding } from "./features/Onboarding";
import { Logs } from "./routes/Logs";
import { Settings } from "./routes/Settings";

export default function App() {
  const onboardingDone = localStorage.getItem("onboarding_completed") === "1";

  return (
    <>
      {!onboardingDone ? <OnboardingRedirect /> : <AppContent />}
    </>
  );
}

function OnboardingRedirect() {
  const navigate = useNavigate();
  return <Onboarding onDone={() => { navigate("/today"); }} />;
}

function AppContent() {
  useWS();
  useBootstrapData();
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-bg text-fg">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto p-4 lg:p-6 xl:p-8">
          <Routes>
            {/* v2.2 新首页与教学入口 */}
            <Route path="/" element={<Navigate to="/today" replace />} />
            <Route path="/today" element={<Today />} />
            <Route path="/explore" element={<Explore />} />
            <Route path="/explore/markets/:marketId" element={<MarketDetail />} />
            <Route path="/practice" element={<Practice />} />
            <Route path="/practice/guided" element={<GuidedPractice />} />
            <Route path="/me" element={<Me />} />

            {/* 学习路径（保留） */}
            <Route path="/learning" element={<Learning />} />
            <Route path="/learning/:chapterId" element={<LearningChapter />} />
            <Route path="/learning/dashboard" element={<LearningDashboard />} />
            <Route path="/glossary" element={<Glossary />} />

            {/* 旧路由 — 保持兼容，不在导航中展示 */}
            <Route path="/advisor" element={<AIAdvisor />} />
            <Route path="/trading" element={<Trading />} />
            <Route path="/desk" element={<TradingDesk />} />
            <Route path="/analysis" element={<Analysis />} />
            <Route path="/strategy" element={<Strategy />} />
            <Route path="/portfolio" element={<Portfolio />} />
            <Route path="/journal" element={<Journal />} />
            <Route path="/logs" element={<Logs />} />
            <Route path="/settings" element={<Settings />} />

            <Route path="*" element={<Navigate to="/today" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
