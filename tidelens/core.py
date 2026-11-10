"""Public-source identity, validation, and conservative evidence labels."""
from __future__ import annotations
from datetime import datetime, timezone
from hashlib import sha256
from html import unescape
from ipaddress import ip_address
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING = {"utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "fbclid", "gclid", "ref"}
SENSITIVE = ("token", "password", "secret", "apikey", "api_key", "access_key", "authorization", "session", "auth", "signature", "credential")
TOPICS = {
    "ai_agent": ("agent", "mcp", "skill", "codex", "workflow", "智能体", "自动化", "rag", "claude"),
    "research": ("科研", "论文", "arxiv", "zotero", "obsidian", "forecast", "时序", "电价"),
    "cloud": ("free", "credits", "免费", "云", "gpu", "学生权益", "api"),
    "contest": ("hackathon", "比赛", "contest", "竞赛", "大赛", "开发者"),
    "video": ("youtube", "bilibili", "b站", "视频", "tutorial"),
}

def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def clean(value: object, limit: int = 420) -> str:
    value = re.sub(r"<[^>]{0,500}>", " ", str(value or ""))
    return " ".join(unescape(value).split())[:limit]

def canonical_url(url: str) -> str:
    """Reject unsafe/private/credentialed URLs; never include tracking or secret query fields."""
    try:
        p = urlsplit(str(url))
        if p.scheme != "https" or p.username or p.password or not p.hostname:
            return ""
        host = p.hostname.lower().rstrip(".")
        if host in {"localhost", "localhost.localdomain"} or host.endswith((".local", ".internal", ".test")):
            return ""
        try:
            if not ip_address(host).is_global:
                return ""
        except ValueError:
            pass
        pairs = parse_qsl(p.query, keep_blank_values=False)
        if any(any(mark in k.casefold() for mark in SENSITIVE) for k, _ in pairs):
            return ""
        pairs = [(k, v) for k, v in pairs if k.lower() not in TRACKING]
        if host in {"www.youtube.com", "youtube.com"} and p.path == "/watch":
            video = [v for k, v in pairs if k == "v"]
            if video and re.fullmatch(r"[\w-]{11}", video[0]):
                return "https://www.youtube.com/watch?v=" + video[0]
        if p.port not in (None, 443):
            return ""
        return urlunsplit(("https", host, p.path.rstrip("/") or "/", urlencode(pairs), ""))
    except (ValueError, TypeError):
        return ""

def topic_for(title: str, excerpt: str) -> str:
    s = (title + " " + excerpt).casefold()
    matches = [(sum(w in s for w in words), name) for name, words in TOPICS.items()]
    count, name = max(matches)
    return name if count else "other"

def event(title: str, url: str, platform: str, excerpt: str = "",
          source_id: str = "", published_hint: str = "", evidence: str = "feed_metadata_only") -> dict | None:
    url = canonical_url(url)
    title = clean(title, 220)
    if not url or not title:
        return None
    excerpt = clean(excerpt, 500)
    return {
        "id": sha256(url.encode()).hexdigest()[:24],
        "title": title,
        "url": url,
        "source": clean(source_id, 64),
        "platform": clean(platform, 64),
        "excerpt": excerpt,
        "published_hint": clean(published_hint, 90),
        "topic": topic_for(title, excerpt),
        "evidence_level": evidence,
        "observed_utc": now_utc(),
        "claimed": False,
        "delivered": False,
    }

def selection_score(item: dict) -> int:
    topic = item.get("topic", "")
    return {"contest": 6, "ai_agent": 5, "research": 5, "cloud": 4, "video": 3}.get(topic, 1) + int("official" in item.get("evidence_level", ""))
