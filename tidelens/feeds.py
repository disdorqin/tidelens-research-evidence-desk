"""Bounded public RSS/Atom ingestion. Entries are leads, never verified articles."""
from __future__ import annotations
from urllib.request import Request, build_opener, HTTPRedirectHandler
from xml.etree import ElementTree as ET
from .core import canonical_url, event

MAX_BYTES = 900_000
MAX_ITEMS = 30

def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]

def xml_root(raw: bytes):
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("DTD/ENTITY not permitted")
    if len(raw) > MAX_BYTES:
        raise ValueError("feed exceeds size cap")
    return ET.fromstring(raw)

def child_text(element, names: set[str]) -> str:
    for child in element:
        if local_name(child.tag) in names:
            return " ".join(" ".join(child.itertext()).split())[:1200]
    return ""

def parse_feed(raw: bytes, source: dict) -> list[dict]:
    root = xml_root(raw)
    items = []
    for element in root.iter():
        if local_name(element.tag) not in {"item", "entry"}:
            continue
        title = child_text(element, {"title"})
        url = ""
        for child in element:
            if local_name(child.tag) == "link":
                candidate = child.get("href") or (child.text or "").strip()
                if candidate and child.get("rel", "alternate") == "alternate":
                    url = candidate
                    break
                url = url or candidate
        if url.startswith("/"):
            from urllib.parse import urljoin
            url = urljoin(source["url"], url)
        excerpt = child_text(element, {"summary", "description", "encoded", "content"})
        timestamp = child_text(element, {"updated", "published", "pubDate", "date"})
        grade = "official_feed_metadata" if source.get("trust") == "official" else "third_party_feed_metadata"
        entry = event(title, url, source.get("name", source["id"]), excerpt, source["id"], timestamp, grade)
        if entry:
            items.append(entry)
        if len(items) >= min(MAX_ITEMS, int(source.get("max_items", 15))):
            break
    return items

class ValidatingRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not canonical_url(newurl):
            raise ValueError("unsafe redirect rejected")
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def fetch_feed(url: str, *, timeout: float = 13) -> bytes:
    if not canonical_url(url):
        raise ValueError("feed source must be a safe public HTTPS URL")
    request = Request(url, headers={
        "User-Agent": "TideLens/0.1 (noncommercial public feed reader)",
        "Accept": "application/atom+xml,application/rss+xml,text/xml,application/xml",
    })
    with build_opener(ValidatingRedirect()).open(request, timeout=timeout) as resp:
        if not canonical_url(resp.geturl()):
            raise ValueError("unsafe final feed URL")
        data = resp.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("feed response too large")
        return data

def collect(sources: list[dict], fetcher=fetch_feed) -> tuple[list[dict], list[dict]]:
    """Source failures are visible, never silently replaced with empty success."""
    items = []
    reports = []
    for source in sources:
        if not source.get("enabled", True):
            continue
        label = str(source.get("id", ""))[:64]
        report = {"id": label, "status": "error", "items": 0}
        try:
            if source.get("type", "feed") != "feed":
                raise ValueError("unsupported source type")
            if not label or not canonical_url(source.get("url", "")):
                raise ValueError("invalid source")
            results = parse_feed(fetcher(source["url"]), source)
            if not results:
                raise ValueError("no usable entries in feed")
            items += results
            report.update(status="ok", items=len(results))
        except (OSError, ValueError, KeyError, ET.ParseError, TimeoutError) as exc:
            report["error_type"] = type(exc).__name__
        reports.append(report)
    return items, reports
