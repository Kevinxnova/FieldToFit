import { DeveloperProjects } from "./Community";
import { ContinuousWatch, WatchAI, watchAnchor, watchNames, type WatchCollection } from '../components/workspace/ContinuousWatch';
import { ReadingContents } from '../components/workspace/ReadingContents';
import { NewsReading, newsAnchor, type NewsCollection } from '../components/workspace/NewsReading';
import { PublicationHistory } from '../components/workspace/PublicationHistory';
import { SourceContext, ObjectSourceStatus, type SourceCheck } from '../components/workspace/SourceStatus';
import { MaterialPackage, type PackageRef } from '../components/workspace/MaterialPackage';
import { ModelLandscape } from '../components/workspace/ModelLandscape';
import { version as appVersion } from '../../package.json';
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
  const [query,setQuery]=useState(params.get('q')||'');
  const q=params.get('q')||'';const type=params.get('type')||'';
  useEffect(()=>setQuery(q),[q]);
  const news=useRemote<NewsCollection>('/v1/platform/news');
  const watch=useRemote<WatchCollection>('/v1/platform/watch?'+new URLSearchParams({q,type}));
  const filtered=!!(q||type);
  if(params.get('object'))return <LegacyCatalog/>;
  return <div className="platform-page"><header className="platform-hero"><p className="platform-eyebrow">FOR YOU · {pick('给你看','CURATED READING')}</p><h1>{pick('了解 AI 新变化，\n持续关注重要模型与项目。','Follow AI developments.\nUnderstand the models and projects.')}</h1><p className="platform-lead">{pick('这里提供模型能力与价格图、公司与产品近期动态，以及模型、工具、Agent、Skill、Harness 五类持续关注资料。先用图表了解模型位置，再读动态中的变化与解读；想深入某个项目，就看版本表与原始出处，或把资料交给你的 AI。','Explore model capability and pricing, recent company and product developments, and five groups of ongoing-watch profiles. Start with the charts, read the developments, then explore versions and sources or hand the materials to your AI.')}</p><div className="platform-actions"><a className="button primary" href="#model-landscape">{pick("浏览模型图表","Explore model charts")}</a><a className="button" href="#recent-news">{pick("阅读近期动态","Read developments")}</a><Link className="button" to="/for-your-ai">{pick("交给我的 AI","Give to my AI")}</Link></div><div className="platform-hero-meta"><span>{pick('每 1 天检查 · 审核后更新','Daily checks · Reviewed updates')}</span><Link to="/about">{pick('为什么做 FieldToFit','Why FieldToFit')} ↗</Link></div></header>
    <p className="reading-page-summary">{news.data?.total??'—'} {pick('条动态 ·','developments ·')} {watch.data?.total??'—'} {pick(filtered?'个匹配的持续关注主体':'个持续关注主体',filtered?'matching profiles':'ongoing-watch profiles')}</p>
    <div className="reading-layout"><ReadingContents newsTotal={news.data?.total??null} news={(news.data?.items||[]).map(n=>({id:newsAnchor(n.id),title:n.name}))} resources={(watch.data?.items||[]).map(i=>({id:watchAnchor(i.id),title:i.name}))} groups={(watch.data?.groups||[]).filter(g=>g.count>0).map(g=>({id:'watch-group-'+g.id,title:g.name+' · '+g.count,items:(watch.data?.items||[]).filter(i=>i.type===g.id).map(i=>({id:watchAnchor(i.id),title:i.name}))}))} resourceTotal={watch.data?.total??null} loading={watch.loading} filtered={filtered}/>
    <div className="reading-body"><ModelLandscape/><NewsReading {...news}/>
    <section className="watch-section"><div className="platform-section-heading"><h2 id="resource-dossiers" tabIndex={-1}>{pick('持续关注','Ongoing watch')}</h2><span>{watch.data?.collection_total??'—'} {pick('个跟踪主体','profiles')}</span></div><p className="platform-lead">{pick('跟踪重要模型与项目，看清能力、版本和演进。','Follow important models and projects: capabilities, versions and evolution.')}</p>
    <form className="platform-search" onSubmit={e=>{e.preventDefault();setParams(p=>{p.set('q',query);p.delete('cursor');return p;});}}><input aria-label={pick('搜索持续关注','Search ongoing watch')} placeholder={pick('搜索名称、版本或关键词','Search names, versions or keywords')} value={query} onChange={e=>setQuery(e.target.value)}/><button className="button">{pick('搜索','Search')}</button><select aria-label={pick('持续关注类型','Watch type')} value={type} onChange={e=>setParams(p=>{p.set('type',e.target.value);p.delete('cursor');return p;})}><option value="">{pick('全部五类','All five groups')}</option>{Object.entries(watchNames).map(([id,name])=><option key={id} value={id}>{name}</option>)}</select></form>
    {filtered&&<button className="text-button" onClick={()=>setParams(p=>{p.delete('q');p.delete('type');return p;})}>{pick('清除全部筛选','Clear filters')}</button>}
    <ContinuousWatch result={watch}/></section><DeveloperProjects/>
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
  const [accessRevision, setAccessRevision] = useState(0);
  const [connection, setConnection] = useState('');
  const [busy, setBusy] = useState(false);
  const [token, setToken] = useState('');
  const [copyFailed, setCopyFailed] = useState(false);
  const endpoint = new URL(BASE + '/mcp/curated', location.origin).href;
  const local = ['localhost', '127.0.0.1', '[::1]'].includes(new URL(endpoint).hostname);
  const config = JSON.stringify({ mcpServers: { fieldtofit: { url: endpoint } } }, null, 2);
  const instructions = pick(
    `请将 FieldToFit 添加为只读远程 HTTP MCP 服务。地址：${endpoint}。配置示例：\n${config}\n先用 curated_news 读取近期动态，用 curated_watch 检索持续关注资料。保留来源、版本、核验日期与未知项；编辑解读不等于原文，链接资料请按需继续读取。再结合我提供的需求继续工作。如果你无法添加 MCP，请指导我在客户端的 MCP/连接器设置中添加；不要声称已经连接。`,
    `Add FieldToFit as a read-only remote HTTP MCP server: ${endpoint}. Example configuration:\n${config}\nRead curated_news for developments and curated_watch for profiles. Preserve sources, revisions, review dates and unknowns. Editorial notes are not upstream text; follow links as needed. Continue with my requirements. If you cannot add MCP servers, guide me through the client's connector settings; do not claim to be connected.`
  ) + (local ? pick('\n这是本机地址，仅同机客户端可访问。','\nThis address is only reachable from this computer.') : '');
  const copy = async (body: string) => {
    try { await navigator.clipboard.writeText(body); setCopyFailed(false); notify(pick('已复制','Copied')); }
    catch { setCopyFailed(true); notify(pick('请从下方文本框手动复制','Copy from the text area below')); }
  };
  const connect = async () => {
    setBusy(true); setConnection('');
    try {
      const headers: Record<string,string> = { 'Content-Type':'application/json', Accept:'application/json, text/event-stream' };
      if (readToken()) headers.Authorization = 'Bearer ' + readToken();
      const response = await fetch(endpoint, { method:'POST', headers, signal:AbortSignal.timeout(15000), body:JSON.stringify({ jsonrpc:'2.0', id:1, method:'initialize', params:{ protocolVersion:'2025-11-25', capabilities:{}, clientInfo:{ name:'fieldtofit-platform-web', version:appVersion } } }) });
      const data = await response.json();
      if (!response.ok || data.error) throw Error(data.detail || data.error?.message || data.error || `HTTP ${response.status}`);
      setConnection(pick('网站到 MCP 服务连接成功；你的 AI 客户端仍需完成配置。', 'The website can reach MCP. Your AI client still needs configuration.'));
    } catch (e) { setConnection((e as Error).message); } finally { setBusy(false); }
  };
  return <div className="platform-page"><header className="platform-hero"><p className="platform-eyebrow">FOR YOUR AI · {pick('给 AI 用','SOURCE MATERIALS')}</p><h1>{pick('把 FieldToFit，\n接入你的 AI。','Connect FieldToFit.\nGive your AI the sources.')}</h1><p className="platform-lead">{pick('这里提供与 For you 同源的近期动态、持续关注资料、版本和出处。复制 MCP 接入说明给你的 AI，或在支持远程 MCP 的客户端中添加服务；接入后，让它按你的问题检索和读取。暂时无法接入，也可以下载下方资料直接交给 AI。','Access the same developments, profiles, versions and sources as For you. Copy the MCP setup instructions for your AI or add the service in a remote-MCP client, then ask it to read the materials relevant to your question. You can also download profiles below.')}</p><div className="platform-actions"><button className="button primary" onClick={()=>copy(instructions)}>{pick('复制 MCP 接入说明','Copy MCP setup instructions')}</button><a className="button" href="#ai-materials">{pick('浏览与下载资料','Browse and download')}</a></div><p className="muted">{pick('复制说明不会自动完成连接；不同客户端的配置格式可能不同。公开只读，无需注册。','Copying does not automatically connect your client; configuration formats vary. Public, read-only access needs no registration.')}</p>{copyFailed&&<textarea aria-label={pick('MCP 接入说明','MCP setup instructions')} readOnly rows={8} value={instructions}/>}</header>
    <section className="platform-panel"><h2>{pick('连接方式','Connection')}</h2><p>{pick('在客户端添加远程 HTTP MCP 服务，填入下面的地址。支持 JSON 配置的客户端可参考配置示例。','Add a remote HTTP MCP server in your client using this URL. Clients supporting JSON can use the example below.')}</p><pre className="platform-original">{endpoint}</pre><div className="platform-actions"><button className="button" onClick={()=>copy(endpoint)}>{pick('复制 MCP 地址','Copy MCP URL')}</button><button className="button" disabled={busy} onClick={connect}>{pick('测试 MCP 服务','Test MCP service')}</button></div>{connection&&<p role="status">{connection}</p>}
      <details><summary>{pick('查看 JSON 配置','JSON configuration')}</summary><pre className="platform-original">{config}</pre><button className="button" onClick={()=>copy(config)}>{pick('复制配置','Copy configuration')}</button></details>
      {local&&<p className="platform-notice">{pick('这是本机地址，其他设备或云端 AI 无法直接访问。请使用同机客户端，或下载资料。','This is a local address. Use a client on this computer or download materials.')}</p>}
      <details><summary>{pick('私有部署与 stdio','Private access and stdio')}</summary><p>{pick('读取令牌只保存于本次浏览器会话，不进入复制配置。客户端需另设 Authorization: Bearer；不要使用管理员密码。','Read tokens stay in this browser session and are excluded from copied configurations. Set Authorization: Bearer in your client; never use the admin password.')}</p><form className="platform-search" onSubmit={e=>{e.preventDefault();if(token)sessionStorage.setItem('fieldtofit-read-token',token);else sessionStorage.removeItem('fieldtofit-read-token');setToken('');setAccessRevision(r=>r+1);notify(pick('读取设置已更新','Read access updated'));}}><input type="password" autoComplete="off" aria-label={pick('读取令牌','Read token')} value={token} onChange={e=>setToken(e.target.value)}/><button className="button">{pick('保存读取设置','Save read access')}</button></form><p>{pick('在已启动后端的项目目录中运行 stdio 桥接：','With the backend running, start the stdio bridge from the project directory:')}</p><pre className="platform-original">.venv/bin/python -m backend.mcp_stdio</pre><p>FIELDTOFIT_MCP_URL = {endpoint}</p></details>
    </section>
    <div id="ai-materials"><WatchAI key={accessRevision}/></div><DeveloperProjects key={accessRevision} ai/>
    <section className="platform-panel"><h2>{pick('接入后，可以这样问','After connecting, try this')}</h2><blockquote>{pick('从 FieldToFit 读取最近的 AI 动态，以及我关注的模型或项目资料。先列出发生了哪些变化和对应来源，再结合我接下来提供的任务继续分析；区分官方声明、编辑解读和没有核实的信息。','Read recent developments and the models or projects I follow from FieldToFit. List changes and sources, then analyze them against the task I provide. Distinguish official claims, editorial notes and unverified information.')}</blockquote><ul className="platform-reading-steps"><li><code>curated_news</code><p>{pick('公司与产品动态、分点解读、关联资料和原始出处。','Company and product developments, editorial points, related materials and sources.')}</p></li><li><code>curated_watch</code><p>{pick('模型、工具、Agent、Skill、Harness 的介绍、版本表、解读和核验日期；支持关键词和类型筛选。','Model, tool, Agent, Skill and Harness profiles, version tables, notes and review dates; filter by keyword and type.')}</p></li></ul><p className="muted">{pick('当前这两组资料的原始文章通过链接读取，中文整理不冒充原文。每 1 天检查是维护周期，实际内容以资料中的核验日期为准。','Original articles in these collections are linked, not stored in full. Editorial notes are not source text. Daily checks are the maintenance cadence; refer to each record’s review date.')}</p></section>
  </div>;
}

