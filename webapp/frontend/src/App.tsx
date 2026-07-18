import { Route, Routes, Navigate, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { Sidebar } from "./components/Sidebar";
import { MobileTabBar } from "./components/MobileTabBar";
import { Header } from "./components/Header";
import { useWS } from "./lib/ws";
import { useBootstrapData } from "./lib/useBootstrapData";
import { Today } from "./routes/Today";
import { Explore } from "./routes/Explore";
import { MarketDetail } from "./routes/MarketDetail";
import { Practice } from "./routes/Practice";
import { GuidedPractice } from "./routes/GuidedPractice";
import { ScenarioTraining } from "./routes/ScenarioTraining";
import { FreePractice } from "./routes/FreePractice";
import { ReviewCenter } from "./routes/ReviewCenter";
import { StageExam } from "./routes/StageExam";
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

  // v2.4: App 启动每日签到（幂等）
  useEffect(() => {
    fetch("/api/checkin", { method: "POST" }).catch(() => {});
  }, []);

  return (
    <div className="relative flex h-screen w-screen overflow-hidden bg-bg text-fg">
      {/* Liquid Glass 氛围光背景 */}
      <div className="ambient-bg" aria-hidden="true" />

      <Sidebar />
      <div className="relative z-10 flex flex-col flex-1 overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto px-4 pb-24 lg:pb-8 lg:px-6 xl:px-8">
          <Routes>
            {/* v2.2 新首页与教学入口 */}
            <Route path="/" element={<Navigate to="/today" replace />} />
            <Route path="/today" element={<Today />} />
            <Route path="/explore" element={<Explore />} />
            <Route path="/explore/markets/:marketId" element={<MarketDetail />} />
            <Route path="/practice" element={<Practice />} />
            <Route path="/practice/guided" element={<GuidedPractice />} />
            <Route path="/practice/scenario/:scenarioId" element={<ScenarioTraining />} />
            <Route path="/practice/free" element={<FreePractice />} />
            <Route path="/me/reviews" element={<ReviewCenter />} />
            <Route path="/me" element={<Me />} />

            {/* 学习路径（保留） */}
            <Route path="/learning" element={<Learning />} />
            <Route path="/learning/:chapterId" element={<LearningChapter />} />
            <Route path="/learning/exam/:stageId" element={<StageExam />} />
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
      <MobileTabBar />
    </div>
  );
}
