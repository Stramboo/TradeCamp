import { Route, Routes, Navigate } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import { Header } from "./components/Header";
import { useWS } from "./lib/ws";
import { useBootstrapData } from "./lib/useBootstrapData";
import { Dashboard } from "./routes/Dashboard";
import { Trading } from "./routes/Trading";
import { Analysis } from "./routes/Analysis";
import { Strategy } from "./routes/Strategy";
import { Logs } from "./routes/Logs";
import { Settings } from "./routes/Settings";

export default function App() {
  useWS();
  useBootstrapData();
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-bg text-fg">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto p-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/trading" element={<Trading />} />
            <Route path="/analysis" element={<Analysis />} />
            <Route path="/strategy" element={<Strategy />} />
            <Route path="/logs" element={<Logs />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
