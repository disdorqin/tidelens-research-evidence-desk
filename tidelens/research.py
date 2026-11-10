"""STEM2Connect Scientific Research: bounded, traceable arXiv evidence cards.

Only metadata and short quotations from author-submitted public abstracts are
committed for the reviewer demo. Full abstracts remain under an ignored state
directory, allowing rechecks without copying papers or personal information.
A matched quote proves the text occurs in the source abstract -- not that the
paper's claims are correct or peer reviewed.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET
import json
import re

from .core import clean
from .feeds import fetch_feed, xml_root
from .llm import summarize

ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"
FEED_URL = ("https://export.arxiv.org/api/query?"
            "search_query=cat:cs.AI&start=0&max_results=12&"
            "sortBy=submittedDate&sortOrder=descending")
ID = re.compile(r"^(?:\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?$")
RESEARCH_SCHEMA = "tidelens-scientific-research/v1"
TOPIC_WORDS = {
    "agents": ("agent", "multi-agent", "reinforcement learning", "memory", "tool use"),
    "forecast": ("forecast", "time series", "prediction", "energy", "power grid"),
    "evaluation": ("evaluation", "benchmark", "reliability", "verification", "trustworthy"),
}

def _tagtext(element: ET.Element, name: str) -> str:
    return " ".join((element.findtext(ATOM + name) or "").split())

def _paper_id(url: str) -> str:
    parts = urlsplit(url)
    if parts.hostname not in ("arxiv.org", "www.arxiv.org") or not parts.path.startswith("/abs/"):
        return ""
    candidate = parts.path[5:].strip("/")
    return candidate if ID.fullmatch(candidate) else ""

def _short_quote(abstract: str, word_cap: int = 20) -> str:
    """Preserve a contiguous exact span with a small word budget."""
    source = abstract.strip()
    words = list(re.finditer(r"\S+", source))
    if not words:
        return ""
    n = min(len(words), word_cap)
    end = words[n-1].end()
    return source[:end].strip()

def _topics(title: str, abstract: str) -> list[str]:
    corpus = (title + " " + abstract).casefold()
    return [tag for tag, words in TOPIC_WORDS.items()
            if any(w in corpus for w in words)] or ["general"]

def parse_arxiv_atom(raw: bytes, limit: int = 12) -> list[dict]:
    root = xml_root(raw)
    if root.tag != ATOM + "feed":
        raise ValueError("expected_arxiv_atom_feed")
    seen: set[str] = set()
    out: list[dict] = []
    for entry in root.findall(ATOM + "entry"):
        url = _tagtext(entry, "id")
        pid = _paper_id(url)
        title = clean(_tagtext(entry, "title"), 190)
        abstract = clean(_tagtext(entry, "summary"), 3500)
        updated = _tagtext(entry, "updated")
        published = _tagtext(entry, "published")
        if not pid or not title or len(abstract) < 80 or pid in seen:
            continue
        if not published.startswith("20"):
            continue
        seen.add(pid)
        authors = [clean(_tagtext(n, "name"), 80)
                   for n in entry.findall(ATOM + "author")]
        quote = _short_quote(abstract)
        if len(quote) < 15 or quote not in abstract:
            continue
        out.append({
            "id": pid,
            "title": title,
            "url": "https://arxiv.org/abs/" + pid,
            "authors": authors[:3],
            "author_count_shown": min(len(authors), 3),
            "published_utc": published,
            "updated_utc": updated,
            "abstract": abstract,
            "abstract_sha256": sha256(abstract.encode("utf-8")).hexdigest(),
            "evidence_quote": quote,
            "quote_exact_match": True,
            "topics": _topics(title, abstract),
            "evidence_level": "author_submitted_arxiv_abstract",
            "peer_review_confirmed": False,
        })
        if len(out) >= max(1, min(limit, 30)):
            break
    return out

def snapshot(raw: bytes, *, limit: int = 12, models=None, transport=None,
             published_at: str | None = None) -> tuple[dict, dict]:
    papers = parse_arxiv_atom(raw, limit=limit)
    if not papers:
        raise ValueError("no_usable_research_entries")
    raw_internal = {
        "schema": RESEARCH_SCHEMA, "source_feed": FEED_URL,
        "papers": papers, "private_full_abstracts": True,
    }
    public = []
    model_calls = 0
    for paper in papers:
        card = {k:paper[k] for k in
                ("id", "title", "url", "authors", "author_count_shown",
                 "published_utc", "updated_utc", "abstract_sha256",
                 "evidence_quote", "quote_exact_match", "topics",
                 "evidence_level", "peer_review_confirmed")}
        card["verification"] = {
            "quote_in_original_abstract": True,
            "abstract_source": "arXiv author-submitted Atom metadata",
            "full_paper_read": False,
            "independent_reproduction": False,
        }
        card["ai"] = {"status":"not_run", "summary":None,"quote":None}
        if models and model_calls < 2:
            model_calls += 1
            answer = summarize(paper["abstract"], models, transport=transport)
            if answer.get("method") == "model_quote_checked" and (
                    answer.get("quote") in paper["abstract"]):
                card["ai"] = {
                    "status":"quote_checked",
                    "summary":clean(answer["summary"], 210),
                    "quote":answer["quote"],
                    "source_quote_verified":True,
                    "provider":clean(answer["provider"], 55),
                }
            else:
                card["ai"]["status"]="unavailable_or_unverified"
        public.append(card)
    return ({
        "schema": RESEARCH_SCHEMA, "snapshot_utc":
            published_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source":"arxiv_public_api", "source_url":FEED_URL,
        "is_live_source_snapshot":True,
        "is_user_or_peer_reviewed":False,
        "disclaimer":("Original author-submitted public abstracts; quoted words checked "
                      "against the retrieved abstract. No full paper, peer review, "
                      "scientific truth or user registration is certified."),
        "papers":public,
    }, raw_internal)

def build(*, output: Path, state: Path, limit: int = 12,
          models=None, transport=None, fetcher=fetch_feed) -> dict:
    """Only writes the public card set to an explicitly named JSON file."""
    output=Path(output)
    state=Path(state)
    if output.name!="research-data.json":
        raise ValueError("public_filename_not_allowlisted")
    if ".state" not in state.parts:
        raise ValueError("internal_state_must_be_ignored")
    raw = fetcher(FEED_URL)
    public, private = snapshot(raw, limit=limit, models=models, transport=transport)
    state.mkdir(parents=True,exist_ok=True)
    # Full abstracts stay in ignored state; do not commit or send them to users.
    state_target=state/"arxiv-full-abstracts.json"
    temp=state_target.with_suffix(".tmp")
    temp.write_text(json.dumps(private,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    temp.replace(state_target)
    output.parent.mkdir(parents=True,exist_ok=True)
    temp_public=output.with_suffix(".json.tmp")
    temp_public.write_text(json.dumps(public,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    temp_public.replace(output)
    return {
        "status":"real_public_arxiv_snapshot",
        "papers":len(public["papers"]),
        "short_quotes_exact_match":sum(x["quote_exact_match"] for x in public["papers"]),
        "model_quote_checked":sum(x["ai"]["status"]=="quote_checked" for x in public["papers"]),
        "full_papers_read":0,
        "output":str(output),
    }
