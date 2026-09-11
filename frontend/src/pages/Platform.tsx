import { ContinuousWatch, WatchAI, watchAnchor, watchNames, type WatchCollection } from '../components/workspace/ContinuousWatch';
import { ReadingContents } from '../components/workspace/ReadingContents';
import { NewsReading, newsAnchor, type NewsCollection } from '../components/workspace/NewsReading';
import { PublicationHistory } from '../components/workspace/PublicationHistory';
import { SourceContext, ObjectSourceStatus, type SourceCheck } from '../components/workspace/SourceStatus';
import { MaterialPackage, type PackageRef } from '../components/workspace/MaterialPackage';
import { EditionOverview, ChangeReader } from '../components/workspace/PlatformHistory';
import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link, Navigate, useSearchParams } from "react-router-dom";
import { BASE, readToken, request, useRemote, type Fact } from "../api/knowledge";
import { dateText, SourceLink, useWorkspace } from "../components/workspace/UI";

type Material = { id: string; title: string; source_url: string; locator: string; upstream_version: string | null; coverage: string; source_coverage: string; access_state: string; characters: number; note: string; content_hash: string };
type ObjectData = { id: string; name: string; original_name: string; types: string[]; introduction: string; official_url: string; upstream_version: string | null; checked_at: string | null; source_published_at: string | null; facts: Record<string, Fact>; attention: { kind: string; explanation: string; observed_at: string; platform?: string; value?: number; window?: string; evidence: { source_url: string; quote: string } }[]; materials: Material[]; unknown_fields: string[] };
type Publication = { source_check?: SourceCheck; unavailable?: boolean; object: ObjectData; revision: number; published_at: string; selection_state?: string; is_current?: boolean; freshness?: string };
type Catalog = { items: Publication[]; total: number; next_offset: number | null; next_cursor: string | null; previous_cursor: string | null; snapshot: string; offset: number; scope: string };
type Exported = Publication & { markdown: string };
const typeNames: Record<string, string> = { model: "Model", tool: "Tool", agent: "Agent", skill: "Skill", harness: "Harness", research: "Research", library: "Library", dataset: "Dataset", application: "Application" };
const objectLink = (pub: Publication, context?: URLSearchParams) => {
  const params = new URLSearchParams(context);
  params.set('object', pub.object.id); params.set('revision', String(pub.revision));
  return '/for-you?' + params;
};
const apiRoot = () => new URL(BASE + "/v1/platform", window.location.origin).href;
const value = (fact?: Fact) => !fact || fact.status === "unknown" ? "—" : typeof fact.value === "string" ? fact.value : JSON.stringify(fact.value);
function LoadState({ loading, error, retry }: { loading: boolean; error: string; retry: () => void }) {
  const { pick } = useWorkspace();
  return <>{loading && <p role="status">{pick("正在读取资料…", "Loading materials…")}</p>}{error && <div className="platform-notice" role="alert"><p>{pick("暂时无法读取资料：", "Could not read materials: ")}{error}</p><button className="button" onClick={retry}>{pick("重试", "Retry")}</button><Link to="/for-your-ai">{pick("检查读取配置", "Check read access")}</Link></div>}</>;
}
function Badges({ types }: { types: string[] }) { return <div className="platform-badges">{types.map(t => <span key={t}>{typeNames[t] || t}</span>)}</div>; }

function Handoff({ pub }: { pub: Publication }) {
  const { pick, notify } = useWorkspace();
  const [content, setContent] = useState(""); const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  const acquire = async (download = false) => {
    setBusy(true); setError("");
    try {
      const result = await request<Exported>(`/v1/platform/objects/${pub.object.id}/export?format=json&revision=${pub.revision}`);
      const local = ['localhost', '127.0.0.1', '[::1]'].includes(new URL(apiRoot()).hostname);
      const body = result.markdown.split('/api/v1/platform').join(apiRoot()) + "\n\n" + pick("请按清单读取需要的原文，保留来源、版本与未知项，再结合我另行提供的需求继续处理。", "Read the original materials as needed. Preserve sources, versions and unknowns, then use the needs I provide separately.") + (local ? "\n\n" + pick("读取入口是本机地址，其他设备或云端 AI 不能直接访问；请使用同机客户端或另行提供可访问的材料。", "Reading links point to this computer. Other devices and cloud AI cannot access them directly; use a local client or provide accessible materials separately.") : '');
      setContent(body);
      if (download) {
        const url = URL.createObjectURL(new Blob([body], { type: 'text/markdown;charset=utf-8' }));
        const a = document.createElement('a'); a.href = url; a.download = `fieldtofit-${pub.object.id}-${pub.revision}.md`; a.click(); URL.revokeObjectURL(url);
      } else {
        try { await navigator.clipboard.writeText(body); notify(pick("资料清单已复制", "Material manifest copied")); }
        catch { notify(pick("请从展开的文本框手动复制", "Copy from the expanded text area")); }
      }
    } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  };
  return <div className="platform-handoff"><div className="platform-actions"><button className="button primary" disabled={busy} onClick={() => acquire()}>{pick("交给我的 AI", "Give to my AI")}</button><button className="button" disabled={busy} onClick={() => acquire(true)}>{pick("下载资料清单", "Download manifest")}</button></div>{error && <p role="alert">{error}</p>}{content && <details open><summary>{pick("已复制的资料与引用", "Materials and citations")}</summary><p>{pick("此文件包含介绍、事实、引用及原文读取入口；完整正文需继续读取。", "This manifest includes facts, citations and reading links; continue reading for full text.")}</p><textarea aria-label={pick("给 AI 的资料", "Materials for AI")} readOnly value={content} rows={10} /></details>}</div>;
}

