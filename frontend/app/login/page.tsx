"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { login, setSessionId } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async () => {
    if (!input.trim()) { setError("请粘贴 Cookie"); return; }
    setLoading(true); setError("");
    try {
      const res = await login("douyin", input.trim());
      setSessionId(res.session_id);
      router.replace("/favorites");
    } catch (e: any) {
      let msg = "登录失败";
      try { const j = JSON.parse(e.message); msg = j.detail || j.message || e.message; } catch { msg = e.message; }
      setError(msg);
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-b from-gray-950 to-gray-900">
      <div className="w-full max-w-md">
        <div className="text-center mb-10">
          <div className="text-5xl mb-4">📚</div>
          <h1 className="text-3xl font-bold">Knowledge RAG</h1>
          <p className="text-gray-400 mt-2">把你的收藏夹变成可对话的知识库</p>
        </div>
        <div className="bg-[var(--bg-card)] rounded-2xl p-8 border border-gray-800 shadow-xl">
          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-2">登录到抖音</h2>
            <ol className="text-sm text-gray-400 space-y-1 list-decimal list-inside">
              <li>打开抖音网页版 (douyin.com) 并登录</li>
              <li>按 F12 打开开发者工具 → Network 标签</li>
              <li>刷新页面，点击任意请求</li>
              <li>在 Request Headers 中找到 Cookie 字段</li>
              <li>复制完整的 Cookie 值到下方输入框</li>
            </ol>
          </div>
          <textarea className="w-full bg-gray-900 border border-gray-700 rounded-xl p-4 text-sm h-28 font-mono focus:border-indigo-500 focus:outline-none resize-none transition-colors"
            placeholder="在此粘贴 Cookie..."
            value={input} onChange={e => setInput(e.target.value)} />
          <div className="flex gap-3 mt-4">
            <button
              className="flex-1 bg-indigo-500 hover:bg-indigo-600 text-white font-medium py-3 rounded-xl transition-all disabled:opacity-50 shadow-lg shadow-indigo-500/20"
              onClick={handleLogin} disabled={loading}>{loading ? "验证中..." : "登录"}</button>
          </div>
          {error && (
            <div className="mt-4 bg-red-900/30 border border-red-800/50 text-red-400 text-sm rounded-xl p-4">
              <strong>错误：</strong> {error.replace(/"/g, "'")}
              <p className="mt-2 text-xs text-red-400/70">Cookie 可能已过期，请重新从 douyin.com 获取</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
