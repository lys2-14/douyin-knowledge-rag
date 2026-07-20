"""
Export workflow — structured export helpers.
"""
from __future__ import annotations

from datetime import datetime


def videos_to_markdown(
    videos: list[dict],
    folder_title: str = "",
    include_summary: bool = True,
    include_transcript: bool = False,
) -> str:
    """Format a list of video dicts as Markdown."""
    lines = [
        f"# {folder_title or '知识库'}",
        f"> 导出时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"> 视频数量: {len(videos)}",
        "",
    ]

    for v in videos:
        lines.append(f"## 🎬 {v.get('title', 'Untitled')}")
        if v.get("author_name"):
            lines.append(f"- **作者**: {v['author_name']}")
        if v.get("duration"):
            d = v["duration"]
            lines.append(f"- **时长**: {d // 60}:{d % 60:02d}")
        if v.get("video_url"):
            lines.append(f"- **链接**: {v['video_url']}")
        if v.get("hashtags"):
            lines.append(f"- **标签**: {' '.join('#' + t for t in v['hashtags'])}")
        lines.append("")

        if include_summary and v.get("summary"):
            lines.append("### 📝 摘要")
            lines.append(v["summary"])
            lines.append("")

        if include_transcript and v.get("transcript"):
            lines.append("### 📜 逐字稿")
            lines.append(v["transcript"])
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


__all__ = ["videos_to_markdown"]

