"""Versioned records. No network access or model calls in read paths."""

import hashlib
import html
import json
import re
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from backend.db import get_db

KINDS = {"event", "paper", "resource"}
TOPICS = {"models": "模型", "agents": "Agent", "research": "研究", "engineering": "开发",
          "business": "商业", "vertical": "垂直应用", "learning": "学习", "data": "数据"}
FACT_KEYS = {"capabilities", "limitations", "language", "deployment", "hardware", "license", "cost",
             "inputs", "outputs", "dependencies", "usage", "extension", "prerequisites", "method",
             "experiments", "publication", "authors", "doi", "dataset", "metric", "protocol",
             "platform", "hardware_vram_gb", "cost_monthly_usd", "dataset_version", "split", "model_version",
             "compatibility", "allowed_tools"}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def decode(value, fallback):
    try:
        return json.loads(value) if isinstance(value, str) else value
    except (ValueError, TypeError):
        return fallback


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def canonical_url(url):
    p = urlsplit(url.strip())
    if p.scheme not in {"http", "https"} or not p.hostname or p.username or p.password:
        raise ValueError("A public HTTP(S) source URL is required")
    host = p.netloc.lower()
    path = p.path.rstrip("/") or "/"
    # Preserve semantic query parameters (paper IDs, versions, article IDs).
    query = urlencode(sorted((k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
                             if not k.lower().startswith("utm_") and k not in {"fbclid", "gclid"}))
    return urlunsplit((p.scheme.lower(), host, path, query, ""))


def stable_id(*parts):
    return hashlib.sha256("\0".join(str(p) for p in parts).encode()).hexdigest()[:24]


def row_record(row):
    d = dict(row)
    for key, fallback in [("topics", []), ("facts", {}), ("metadata", {})]:
        d[key] = decode(d[key], fallback)
    checked = d.get("checked_at")
    try:
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(checked.replace("Z", "+00:00"))).total_seconds()
        d["freshness"] = "current" if age <= 86400 else "stale"
    except (ValueError, TypeError, AttributeError):
        d["freshness"] = "unknown"
    return d


def init_knowledge():
    schema = (Path(__file__).parent / "schema.sql").read_text()
    with get_db() as db:
        for statement in schema.split(";"):
            if statement.strip():
                db.execute(statement)
    from backend.knowledge.sources import seed_sources
    seed_sources()
    sync_legacy()


def classify_topics(text, kind="resource"):
    text = text.lower()
    patterns = {"models": r"llm|language model|diffusion|模型|transformer",
                "agents": r"agent|智能体|mcp", "research": r"paper|research|论文|arxiv|benchmark",
                "engineering": r"code|coding|developer|framework|library|代码|开发|github",
                "business": r"funding|raises|acqui|billion|融资|商业|company",
                "vertical": r"health|education|medical|office|video|教育|医疗|办公|视频",
                "learning": r"learn|tutorial|course|学习|教程|入门",
                "data": r"dataset|data set|benchmark|数据|评测"}
    tags = [k for k, pattern in patterns.items() if re.search(pattern, text)]
    return list(dict.fromkeys((["research"] if kind == "paper" else []) + tags))


def relevant(text):
    return bool(re.search(r'\b(ai|llm|gpt|claude|gemini|agent|agents|agentic|openai|anthropic|qwen|deepseek|hugging\s?face|ollama|vllm|langchain|rag|mcp|neural|transformer|machine learning|deep learning|artificial intelligence)\b|人工智能|智能体|大模型|机器学习|深度学习', text, re.I))


def plain_text(value):
    return html.unescape(re.sub(r'<[^>]+>', ' ', value or '')).strip()


