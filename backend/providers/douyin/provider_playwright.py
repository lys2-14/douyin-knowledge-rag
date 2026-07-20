"""Douyin provider using Playwright Async API + Edge + webpack module API.

Bypasses X-Bogus signing by running API calls inside the browser context
via Douyin's internal webpack module.

Reference: https://github.com/Jonesxq/douyin_RAG

Key design:
- validate_credentials: opens VISIBLE browser ONCE, injects cookies, saves storage_state
- get_folders / get_videos: reuses saved storage_state with HEADLESS browser
- Anti-detection: hides webdriver, sets realistic UA/languages/plugins
- Cache: fetched data is cached so subsequent calls don't re-open browser
"""

from __future__ import annotations

import asyncio
import json
import time
import traceback
from pathlib import Path
from typing import Optional

from backend.providers.base import BaseProvider, FolderInfo, UserInfo, VideoInfo

_PLAYWRIGHT_AVAILABLE = False
try:
    from playwright.async_api import async_playwright
    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PLAYWRIGHT_STATE = PROJECT_ROOT / "data" / "playwright_state.json"

_ANTI_DETECT_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
window.chrome = { runtime: {} };
"""


class DouyinPlaywrightProvider(BaseProvider):
    """Douyin provider using Playwright Async API."""

    def __init__(self):
        self._browser = None
        self._context = None
        self._page = None
        self._pw = None
        self._browser_lock = asyncio.Lock()
        self._snapshot_cache = None
        self._cache_timestamp = 0.0
        _ensure_state_dir()

    @property
    def platform(self) -> str:
        return "douyin"

    async def _launch_browser(self, headless: bool = False):
        """Launch Playwright browser with fallback attempts."""
        self._pw = await async_playwright().start()
        candidates = [
            {"channel": "msedge", "headless": headless},
            {"headless": headless},
        ]
        last_error = None
        for opts in candidates:
            try:
                self._browser = await self._pw.chromium.launch(
                    **opts,
                    args=[
                        "--disable-gpu",
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-blink-features=AutomationControlled",
                    ],
                )
                print(f"[PW] Browser launched (headless={headless})", flush=True)
                return
            except Exception as e:
                last_error = e
                continue
        raise RuntimeError(f"Failed to launch browser: {last_error}")

    async def _ensure_browser(self, headless: bool = False):
        """Ensure browser is alive; launch if needed."""
        async with self._browser_lock:
            if self._page is not None:
                try:
                    await self._page.evaluate("1")
                    return
                except Exception:
                    pass
            await self._close_browser()
            await self._launch_browser(headless=headless)

    async def _create_context(self, cookie_str: str = "", reuse_state: bool = False):
        await self._ensure_browser(headless=reuse_state)
        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0"
            ),
        }
        if reuse_state and PLAYWRIGHT_STATE.exists():
            context_options["storage_state"] = str(PLAYWRIGHT_STATE)
        self._context = await self._browser.new_context(**context_options)
        if cookie_str and not reuse_state:
            cd = self._parse_cookies(cookie_str)
            cs = [{"name": k, "value": v, "domain": ".douyin.com", "path": "/"} for k, v in cd.items()]
            if cs:
                await self._context.add_cookies(cs)
        self._page = await self._context.new_page()
        await self._page.add_init_script(_ANTI_DETECT_SCRIPT)

    async def _close_browser(self):
        try:
            if self._context: await self._context.close()
            if self._browser: await self._browser.close()
            if self._pw: await self._pw.close()
        except Exception:
            pass
        self._context = None
        self._browser = None
        self._page = None
        self._pw = None

    async def _navigate_and_wait(self):
        target_url = "https://www.douyin.com/"
        try:
            await self._page.goto(target_url, wait_until="domcontentloaded", timeout=90000)
        except Exception as e:
            print(f"[PW] goto warning: {e}", flush=True)
        await asyncio.sleep(4)
        try:
            current_url = self._page.url
            if "verify" in current_url.lower() or "captcha" in current_url.lower():
                raise RuntimeError("抖音触发了安全验证")
        except RuntimeError:
            raise
        except Exception:
            pass
        for attempt in range(3):
            try:
                await self._page.wait_for_function(
                    "typeof window.webpackChunkdouyin_web !== 'undefined'", timeout=30000
                )
                print(f"[PW] webpack found (attempt {attempt+1})", flush=True)
                await asyncio.sleep(1)
                return
            except Exception:
                print(f"[PW] webpack not found, attempt {attempt+1}/3", flush=True)
                if attempt < 2:
                    await self._page.reload(wait_until="domcontentloaded", timeout=60000)
                    await asyncio.sleep(3)
        try:
            fav_url = "https://www.douyin.com/user/self?showTab=favorite_collection"
            await self._page.goto(fav_url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(4)
            await self._page.wait_for_function(
                "typeof window.webpackChunkdouyin_web !== 'undefined'", timeout=30000
            )
            print("[PW] webpack found at favorites page", flush=True)
            return
        except Exception:
            pass
        raise RuntimeError("抖音页面加载失败：无法获取 webpack 模块。")

    @staticmethod
    def _parse_cookies(creds: str) -> dict[str, str]:
        if not creds or not creds.strip():
            raise ValueError("Cookie 内容为空")
        try:
            return json.loads(creds)
        except (json.JSONDecodeError, TypeError):
            pass
        cd = {}
        for part in creds.split(";"):
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                cd[k.strip()] = v.strip()
        if not cd:
            raise ValueError("无法解析 Cookie 字符串")
        return cd

    @staticmethod
    def _build_collects_js() -> str:
        return """
        (async () => {
            const chunks = window.webpackChunkdouyin_web;
            if (!Array.isArray(chunks)) return {ok:false, error:"no_webpack"};
            const req = chunks.push([[Symbol("c")], {}, r => r]);
            try { chunks.pop(); } catch(e) {}
            if (!req || !req.m) return {ok:false, error:"no_require"};
            let mid = null;
            for (const [id, mod] of Object.entries(req.m)) {
                let src = "";
                try { src = Function.prototype.toString.call(mod); } catch(e) { continue; }
                if (src.includes("/aweme/v1/web/collects/list/") && src.includes("/aweme/v1/web/collects/video/list/")) {
                    mid = id; break;
                }
            }
            if (!mid) return {ok:false, error:"module_not_found"};
            const api = req(Number(mid));
            const listFn = api.So;
            const videoFn = api.d6;
            if (typeof listFn !== "function" || typeof videoFn !== "function")
                return {ok:false, error:"bad_exports", keys:Object.keys(api||{})};
            const collections = [];
            let cursor = 0, guard = 0;
            while (guard < 30 && collections.length < 100) {
                guard++;
                const r = await listFn({cursor, offset:30});
                if (!r || r.statusCode !== 0) break;
                for (const c of (Array.isArray(r.data) ? r.data : []))
                    if (c && c.collectionFolderId) collections.push(c);
                cursor = Number(r.cursor || 0);
                if (!r.hasMore) break;
            }
            const byCol = {};
            for (const c of collections) {
                const cid = String(c.collectionFolderId);
                const rows = [];
                const seen = new Set();
                let cCur = 0, cG = 0;
                while (cG < 120 && rows.length < 500) {
                    cG++;
                    const vr = await videoFn({collectsId:cid, cursor:cCur, offset:20});
                    if (!vr || vr.statusCode !== 0) break;
                    for (const v of (Array.isArray(vr.data) ? vr.data : [])) {
                        const vid = String(v?.awemeId || v?.groupId || "").trim();
                        if (!vid || seen.has(vid)) continue;
                        seen.add(vid);
                        rows.push({awemeId:vid, title:String(v?.itemTitle||v?.desc||""), author:String(v?.authorInfo?.nickname||""), durationMs:Number(v?.video?.duration||0)});
                    }
                    cCur = Number(vr.cursor || 0);
                    if (!vr.hasMore) break;
                }
                byCol[cid] = rows;
            }
            return {ok:true, collections, itemsByCollection:byCol};
        })()
        """

    async def _fetch_snapshot(self) -> dict:
        js = self._build_collects_js()
        result = await self._page.evaluate(js)
        if not isinstance(result, dict):
            raise RuntimeError(f"Unexpected response: {type(result).__name__}")
        if not result.get("ok"):
            raise RuntimeError(f"Collects module failed: {result.get('error', 'unknown')}")
        return result

    async def validate_credentials(self, creds: str) -> UserInfo:
        print("[PW] ===== validate_credentials =====", flush=True)
        if PLAYWRIGHT_STATE.exists():
            try:
                await self._create_context(reuse_state=True)
                await self._navigate_and_wait()
                cookies = await self._context.cookies()
                has_session = any(c["name"] in {"sessionid","sid_guard","sessionid_ss"} for c in cookies)
                if has_session:
                    print("[PW] Saved state is still valid", flush=True)
                    return UserInfo(platform_user_id="pw_user", username="抖音用户", raw={"method":"storage_state"})
            except Exception as e:
                print(f"[PW] Saved state invalid: {e}", flush=True)
                await self._close_browser()
        print("[PW] Starting fresh login...", flush=True)
        try:
            await self._create_context(cookie_str=creds)
            await self._navigate_and_wait()
            cookies = await self._context.cookies()
            session_cookies = [c for c in cookies if c["name"] in {"sessionid","sid_guard","sessionid_ss"}]
            if not session_cookies:
                try:
                    page_url = self._page.url
                except:
                    page_url = ""
                await self._close_browser()
                raise RuntimeError(f"Cookie 验证失败：未找到登录会话。当前页面: {page_url}")
            try:
                state_dir = PLAYWRIGHT_STATE.parent
                state_dir.mkdir(parents=True, exist_ok=True)
                await self._context.storage_state(path=str(PLAYWRIGHT_STATE))
            except Exception as e:
                print(f"[PW] Could not save state: {e}", flush=True)
            print(f"[PW] Login successful! {len(session_cookies)} session cookies", flush=True)
            return UserInfo(platform_user_id="pw_user", username="抖音用户", raw={"method":"cookie"})
        except RuntimeError:
            raise
        except Exception as e:
            await self._close_browser()
            traceback.print_exc()
            raise RuntimeError(f"Login failed: {e}")

    async def get_folders(self, session_creds: str) -> list[FolderInfo]:
        print("[PW] ===== get_folders =====", flush=True)
        if self._snapshot_cache and (time.time() - self._cache_timestamp) < 300:
            return self._folders_from_cache()
        try:
            await self._create_context(reuse_state=True)
            await self._navigate_and_wait()
            result = await self._fetch_snapshot()
            self._cache_result(result)
            print(f"[PW] Fetched {len(result.get('collections',[]))} collections", flush=True)
            return self._folders_from_cache()
        except RuntimeError:
            raise
        except Exception as e:
            traceback.print_exc()
            raise RuntimeError(f"获取收藏夹失败: {e}")
        finally:
            await self._close_browser()

    async def get_videos(self, folder_id: str, session_creds: str, cursor: str = "") -> tuple[list[VideoInfo], str]:
        print(f"[PW] ===== get_videos({folder_id}) =====", flush=True)
        if self._snapshot_cache and (time.time() - self._cache_timestamp) < 300:
            rows = self._snapshot_cache.get("items_by_collection", {}).get(folder_id, [])
            if rows:
                print(f"[PW] Returning {len(rows)} cached videos", flush=True)
                return self._rows_to_videos(rows), ""
        try:
            await self._create_context(reuse_state=True)
            await self._navigate_and_wait()
            result = await self._fetch_snapshot()
            self._cache_result(result)
            rows = result.get("itemsByCollection", {}).get(folder_id, [])
            print(f"[PW] Fetched {len(rows)} videos", flush=True)
            return self._rows_to_videos(rows), ""
        except RuntimeError:
            raise
        except Exception as e:
            traceback.print_exc()
            raise RuntimeError(f"获取视频列表失败: {e}")
        finally:
            await self._close_browser()

    async def get_video_detail(self, video_id: str, session_creds: str) -> VideoInfo:
        return VideoInfo(platform_video_id=video_id, title="")

    async def get_audio_url(self, video_id: str, session_creds: str) -> Optional[str]:
        return None

    async def download_audio(self, video_id: str, session_creds: str, target_path: str) -> Optional[str]:
        return None

    def _cache_result(self, result: dict):
        self._snapshot_cache = {
            "collections": result.get("collections", []),
            "items_by_collection": result.get("itemsByCollection", {}),
        }
        self._cache_timestamp = time.time()

    def _folders_from_cache(self) -> list[FolderInfo]:
        raw = self._snapshot_cache.get("collections", []) if self._snapshot_cache else []
        folders = []
        for c in raw:
            cid = str(c.get("collectionFolderId") or "").strip()
            if not cid: continue
            folders.append(FolderInfo(
                platform_folder_id=cid,
                title=str(c.get("collectionFolderName") or "收藏夹")[:255],
                video_count=max(int(c.get("videoTotal") or 0), 0),
                cover_url=str(c.get("cover")) if c.get("cover") else None,
            ))
        return folders

    @staticmethod
    def _rows_to_videos(rows: list[dict]) -> list[VideoInfo]:
        videos = []
        for row in rows:
            aid = str(row.get("awemeId") or "").strip()
            if not aid: continue
            videos.append(VideoInfo(
                platform_video_id=aid,
                title=str(row.get("title") or "Untitled")[:500],
                author_name=str(row.get("author") or "").strip()[:255],
                duration=DouyinPlaywrightProvider._dur(row.get("durationMs")),
                video_url="https://www.douyin.com/video/" + aid,
            ))
        return videos

    @staticmethod
    def _dur(raw) -> Optional[int]:
        if raw is None: return None
        try: d = int(raw)
        except (TypeError, ValueError): return None
        if d <= 0: return None
        return d // 1000 if d > 1000 else d



    def _generate_cookie_file(self) -> str:
        """Convert Playwright saved state to a Netscape cookie file for yt-dlp."""
        import os, json, tempfile
        from pathlib import Path
        state_path = Path(__file__).resolve().parent.parent.parent.parent / "data" / "playwright_state.json"
        if not state_path.exists():
            print("[PW] No saved state for cookie export", flush=True)
            return ""
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception as e:
            print(f"[PW] Failed to read state: {e}", flush=True)
            return ""
        cookies = state.get("cookies", []) if isinstance(state, dict) else []
        if not cookies:
            print("[PW] No cookies in saved state", flush=True)
            return ""
        fd, tmp_path = tempfile.mkstemp(suffix=".txt", prefix="douyin_cookies_")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("# Netscape HTTP Cookie File\n")
            f.write("# Generated from Playwright storage state\n")
            for c in cookies:
                if not isinstance(c, dict): continue
                domain = str(c.get("domain") or "").strip()
                name = str(c.get("name") or "").strip()
                value = str(c.get("value") or "")
                if not domain or not name: continue
                sub = "TRUE" if domain.startswith(".") else "FALSE"
                cpath = str(c.get("path") or "/")
                secure = "TRUE" if bool(c.get("secure")) else "FALSE"
                exp = c.get("expires")
                try:
                    expires = int(float(exp)) if exp and float(exp) > 0 else 0
                except (TypeError, ValueError):
                    expires = 0
                f.write("	".join([domain, sub, cpath, secure, str(expires), name, value]) + "\n")


        print(f"[PW] Cookie file generated ({len(cookies)} cookies)", flush=True)
        return tmp_path

    async def download_audio(self, video_id: str, session_creds: str, target_path: str) -> Optional[str]:
        """Download audio using yt-dlp with cookies from saved state."""
        print(f"[PW] download_audio({video_id})", flush=True)
        import os
        local_appdata = os.environ.get("LOCALAPPDATA", "")
        ffmpeg_dir = os.path.join(local_appdata, "ffmpegio", "ffmpeg-downloader", "ffmpeg", "bin")
        if os.path.exists(os.path.join(ffmpeg_dir, "ffmpeg.exe")):
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
        video_url = f"https://www.douyin.com/video/{video_id}"
        cookie_file = self._generate_cookie_file()
        if not cookie_file:
            print("[PW] No cookie file, skip audio download", flush=True)
            return None
        try:
            import yt_dlp
            import asyncio
            def _dl():
                output_dir = os.path.dirname(target_path)
                os.makedirs(output_dir, exist_ok=True)
                basename = os.path.splitext(os.path.basename(target_path))[0]
                ydl_opts = {
                    "outtmpl": os.path.join(output_dir, f"{basename}.%(ext)s"),
                    "format": "bestaudio/best",
                    "noplaylist": True,
                    "quiet": True,
                    "no_warnings": True,
                    "cookiefile": cookie_file,
                    "http_headers": {
                        "Referer": "https://www.douyin.com/",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    },
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "128",
                    }],
                    "retries": 3,
                }
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.extract_info(video_url, download=True)
                except Exception as e:
                    print(f"[PW] yt-dlp postproc failed: {e}", flush=True)
                    ydl_opts_nopp = dict(ydl_opts)
                    ydl_opts_nopp.pop("postprocessors", None)
                    ydl_opts_nopp["format"] = "bestaudio[ext=m4a]/bestaudio[ext=webm]/best"
                    try:
                        with yt_dlp.YoutubeDL(ydl_opts_nopp) as ydl:
                            ydl.extract_info(video_url, download=True)
                    except Exception as e2:
                        print(f"[PW] yt-dlp also failed: {e2}", flush=True)
                        return None
                for ext in [".mp3", ".m4a", ".opus", ".webm", ".wav"]:
                    p = os.path.join(output_dir, f"{basename}{ext}")
                    if os.path.exists(p):
                        print(f"[PW] Audio downloaded: {p}", flush=True)
                        return p
                return None
            return await asyncio.to_thread(_dl)
        except Exception as e:
            print(f"[PW] Audio download failed: {e}", flush=True)
            return None

def _ensure_state_dir():
    state_dir = PLAYWRIGHT_STATE.parent
    state_dir.mkdir(parents=True, exist_ok=True)


__all__ = ["DouyinPlaywrightProvider"]