export function AboutFieldToFit() {
  const { pick } = useWorkspace(); const health = useRemote<{version:string}>('/health');
  return <div className="platform-page platform-about">
    <header className="platform-hero brand-story">
      <img className="about-brand brand-light" src="/brand/logo-horizontal-ink.svg" alt="FieldToFit" />
      <img className="about-brand brand-dark" src="/brand/logo-horizontal-paper.svg" alt="FieldToFit" />
      <p className="platform-eyebrow">ABOUT FIELDTOFIT · v{appVersion}</p>
      <h1 className="field-to-fit">FIELD <span aria-label="to">→</span> FIT</h1>
      <p className="platform-lead">{pick("FieldToFit 是人与 AI 共享的动态 AI 地图：看清已有方案，判断是否适配，选择正确的采用与构建路线。", "FieldToFit is a living AI map shared by people and AI: understand existing solutions, judge their fit, and choose the right path to adopt or build.")}</p>
      <div className="brand-logic">
        <article><span className="brand-step">01</span><h2>Field</h2><p>{pick("动态、论文、模型、工具、开源项目和开发资料组成的 AI 全景。", "The AI landscape: developments, papers, models, tools, open-source projects and development materials.")}</p></article>
        <article><span className="brand-step">02</span><h2>To</h2><p>{pick("持续跟踪、整理、比较、验证和筛选。", "Ongoing tracking, organization, comparison, verification and selection.")}</p></article>
        <article><span className="brand-step">03</span><h2>Fit</h2><p>{pick("结合用户的任务、条件与限制，判断什么真正适用。", "Understand what truly fits the user's task, conditions and constraints.")}</p></article>
      </div>
    </header>
    <section className="platform-panel"><p className="platform-eyebrow">FOR YOU · FOR YOUR AI</p><h2>{pick('同一套资料，两种使用方式','One collection, two ways to use it')}</h2><p>{pick('AI 资料分散、版本变化快，好的项目也容易被信息流淹没。我们把值得关注的变化和已有成果整理下来，方便你读懂，也方便你的 AI 继续读取。','AI materials are scattered, versions change quickly, and useful projects can get lost in the feed. We organize developments and existing work for you to understand and your AI to explore.')}</p><div className="platform-facts"><article><h3>For you</h3><p>{pick('浏览模型图表、近期动态和持续关注资料，从清晰的介绍进入版本与出处。','Explore model charts, developments and profiles, then follow versions and sources.')}</p><Link className="button primary" to="/for-you">{pick('开始阅读','Start reading')}</Link></article><article><h3>For your AI</h3><p>{pick('通过 MCP 连接，或复制、下载资料，让你的 AI 结合需求继续工作。','Connect through MCP or copy and download materials for your AI to use with your requirements.')}</p><Link className="button" to="/for-your-ai">{pick('连接我的 AI','Connect my AI')}</Link></article></div></section>
    <section className="platform-panel"><h2>{pick('这里收录什么','What we collect')}</h2><div className="community-grid"><article><h3>{pick('重点动态','Developments')}</h3><p>{pick('公司与产品发布、论文与开发进展，保留原始出处及分点解读。','Company and product releases, research and development, with sources and editorial notes.')}</p></article><article><h3>{pick('模型与开发资源','Models and development resources')}</h3><p>{pick('持续关注模型、工具、Agent、Skill 与 Harness，整理版本、能力和使用条件。','Models, tools, Agents, Skills and Harnesses, with versions, capabilities and requirements.')}</p></article><article><h3>{pick('开发者投稿项目','Developer-submitted projects')}</h3><p>{pick('收录经过审核的个人和团队项目，说明用途、使用方式与协作需求。','Reviewed individual and team projects, their purpose, usage and collaboration needs.')}</p><Link to="/community#submit-project">{pick('了解投稿','About submissions')}</Link></article></div></section>
    <section className="platform-panel"><h2>{pick('资料如何维护','How materials are maintained')}</h2><p>{pick('优先核对官方公告、作者文档、仓库与论文，保留来源、版本和核验日期。作者声明、编辑解读与实际测试分别标注；资料中的未知和缺项明确保留。','We prioritize announcements, author documentation, repositories and papers, preserving sources, versions and review dates. Author claims, editorial notes and actual tests remain distinct; unknowns and gaps stay explicit.')}</p><p>{pick('每 1 天检查来源，有值得发布的变化再更新内容。平台维护资料，具体任务的比较、选择与构建由你和你的 AI 继续完成。','We check sources daily and publish meaningful reviewed changes. You and your AI continue with task-specific comparisons, choices and building.')}</p><Link to="/sources">{pick('查看数据来源与状态','See sources and status')}</Link></section>
    <section className="platform-panel community-invitation"><h2>{pick('一起建设 AI 应用资料库','Build an AI application database together')}</h2><p>{pick('FieldToFit 计划逐步建立围绕 AI 应用的共建社区。你可以提交项目、推荐资源、补充资料，或参与开发。','FieldToFit plans to build a community around AI applications. Submit projects, recommend resources, improve materials or contribute development.')}</p><Link className="button primary" to="/community">{pick('了解社区与参与共建','Explore the community')}</Link></section>
    <section className="platform-panel"><h2>{pick('当前版本与项目链接','Version and project links')}</h2><p>{pick('运行版本：','Running version: ')}{health.data?.version||pick('暂未取得','Unavailable')}</p><p>{pick('本版更新、历史变化与已知范围，请查看版本更新记录。','See the changelog for this release, earlier changes and known limitations.')}</p><div className="platform-actions"><SourceLink url="https://github.com/Kevinxnova/FieldToFit">GitHub</SourceLink><SourceLink url="https://github.com/Kevinxnova/FieldToFit/blob/main/CHANGELOG.md">{pick('版本更新记录','Changelog')}</SourceLink><SourceLink url="https://github.com/Kevinxnova/FieldToFit/blob/main/docs/guides/local-development.md">{pick('自行部署','Self-host')}</SourceLink></div><p className="muted">{pick('源码采用 MIT 许可，第三方资料保留原有来源和适用许可。','Source code is MIT licensed; third-party materials retain their attribution and terms.')}</p></section>
  </div>;
}

export function LegacyPlatformEntry() {
  const [params] = useSearchParams(); const next = new URLSearchParams({legacy:'1'});
  if (params.get('q')) next.set('q', params.get('q')!);
  const type = params.get('kind') === 'paper' ? 'research' : params.get('object_type');
  if (type && type in typeNames) next.set('type', type);
  return <Navigate replace to={'/for-you?' + next} />;
}