function MaterialReader({ pub, material }: { pub: Publication; material: Material }) {
  const { pick } = useWorkspace();
  const [body, setBody] = useState(""); const [next, setNext] = useState<number | null>(0); const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  const load = async () => {
    if (next === null) return;
    setBusy(true); setError("");
    try {
      const result = await request<{ body: string; next_offset: number | null }>(`/v1/platform/objects/${pub.object.id}/materials/${material.id}?revision=${pub.revision}&offset=${next}&limit=12000`);
      setBody(previous => previous + result.body); setNext(result.next_offset);
    } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  };
  return <article className="platform-material"><div className="platform-section-heading"><h3>{material.title}</h3><span>{material.coverage === "full_text" ? pick("此文档文字完整", "Stored document text") : material.coverage === "link_only" ? pick("仅链接", "Link only") : pick("部分文本", "Partial text")}</span></div><SourceLink url={material.source_url}>{pick("原始来源", "Original source")}</SourceLink><p>{material.locator} · {material.characters.toLocaleString()} {pick("字符", "characters")} · {material.upstream_version || pick("上游版本未知", "Upstream version unknown")}</p><p className="muted">{material.note}</p>
    {material.access_state === 'readable' && <button className="button" disabled={busy || next === null} onClick={load}>{busy ? pick("正在读取…", "Reading…") : next === null ? pick("已读完所存文本", "All stored text loaded") : body ? pick("继续读取", "Continue reading") : pick("读取原文", "Read original text")}</button>}
    {error && <p role="alert">{error}</p>}{body && <pre className="platform-original">{body}</pre>}
  </article>;
}

function Detail({ id, revision, onClose }: { id: string; revision: string; onClose: () => void }) {
  const { pick, zh } = useWorkspace();
  const result = useRemote<Publication>(`/v1/platform/objects/${encodeURIComponent(id)}` + (revision ? `?revision=${encodeURIComponent(revision)}` : ''));
  const title = useRef<HTMLHeadingElement>(null);
  useEffect(() => { title.current?.focus(); }, [result.data]);
  const pub = result.data; const obj = pub?.object;
  return <section className="platform-detail"><button className="text-button" onClick={onClose}>← {pick("返回资源档案", "Back to dossiers")}</button><LoadState {...result} retry={result.reload} />{pub && obj && <>
    <Badges types={obj.types} /><h1 ref={title} tabIndex={-1}>{obj.name}</h1><p className="platform-lead">{obj.introduction}</p>
    {pub.is_current === false && <p className="platform-notice">{pick("这是已审核的历史版本，当前资料已变化或不在精选范围。", "This is a reviewed historical revision; the object has changed or is no longer selected.")}</p>}
    <p className="muted">{pick("精选发布", "Published")} {dateText(pub.published_at, zh)} · {pick("资料版本", "Source version")} {obj.upstream_version || pick("未知，以内容哈希追溯", "Unknown; content hashes retained")}</p>
    <ObjectSourceStatus source={pub.source_check} /><SourceLink url={obj.official_url}>{pick("官方入口", "Official source")}</SourceLink>
    <h2>{pick("为什么收录", "Why included")}</h2>{obj.attention.map((s, i) => <div className="platform-reason" key={i}><p>{s.explanation}</p><small>{s.kind === 'metric' ? `${s.platform} · ${s.value} · ${s.window}` : s.kind === 'editorial' ? pick("编辑选择理由", "Editorial reason") : pick("来源发布记录", "Source release")} · {dateText(s.observed_at, zh)}</small><SourceLink url={s.evidence.source_url}>{pick("核对依据", "Check evidence")}</SourceLink></div>)}
    <h2>{pick("公开事实与限制", "Documented facts and limitations")}</h2><div className="platform-facts">{Object.entries(obj.facts).map(([key, fact]) => <article key={key}><h3>{({ capabilities: pick("公开能力", "Capabilities"), limitations: pick("限制与边界", "Limitations"), cost: pick("费用", "Cost"), hardware: pick("硬件条件", "Hardware") } as Record<string, string>)[key] || key}</h3><p>{value(fact)}</p><small>{fact.status === 'unknown' ? pick("未核实", "Unknown") : fact.status === 'official_claim' ? pick("作者声明", "Author claim") : fact.status}</small>{fact.source_url && <SourceLink url={fact.source_url}>{pick("来源", "Source")}</SourceLink>}{fact.quote && <details><summary>{pick("查看引文", "Show quotation")}</summary><blockquote>{fact.quote}</blockquote></details>}</article>)}</div>
    <h2>{pick("原始材料", "Original materials")}</h2><p className="muted">{pick("覆盖范围仅指下面已登记的材料，不代表整个项目的全部文档。", "Coverage refers to the materials below, not all upstream documentation.")}</p>{obj.materials.map(m => <MaterialReader key={`${pub.revision}:${m.id}`} pub={pub} material={m} />)}
    <PublicationHistory key={`history:${id}:${pub.revision}`} id={id} revision={pub.revision} /><Handoff key={pub.revision} pub={pub} /><MaterialPackage key={`package:${pub.object.id}:${pub.revision}`} references={[{id:pub.object.id, revision:pub.revision, name:pub.object.name}]} /><Link to={`/feedback?record_id=${obj.id}`}>{pick("反馈资料错误或缺失", "Report errors or missing material")}</Link>
  </>}</section>;
}

