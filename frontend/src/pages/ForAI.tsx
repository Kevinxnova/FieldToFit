import { useEffect, useRef, useState } from 'react';
import { Link } from '@fieldtofit/locale/router';
import { BASE, readToken } from '../api/knowledge';
import { Icon, useWorkspace } from '../components/workspace/UI';
import { VisitReady } from '../components/workspace/SiteVisits';
import { trackAction } from '../components/workspace/Traffic';
import { UnifiedLookup } from '../components/workspace/UnifiedLookup';
import { WatchAI } from '../components/workspace/ContinuousWatch';
import { MapsAI } from '../components/workspace/TechnicalMaps';
import { CodexShare } from '../components/workspace/CodexShare';
import { DeveloperProjects } from './Community';
import { searchPages } from '../search';
import { version } from '../../package.json';
import guideData from '../../../backend/seo/ai_clients.json';
import './for-ai.css';

type Pair = string[];
type Mode = { id: string; label: Pair; path: string; start: Pair; setup: Pair; verify: Pair; source: string; command?: string; transport?: string; note?: Pair };
type Client = { id: string; name: string; logo: string; caption: Pair; modes: Mode[]; note?: Pair };
const clients: Client[] = guideData.clients;
const publicEndpoint = 'https://fieldtofit.top/api/mcp/curated';

function ClientLogo({ client }: { client: Client }) {
  return <span className={'ai-client-mark ai-mark-' + client.id} aria-hidden="true"><img src={client.logo} alt="" width="32" height="32"/></span>;
}

/** A copy failure exposes this exact payload, never a different control's value. */
export function CopyAction({ text, label, primary = false, tracked = false }: { text: string; label: string; primary?: boolean; tracked?: boolean }) {
  const { pick } = useWorkspace();
  const [state, setState] = useState<'idle' | 'copied' | 'failed'>('idle');
  const current = useRef(0);
  useEffect(() => { current.current++; setState('idle'); return () => { current.current++; }; }, [text]);
  async function copy() {
    const attempt = ++current.current;
    try {
      await navigator.clipboard.writeText(text);
      if (attempt !== current.current) return;
      setState('copied');
      if (tracked) trackAction('mcp_address_copy');
    } catch { if (attempt === current.current) setState('failed'); }
  }
  return <div className="ai-copy"><button type="button" className={'button ' + (primary ? 'primary' : '')} onClick={copy}><Icon name={state === 'copied' ? 'check' : 'copy'} size={15}/>{label}</button><span className="ai-copy-state" role="status">{state === 'copied' ? pick('已复制', 'Copied') : state === 'failed' ? pick('复制未完成，请手动复制下方内容。', 'Copy failed. Copy the text below manually.') : ''}</span>{state === 'failed' && <textarea readOnly value={text} rows={4} aria-label={label + pick('：手动复制', ': manual copy')} onFocus={event => event.currentTarget.select()}/>}</div>;
}

function ServiceCheck({ endpoint }: { endpoint: string }) {
  const { pick } = useWorkspace();
  const [state, setState] = useState<'idle' | 'busy' | 'ready' | 'error'>('idle');
  const [error, setError] = useState('');
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => { controller.current?.abort(); controller.current = null; }, []);
  async function check() {
    controller.current?.abort();
    const active = new AbortController(); controller.current = active;
    const timeout = window.setTimeout(() => active.abort(), 15000);
    setState('busy'); setError('');
    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json', Accept: 'application/json, text/event-stream' };
      const token = readToken(); if (token) headers.Authorization = 'Bearer ' + token;
      const response = await fetch(endpoint, { method: 'POST', headers, signal: active.signal, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'initialize', params: { protocolVersion: '2025-11-25', capabilities: {}, clientInfo: { name: 'fieldtofit-platform-web', version } } }) });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      if (data.error || !data.result?.serverInfo || !data.result?.protocolVersion) throw new Error('MCP');
      if (controller.current !== active) return;
      setState('ready'); trackAction('mcp_service_check');
    } catch (reason) {
      if (controller.current !== active) return;
      setError(reason instanceof Error ? reason.message : 'MCP'); setState('error');
    } finally { window.clearTimeout(timeout); }
  }
  return <div className="ai-service-check"><button className="text-button" disabled={state === 'busy'} onClick={check}><Icon name="source" size={15}/>{state === 'busy' ? pick('正在检查…', 'Checking…') : pick('检查本站服务', 'Check this service')}</button><p role="status">{state === 'ready' ? pick('本站服务可达。请在自己的 AI 中完成实际读取，确认接入。', 'This service is reachable. Confirm setup by reading materials in your own AI.') : state === 'error' ? pick('暂时无法连接，请检查网络或读取权限后重试。', 'Could not connect. Check your network or read access, then retry.') + (error.startsWith('HTTP ') ? ` (${error})` : '') : pick('这里检查服务可用性；不会代替你连接客户端。', 'Checks service availability; does not connect your client.')}</p></div>;
}

