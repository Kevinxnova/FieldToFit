"""Daily source registry and ingestion, with bounded public document retrieval."""

import base64
import hashlib
import ipaddress
import json
import logging
import os
import re
import socket
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, quote

import feedparser
import httpx

from backend.db import get_db
from backend.knowledge.store import (now, encode, decode, canonical_url, stable_id, save_discovery as save_record,
                                      add_evidence, relate, get_record, sync_legacy, relevant)

logger = logging.getLogger(__name__)


def seed_sources():
    from backend.scrapers.rss_news import RSS_FEEDS
    seeds = [
        ("github", "GitHub Trending", "engineering", "https://github.com/trending", "legacy", {"name": "github"}),
        ("github-skills", "Agent Skills · author repositories", "engineering", "https://github.com/anthropics/skills", "github_skills", {"repos": ["anthropics/skills"], "limit": 30}),
        ("github-projects", "Agent frameworks · maintained repositories", "engineering", "https://github.com/", "github_projects",
         {"projects": [{"repo": "langchain-ai/langgraph", "type": "agent"}, {"repo": "microsoft/autogen", "type": "agent"}, {"repo": "huggingface/smolagents", "type": "agent"}]}),
        ("hackernews", "Hacker News", "community", "https://news.ycombinator.com/", "legacy", {"name": "hackernews"}),
        ("producthunt", "Product Hunt", "community", "https://www.producthunt.com/", "legacy", {"name": "producthunt"}),
        ("arxiv", "arXiv · AI research", "research", "https://export.arxiv.org/api/query", "arxiv", {"limit": 100}),
        ("hf-models", "Hugging Face · Models", "models", "https://huggingface.co/api/models", "huggingface", {"type": "models", "limit": 30}),
        ("hf-datasets", "Hugging Face · Datasets", "data", "https://huggingface.co/api/datasets", "huggingface", {"type": "datasets", "limit": 30}),
        ("hf-spaces", "Hugging Face · Spaces", "vertical", "https://huggingface.co/api/spaces", "huggingface", {"type": "spaces", "limit": 20}),
        ("openreview", "OpenReview · public papers", "research", "https://api2.openreview.net/notes", "openreview", {"venue": "ICLR.cc/2026/Conference", "limit": 30}),
        ("github-releases", "Official project releases", "engineering", "https://api.github.com/", "github_releases",
         {"repos": ["huggingface/transformers", "langchain-ai/langchain", "ollama/ollama", "QwenLM/Qwen3", "deepseek-ai/DeepSeek-V3", "MoonshotAI/Kimi-K2", "THUDM/GLM-4", "MiniMax-AI/MiniMax-M1", "microsoft/autogen", "anthropics/claude-code"], "limit": 3}),
    ]
    for name, url in RSS_FEEDS:
        seeds.append(("rss-" + stable_id(url)[:10], name, "official" if "Blog" in name else "business", url, "rss", {"limit": 30}))
    with get_db() as db:
        for sid, name, category, url, adapter, config in seeds:
            db.execute("INSERT OR IGNORE INTO knowledge_sources(id,name,category,url,adapter,config) VALUES(?,?,?,?,?,?)",
                       (sid, name, category, url, adapter, encode(config)))


def list_sources():
    with get_db() as db:
        rows = [dict(r) for r in db.execute("SELECT * FROM knowledge_sources ORDER BY category,name").fetchall()]
    for row in rows:
        row["config"] = decode(row["config"], {})
        row["enabled"] = bool(row["enabled"])
    return rows