export function ForYou() {
  const {pick}=useWorkspace();const [params,setParams]=useSearchParams();
  const [query,setQuery]=useState(params.get('q')||'');const [legacy,setLegacy]=useState(false);
  const q=params.get('q')||'';const type=params.get('type')||'';
  useEffect(()=>setQuery(q),[q]);
  const news=useRemote<NewsCollection>('/v1/platform/news');
  const watch=useRemote<WatchCollection>('/v1/platform/watch?'+new URLSearchParams({q,type}));
  const filtered=!!(q||type);
  if(params.get('object'))return <LegacyCatalog/>;
  return <div className="platform-page"><header className="platform-hero"><p className="platform-eyebrow">FOR YOU · {pick('给你看','CURATED READING')}</p><h1>{pick('看见重点，\n读到来处。','Find what matters.\nRead the source.')}</h1><p className="platform-lead">{pick('先读近期动态，再持续关注重要模型与项目。保留版本、观点与出处，把更多依据交给你的 AI。','Read recent developments, then follow important models and projects. Keep versions, commentary and sources for your AI.')}</p><div className="platform-hero-meta"><span>{pick('每 1 天检查 · 审核后更新','Daily checks · Reviewed updates')}</span><Link to="/about">{pick('为什么做 FieldToFit','Why FieldToFit')} ↗</Link></div></header>
    <p className="reading-page-summary">{news.data?.total??'—'} {pick('条动态 ·','developments ·')} {watch.data?.total??'—'} {pick(filtered?'个匹配的持续关注主体':'个持续关注主体',filtered?'matching profiles':'ongoing-watch profiles')}</p>
    <div className="reading-layout"><ReadingContents newsTotal={news.data?.total??null} news={(news.data?.items||[]).map(n=>({id:newsAnchor(n.id),title:n.name}))} resources={(watch.data?.items||[]).map(i=>({id:watchAnchor(i.id),title:i.name}))} groups={(watch.data?.groups||[]).filter(g=>g.count>0).map(g=>({id:'watch-group-'+g.id,title:g.name+' · '+g.count,items:(watch.data?.items||[]).filter(i=>i.type===g.id).map(i=>({id:watchAnchor(i.id),title:i.name}))}))} resourceTotal={watch.data?.total??null} loading={watch.loading} filtered={filtered}/>
    <div className="reading-body"><NewsReading {...news}/>
    <section className="watch-section"><div className="platform-section-heading"><h2 id="resource-dossiers" tabIndex={-1}>{pick('持续关注','Ongoing watch')}</h2><span>{watch.data?.collection_total??'—'} {pick('个跟踪主体','profiles')}</span></div><p className="platform-lead">{pick('跟踪重要模型与项目，看清能力、版本和演进。','Follow important models and projects: capabilities, versions and evolution.')}</p>
    <form className="platform-search" onSubmit={e=>{e.preventDefault();setParams(p=>{p.set('q',query);p.delete('cursor');return p;});}}><input aria-label={pick('搜索持续关注','Search ongoing watch')} placeholder={pick('搜索名称、版本或关键词','Search names, versions or keywords')} value={query} onChange={e=>setQuery(e.target.value)}/><button className="button">{pick('搜索','Search')}</button><select aria-label={pick('持续关注类型','Watch type')} value={type} onChange={e=>setParams(p=>{p.set('type',e.target.value);p.delete('cursor');return p;})}><option value="">{pick('全部五类','All five groups')}</option>{Object.entries(watchNames).map(([id,name])=><option key={id} value={id}>{name}</option>)}</select></form>
    {filtered&&<button className="text-button" onClick={()=>setParams(p=>{p.delete('q');p.delete('type');return p;})}>{pick('清除全部筛选','Clear filters')}</button>}
    <ContinuousWatch result={watch}/></section>
    <details className="previous-editions"><summary>{pick('查看旧版概览归档','Previous overview editions')}</summary><EditionOverview/></details>
    <details className="previous-editions" onToggle={e=>setLegacy(e.currentTarget.open)}><summary>{pick('历史资料与原文库','Stored-source library')}</summary><p className="muted">{pick('保留此前已发布资料、原文读取与历史修订；与上方持续关注的本期内容分别维护。','Earlier publications, stored texts and historical revisions remain available separately.')}</p>{legacy&&<LegacyCatalog/>}</details>
    </div></div></div>;
}

