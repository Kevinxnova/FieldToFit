import { ForYouHero } from '../components/workspace/ForYouHero';
import { ProfileNewsOverview } from '../components/workspace/ProfileNewsOverview';
import { FollowUpdates } from '../components/workspace/FollowUpdates';
import { searchPages } from '../search';
import { VisitReady } from '../components/workspace/SiteVisits';
import { AliasNotice } from '../components/workspace/PublicMaintenance';
import { DeveloperProjects } from "./Community";
import { ContinuousWatch, watchAnchor, watchNames, type WatchCollection } from '../components/workspace/ContinuousWatch';
import { ReadingContents } from '../components/workspace/ReadingContents';
import { NewsReading, newsAnchor, type NewsCollection } from '../components/workspace/NewsReading';
import { PublicationHistory } from '../components/workspace/PublicationHistory';
import { SourceContext, ObjectSourceStatus, type SourceCheck } from '../components/workspace/SourceStatus';
import { MaterialPackage, type PackageRef } from '../components/workspace/MaterialPackage';
import { ModelLandscape } from '../components/workspace/ModelLandscape';
import { version as appVersion } from '../../package.json';
import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link, Navigate, useSearchParams } from "@fieldtofit/locale/router";
import { BASE, request, useRemote, type Fact } from "../api/knowledge";
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
  return <section className="platform-detail"><VisitReady ready={!!pub && !!obj && !result.loading && !result.error}/><button className="text-button" onClick={onClose}>← {pick("返回资源档案", "Back to dossiers")}</button><LoadState {...result} retry={result.reload} />{pub && obj && <>
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
  const [following,setFollowing]=useState(false);
  if(params.get('object'))return <LegacyCatalog/>;
  return <div className="platform-page"><VisitReady ready={!!news.data && !!watch.data && !news.loading && !watch.loading && !news.error && !watch.error}/><AliasNotice/><ForYouHero onRead={()=>setFollowing(false)}/>
    {news.data&&!news.error&&<p className="section-overview"><strong>{news.data.title}</strong><span className="muted"> · {news.data.reviewed_at}</span></p>}
    <p className="reading-page-summary">{news.data?.total??'—'} {pick('条动态 ·','developments ·')} {watch.data?.total??'—'} {pick(filtered?'个匹配的持续关注主体':'个持续关注主体',filtered?'matching profiles':'ongoing-watch profiles')}</p>
    <FollowUpdates active={following} onActive={setFollowing}/><div hidden={following} className="reading-layout"><ReadingContents technicalMaps={!!news.data?.items.some(n=>n.technical_map)} codexProgress={!!news.data?.codex_progress?.total} newsTotal={news.data?.total??null} news={(news.data?.items||[]).map(n=>({id:newsAnchor(n.id),title:n.name}))} resources={(watch.data?.items||[]).map(i=>({id:watchAnchor(i.id),title:i.name}))} groups={(watch.data?.groups||[]).filter(g=>g.count>0).map(g=>({id:'watch-group-'+g.id,title:g.name+' · '+g.count,items:(watch.data?.items||[]).filter(i=>i.type===g.id).map(i=>({id:watchAnchor(i.id),title:i.name}))}))} resourceTotal={watch.data?.total??null} loading={watch.loading} filtered={filtered}/>
    <div className="reading-body"><ModelLandscape/><NewsReading {...news}/>
    <section className="watch-section"><div className="platform-section-heading"><h2 id="resource-dossiers" tabIndex={-1}>{pick('持续关注','Ongoing watch')}</h2><span>{watch.data?.collection_total??'—'} {pick('个跟踪主体','profiles')}</span></div><div className="section-overview"><strong>{pick('把一次发现，放回长期维护的对象档案。','Put each discovery in a maintained object dossier.')}</strong><p>{pick('模型、Agent、工具、Skill 与 Harness，保留版本、原文和采用条件。','Models, agents, tools, skills and harnesses retain versions, sources and adoption conditions.')}</p><ProfileNewsOverview news={news.error?[]:news.data?.items||[]} ids={watch.data?.items.map(i=>i.id)||[]}/>{watch.data&&!watch.error&&<p className="overview-coverage">{pick('当前范围：','Current selection: ')}{watch.data.total} · {watch.data.groups.filter(g=>g.count>0).map(g=>g.name+' '+g.count).join(' / ')} · {pick('资料核对日期见各档案，非每日检查成功数。','Review dates are per profile, not a count of successful daily checks.')}</p>}</div>
    <form className="platform-search" onSubmit={e=>{e.preventDefault();setParams(p=>{p.set('q',query);p.delete('cursor');return p;});}}><input aria-label={pick('搜索持续关注','Search ongoing watch')} placeholder={pick('搜索名称、版本或关键词','Search names, versions or keywords')} value={query} onChange={e=>setQuery(e.target.value)}/><button className="button">{pick('搜索','Search')}</button><select aria-label={pick('持续关注类型','Watch type')} value={type} onChange={e=>setParams(p=>{p.set('type',e.target.value);p.delete('cursor');return p;})}><option value="">{pick('全部五类','All five groups')}</option>{Object.entries(watchNames).map(([id,name])=><option key={id} value={id}>{name}</option>)}</select></form>
    {filtered&&<button className="text-button" onClick={()=>setParams(p=>{p.delete('q');p.delete('type');return p;})}>{pick('清除全部筛选','Clear filters')}</button>}
    <ContinuousWatch result={watch} news={news.error?[]:news.data?.items||[]}/></section><DeveloperProjects/>
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

export { ForAI } from './ForAI';

export function AboutFieldToFit() {
  const { pick } = useWorkspace(); const health = useRemote<{version:string}>('/health');
  return <div className="platform-page platform-about"><VisitReady/>
    <header className="platform-hero brand-story">
      <img className="about-brand brand-light" src="/brand/logo-horizontal-ink.svg" alt="FieldToFit" />
      <img className="about-brand brand-dark" src="/brand/logo-horizontal-paper.svg" alt="FieldToFit" />
      <p className="platform-eyebrow">ABOUT FIELDTOFIT · v{appVersion}</p>
      <h1 className="field-to-fit">FIELD <span aria-label="to">→</span> FIT</h1>
      <p className="platform-lead">{pick(...searchPages['/about'].description)}</p>
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
    <section className="platform-panel"><h2>{pick('当前版本与项目链接','Version and project links')}</h2><p>{pick('运行版本：','Running version: ')}{health.data?.version||pick('暂未取得','Unavailable')}</p><p>{pick('本版更新、历史变化与已知范围，请查看版本更新记录。','See the changelog for this release, earlier changes and known limitations.')}</p><div className="platform-actions"><SourceLink url="https://github.com/Kevinxnova/FieldToFit">GitHub</SourceLink><Link to="/changelog">{pick('版本更新记录','Changelog')}</Link><SourceLink url="https://github.com/Kevinxnova/FieldToFit/blob/main/docs/guides/local-development.md">{pick('自行部署','Self-host')}</SourceLink></div><p className="muted">{pick('源码采用 MIT 许可，第三方资料保留原有来源和适用许可。','Source code is MIT licensed; third-party materials retain their attribution and terms.')}</p></section>
  </div>;
}

export function LegacyPlatformEntry() {
  const [params] = useSearchParams(); const next = new URLSearchParams({legacy:'1'});
  if (params.get('q')) next.set('q', params.get('q')!);
  const type = params.get('kind') === 'paper' ? 'research' : params.get('object_type');
  if (type && type in typeNames) next.set('type', type);
  return <Navigate replace to={'/for-you?' + next} />;
}
