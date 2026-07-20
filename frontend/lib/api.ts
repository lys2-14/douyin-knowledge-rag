/**
 * API client for backend communication.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    // Try to extract detail from JSON error response
    let msg = text;
    try { const j = JSON.parse(text); msg = j.detail || j.message || text; } catch {}
    throw new ApiError(res.status, msg);
  }

  return res.json();
}

// ── Auth ────────────────────────────────────────────

export interface LoginResponse {
  session_id: string;
  platform_user_id: string;
  platform_username: string;
  platform_avatar?: string;
}

export interface UserSessionInfo {
  session_id: string;
  provider: string;
  platform_username: string;
  is_valid: boolean;
  last_active_at: string;
}

export async function login(provider: string, creds: string): Promise<LoginResponse> {
  return request<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ provider, creds }),
  });
}

export async function getSessionStatus(): Promise<UserSessionInfo> {
  const sid = getSessionId();
  return request<UserSessionInfo>("/auth/status", {
    headers: { "X-Session-ID": sid || "" },
  });
}

export async function logout(): Promise<void> {
  const sid = getSessionId();
  await request("/auth/logout", {
    method: "DELETE",
    headers: { "X-Session-ID": sid || "" },
  });
  if (typeof window !== "undefined") {
    localStorage.removeItem("session_id");
  }
}

// ── Favorites ───────────────────────────────────────

export interface FolderItem {
  id: number;
  platform_folder_id: string;
  title: string;
  description?: string;
  video_count: number;
  cover_url?: string;
  is_selected: boolean;
  last_sync_at?: string;
}

export interface VideoItem {
  id: number;
  platform_video_id: string;
  title: string;
  author_name?: string;
  duration?: number;
  cover_url?: string;
  processing_stage: string;
  is_processed: boolean;
}

export async function getFolders(): Promise<FolderItem[]> {
  const sid = getSessionId();
  return request<FolderItem[]>("/favorites/folders", {
    headers: { "X-Session-ID": sid || "" },
  });
}

export async function getVideos(folderId: number): Promise<VideoItem[]> {
  const sid = getSessionId();
  return request<VideoItem[]>(`/favorites/folders/${folderId}/videos`, {
    headers: { "X-Session-ID": sid || "" },
  });
}

export async function toggleFolder(folderId: number, selected: boolean): Promise<void> {
  const sid = getSessionId();
  await request(`/favorites/folders/${folderId}/select?selected=${selected}`, {
    method: "PUT",
    headers: { "X-Session-ID": sid || "" },
  });
}

// ── Knowledge ───────────────────────────────────────

export interface SyncStatus {
  task_id: string;
  folder_id: number;
  status: string;
  progress_total: number;
  progress_done: number;
  progress_current?: string;
  error?: string;
}

export interface KnowledgeStatus {
  total_videos: number;
  processed: number;
  pending: number;
  failed: number;
}

export async function startSync(folderIds: number[]): Promise<{ task_ids: string[] }> {
  const sid = getSessionId();
  return request<{ task_ids: string[] }>("/knowledge/sync", {
    method: "POST",
    headers: { "X-Session-ID": sid || "" },
    body: JSON.stringify({ folder_ids: folderIds }),
  });
}

export async function getKnowledgeStatus(): Promise<KnowledgeStatus> {
  const sid = getSessionId();
  return request<KnowledgeStatus>("/knowledge/status", {
    headers: { "X-Session-ID": sid || "" },
  });
}

export async function getSyncTasks(): Promise<SyncStatus[]> {
  const sid = getSessionId();
  return request<SyncStatus[]>("/knowledge/tasks", {
    headers: { "X-Session-ID": sid || "" },
  });
}

// ── Chat ────────────────────────────────────────────

export interface SourceItem {
  platform_video_id: string;
  title: string;
  author?: string;
  snippet: string;
  score: number;
  url?: string;
}

export interface ChatResponse {
  answer: string;
  sources: SourceItem[];
  conversation_id: string;
}

export async function ask(
  question: string,
  folderIds?: number[]
): Promise<ChatResponse> {
  const sid = getSessionId();
  return request<ChatResponse>("/chat/ask", {
    method: "POST",
    headers: { "X-Session-ID": sid || "" },
    body: JSON.stringify({ question, folder_ids: folderIds }),
  });
}

export type StreamEvent =
  | { type: "sources"; content: SourceItem[] }
  | { type: "token"; content: string };

export async function* askStream(
  question: string,
  folderIds?: number[]
): AsyncGenerator<StreamEvent> {
  const sid = getSessionId();
  const res = await fetch(`${API_BASE}/chat/ask/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Session-ID": sid || "",
    },
    body: JSON.stringify({ question, folder_ids: folderIds }),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`请求失败: ${res.status} ${text}`);
  }

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6));
          yield data as StreamEvent;
        } catch { /* skip malformed SSE line */ }
      }
    }
  }
}

// ── Session helpers ─────────────────────────────────

export function getSessionId(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem("session_id");
  }
  return null;
}

export function setSessionId(sid: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem("session_id", sid);
  }
}

export function clearSessionId(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem("session_id");
  }
}

export { ApiError };
