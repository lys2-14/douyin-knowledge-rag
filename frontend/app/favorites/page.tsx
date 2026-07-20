"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getSessionId, getFolders, toggleFolder, startSync, getKnowledgeStatus, FolderItem } from "@/lib/api";
import NavBar from "@/components/NavBar";

export default function FavoritesPage() {
  const router = useRouter();
  const [folders, setFolders] = useState<FolderItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [status, setStatus] = useState<any>(null);

  useEffect(() => {
    if (!getSessionId()) { router.replace("/login"); return; }
    getFolders()
      .then(f => getKnowledgeStatus().then(s => { setFolders(f); setStatus(s); }).catch(() => setFolders(f)))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [router]);

  async function handleSync() {
    const ids = folders.filter(f => f.is_selected).map(f => f.id);
    if (ids.length === 0) return;
    setSyncing(true);
    try { await startSync(ids); alert("同步任务已启动！"); }
    catch (e: any) { alert(e.message); }
    finally { setSyncing(false); }
  }

  if (loading) return <div className="flex items-center justify-center min-h-screen"><div className="animate-spin h-8 w-8 border-2 border-indigo-500 border-t-transparent rounded-full" /></div>;

  return (
    <div className="min-h-screen">
      <NavBar />
      <main className="p-6 max-w-6xl">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold">我的收藏夹</h1>
            <p className="text-gray-400 text-sm mt-1">选择收藏夹并同步到知识库</p>
          </div>
          <div className="flex gap-3">
            {status && <span className="text-xs text-gray-500 self-center">{status.processed}/{status.total_videos} 已处理</span>}
            <button className="bg-indigo-500 hover:bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm transition-colors disabled:opacity-50"
              onClick={handleSync} disabled={syncing || folders.filter(f => f.is_selected).length === 0}>
              {syncing ? "启动中..." : "同步选中收藏夹"}
            </button>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {folders.map(f => (
            <div key={f.id} className="bg-[var(--bg-card)] rounded-xl p-5 border border-gray-800 hover:border-gray-700 transition-all">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <Link href={"/favorites/" + f.id} className="font-semibold hover:text-indigo-400 transition-colors">{f.title}</Link>
                  <p className="text-xs text-gray-500 mt-1">{f.video_count} 个视频</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer ml-3 flex-shrink-0">
                  <input type="checkbox" className="sr-only peer" checked={f.is_selected}
                    onChange={async () => {
                      await toggleFolder(f.id, !f.is_selected);
                      setFolders(folders.map(x => x.id === f.id ? { ...x, is_selected: !x.is_selected } : x));
                    }} />
                  <div className="w-9 h-5 bg-gray-700 rounded-full peer peer-checked:bg-indigo-500 peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all" />
                </label>
              </div>
              {f.description && <p className="text-sm text-gray-400 line-clamp-2 mb-3">{f.description}</p>}
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