export function ForAI() {
  const { pick, zh, notify } = useWorkspace();
  const [clientId, setClientId] = useState('codex');
  const [modeId, setModeId] = useState('desktop');
  const [accessRevision, setAccessRevision] = useState(0);
  const [token, setToken] = useState('');
  const client = clients.find(item => item.id === clientId)!;
  const mode = client.modes.find(item => item.id === modeId) || client.modes[0];
  const t = (pair: Pair) => pair[zh ? 0 : 1];
  const endpoint = new URL(BASE + '/mcp/curated', location.origin).href;
  const local = ['localhost', '127.0.0.1', '[::1]'].includes(new URL(endpoint).hostname);
  const cloudLocal = local && clientId === 'claude' && mode.id === 'desktop';
  const command = mode.command?.replace('{endpoint}', `'${endpoint.replace(/'/g, "'\\''")}'`);
  const config = JSON.stringify({ mcpServers: { fieldtofit: { type: 'http', url: endpoint } } }, null, 2);
  const languageHint = zh ? '' : ' Pass lang="en" in every FieldToFit tool call.';
  const testQuestion = pick('请通过已连接的 FieldToFit 查找 Claude，读取一项完整资料，简述内容并附上出处、资料修订与核验日期。区分整理内容、已存原文和仅链接资料。如果无法调用连接，请明确说明，不要用已有知识代答。', 'Use the connected FieldToFit service to find Claude and read one complete entry. Summarize it with sources, publication revision and review date. Distinguish editorial content, stored text and link-only sources. If the connection is unavailable, say so instead of answering from memory.') + languageHint;
  const instructions = pick(`请将 FieldToFit 添加为只读远程 HTTP MCP 服务：${endpoint}。先用 curated_lookup 检索，按结果 reading 读取完整内容，按材料 reading 使用 curated_material 续读原文，或用 curated_bundle 打包。使用 curated_changes 的 scope=workspace 读取当前资料变化；scope=legacy 使用独立游标。保留出处、版本、核验日期、材料覆盖和未知项。无法配置时请指导我操作，不要声称已经连接。`, `Add FieldToFit as a read-only HTTP MCP service: ${endpoint}. Use curated_lookup, follow result reading instructions for full entries and curated_material for source text, or curated_bundle for packages. Read changes with curated_changes scope=workspace; retain a separate cursor for scope=legacy. Preserve sources, revisions, review dates, coverage and unknowns. If you cannot configure it, guide me without claiming a connection.`) + languageHint;
  const examples = [
    { title: pick('跟上最近的变化', 'Catch up on changes'), text: pick('最近有哪些值得关注的 AI 更新？', 'What has changed in AI recently?'), prompt: pick('通过 FieldToFit 读取近期已发布的 AI 动态，选出三项变化并解释其意义，附上出处与原事件日期；区分官方声明、本站解读和未核实的信息。', 'Read recent published AI developments from FieldToFit. Explain three changes and why they matter, with sources and original event dates. Distinguish official claims, editorial notes and unverified information.') },
    { title: pick('深入一个项目', 'Explore a project'), text: pick('帮我了解 Pi，以及它的使用条件。', 'Help me understand Pi and its requirements.'), prompt: pick('通过 FieldToFit 查找 Pi coding agent，读取完整档案及可用材料，说明用途、当前收录版本、使用条件与限制，并附上来源和核验日期。缺失内容请明确说明。', 'Find Pi coding agent in FieldToFit. Read its full profile and available materials, explain its purpose, recorded version, requirements and limitations, and cite sources and review dates. Identify missing information.') },
    { title: pick('带着原文继续分析', 'Work from the sources'), text: pick('找到相关原文，再结合我的问题分析。', 'Find the source text, then analyze my question.'), prompt: pick('我会给你一个问题。请从 FieldToFit 检索相关资料，按材料清单续读可用原文，再基于证据回答。标明出处、版本、全文或节选范围；仅有链接时请说明，不把整理内容当作上游原文。', 'I will give you a question. Search FieldToFit, follow its manifests to read available source text, then answer from that evidence. Cite sources, revisions and full-text or excerpt coverage. Flag link-only material and keep editorial notes distinct from upstream text.') },
  ];
  return <div className="platform-page ai-page"><VisitReady/>
    <header className="ai-hero">
      <div className="ai-hero-copy"><p className="ai-kicker"><span/> FOR YOUR AI</p><h1>{pick(...searchPages['/for-your-ai'].heading)}</h1><p className="ai-intro">{pick(...searchPages['/for-your-ai'].description)}</p><div className="ai-trust"><span><Icon name="source" size={14}/>{pick('出处可追溯', 'Traceable sources')}</span><span><Icon name="book" size={14}/>{pick('公开资料，只读接入', 'Public materials, read-only')}</span></div><div className="ai-hero-actions"><a className="button primary" href="#ai-connect">{pick('连接我的 AI', 'Connect my AI')} <Icon name="arrow" size={16}/></a><a className="ai-inline-link" href="#ai-materials">{pick('直接带走资料', 'Take a source package')} <Icon name="arrow" size={16}/></a></div></div>
      <div className="ai-connection-art" aria-hidden="true"><div className="ai-art-grid"/><span className="ai-art-label">FIELDTOFIT / SOURCE LAYER</span><div className="ai-source-stack"><span><i>01</i>{pick('动态', 'Updates')}</span><span><i>02</i>{pick('档案', 'Profiles')}</span><span><i>03</i>{pick('原文', 'Sources')}</span></div><div className="ai-glass-orb"><svg className="ai-brand-mark" viewBox="0 0 160 112" fill="currentColor" focusable="false"><rect x="0" y="32" width="24" height="24"/><rect x="32" y="32" width="24" height="24"/><rect x="0" y="64" width="24" height="24"/><rect x="32" y="64" width="24" height="24"/><path d="M64 0H160V24H104V32H88V80H104V112H64Z"/><rect x="96" y="40" width="24" height="24"/><rect x="128" y="40" width="24" height="24"/></svg></div><div className="ai-art-path"><i/><i/><i/></div><div className={'ai-target ai-target-'+clientId}><ClientLogo client={client}/><strong>{client.name}</strong></div><span className="ai-art-foot">{pick('同一份资料，延伸到你的 AI', 'YOUR SOURCES, WITHIN REACH')}</span></div>
    </header>

    <section className="ai-onboarding" id="ai-connect" aria-labelledby="ai-connect-title">
      <div className="ai-section-heading"><div><p className="ai-kicker">01 / CONNECT</p><h2 id="ai-connect-title">{pick('你使用哪款 AI？', 'Choose your AI.')}</h2></div><p>{pick('选好客户端，跟着三步接入。', 'Pick your client. Follow three steps.')}</p></div>
      <div className="ai-client-picker" role="group" aria-label={pick('选择 AI 客户端', 'Choose an AI client')}>{clients.map(item => <button key={item.id} type="button" aria-pressed={item.id === clientId} onClick={() => {setClientId(item.id);setModeId(item.modes[0].id);}}><ClientLogo client={item}/><span><strong>{item.name}</strong><small>{t(item.caption)}</small></span><span className="ai-choice-dot">{item.id === clientId && <Icon name="check" size={12}/>}</span></button>)}</div>
      <div className="ai-guide">
        <div className="ai-guide-top"><h3>{pick('连接到 ', 'Connect to ')}{client.name}</h3>{client.modes.length > 1 && <div className="ai-mode-picker" role="group" aria-label={pick('接入方式', 'Setup method')}>{client.modes.map(item => <button key={item.id} aria-pressed={mode.id === item.id} onClick={() => setModeId(item.id)}>{t(item.label)}</button>)}</div>}</div>
        {cloudLocal && <p className="ai-local-notice">{pick('你正在本机预览。Claude 云端无法访问此地址；公开站点请使用：', 'This is a local preview. Claude’s cloud cannot reach this address. For the public site, use: ')}<a href={publicEndpoint}>{publicEndpoint}</a></p>}
        <div className="ai-guide-grid"><ol className="ai-steps">
          <li><span>1</span><div><h4>{pick('找到添加入口', 'Open the setup')}</h4><p>{t(mode.start)}</p><span className="ai-route">{mode.path}</span></div></li>
          <li><span>2</span><div><h4>{command ? pick('复制并运行命令', 'Copy and run the command') : pick('填入连接信息', 'Add the connection details')}</h4><p>{t(mode.setup)}</p></div></li>
          <li><span>3</span><div><h4>{pick('回到 AI，试着读一份资料', 'Ask your AI to read a source')}</h4><p>{t(mode.verify)}</p><a className="ai-inline-link" href="#ai-first-read">{pick('查看测试问题', 'Go to the test question')} <Icon name="arrow" size={14}/></a></div></li>
        </ol>
        <div className="ai-setup-panel"><div className="ai-panel-caption"><span>{command ? 'TERMINAL' : pick('填写示意', 'CONNECTION DETAILS')}</span><span>{client.name}</span></div>
          {command ? <><pre className="ai-command"><code>{command}</code></pre><CopyAction text={command} label={pick('复制接入命令', 'Copy setup command')} primary tracked/><p className="ai-panel-note">{pick('在你自己的终端运行；复制不会执行命令。', 'Run in your own terminal. Copying does not execute it.')}</p></> : <><div className="ai-field"><span>{pick('名称', 'Name')}</span><strong>fieldtofit</strong></div><div className="ai-field"><span>{pick('连接类型', 'Transport')}</span><strong>{mode.transport}</strong></div><div className="ai-field ai-url-field"><span>{pick('服务地址', 'Server URL')}</span><code>{endpoint}</code></div><CopyAction text={endpoint} label={pick('复制服务地址', 'Copy server URL')} primary tracked/><p className="ai-panel-note">{pick('正式站公开资料无需 FieldToFit 账号。', 'Public site materials need no FieldToFit account.')}</p></>}
          <ServiceCheck key={clientId + mode.id + accessRevision + endpoint} endpoint={endpoint}/>
        </div></div>
        <div className="ai-guide-footer"><span>{pick('步骤核对于 ', 'Instructions checked ')}{guideData.checked_at}</span><a href={mode.source} target="_blank" rel="noreferrer">{client.name} {pick('官方接入说明', 'official setup guide')} ↗</a></div>
        {(mode.note || client.note) && <p className="ai-guide-note">{mode.note && t(mode.note)}{mode.note && client.note ? ' ' : ''}{client.note && t(client.note)}</p>}
        {local && !cloudLocal && <p className="ai-guide-note">{pick('当前是本机服务地址，仅同机客户端可访问。其他设备请打开正式网站获取地址。', 'This local URL is only reachable on this computer. Open the public site for other devices.')}</p>}
      </div>
    </section>

    <section className="ai-first-read" id="ai-first-read" aria-labelledby="ai-first-title"><div><p className="ai-kicker">02 / FIRST CONVERSATION</p><h2 id="ai-first-title">{pick('第一句话，从这里开始。', 'Start the conversation.')}</h2><p>{pick('添加服务后，把这句话发给你的 AI。', 'After adding the service, send this to your AI.')}</p></div><div className="ai-question"><span className="ai-quote-mark" aria-hidden="true">“</span><p>{pick('从 FieldToFit 找到 Claude 的资料，读完一项，并告诉我出处。', 'Find Claude in FieldToFit, read one entry, and show me the sources.')}</p><CopyAction text={testQuestion} label={pick('复制测试问题', 'Copy test question')}/></div><p className="ai-read-result"><Icon name="check" size={17}/>{pick('看到实际工具调用，以及带出处、修订和核验日期的回答，才算完成这次读取。', 'Look for an actual tool call and an answer with sources, revision and review date to confirm the read.')}</p></section>

    <section className="ai-examples" aria-label={pick('接入后的提问示例', 'Questions to try after setup')}>{examples.map((example, i) => <article key={i}><span className="ai-example-index">0{i + 1}</span><h3>{example.title}</h3><p>{example.text}</p><CopyAction key={example.prompt} text={example.prompt + languageHint} label={pick('复制这个问题', 'Copy this question')}/></article>)}</section>

    <section className="ai-materials" id="ai-materials" aria-labelledby="ai-materials-title"><div className="ai-section-heading"><div><p className="ai-kicker">03 / TAKE IT WITH YOU</p><h2 id="ai-materials-title">{pick('先挑一份资料，也可以。', 'Start with a source package.')}</h2></div><p>{pick('搜索、预览，再复制或下载给 AI。', 'Search, preview, then copy or download for your AI.')}</p></div><UnifiedLookup key={'lookup-'+accessRevision}/><details className="ai-disclosure"><summary>{pick('浏览全部持续关注档案', 'Browse all ongoing-watch profiles')}<span>↗</span></summary><WatchAI key={'watch-'+accessRevision}/><DeveloperProjects key={'projects-'+accessRevision} ai/></details><details className="ai-disclosure"><summary>{pick('技术报告与分析资料', 'Technical reports and analysis')}<span>↗</span></summary><MapsAI/></details></section>

    <section className="ai-advanced" aria-labelledby="ai-advanced-title"><div className="ai-section-heading"><div><p className="ai-kicker">04 / KEEP EXPLORING</p><h2 id="ai-advanced-title">{pick('让资料持续跟上。', 'Keep your sources close.')}</h2></div><Link to="/for-you">For you <span aria-hidden="true">↗</span></Link></div>
      <section className="ai-sync" id="ai-codex-sync"><div><Icon name="clock" size={22}/><h3>{pick('Codex 专题，每日同步', 'Codex topic, daily sync')}</h3><p>{pick('通过专题专用连接读取全部日志，再接收新增、更正和撤回。', 'Use the dedicated topic connection to read the logs, then follow additions, corrections and removals.')}</p></div><CodexShare initiallyOpen/><Link className="ai-inline-link" to="/for-you#news-codex-28-days">{pick('查看专题日志', 'View the topic logs')} <Icon name="arrow" size={15}/></Link></section>
      <details className="ai-disclosure"><summary>{pick('通用接入、私有部署与更多帮助', 'General setup, private hosting and help')}<span>＋</span></summary><div className="ai-help"><h3>{pick('通用 HTTP MCP 配置', 'Generic HTTP MCP configuration')}</h3><p>{pick('客户端字段可能不同，请以所用客户端的官方说明为准。', 'Client fields vary; follow your client’s official documentation.')}</p><pre>{config}</pre><CopyAction text={config} label={pick('复制通用配置', 'Copy generic configuration')} tracked/><CopyAction key={instructions} text={instructions} label={pick('复制 MCP 接入说明', 'Copy MCP setup instructions')} tracked/>
      <h3>{pick('找不到入口或读取失败？', 'Missing a setting or unable to read?')}</h3><p>{pick('核对上方官方说明和客户端版本。已添加同名服务时先检查现有配置；没有工具时重新打开会话，并核对工具是否启用。也可以使用上方资料下载。', 'Check the official guide and your client version. If the name already exists, inspect its configuration. If tools are missing, reopen the session and check whether they are enabled. You can also download materials above.')}</p>
      <h3>{pick('私有部署的读取权限', 'Read access for private deployments')}</h3><p>{pick('读取令牌只保存在本次浏览器会话，不进入复制内容。客户端需要另行设置 Authorization: Bearer；不要使用管理员密码。', 'Read tokens stay in this browser session and are excluded from copied content. Configure Authorization: Bearer separately in the client; never use an admin password.')}</p><form className="platform-search" onSubmit={event => {event.preventDefault();if (token) sessionStorage.setItem('fieldtofit-read-token', token);else sessionStorage.removeItem('fieldtofit-read-token');setToken('');setAccessRevision(value => value + 1);notify(pick('读取设置已更新', 'Read access updated'));}}><input type="password" autoComplete="off" aria-label={pick('读取令牌', 'Read token')} value={token} onChange={event => setToken(event.target.value)}/><button className="button">{pick('保存读取设置', 'Save read access')}</button></form><h3>{pick('本地 stdio 桥接', 'Local stdio bridge')}</h3><p>{pick('后端运行后，在项目目录启动；客户端需要该 Python 的绝对路径。', 'With the backend running, start from the project directory; your client needs the absolute Python path.')}</p><pre>.venv/bin/python -m backend.mcp_stdio</pre><p>FIELDTOFIT_MCP_URL = {endpoint}</p></div></details>
    </section>
  </div>;
}
