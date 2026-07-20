"use client";
import { useEffect, useState, use } from "react";
import { useRouter } from "next/navigation";
import { getVideos, getSessionId, VideoItem } from "@/lib/api";
import NavBar from "@/components/NavBar";

export default function FolderDetail({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const { id } = use(params);
  const [videos, setVideos] = useState<VideoItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!getSessionId()) { router.replace("/login"); return; }
    setLoading(true);
    setErrorMsg(null);
    getVideos(parseInt(id))
      .then(setVideos)
      .catch((err: any) => {
        let msg = "连接后台失败";
        if (err instanceof Error) {
          try { const parsed = JSON.parse(err.message); msg = parsed.detail || err.message; } catch { msg = err.message; }
        }
        setErrorMsg(msg);
      })
      .finally(() => setLoading(false));
  }, [id, router]);

  if (loading) return <div className="flex items-center justify-center min-h-screen"><div className="animate-spin h-8 w-8 border-2 border-indigo-500 border-t-transparent rounded-full" /></div>;

  return (
    <div className="min-h-screen">
      <NavBar />
      <main className="max-w-6xl mx-auto p-6">
        <button className="text-sm text-gray-500 hover:text-indigo-400 mb-6 transition-colors" onClick={() => router.back()}>← 返回</button>
        <h1 className="text-xl font-bold mb-6">视频列表 <span className="text-sm font-normal text-gray-500 ml-2">{videos.length} 个</span></h1>
        {errorMsg && (
          <div className="bg-red-900/30 border border-red-700 rounded-xl p-4 mb-6 text-red-300 text-sm">
            <strong>错误：</strong> {errorMsg.replace(/"/g, "'")}
            <p className="mt-2 text-red-400/70 text-xs">提示：Cookie 可能已过期，请重新登录获取新的 Cookie，或检查后台是否正常运行</p>
          </div>
        )}
        <div className="space-y-3">
          {videos.map(v => (
            <div key={v.id} className="bg-gray-800/50 rounded-xl p-4 border border-gray-800 flex gap-4 items-center">
              {v.cover_url && <img src={v.cover_url} alt={v.title} className="w-16 h-24 object-cover rounded-lg flex-shrink-0" />}
              <div className="flex-1 min-w-0">
                <h3 className="font-medium truncate">{v.title}</h3>
                {v.author_name && <p className="text-sm text-gray-400 mt-1">{v.author_name}</p>}
                <div className="flex gap-3 mt-2 text-xs text-gray-500">
                  {v.duration && <span>{Math.floor(v.duration / 60)}:{String(v.duration % 60).padStart(2, "0")}</span>}
                  <span className={v.is_processed ? "text-green-400" : "text-yellow-400"}>{v.is_processed ? "已入库" : "待处理"}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
        {videos.length === 0 && !errorMsg && <div className="text-center py-20 text-gray-500">暂无视频数据</div>}
      </main>
    </div>
  );
}