function LegacyCatalog() {
  const { pick, zh } = useWorkspace(); const [params, setParams] = useSearchParams();
  const [query, setQuery] = useState(params.get('q') || '');
  const [chosen, setChosen] = useState<PackageRef[]>([]);
  const toggle = (pub: Publication) => setChosen(previous => previous.some(r => r.id === pub.object.id)
    ? previous.filter(r => r.id !== pub.object.id)
    : previous.length < 10 ? [...previous, {id:pub.object.id, revision:pub.revision, name:pub.object.name}] : previous);
  const queryKey = params.get('q') || '';
  useEffect(() => { setQuery(queryKey); }, [queryKey]);
  const filters = new URLSearchParams({ q: queryKey, object_type: params.get('type') || '' });
  for (const key of ['source','since','until']) if (params.get(key)) filters.set(key,params.get(key)!);
  if (params.get('cursor')) filters.set('cursor', params.get('cursor')!);
  const result = useRemote<Catalog>('/v1/platform/objects?' + filters);
  const filtered = ['q','type','source','since','until'].some(k => !!params.get(k));
  const submit = (e: FormEvent) => { e.preventDefault(); setParams(p => { p.set('q', query); p.delete('offset'); p.delete('cursor'); p.delete('object'); p.delete('revision'); return p; }); };
  const close = () => { setParams(p => { p.delete('object'); p.delete('revision'); return p; }); };
  if (params.get('object')) return <Detail key={params.get('object') + ':' + params.get('revision')} id={params.get('object')!} revision={params.get('revision') || ''} onClose={close} />;
  return <div className="legacy-library">
    <section className="dossier-section"><div className="platform-section-heading"><h2 id="legacy-library" tabIndex={-1}>{pick("历史资料与原文库", "Stored-source library")}</h2><span>{result.data?.total ?? '—'} {pick("项已审核对象", "reviewed objects")}</span></div>
    <p className="muted">{pick('值得持续关注的模型、工具、Agent、Skill 与 Harness。档案保留版本、原文和使用条件。', 'Models, tools, agents, skills and harnesses to follow. Dossiers retain versions, sources and conditions.')}</p>
    {filtered && <button className="text-button" onClick={() => setParams(p => { ['q','type','source','since','until','cursor','offset'].forEach(k=>p.delete(k)); return p; })}>{pick('清除全部资源筛选', 'Clear dossier filters')}</button>}
    <SourceContext /><form className="platform-search" onSubmit={submit}><input aria-label={pick("搜索原文库对象", "Search selected objects")} placeholder={pick("搜索名称或关键词", "Search names or keywords")} value={query} onChange={e => setQuery(e.target.value)} /><button className="button" type="submit">{pick("搜索", "Search")}</button><details><summary>{pick("按类型筛选", "Filter by type")}</summary><select aria-label={pick("原文库对象类型", "Selected object type")} value={params.get('type') || ''} onChange={e => setParams(p => { p.set('type', e.target.value); p.delete('offset'); p.delete('cursor'); return p; })}><option value="">{pick("全部类型", "All types")}</option>{Object.entries(typeNames).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></details></form>
    <details className="platform-panel platform-selection"><summary>{pick("选择资料，打包交给 AI", "Choose materials for your AI")}</summary><section aria-label={pick('选择资料包内容', 'Select package contents')}><div className="platform-section-heading"><h3>{pick('选择要交给 AI 的资料', 'Choose materials for your AI')}</h3><span>{chosen.length} / 10</span></div><p>{pick('在下方勾选对象，可跨搜索和分页选择。本次选择保留各自的发布修订，刷新页面后清空。', 'Select objects below, including across searches and pages. Each selection keeps its publication revision; reloading clears the selection.')}</p>{chosen.length > 0 && <><ul>{chosen.map(ref => <li key={ref.id}><span>{ref.name} · r{ref.revision}</span><button className="text-button" aria-label={pick('移除 ', 'Remove ') + ref.name} onClick={() => setChosen(previous => previous.filter(r => r.id !== ref.id))}>{pick('移除', 'Remove')}</button></li>)}</ul><button className="text-button" onClick={() => setChosen([])}>{pick('清空选择', 'Clear selection')}</button><MaterialPackage key={chosen.map(r => `${r.id}:${r.revision}`).join(',')} references={chosen} /></>}{chosen.length === 10 && <p role="status">{pick('已选满 10 项；移除后可加入其他对象。', '10 objects selected; remove one to add another.')}</p>}</section></details>
    <LoadState {...result} retry={result.reload} />{result.error && <button className="button" onClick={() => {setParams(p => {p.delete("cursor");return p;});result.reload();}}>{pick("重新读取最新资料", "Restart with current materials")}</button>}{result.data && !result.data.items.length && <p className="platform-notice">{pick("当前范围没有匹配的精选资料，可以更换关键词。", "No selections match this scope. Try another keyword.")}</p>}
    <div className="platform-feed">{result.data?.items.map(pub => pub.unavailable ? <article className="platform-card" key={pub.object.id}><p>{pick("此位置的资料已撤回或不可用。", "This publication is no longer available.")}</p></article> : <article className="platform-card" id={"resource-" + pub.object.id} tabIndex={-1} key={pub.object.id}><div className="platform-section-heading"><Badges types={pub.object.types} /><span>{dateText(pub.published_at, zh)}</span></div><h2><Link to={objectLink(pub,params)}>{pub.object.name}</Link></h2>{pub.is_current === false && <p className="platform-notice">{pick("这是本次浏览保留的历史修订，当前资料已有变化。", "This browsing snapshot retains an earlier publication; current materials have changed.")}</p>}<p className="platform-lead">{pub.object.introduction}</p><details data-auto-expand><summary>{pick("展开档案摘要与材料操作", "Dossier summary and materials")}</summary><div className="platform-reason"><small>{pub.object.attention[0]?.kind === 'editorial' ? pick("编辑选择理由", "Editorial reason") : pick("关注依据", "Attention evidence")}</small><p>{pub.object.attention[0]?.explanation}</p></div><dl><div><dt>{pick("公开能力", "Capabilities")}</dt><dd>{value(pub.object.facts.capabilities)}</dd></div><div><dt>{pick("限制与未知", "Limitations")}</dt><dd>{value(pub.object.facts.limitations)}</dd></div></dl><ObjectSourceStatus source={pub.source_check} /><div className="platform-actions"><Link className="button" to={objectLink(pub,params)}>{pick("查看资料", "Read dossier")}</Link><SourceLink url={pub.object.official_url}>{pick("官方来源", "Official source")}</SourceLink></div><label className="platform-package-choice"><input type="checkbox" checked={chosen.some(r => r.id === pub.object.id)} disabled={chosen.length >= 10 && !chosen.some(r => r.id === pub.object.id)} onChange={() => toggle(pub)} />{pick('加入资料包', 'Add to source package')} · {pub.object.name}</label><Handoff pub={pub} /></details></article>)}</div>
    {result.data && <div className="platform-actions"><button className="button" disabled={result.data.offset === 0} onClick={() => setParams(p => { p.set('cursor', result.data!.previous_cursor!); return p; })}>{pick("上一页", "Previous")}</button><button className="button" disabled={result.data.next_offset === null} onClick={() => setParams(p => { p.set('cursor', result.data!.next_cursor!); return p; })}>{pick("下一页", "Next")}</button></div>}
    </section></div>;
}

export function ForAI() {
  const { pick, notify } = useWorkspace();
  const [params, setParams] = useSearchParams();
  const aiFilters = new URLSearchParams({limit:'100'});
  for (const key of ['source','since','until']) if (params.get(key)) aiFilters.set(key,params.get(key)!);
  const result = useRemote<Catalog>('/v1/platform/objects?' + aiFilters);
  const [accessRevision, setAccessRevision] = useState(0);
  const [connection, setConnection] = useState(''); const [busy, setBusy] = useState(false); const [token, setToken] = useState('');
  const selected = params.get('object') || '';
  const object = useRemote<Publication>(selected ? `/v1/platform/objects/${encodeURIComponent(selected)}` : null);
  const endpoint = new URL(BASE + '/mcp/curated', location.origin).href;
  const local = ['localhost', '127.0.0.1', '[::1]'].includes(new URL(endpoint).hostname);
  const config = JSON.stringify({ mcpServers: { fieldtofit: { url: endpoint } } }, null, 2);
  const connect = async () => {
    setBusy(true); setConnection('');
    try {
      const headers: Record<string,string> = { 'Content-Type':'application/json', Accept:'application/json, text/event-stream' };
      if (readToken()) headers.Authorization = 'Bearer ' + readToken();
      const response = await fetch(endpoint, { method:'POST', headers, signal:AbortSignal.timeout(15000), body:JSON.stringify({ jsonrpc:'2.0', id:1, method:'initialize', params:{ protocolVersion:'2025-11-25', capabilities:{}, clientInfo:{ name:'fieldtofit-platform-web', version:'1' } } }) });
      const data = await response.json();
      if (!response.ok || data.error) throw Error(data.detail || data.error?.message || data.error || `HTTP ${response.status}`);
      setConnection(pick('连接成功 · 只读 MCP；资料是否可用请查看下方清单。', 'Connected to read-only MCP. Check material availability below.'));
    } catch (e) { setConnection((e as Error).message); } finally { setBusy(false); }
  };
  return <div className="platform-page"><header className="platform-hero"><p className="platform-eyebrow">FOR YOUR AI · {pick("给 AI 用", "SOURCE MATERIALS")}</p><h1>{pick("让你的 AI，\n读到更多依据。", "More source material.\nFor your own AI.")}</h1><p className="platform-lead">{pick("同一套精选资料，更完整的读取方式。FieldToFit 提供原文与出处，你的 AI 结合你的需求继续工作。", "The same reviewed collection, with deeper reading access. FieldToFit supplies sources; your AI continues with your needs.")}</p></header>
    <section className="platform-panel"><p className="platform-eyebrow">01 / {pick("连接我的 AI", "CONNECT")}</p><h2>{pick("只读接入，随时取材", "Read-only access to source materials")}</h2><p>{pick("无需注册。基础读取不需要生成模型密钥。", "No registration. Basic reading needs no generation-model key.")}</p><pre className="platform-original">{config}</pre><div className="platform-actions"><button className="button primary" disabled={busy} onClick={connect}>{pick("测试 MCP 连接", "Test MCP connection")}</button><button className="button" onClick={() => navigator.clipboard.writeText(config).then(() => notify(pick('配置已复制','Configuration copied'))).catch(() => notify(pick('请手动复制上方配置','Copy the configuration manually')))}>{pick("复制配置", "Copy configuration")}</button></div>{connection && <p role="status">{connection}</p>}
      {local && <p className="platform-notice">{pick("这是本机地址。其他设备或云端 AI 无法直接访问；可使用同机客户端，或下载下方含原文资料包交给 AI；未包含部分仍需可访问的服务地址。", "This is a local address. Use a client on this computer, or download a source text package below. Omitted text still needs a reachable service.")}</p>}
      <details><summary>{pick("私有部署与 stdio", "Private access and stdio")}</summary><p>{pick("读取令牌仅保存在本次浏览器会话中，不进入复制配置。客户端需自行设置 Authorization: Bearer；管理员密码不能代替读取令牌。", "Read tokens stay in this browser session and are excluded from copied configuration. Configure Authorization: Bearer in your client; never use the admin password.")}</p><form className="platform-search" onSubmit={e => { e.preventDefault(); if (token) sessionStorage.setItem('fieldtofit-read-token',token); else sessionStorage.removeItem('fieldtofit-read-token'); setToken(''); setAccessRevision(r => r + 1); result.reload(); object.reload(); notify(pick('本次会话的读取设置已更新','Read access updated for this session')); }}><input type="password" autoComplete="off" value={token} onChange={e => setToken(e.target.value)} aria-label={pick("读取令牌", "Read token")} placeholder={pick("留空可清除", "Empty to clear")} /><button className="button">{pick("保存读取设置", "Save read access")}</button></form><p>{pick("stdio 客户端在项目根目录运行以下命令；后端必须已启动。", "For stdio, run this from the project root with the backend already running.")}</p><pre className="platform-original">{'.venv/bin/python -m backend.mcp_stdio'}</pre><p>FIELDTOFIT_MCP_URL = {endpoint}</p></details>
    </section>
    <WatchAI key={accessRevision}/><section className="platform-panel"><p className="platform-eyebrow">02 / {pick("可读取的资料", "AVAILABLE MATERIALS")}</p><h2>{pick("历史资料与原文库", "Inspect coverage, then read")}</h2><p>{pick("原文库保留此前发布的对象与材料。上方持续关注通过 curated_watch 读取；近期动态通过 curated_news 读取。", "The stored-source library retains earlier publications. Read ongoing-watch profiles with curated_watch and developments with curated_news.")}</p><SourceContext /><LoadState {...result} retry={result.reload} />{result.data && !result.data.items.length && <p>{pick("暂无通过审核的精选资料；连接成功不等于资料已经齐全。", "No reviewed selections yet. A successful connection does not mean materials are available.")}</p>}<label>{pick("查看一个对象的材料", "Inspect an object's materials")}<select value={selected} onChange={e => setParams(p=>{if(e.target.value)p.set('object',e.target.value);else p.delete('object');return p;})}><option value="">{pick("请选择对象", "Choose an object")}</option>{result.data?.items.filter(p => !p.unavailable).map(p => <option key={p.object.id} value={p.object.id}>{p.object.name}</option>)}</select></label>{result.data?.next_offset !== null && result.data?.next_offset !== undefined && <p>{pick("这里只列前 100 项；完整列表可通过索引分页读取。", "Only the first 100 entries are listed here; paginate the API for the complete scope.")}</p>}<LoadState {...object} retry={object.reload} />{object.data && <><ObjectSourceStatus source={object.data.source_check} /><div className="platform-actions"><Link to={objectLink(object.data)}>{pick("打开人读档案", "Open human-readable dossier")}</Link><Handoff pub={object.data} /></div><PublicationHistory key={`history:${selected}:${object.data.revision}:${accessRevision}`} id={object.data.object.id} revision={object.data.revision} /><MaterialPackage key={`${selected}:${object.data.revision}:${accessRevision}`} references={[{id:object.data.object.id, revision:object.data.revision, name:object.data.object.name}]} /><details><summary>{pick("查看机器可读档案", "Preview machine-readable record")}</summary><pre className="platform-original">{JSON.stringify(object.data,null,2)}</pre></details>{object.data.object.materials.map(m => <MaterialReader key={`${object.data!.revision}:${m.id}`} pub={object.data!} material={m} />)}</>}
    </section>
    <section className="platform-panel"><p className="platform-eyebrow">03 / {pick("读取与更新", "READING & UPDATES")}</p><h2>{pick("从索引，读到原文", "From index to original text")}</h2><ol className="platform-reading-steps"><li><code>curated_news</code><p>{pick("读取公司与产品动态、分点解读和出处；原始文章仅链接，解读不冒充原文。", "Read company/product developments, attributed editorial points and sources; upstream articles are link-only.")}</p></li><li><code>curated_search</code><p>{pick("发现已审核对象；支持名称、关键词和类型。", "Find reviewed objects by name, keyword or type.")}</p></li><li><code>curated_object</code><p>{pick("读取同一发布版本的事实、限制和材料清单。", "Read facts, limitations and the material manifest for one publication revision.")}</p></li><li><code>curated_material</code><p>{pick("按 next_offset 继续读取，直到 has_more 为 false。", "Continue with next_offset until has_more is false.")}</p></li><li><code>curated_export</code><p>{pick("导出带版本与引用的中性清单；不生成任务方案。", "Export a neutral manifest with versions and citations; no task plan is generated.")}</p></li><li><code>curated_bundle</code><p>{pick("把选定的一个或多个对象及所存原文打包，保留版本、缺口与续读位置。", "Package selected objects with stored source text, revisions, gaps and continuation positions.")}</p></li></ol><p>{pick("资料每 1 天检查。索引用 next_cursor 固定同一批资料；变化用 curated_changes 继续读取，概览用 curated_editions / curated_edition 回看。游标保留 7 天，撤回内容即时停止展示。", "Sources are checked daily. Follow next_cursor for a fixed index window, curated_changes for updates, and curated_editions / curated_edition for overviews. Cursors last 7 days; withdrawn content is hidden immediately.")}</p><p><code>{apiRoot()}/objects</code></p></section>
    <ChangeReader key={selected + accessRevision} objectId={selected} />
  </div>;
}

export function AboutFieldToFit() {
  const { pick } = useWorkspace(); const health = useRemote<{version:string}>('/health');
  return <div className="platform-page platform-about">
    <header className="platform-hero brand-story">
      <img className="about-brand brand-light" src="/brand/logo-horizontal-ink.svg" alt="FieldToFit" />
      <img className="about-brand brand-dark" src="/brand/logo-horizontal-paper.svg" alt="FieldToFit" />
      <p className="platform-eyebrow">ABOUT FIELDTOFIT · v1.0.0</p>
      <h1 className="field-to-fit">FIELD <span aria-label="to">→</span> FIT</h1>
      <p className="platform-lead">{pick("FieldToFit 是人与 AI 共享的动态 AI 地图：看清已有方案，判断是否适配，选择正确的采用与构建路线。", "FieldToFit is a living AI map shared by people and AI: understand existing solutions, judge their fit, and choose the right path to adopt or build.")}</p>
      <div className="brand-logic">
        <article><span className="brand-step">01</span><h2>Field</h2><p>{pick("动态、论文、模型、工具、开源项目和开发资料组成的 AI 全景。", "The AI landscape: developments, papers, models, tools, open-source projects and development materials.")}</p></article>
        <article><span className="brand-step">02</span><h2>To</h2><p>{pick("持续跟踪、整理、比较、验证和筛选。", "Ongoing tracking, organization, comparison, verification and selection.")}</p></article>
        <article><span className="brand-step">03</span><h2>Fit</h2><p>{pick("结合用户的任务、条件与限制，判断什么真正适用。", "Understand what truly fits the user's task, conditions and constraints.")}</p></article>
      </div>
    </header>
    <section className="platform-panel"><p className="platform-eyebrow">FOR YOU · FOR YOUR AI</p><h2>{pick("给你看，也给你的 AI 用。", "For you. For your AI.")}</h2><p>{pick("AI 生态每天都在变化，公告、论文、模型、工具和开源项目分散在不同地方。FieldToFit 选择值得关注的对象与变化，整理成易读的介绍，同时保留可供个人 AI 深读的材料、出处和版本。", "AI announcements, papers, models and tools are scattered across many sources. FieldToFit organizes selected developments for people and preserves deeper materials, sources and versions for personal AI agents.")}</p><div className="platform-actions"><Link className="button primary" to="/for-you">{pick("浏览 For you", "Explore For you")}</Link><Link className="button" to="/for-your-ai">{pick("连接我的 AI", "Connect my AI")}</Link></div></section>
    <section className="platform-panel"><h2>{pick("两种阅读方式，同一套依据", "Two reading modes, the same evidence")}</h2><p>{pick("你需要先读懂重点，再决定深入哪里。你的 AI 则需要更多细节：原始文档、代码入口、材料版本和明确的限制。FieldToFit 为两种阅读方式维护同一套资料。", "You need the essentials first. Your AI needs documents, code references, versions and explicit limitations. FieldToFit maintains one shared collection for both.")}</p><div className="platform-facts"><article><h3>For you</h3><p>{pick("从近期动态的速览与解读了解变化，再查阅按模型、工具、Agent、Skill、Harness 分组的持续关注资料。", "Read the overview, understand selected objects and inspect their attention signals and documented limits.")}</p></article><article><h3>For your AI</h3><p>{pick("通过 MCP/API 连接，或复制、下载资料，让自己的 AI 继续读取需要的原文。", "Connect through MCP/API or copy/download a manifest so your own AI can continue reading.")}</p></article></div></section>
    <section className="platform-panel"><h2>{pick("为谁做，做什么", "Who this is for")}</h2><p>{pick("面向研究者、工程师、研究生、学生，以及他们使用的个人 AI 和 Agent。平台负责发现、整理和维护资料；任务中的比较、选择、方案设计由你和你的 AI 继续完成。", "For researchers, engineers, graduate students, students and their personal AI agents. FieldToFit discovers and maintains materials; you and your AI make task-specific comparisons, choices and plans.")}</p></section>
    <section className="platform-panel"><h2>{pick("少量精选，持续维护", "A focused collection, maintained over time")}</h2><p>{pick("优先整理官方公告、作者文档、仓库和论文等一手材料，用公开讨论辅助发现。关注度不等于能力或研究质量，作者声明与实际观察分别标注。", "We prioritize official announcements, author documentation, repositories and papers. Attention is not a measure of capability or research quality; claims and observations remain distinct.")}</p><p>{pick("按 1 天周期检查。每天检查不代表每天有新内容，也不代表覆盖整个 AI 生态。材料缺失、过期、分歧和失败会明确显示。", "Checks run every 1 day. This does not mean new content every day or comprehensive coverage. Missing, stale or conflicting material stays visible.")}</p><Link to="/sources">{pick("查看实际来源状态", "See actual source status")}</Link></section>
    <section className="platform-panel"><h2>{pick("当前进度与参与", "Status and participation")}</h2><p>{pick("当前运行版本为 v1.0.0，提供 For you、For your AI 和可追溯的精选资料。公开账户和跨设备同步待开放；AI 应用案例暂缓。", "Version v1.0.0 provides For you, For your AI and source-backed curated materials. Public accounts and sync remain closed; application cases are pending.")}</p><p>{pick("运行版本：", "Running version: ")}{health.data?.version ? `v${health.data.version.replace(/^v/, "")}` : pick("暂未取得", "Unavailable")}</p><div className="platform-actions"><SourceLink url="https://github.com/Kevinxnova/FieldToFit">GitHub</SourceLink><SourceLink url="https://github.com/Kevinxnova/FieldToFit/blob/codex/fieldtofit-knowledge-workspace/CHANGELOG.md">{pick("版本更新记录", "Changelog")}</SourceLink><SourceLink url="https://github.com/Kevinxnova/FieldToFit/blob/codex/fieldtofit-knowledge-workspace/docs/guides/local-development.md">{pick("自行部署", "Self-host")}</SourceLink><Link to="/feedback">{pick("反馈错误或缺失", "Report errors or gaps")}</Link></div><p className="muted">{pick("项目源码采用 MIT 许可。第三方资料保留其来源和适用许可。", "Source code is MIT licensed. Third-party materials retain their own attribution and terms.")}</p></section>
  </div>;
}

export function LegacyPlatformEntry() {
  const [params] = useSearchParams(); const next = new URLSearchParams({legacy:'1'});
  if (params.get('q')) next.set('q', params.get('q')!);
  const type = params.get('kind') === 'paper' ? 'research' : params.get('object_type');
  if (type && type in typeNames) next.set('type', type);
  return <Navigate replace to={'/for-you?' + next} />;
}