def save_record(data, reason="Source update", record_id=None, connection=None):
    kind = data.get("kind", "resource")
    if kind not in KINDS:
        raise ValueError("Unknown record kind")
    url = canonical_url(data["canonical_url"])
    rid = record_id or stable_id(kind, url)
    stamp = now()
    with (nullcontext(connection) if connection is not None else get_db(atomic=True)) as db:
        identity = db.execute('SELECT id FROM knowledge_records WHERE kind=? AND canonical_url=?', (kind, url)).fetchone()
        if identity and (record_id is None or record_id.startswith('legacy-')):
            rid = identity['id']
        previous_row = db.execute("SELECT * FROM knowledge_records WHERE id=?", (rid,)).fetchone()
        previous = row_record(previous_row) if previous_row else None
        record = {"id": rid, "kind": kind, "canonical_url": url, "title": data["title"].strip(),
                  "title_zh": data.get("title_zh", ""), "summary": data.get("summary", ""),
                  "summary_zh": data.get("summary_zh", ""), "object_type": data.get("object_type", "tool"),
                  "topics": data.get("topics", classify_topics(data["title"] + " " + data.get("summary", ""), kind)),
                  "source_id": data.get("source_id", "manual"), "published_at": data.get("published_at"),
                  "collected_at": (previous or {}).get("collected_at", data.get("collected_at", stamp)),
                  "checked_at": data.get("checked_at"), "updated_at": stamp,
                  "version": str(data.get("version") or ""), "completeness": data.get("completeness", "basic"),
                  "status": data.get("status", "published"), "facts": data.get("facts", {}),
                  "metadata": data.get("metadata", {})}
        if not record["title"] or len(record["title"]) > 1000:
            raise ValueError("Title must contain 1–1000 characters")
        if record["status"] not in {"published", "withdrawn", "pending"}:
            raise ValueError("Invalid publication status")
        if record["completeness"] not in {"basic", "full"}:
            raise ValueError("Completeness must be basic or full; verification is recorded separately")
        if not isinstance(record["facts"], dict) or not isinstance(record["metadata"], dict):
            raise ValueError("Facts and metadata must be objects")
        if not isinstance(record["topics"], list) or any(t not in TOPICS for t in record["topics"]):
            raise ValueError("Invalid topic")
        for key, fact in record["facts"].items():
            if key not in FACT_KEYS or not isinstance(fact, dict) or "value" not in fact:
                raise ValueError("Facts need a supported key, value, evidence URL and status")
            if fact.get("status") not in {"official_claim", "documented", "reported", "inferred", "unknown"}:
                raise ValueError("Fact status must describe its evidence; use verification records for tests")
            if fact["status"] != "unknown":
                canonical_url(fact.get("source_url", ""))
        compare_keys = set(record) - {"updated_at", "checked_at", "collected_at", "facts"}
        def factual_values(facts):
            return {k: {field: value for field, value in fact.items() if field != 'checked_at'} for k, fact in facts.items()}
        changed = previous is None or any(record[k] != previous[k] for k in compare_keys) or factual_values(record['facts']) != factual_values(previous['facts'])
        if not changed:
            db.execute("UPDATE knowledge_records SET checked_at=? WHERE id=?", (record["checked_at"], rid))
            return rid, False
        columns = list(record)
        values = [encode(record[k]) if k in {"facts", "metadata", "topics"} else record[k] for k in columns]
        db.execute(f"INSERT INTO knowledge_records ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)}) "
                   f"ON CONFLICT(id) DO UPDATE SET {','.join(k+'=excluded.'+k for k in columns if k != 'id')}", values)
        db.execute("INSERT INTO knowledge_changes(record_id,action,snapshot,reason,changed_at) VALUES(?,?,?,?,?)",
                   (rid, "created" if previous is None else "updated", encode(record), reason, stamp))
    return rid, True


