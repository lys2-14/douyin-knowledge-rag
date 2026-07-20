"use client";
import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { askStream, getSessionId, getFolders, FolderItem, SourceItem } from "@/lib/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import NavBar from "@/components/NavBar";

interface Message { role: "user" | "assistant"; content: string; sources?: SourceItem[]; }

export default function ChatPage() {
  const router = useRouter();
  const [msgs, setMsgs] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [streamingSources, setStreamingSources] = useState<SourceItem[]>([]);
  const [folders, setFolders] = useState<FolderItem[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const chatRef = useRef<HTMLDivElement>(null);
  const streamingRef = useRef(false);
  const contentRef = useRef("");
  const sourcesRef = useRef<SourceItem[]>([]);

  useEffect(() => {
    if (!getSessionId()) { router.replace("/login"); return; }
    getFolders().then(f => setFolders(f.filter(x => x.is_selected))).catch(() => {});
  }, [router]);

  useEffect(() => { chatRef.current?.scrollTo(0, chatRef.current.scrollHeight); }, [msgs, streamingContent]);

  const send = useCallback(async () => {
    const q = input.trim();
    if (!q || streaming) return;
    setInput("");
    setMsgs(p => [...p, { role: "user", content: q }]);

    contentRef.current = "";
    sourcesRef.current = [];
    streamingRef.current = true;
    setStreaming(true);
    setStreamingContent("");
    setStreamingSources([]);

    try {
      for await (const event of askStream(q, selected.length > 0 ? selected : undefined)) {
        if (!streamingRef.current) break;
        if (event.type === "sources") {
          const items = event.content as SourceItem[];
          sourcesRef.current = items;
          setStreamingSources(items);
        } else if (event.type === "token") {
          contentRef.current += event.content;
          setStreamingContent(contentRef.current);
        }
      }
      setMsgs(p => [...p, { role: "assistant", content: contentRef.current, sources: sourcesRef.current }]);
    } catch (e: any) {
      setMsgs(p => [...p, { role: "assistant", content: e?.message || "请求失败" }]);
    } finally {
      streamingRef.current = false;
      setStreaming(false);
      setStreamingContent("");
      setStreamingSources([]);
    }
  }, [input, streaming, selected]);

  return (
    <div className="min-h-screen flex flex-col">
      <NavBar />
      {folders.length > 0 && (
        <div className="border-b border-gray-800 bg-gray-900/50">
          <div className="max-w-4xl mx-auto px-4 py-2 flex gap-2 flex-wrap items-center text-xs">
            <span className="text-gray-500">筛选:</span>
            {folders.map(f => (
              <button key={f.id} className={"px-2 py-1 rounded-md transition-colors " + (selected.includes(f.id) ? "bg-indigo-500/20 text-indigo-400" : "bg-gray-800 text-gray-500 hover:text-gray-300")}
                onClick={() => setSelected(p => p.includes(f.id) ? p.filter(x => x !== f.id) : [...p, f.id])}>{f.title}</button>
            ))}
          </div>
        </div>
      )}

      <div ref={chatRef} className="flex-1 overflow-y-auto max-w-4xl mx-auto w-full p-4 space-y-4">
        {msgs.length === 0 && !streaming && (
          <div className="text-center py-24">
            <div className="text-6xl mb-4">💬</div>
            <h2 className="text-xl font-bold mb-2">开始对话</h2>
            <p className="text-gray-400 text-sm">基于你的收藏夹知识库进行问答</p>
          </div>
        )}
        {msgs.map((m, i) => (
          <div key={i} className={"flex " + (m.role === "user" ? "justify-end" : "justify-start")}>
            <div className={"max-w-[80%] rounded-2xl p-4 " + (m.role === "user"
              ? "bg-indigo-500/20 border border-indigo-500/30"
              : "bg-gray-800/50 border border-gray-800")}>
              {m.role === "user" ? (
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{m.content}</p>
              ) : (
                <div className="markdown text-sm">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content || "*（空响应）*"}</ReactMarkdown>
                </div>
              )}
              {m.sources && m.sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-700">
                  <p className="text-xs text-gray-500 mb-2">来源 ({m.sources.length})</p>
                  {m.sources.slice(0, 3).map((s, j) => (
                    <div key={j} className="text-xs bg-gray-800 rounded-lg p-2 mb-1">
                      <p className="font-medium truncate text-indigo-300">{s.title}</p>
                      <p className="text-gray-500">{s.author && s.author + " · "}{(s.score * 100).toFixed(0)}%</p>
                    </div>
                  ))}
                  {m.sources.length > 3 && <p className="text-xs text-gray-600">还有 {m.sources.length - 3} 个来源...</p>}
                </div>
              )}
            </div>
          </div>
        ))}
        {streaming && (
          <div className="flex justify-start">
            <div className="bg-gray-800/50 border border-gray-800 rounded-2xl p-4 max-w-[80%]">
              {streamingContent ? (
                <div className="markdown text-sm">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{streamingContent}</ReactMarkdown>
                </div>
              ) : (
                <div className="flex gap-1.5"><div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" /><div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }} /><div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }} /></div>
              )}
              {streamingSources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-700">
                  <p className="text-xs text-gray-500 mb-2">来源 ({streamingSources.length})</p>
                  {streamingSources.slice(0, 3).map((s, j) => (
                    <div key={j} className="text-xs bg-gray-800 rounded-lg p-2 mb-1">
                      <p className="font-medium truncate text-indigo-300">{s.title}</p>
                      <p className="text-gray-500">{s.author && s.author + " · "}{(s.score * 100).toFixed(0)}%</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-gray-800 p-4 bg-gray-950/80">
        <div className="max-w-4xl mx-auto flex gap-3">
          <textarea className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-sm resize-none focus:border-indigo-500 focus:outline-none transition-colors" rows={1}
            placeholder="输入你的问题..." value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
            disabled={streaming} />
          <button className="bg-indigo-500 hover:bg-indigo-600 text-white px-6 py-3 rounded-xl text-sm transition-all disabled:opacity-50 self-end shadow-lg shadow-indigo-500/20"
            onClick={send} disabled={streaming || !input.trim()}>发送</button>
        </div>
      </div>
    </div>
  );
}