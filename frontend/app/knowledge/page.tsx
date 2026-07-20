"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getSyncTasks, getKnowledgeStatus, getSessionId, SyncStatus, KnowledgeStatus as KS } from "@/lib/api";
import NavBar from "@/components/NavBar";

export default function KnowledgePage() {
  const router = useRouter();
  const [status, setStatus] = useState<KS | null>(null);
  const [tasks, setTasks] = useState<SyncStatus[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getSessionId()) { router.replace("/login"); return; }
    const load = async () => {
      try { const [s, t] = await Promise.all([getKnowledgeStatus(), getSyncTasks()]); setStatus(s); setTasks(t); }
      catch (e) { console.error(e); } finally { setLoading(false); }
    };
    load();
    const iv = setInterval(load, 5000);
    return () => clearInterval(iv);
  }, [router]);

  const cards = [
    { label: "总计", value: status?.total_videos || 0, color: "text-indigo-400", bg: "bg-indigo-500/10" },
    { label: "已处理", value: status?.processed || 0, color: "text-green-400", bg: "bg-green-500/10" },
    { label: "待处理", value: status?.pending || 0, color: "text-yellow-400", bg: "bg-yellow-500/10" },
    { label: "失败", value: status?.failed || 0, color: "text-red-400", bg: "bg-red-500/10" },
  ];

  if (loading) return <div className="flex items-center justify-center min-h-screen"><div className="animate-spin h-8 w-8 border-2 border-indigo-500 border-t-transparent rounded-full" /></div>;

  return (
    <div className="min-h-screen">
      <NavBar />
      <main className="p-6 max-w-6xl">
        <h1 className="text-2xl font-bold mb-8">知识库状态</h1>
        <div className="grid grid-cols-4 gap-4 mb-8">
          {cards.map(c => (
            <div key={c.label} className={"rounded-xl p-5 border border-gray-800 text-center " + c.bg}>
              <div className={"text-3xl font-bold " + c.color}>{c.value}</div>
              <div className="text-xs text-gray-500 mt-1">{c.label}</div>
            </div>
          ))}
        </div>
        <h2 className="font-semibold mb-4">同步任务</h2>
        {tasks.length === 0 && (
          <div className="text-center py-16 text-gray-500">
            <p>暂无同步任务</p>
            <p className="text-sm mt-2">在收藏夹页面选择并同步</p>
          </div>
        )}
        <div className="space-y-3">
          {tasks.map(t => (
            <div key={t.task_id} className="bg-gray-800/50 rounded-xl p-5 border border-gray-800">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm">收藏夹 #{t.folder_id}</span>
                <span className={"text-xs px-2 py-1 rounded-full " + (
                  t.status === "completed" ? "bg-green-900/30 text-green-400" :
                  t.status === "failed" ? "bg-red-900/30 text-red-400" :
                  t.status === "running" ? "bg-indigo-900/30 text-indigo-400" : "bg-gray-800 text-gray-500"
                )}>
                  {t.status === "completed" ? "已完成" : t.status === "failed" ? "失败" : t.status === "running" ? "进行中" : "待处理"}
                </span>
              </div>
              {t.progress_total > 0 && (
                <div>
                  <div className="flex justify-between text-xs text-gray-500 mb-1">
                    <span>{t.progress_done}/{t.progress_total}</span>
                    <span>{Math.round((t.progress_done / t.progress_total) * 100)}%</span>
                  </div>
                  <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                    <div className="h-full bg-indigo-500 rounded-full transition-all" style={{ width: (t.progress_done / t.progress_total * 100) + "%" }} />
                  </div>
                </div>
              )}
              {t.progress_current && <p className="text-xs text-gray-500 mt-2">{t.progress_current}</p>}
              {t.error && <p className="text-xs text-red-400 mt-2">错误: {t.error}</p>}
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