def add_evidence(record_id, url, title, body="", locator="", version="", evidence_type="source", coverage="excerpt"):
    url = canonical_url(url)
    if coverage not in {"full_text", "excerpt", "abstract", "link_only"}:
        raise ValueError("Invalid material coverage")
    if len(body) > 2_000_000:
        raise ValueError("Material exceeds 2 MB; split it into sections")
    digest = hashlib.sha256(body.encode()).hexdigest()
    eid = stable_id(record_id, url, version, locator, digest)
    with get_db(atomic=True) as db:
        inserted = db.execute("INSERT OR IGNORE INTO knowledge_evidence VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                   (eid, record_id, url, title, body, locator, version, evidence_type, coverage, now(), digest))
        if inserted.rowcount:
            row = db.execute('SELECT * FROM knowledge_records WHERE id=?', (record_id,)).fetchone()
            snapshot = row_record(row)
            snapshot['evidence_id'] = eid
            stamp = now()
            db.execute('UPDATE knowledge_records SET updated_at=? WHERE id=?', (stamp, record_id))
            db.execute('INSERT INTO knowledge_changes(record_id,action,snapshot,reason,changed_at) VALUES(?,?,?,?,?)',
                       (record_id, 'evidence_added', encode(snapshot), 'New source material or material revision indexed', stamp))
    return eid


def relate(from_id, to_id, relation, evidence_url, note=""):
    if from_id == to_id or relation not in {"release", "implementation", "dataset", "model", "benchmark", "alternative", "dependency", "integration", "related"}:
        raise ValueError("Invalid relationship")
    evidence_url = canonical_url(evidence_url)
    with get_db() as db:
        for rid in (from_id, to_id):
            if not db.execute("SELECT id FROM knowledge_records WHERE id=?", (rid,)).fetchone():
                raise ValueError("Related record not found")
        relation_id=stable_id(from_id,to_id,relation)
        old=db.execute('SELECT evidence_url,note FROM knowledge_relations WHERE id=?',(relation_id,)).fetchone()
        if old and old['evidence_url']==evidence_url and old['note']==note: return
        stamp=now()
        db.execute("INSERT INTO knowledge_relations VALUES(?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET note=excluded.note,evidence_url=excluded.evidence_url,updated_at=excluded.updated_at",
                   (relation_id, from_id, to_id, relation, evidence_url, note, stamp))
        for rid in (from_id,to_id):
            snapshot=row_record(db.execute('SELECT * FROM knowledge_records WHERE id=?',(rid,)).fetchone())
            db.execute('UPDATE knowledge_records SET updated_at=? WHERE id=?',(stamp,rid))
            db.execute('INSERT INTO knowledge_changes(record_id,action,snapshot,reason,changed_at) VALUES(?,?,?,?,?)',(rid,'relationship_updated',encode(snapshot),'Relationship evidence updated: '+relation,stamp))


def sync_legacy():
    with get_db() as db:
        rows = [dict(r) for r in db.execute("SELECT * FROM tools").fetchall()]
        imported = {r["id"]: decode(r["metadata"], {}) for r in db.execute("SELECT id,metadata FROM knowledge_records WHERE id LIKE 'legacy-%'").fetchall()}
    for row in rows:
        rid = f"legacy-{row['id']}"
        fingerprint = stable_id('migration-v3', encode(row))
        if imported.get(rid, {}).get("legacy_hash") == fingerprint:
            continue
        category = row.get("discovery_category")
        host = urlsplit(row['url']).hostname or ''
        is_repo = host.lower() == 'github.com' and len(urlsplit(row['url']).path.strip('/').split('/')) == 2
        is_hn_story = row['source'] == 'hackernews' and not is_repo
        kind = "event" if category == "news" or row.get("content_type") == "article" or row["source"] == "rss_news" or is_hn_story else "resource"
        is_in_scope = is_repo or relevant(row['title'] + ' ' + (row.get('description') or '')) or row.get('domain') == 'ai' or row.get('is_metis_pick') or row.get('is_featured')
        status = 'published' if is_in_scope else 'pending'
        if row['status'] in {'archived', 'skipped'}:
            status = 'withdrawn'
        data = {"kind": kind, "canonical_url": row["url"], "title": row["title"],
                "title_zh": plain_text(row.get("title_zh")), "summary": plain_text(row.get("description")),
                "summary_zh": plain_text(row.get("description_zh")), "object_type": 'news' if kind == 'event' else 'project' if is_repo else row.get("content_type") or "tool",
                "source_id": row["source"], "collected_at": row["first_seen"],
                "published_at": None, "checked_at": None,
                "status": status,
                "metadata": {"legacy_id": row["id"], "legacy_hash": fingerprint, "review_reason": '' if is_in_scope else 'AI relevance or resource identity needs review',
                             "metrics": decode(row.get("metrics"), {}), "imported": True,
                             "date_note": "Original publication time was not collected",
                             "generated_summary": row.get("short_summary_zh") or row.get("short_summary") or ""}}
        # Preserve editorial corrections on subsequent imports.
        if imported.get(rid, {}).get("editorial_override"):
            continue
        try:
            saved_id, _ = save_record(data, "Imported from existing Metis data; not independently verified", rid)
            add_evidence(saved_id, row.get("source_url") or row["url"], row["title"], plain_text(row.get("description")),
                         evidence_type="discovery", coverage="excerpt" if row.get("description") else "link_only")
        except ValueError:
            continue


def get_record(rid, include_body=False, include_withdrawn=False):
    with get_db() as db:
        row = db.execute("SELECT * FROM knowledge_records WHERE id=?", (rid,)).fetchone()
        if not row or (row["status"] != "published" and not include_withdrawn):
            return None
        record = row_record(row)
        evidence = [dict(r) for r in db.execute("SELECT * FROM knowledge_evidence WHERE record_id=? ORDER BY retrieved_at DESC,id", (rid,)).fetchall()]
        for e in evidence:
            e["characters"] = len(e["body"])
            if not include_body:
                del e["body"]
        record["evidence"] = evidence
        conflicts=[dict(c) for c in db.execute("SELECT * FROM knowledge_conflicts WHERE record_id=? AND status='open'",(rid,)).fetchall()]
        for conflict in conflicts:
            conflict['alternatives']=decode(conflict['alternatives'],[])
            if conflict['field'] in record['facts']:
                record['facts'][conflict['field']]['conflict']=True
        record['conflicts']=conflicts
        record["relations"] = [dict(r) for r in db.execute(
            "SELECT l.*, r.title AS related_title,r.id AS related_id,r.kind AS related_kind FROM knowledge_relations l "
            "JOIN knowledge_records r ON r.id=CASE WHEN l.from_id=? THEN l.to_id ELSE l.from_id END "
            "WHERE (l.from_id=? OR l.to_id=?) AND r.status='published'", (rid, rid, rid)).fetchall()]
        record["verifications"] = [dict(r) for r in db.execute("SELECT * FROM knowledge_verifications WHERE record_id=? ORDER BY checked_at DESC", (rid,)).fetchall()]
        record["history"] = [dict(r) for r in db.execute("SELECT seq,action,reason,changed_at FROM knowledge_changes WHERE record_id=? ORDER BY seq DESC LIMIT 100", (rid,)).fetchall()]
        siblings=db.execute("SELECT * FROM knowledge_records WHERE status='published' AND metadata LIKE ?",('%"merged_into": "'+rid+'"%',)).fetchall()
        record['grouped_sources']=[{'id':r['id'],'title':r['title'],'url':r['canonical_url'],'source_id':r['source_id']} for r in siblings]
        record["history_truncated"] = len(record["history"]) == 100
        record["verification_status"] = "passed" if any(v["result"] == "passed" and v["version"] == record["version"] for v in record["verifications"]) else "not_verified"
        return record


SEARCH_SYNONYMS = {
    "论文": ["paper", "research", "arxiv"], "模型": ["model", "llm"], "智能体": ["agent"],
    "开发": ["code", "developer", "framework"], "代码": ["code", "coding"], "开源": ["open source", "github"],
    "学习": ["learn", "tutorial", "course"], "数据": ["data", "dataset"], "评测": ["benchmark", "evaluation"],
    "本地": ["local", "self-host", "offline"], "文档": ["document", "pdf"], "中文": ["chinese", "multilingual"],
    "视频": ["video"], "语音": ["audio", "speech"], "搜索": ["search", "retrieval"], "复现": ["reproduction", "implementation"],
    "技能": ["skill", "skills"],
}


def query_terms(q):
    q = q.strip().lower()[:500]
    terms = re.findall(r"[a-z0-9][a-z0-9+.#_-]*", q)
    chinese = re.findall(r"[\u4e00-\u9fff]+", q)
    for word in chinese:
        known = [k for k in SEARCH_SYNONYMS if k in word]
        terms.extend(known or [word])
    for word, synonyms in SEARCH_SYNONYMS.items():
        if word in q:
            terms.extend(synonyms)
    return list(dict.fromkeys(t for t in terms if t not in {"a", "the", "for", "to", "with", "and", "i", "want"}))[:32]


def search_records(q="", kind="", topic="", source="", since="", until="", object_type="", limit=24, offset=0, sort="recent", ids=None, capability=""):
    limit, offset = int(limit), int(offset)
    if limit < 1 or limit > 100 or offset < 0 or offset > 100000:
        raise ValueError("limit must be 1–100 and offset 0–100000")
    if not isinstance(object_type,str) or len(object_type)>80:
        raise ValueError('Object type must be a string of at most 80 characters')
    where, params = ["status='published'", "metadata NOT LIKE '%\"merged_into\"%'"], []
    if kind == 'information':
        where.append("kind IN ('event','paper')")
        kind = ''
    if kind and kind not in KINDS:
        raise ValueError('Invalid record kind')
    for key, value in [("kind", kind), ("source_id", source), ("object_type", object_type)]:
        if value:
            where.append(f"{key}=?"); params.append(value)
    if not isinstance(capability, str) or len(capability) > 80:
        raise ValueError('Capability must be a string of at most 80 characters')
    if capability.strip():
        where.append("EXISTS (SELECT 1 FROM json_each(knowledge_records.metadata,'$.capability_tags') tag WHERE tag.type='text' AND lower(trim(tag.value))=lower(?))")
        params.append(capability.strip())
    if topic:
        if topic not in TOPICS:
            raise ValueError('Invalid topic')
        where.append("topics LIKE ?"); params.append('%"' + topic + '"%')
    for value, op in [(since, ">="), (until, "<=")]:
        if value:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            where.append(f"date(published_at) {op} date(?)"); params.append(value)
    if ids is not None:
        ids = list(dict.fromkeys(ids))[:100]
        if not ids:
            where.append("1=0")
        else:
            where.append(f"id IN ({','.join('?' for _ in ids)})"); params.extend(ids)
    terms = query_terms(q)
    # Search task content, not provenance URLs (otherwise every paper.pdf matches a PDF-tool task).
    field = "lower(title || ' ' || title_zh || ' ' || summary || ' ' || summary_zh || ' ' || topics || ' ' || COALESCE(json_extract(metadata,'$.capability_tags'),'') || ' ' || COALESCE(json_extract(facts,'$.capabilities.value'),''))"
    rank_sql, rank_params = "0", []
    if q.strip():
        terms = terms or [q.strip().lower()]
        escaped = ["%" + t.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%" for t in terms]
        predicates = [f"{field} LIKE ? ESCAPE '\\'" for _ in escaped]
        where.append("(" + " OR ".join(predicates) + ")"); params.extend(escaped)
        rank_sql = " + ".join(f"CASE WHEN {p} THEN 1 ELSE 0 END" for p in predicates)
        rank_params = escaped
    clause = " AND ".join(where)
    order = "match_score DESC," if terms else ""
    order += "COALESCE(published_at,collected_at) DESC,id DESC" if sort != "title" else "title COLLATE NOCASE,id"
    with get_db() as db:
        total = db.execute(f"SELECT COUNT(*) FROM knowledge_records WHERE {clause}", params).fetchone()[0]
        rows = db.execute(f"SELECT *,({rank_sql}) AS match_score FROM knowledge_records WHERE {clause} ORDER BY {order} LIMIT ? OFFSET ?",
                          [*rank_params, *params, limit, offset]).fetchall()
    return {"items": [row_record(r) for r in rows], "total": total, "limit": limit, "offset": offset,
            "next_offset": offset + limit if offset + limit < total else None,
            "query": q, "expanded_terms": terms, "scope": "Metis indexed published records; not an exhaustive web search",
            "date_basis": "publication date for date filters; unknown dates are excluded", "api_version": "1"}


def constraint_match(record, constraints):
    from backend.knowledge.tasks import match_conditions
    return match_conditions(record, constraints)


def catalog():
    """Observed filter values, including only visible, ungrouped resource records."""
    from collections import Counter
    with get_db() as db:
        rows = db.execute("SELECT object_type,metadata FROM knowledge_records WHERE kind='resource' AND status='published' AND metadata NOT LIKE '%\"merged_into\"%'").fetchall()
    types, capabilities = Counter(), Counter()
    for row in rows:
        types[row['object_type']] += 1
        tags = decode(row['metadata'], {}).get('capability_tags', [])
        if isinstance(tags, list):
            capabilities.update({tag.strip().lower() for tag in tags if isinstance(tag, str) and 0 < len(tag.strip()) <= 80})
    return {'types': [{'value': value, 'count': count} for value, count in sorted(types.items())],
            'capabilities': [{'value': value, 'count': count} for value, count in sorted(capabilities.items())],
            'scope': 'Observed labels in published resources; labels are discovery aids, not verified capabilities'}


def task_pack(goal, constraints=None, persona="engineer", limit=12, **kwargs):
    from backend.knowledge.tasks import pack
    return pack(goal, constraints, persona, limit, **kwargs)


def changes(after=0, limit=100, since="", record_id="", record_ids=None, topics=None, until_cursor=None):
    after, limit = int(after), int(limit)
    if after < 0 or not 1 <= limit <= 100:
        raise ValueError("Invalid change cursor or limit")
    clause, params = ["c.seq>?"], [after]
    if since:
        datetime.fromisoformat(since.replace("Z", "+00:00"))
        clause.append("c.changed_at>=?"); params.append(since)
    if record_id:
        clause.append("c.record_id=?"); params.append(record_id)
    if record_ids is not None or topics is not None:
        ids = list(dict.fromkeys(record_ids or [])); tags = list(dict.fromkeys(topics or []))
        if len(ids)>100 or len(tags)>20 or any(t not in TOPICS for t in tags):
            raise ValueError('Invalid followed scope')
        filters=[]
        if ids:
            filters.append("c.record_id IN ("+','.join('?' for _ in ids)+")"); params.extend(ids)
        for topic in tags:
            filters.append("r.topics LIKE ?"); params.append('%"'+topic+'"%')
        clause.append('('+' OR '.join(filters)+')' if filters else '0=1')
    if until_cursor is not None:
        clause.append('c.seq<=?'); params.append(int(until_cursor))
    with get_db() as db:
        latest=db.execute('SELECT COALESCE(MAX(seq),0) FROM knowledge_changes').fetchone()[0]
        rows = [dict(r) for r in db.execute("SELECT c.*,r.status AS current_status FROM knowledge_changes c LEFT JOIN knowledge_records r ON r.id=c.record_id WHERE " + " AND ".join(clause) + " ORDER BY c.seq LIMIT ?", [*params, limit + 1]).fetchall()]
    more = len(rows) > limit
    rows = rows[:limit]
    for row in rows:
        row["snapshot"] = decode(row["snapshot"], {})
        status = row.pop('current_status')
        if status != 'published' or row['snapshot'].get('status') != 'published':
            row['snapshot'] = {'id': row['record_id'], 'status': status or 'unavailable'}
            row['reason'] = 'Record is not publicly available'
    return {"items": rows, "next_cursor": rows[-1]["seq"] if rows else after, "has_more": more, "latest_cursor": latest, "api_version": "1"}


def overview():
    with get_db() as db:
        counts = {r[0]: r[1] for r in db.execute("SELECT kind,COUNT(*) FROM knowledge_records WHERE status='published' GROUP BY kind").fetchall()}
        complete = db.execute("SELECT COUNT(*) FROM knowledge_records WHERE status='published' AND completeness='full'").fetchone()[0]
        verified = db.execute("SELECT COUNT(DISTINCT v.record_id) FROM knowledge_verifications v JOIN knowledge_records r ON r.id=v.record_id WHERE v.result='passed' AND v.version=r.version AND r.status='published'").fetchone()[0]
        last = db.execute("SELECT MAX(last_success_at) FROM knowledge_sources").fetchone()[0]
        sources = db.execute("SELECT COUNT(*) FROM knowledge_sources WHERE enabled=1").fetchone()[0]
    counts = {kind: counts.get(kind, 0) for kind in KINDS}
    return {"counts": counts, "complete": complete, "verified": verified, "sources": sources,
            "last_update": last, "interval_days": 1, "topics": TOPICS, "api_version": "1"}


def save_discovery(data, reason='Source observation', record_id=None):
    """Source refreshes must not erase editorial work or resurrect withdrawn records."""
    with get_db() as db:
        row=db.execute('SELECT * FROM knowledge_records WHERE kind=? AND canonical_url=?',
                       (data.get('kind','resource'),canonical_url(data['canonical_url']))).fetchone()
    if row:
        previous=row_record(row)
        same_version=previous['version']==str(data.get('version') or '')
        merged={**previous,**data}
        merged['metadata']={**previous['metadata'],**data.get('metadata',{})}
        merged['facts']={**(previous['facts'] if same_version else {}),**data.get('facts',{})}
        merged['title_zh']=previous['title_zh']; merged['summary_zh']=previous['summary_zh']
        if previous['metadata'].get('editorial_override'):
            for key in ('title','title_zh','summary','summary_zh','facts','topics','object_type','completeness','status'):
                merged[key]=previous[key]
        elif previous['status']=='withdrawn':
            merged['status']='withdrawn'
        if not same_version:
            merged['completeness']='basic'
            for key in ('editorial','material','organized_at','document_evidence_id','summary_en'):
                merged['metadata'].pop(key,None)
            merged['summary_zh']=''
        return save_record(merged,reason,previous['id'])
    return save_record(data,reason,record_id)