def public_url(url):
    canonical_url(url)
    p = urlsplit(url)
    if p.port and p.port not in {80, 443}:
        raise ValueError("Source URLs must use standard HTTP(S) ports")
    addresses = socket.getaddrinfo(p.hostname, p.port or (443 if p.scheme == "https" else 80), type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError("Source must resolve to a public network address")


def fetch(url, headers=None, max_bytes=2_000_000, with_headers=False):
    """Validate redirects, limit response size and never use environment proxy credentials."""
    request_headers = {"User-Agent": "FieldToFit/2.0 (+https://github.com/Kevinxnova/fieldtofit)", **(headers or {})}
    with httpx.Client(timeout=15, follow_redirects=False, trust_env=False) as client:
        for _ in range(5):
            public_url(url)
            with client.stream("GET", url, headers=request_headers) as response:
                if response.is_redirect:
                    next_url = urljoin(url, response.headers.get("location", ""))
                    if urlsplit(next_url).hostname != urlsplit(url).hostname:
                        request_headers.pop("Authorization", None)
                    url = next_url
                    continue
                response.raise_for_status()
                chunks, size = [], 0
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > max_bytes:
                        raise ValueError("Source document exceeds the configured size limit")
                    chunks.append(chunk)
                result = (b"".join(chunks), str(response.url), response.headers.get("content-type", ""))
                return (*result, dict(response.headers)) if with_headers else result
    raise ValueError("Too many redirects")


def fetch_json(url, headers=None):
    body, _, _ = fetch(url, headers)
    return json.loads(body)


class ReadableHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self.skip += 1
        if tag in {"p", "div", "section", "h1", "h2", "h3", "li", "br", "pre"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"}:
            self.skip = max(0, self.skip - 1)

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def plain_html(text):
    parser = ReadableHTML()
    parser.feed(text)
    return "\n".join(line.strip() for line in "".join(parser.parts).splitlines() if line.strip())


def entry_date(entry, field="published"):
    value = entry.get(field + "_parsed")
    return datetime(*value[:6], tzinfo=timezone.utc).isoformat().replace("+00:00", "Z") if value else None


def documented(value, url, version="", status="documented", **extra):
    return {"value": value, "source_url": url, "status": status, "version": version, "checked_at": now(), **extra}


def ingest_feed(source, body):
    feed = feedparser.parse(body)
    if feed.bozo and not feed.entries:
        raise ValueError("The source did not return a readable feed")
    found = changed = 0
    for entry in feed.entries[:int(source["config"].get("limit", 30))]:
        if not entry.get("link") or not entry.get("title"):
            continue
        content = entry.get("content", [{}])[0].get("value") or entry.get("summary", "")
        text = plain_html(content)
        if source['category'] != 'official' and not relevant(entry.title + ' ' + text):
            continue
        record = {"kind": "event", "canonical_url": entry.link, "title": entry.title,
                  "summary": text[:2000], "source_id": source["id"], "object_type": "news",
                  "published_at": entry_date(entry), "checked_at": now(),
                  "metadata": {"publisher": source["name"], "source_updated_at": entry_date(entry, "updated")}}
        rid, change = save_record(record)
        add_evidence(rid, entry.link, entry.title, text, locator="Publisher feed entry",
                     evidence_type="official_claim" if source["category"] == "official" else "reported", coverage="excerpt")
        found += 1; changed += change
    return found, changed


def ingest_arxiv(source, payload=None):
    limit = min(int(source["config"].get("limit", 100)), 200)
    categories = " OR ".join("cat:" + c for c in ["cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.RO", "stat.ML"])
    url = source["url"] + "?search_query=" + quote(categories) + f"&sortBy=lastUpdatedDate&sortOrder=descending&max_results={limit}"
    body = payload if payload is not None else fetch(url)[0]
    feed = feedparser.parse(body)
    if not feed.entries:
        raise ValueError("arXiv returned no parsable entries")
    changed = 0
    for entry in feed.entries:
        entry_url = entry.id.replace("http://", "https://")
        version = re.search(r"v\d+$", entry_url)
        version = version.group() if version else ""
        url = re.sub(r"v\d+$", "", entry_url)
        authors = [a.get("name", "") for a in entry.get("authors", [])]
        facts = {"authors": documented(authors, entry_url, version),
                 "publication": documented(entry.get("arxiv_journal_ref") or "arXiv preprint; peer-review status not confirmed", entry_url, version)}
        if entry.get("arxiv_doi"):
            facts["doi"] = documented(entry.arxiv_doi, entry_url, version)
        rid, change = save_record({"kind": "paper", "canonical_url": url, "title": " ".join(entry.title.split()),
                                  "summary": " ".join(entry.summary.split()), "source_id": source["id"],
                                  "object_type": "paper", "version": version, "published_at": entry_date(entry),
                                  "checked_at": now(), "facts": facts,
                                  "metadata": {"authors": authors, "paper_id": url.rsplit("/", 1)[-1],
                                               "source_updated_at": entry_date(entry, "updated"), "version_url": entry_url,
                                               "categories": [x.term for x in entry.get("tags", [])],
                                               "document_url": entry_url.replace("/abs/", "/html/")}})
        add_evidence(rid, entry_url, entry.title, entry.summary, "Abstract", version, "official_claim", "abstract")
        changed += change
    return len(feed.entries), changed


def ingest_huggingface(source, payload=None):
    config = source["config"]
    typ = config["type"]
    items = payload if payload is not None else fetch_json(source["url"] + f"?sort=lastModified&direction=-1&limit={min(int(config.get('limit', 20)), 100)}&full=true")
    changed = 0
    for item in items:
        name = item.get("id") or item.get("modelId")
        if not name:
            continue
        path = name if typ == "models" else typ + "/" + name
        url = "https://huggingface.co/" + path
        card = item.get("cardData") or {}
        version = item.get("sha") or ""
        facts = {}
        for source_key, key in [("license", "license"), ("language", "language"), ("datasets", "dataset")]:
            if source_key in card:
                facts[key] = documented(card[source_key], url, version, "official_claim")
        object_type = {"models": "model", "datasets": "dataset", "spaces": "application"}[typ]
        rid, change = save_record({"kind": "resource", "canonical_url": url, "title": name,
                                  "summary": card.get("description") or item.get("pipeline_tag") or "",
                                  "source_id": source["id"], "object_type": object_type, "version": version,
                                  "checked_at": now(), "published_at": item.get("createdAt"), "facts": facts,
                                  "metadata": {"metrics": {"downloads": item.get("downloads"), "likes": item.get("likes")},
                                               "source_updated_at": item.get("lastModified"),
                                               "document_url": url + f"/raw/{quote(version or 'main')}/README.md"}})
        add_evidence(rid, url, name + " · Hub metadata", encode(item), "Hub API metadata", version, "official_claim", "excerpt")
        changed += change
    return len(items), changed


def ingest_openreview(source, payload=None):
    config = source["config"]
    url = source["url"] + "?content.venueid=" + quote(config["venue"], safe="") + f"&limit={min(int(config.get('limit',30)),100)}"
    data = payload if payload is not None else fetch_json(url)
    if not isinstance(data.get("notes"), list):
        raise ValueError("OpenReview public notes are unavailable")
    changed = 0
    for note in data["notes"]:
        content = note.get("content", {})
        def val(key, default=""):
            value = content.get(key, default)
            return value.get("value", default) if isinstance(value, dict) else value
        title = val("title")
        if not title:
            continue
        url = "https://openreview.net/forum?id=" + note["id"]
        published = note.get("pdate") or note.get("cdate")
        rid, change = save_record({"kind": "paper", "canonical_url": url, "title": title,
                                  "summary": val("abstract"), "source_id": source["id"], "object_type": "paper",
                                  "checked_at": now(), "published_at": datetime.fromtimestamp(published / 1000, timezone.utc).isoformat() if published else None,
                                  "version": str(note.get("mdate", "")),
                                  "facts": {"authors": documented(val("authors", []), url),
                                            "publication": documented(val("venue", "Public submission; review status unknown"), url)},
                                  "metadata": {"authors": val("authors", []), "venue": val("venue"), "paper_id": note["id"]}})
        add_evidence(rid, url, title, val("abstract"), "Abstract", str(note.get("mdate", "")), "official_claim", "abstract")
        changed += change
    return len(data["notes"]), changed


def ingest_github_releases(source):
    found = changed = 0
    errors = []
    headers = {"Accept": "application/vnd.github+json"}
    if os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    for repo in source["config"].get("repos", [])[:20]:
        if not re.fullmatch(r"[\w.-]+/[\w.-]+", repo):
            raise ValueError("Invalid repository identifier")
        try:
            items = fetch_json(f"https://api.github.com/repos/{repo}/releases?per_page=3", headers)
            for item in items:
                if item.get("draft"):
                    continue
                tag = item["tag_name"]
                repository_url = "https://github.com/" + repo
                with get_db() as db:
                    parent = db.execute("SELECT id FROM knowledge_records WHERE kind='resource' AND canonical_url=?", (canonical_url(repository_url),)).fetchone()
                parent_id, parent_change = (parent['id'], False) if parent else (None, False)
                if parent_id is None:
                    parent_id, parent_change = save_record({"kind": "resource", "canonical_url": repository_url, "title": repo,
                        "source_id": source["id"], "object_type": "library", "checked_at": now(), "metadata": {"repository": repo}})
                rid, change = save_record({"kind": "event", "canonical_url": item["html_url"],
                    "title": f"{repo} · {item.get('name') or tag}", "summary": (item.get("body") or "")[:2000],
                    "source_id": source["id"], "object_type": "release", "version": tag,
                    "published_at": item.get("published_at"), "checked_at": now(), "metadata": {"repository": repo, "prerelease": item.get("prerelease", False)}})
                add_evidence(rid, item["html_url"], "Release notes", item.get("body") or "", "Release body", tag, "official_claim", "full_text")
                relate(rid, parent_id, "release", item["html_url"], "Official repository release")
                found += 1; changed += change + parent_change
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            errors.append(f"{repo}: {type(exc).__name__}")
    if errors:
        raise PartialSourceError(found, changed, "; ".join(errors))
    return found, changed


class PartialSourceError(Exception):
    def __init__(self, found, changed, message):
        super().__init__(message)
        self.found, self.changed = found, changed


def collect_source(source):
    adapter = source["adapter"]
    if adapter == 'platform_repository':
        from backend.knowledge.platform_maintenance import collect
        return collect(source)
    if adapter == "github_skills":
        from backend.knowledge.skills import collect
        return collect(source)
    if adapter == "github_projects":
        from backend.knowledge.repositories import collect
        return collect(source)
    if adapter == "pages":
        found=changed=0
        for item in source['config'].get('pages',[]):
            body,url,ctype=fetch(item['url'])
            text=plain_html(body.decode('utf-8',errors='replace')) if 'html' in ctype else body.decode('utf-8',errors='replace')
            rid,did_change=save_record({'kind':item.get('kind','resource'),'title':item['title'],'canonical_url':url,
                'source_id':source['id'],'object_type':item.get('object_type','tool'),'summary':text[:2000],
                'checked_at':now(),'metadata':{'document_url':url,'publisher':source['name']}})
            add_evidence(rid,url,item['title'],text,'Official page',evidence_type='documented',coverage='full_text')
            found+=1; changed+=did_change
        return found,changed
    if adapter == "rss":
        body, _, _ = fetch(source["url"])
        return ingest_feed(source, body)
    if adapter in {"arxiv", "huggingface", "openreview"}:
        from backend.knowledge.paging import collect_pages
        return collect_pages(source)
    if adapter == "github_releases":
        return ingest_github_releases(source)
    if adapter == "legacy":
        from backend.scrapers.github import GitHubScraper
        from backend.scrapers.hackernews import HNScraper
        from backend.scrapers.producthunt import ProductHuntScraper
        name = source["config"]["name"]
        if name == "producthunt" and not os.getenv("PRODUCTHUNT_API_TOKEN"):
            raise ValueError("Product Hunt token is not configured")
        scraper = {"github": GitHubScraper, "hackernews": HNScraper, "producthunt": ProductHuntScraper}[name]()
        result = scraper.run()
        sync_legacy()
        if result["status"] != "success":
            raise PartialSourceError(result["tools_found"], result["tools_new"], "Legacy source failed; see scrape logs")
        return result["tools_found"], result["tools_new"]
    raise ValueError("Unsupported source adapter")


def run_daily(source_id=None, force=False, budget_seconds=240):
    start = time.monotonic()
    sources = sorted(list_sources(), key=lambda s: s["last_attempt_at"] or "")
    results = []
    for source in sources:
        if not source["enabled"] or (source_id and source["id"] != source_id):
            continue
        if time.monotonic() - start > budget_seconds:
            results.append({"source": source["id"], "status": "deferred", "error": "Daily run time budget reached"})
            continue
        stamp = now()
        with get_db() as db:
            # A single SQL claim prevents overlapping scheduled runs from fetching the same source.
            extra = "" if force else " AND (last_attempt_at IS NULL OR datetime(last_attempt_at)<=datetime('now','-1 day'))"
            claim = db.execute("UPDATE knowledge_sources SET status='running',last_attempt_at=? WHERE id=? "
                               "AND (status!='running' OR datetime(last_attempt_at)<datetime('now','-1 day'))" + extra, (stamp, source["id"]))
            if not claim.rowcount:
                continue
            run_id = db.execute("INSERT INTO knowledge_runs(source_id,started_at,status) VALUES(?,?,'running')", (source["id"], stamp)).lastrowid
        found = changed = 0
        status, error = "success", ""
        try:
            found, changed = collect_source(source)
        except PartialSourceError as exc:
            status, error, found, changed = "partial", str(exc), exc.found, exc.changed
        except Exception as exc:
            logger.warning("Source %s failed: %s", source["id"], type(exc).__name__)
            status, error = "error", str(exc)[:500]
        with get_db() as db:
            db.execute("UPDATE knowledge_runs SET finished_at=?,status=?,found=?,changed=?,error=? WHERE id=?", (now(), status, found, changed, error, run_id))
            db.execute("UPDATE knowledge_sources SET status=?,error=?,last_success_at=CASE WHEN ?='success' THEN ? ELSE last_success_at END WHERE id=?",
                       (status, error, status, now(), source["id"]))
        results.append({"source": source["id"], "status": status, "found": found, "changed": changed, "error": error})
    failed = any(r["status"] in {"error", "partial", "deferred"} for r in results)
    return {"status": "partial" if failed else "success", "interval_days": 1, "results": results}


def enrich_record(record_id):
    from backend.knowledge.materials import retrieve
    return retrieve(record_id)
