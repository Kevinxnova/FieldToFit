import { useSearchParams } from 'react-router-dom';
import { useRemote } from '../../api/knowledge';
import { dateText, useWorkspace } from './UI';

export type SourceCheck = { id: string | null; name: string; state: string; last_attempt_at: string | null; last_success_at: string | null; objects?: number; pending_review?: boolean; material_checks?: {material_id:string;checked_at:string;matches_publication:boolean}[] };
function StateName({state}: {state: string}) {
  const { pick } = useWorkspace();
  const names: Record<string, string> = {current:pick('最近 1 天成功','Succeeded within 1 day'), stale:pick('超过 1 天未成功','No success within 1 day'), unknown:pick('暂无成功记录','No successful check'), unregistered:pick('未接入日检查','Not connected to daily checks'), paused:pick('已停用','Paused'), running:pick('检查进行中','Check running'), error:pick('最近检查失败','Latest check failed'), failed:pick('最近检查失败','Latest check failed'), partial:pick('最近仅部分成功','Latest check partially succeeded')};
  return <>{names[state] || names.unknown}</>;
}
export function ObjectSourceStatus({source}: {source?: SourceCheck}) {
  const { pick, zh } = useWorkspace();
  if (!source) return null;
  return <div className="muted"><p>{pick('采集来源：','Collection source: ')}{source.id === 'manual' ? pick('人工整理', 'Manual collection') : source.name} · <StateName state={source.state} /> · {pick('最后成功：','Last success: ')}{source.last_success_at ? dateText(source.last_success_at,zh) : pick('未知','Unknown')}<br />{pick('检查成功不等于新材料已审核发布。','A successful check does not mean changed materials have been reviewed and published.')}</p>{source.pending_review && <p className="platform-notice">{pick('已发现待整理或待审核的材料，当前展示上次审核通过的版本。','New material awaits organization or review. This is the last reviewed publication.')}</p>}{!!source.material_checks?.length && <details><summary>{pick('查看原文检查记录','Source text checks')} · {source.material_checks.length}</summary><ul>{source.material_checks.map(m => <li key={m.material_id}>{dateText(m.checked_at,zh)} · {m.matches_publication ? pick('内容与此发布版本一致','Matches this publication') : pick('内容已变化，尚未替换此版本','Changed; this publication is retained')}</li>)}</ul></details>}</div>;
}
export function SourceContext() {
  const {pick, zh} = useWorkspace();
  const [params, setParams] = useSearchParams();
  const result = useRemote<{items:SourceCheck[]}>('/v1/platform/sources');
  const update = (key:string, value:string) => setParams(p => {
    if (value) p.set(key,value); else p.delete(key);
    ['cursor','offset','object','revision'].forEach(k => p.delete(k)); return p;
  });
  return <div className="platform-source-context">
    <details><summary>{pick('来源与发布日期筛选','Filter by source and publication date')}</summary>
      <p className="muted">{pick('日期按 FieldToFit 精选发布时间（UTC），包含首尾两天；不代表上游发布日期。筛选只作用于资料列表，不改变概览期次。','Dates use FieldToFit publication time (UTC), including both endpoints, not upstream release dates. Filters affect the object list, not overview editions.')}</p>
      <div className="platform-source-filters"><label>{pick('采集来源','Collection source')}<select aria-label={pick('采集来源','Collection source')} value={params.get('source') || ''} onChange={e=>update('source',e.target.value)}><option value="">{pick('全部采集来源','All collection sources')}</option>{result.data?.items.filter(s=>s.id).map(s=><option key={s.id} value={s.id!}>{s.id === 'manual' ? pick('人工整理', 'Manual collection') : s.name}</option>)}{params.get('source') && !result.data?.items.some(s=>s.id===params.get('source')) && <option value={params.get('source')!}>{params.get('source')} · {pick('当前未列出','Not currently listed')}</option>}</select></label>
        <label>{pick('精选发布起始日（UTC）','Published from (UTC)')}<input type="date" aria-label={pick('精选发布起始日（UTC）','Published from (UTC)')} value={params.get('since') || ''} onChange={e=>update('since',e.target.value)} /></label>
        <label>{pick('精选发布截止日（UTC）','Published through (UTC)')}<input type="date" aria-label={pick('精选发布截止日（UTC）','Published through (UTC)')} value={params.get('until') || ''} onChange={e=>update('until',e.target.value)} /></label>
      </div>{['source','since','until'].some(k=>params.has(k)) && <button className="text-button" onClick={()=>setParams(p=>{['source','since','until','cursor','offset','object','revision'].forEach(k=>p.delete(k));return p;})}>{pick('清除来源和日期筛选','Clear source and date filters')}</button>}
    </details>
    <details><summary>{pick('当前精选来源的检查状态','Check status of current selection sources')}</summary>
      <p>{pick('每 1 天检查。这里显示当前精选关联的采集源状态；不表示每份原文已重新获取，也不改变概览发布日期。','Checked every 1 day. These are collection-source checks, not re-fetches of every document or new overview publication dates.')}</p>
      {result.loading && <p role="status">{pick('正在读取来源状态…','Loading source status…')}</p>}
      {result.error && <p role="alert">{result.error}</p>}
      {result.data?.items.length===0 && <p>{pick('当前没有精选对象对应的来源。','No sources attached to current selections.')}</p>}
      <ul>{result.data?.items.map(s=><li key={s.id || 'unknown'}><strong>{s.id === 'manual' ? pick('人工整理', 'Manual collection') : s.name}</strong> · {s.objects} {pick('项','objects')} · <StateName state={s.state} /><p className="muted">{pick('最后尝试：','Last attempt: ')}{s.last_attempt_at?dateText(s.last_attempt_at,zh):pick('未知','Unknown')} · {pick('最后成功：','Last success: ')}{s.last_success_at?dateText(s.last_success_at,zh):pick('未知','Unknown')}</p></li>)}</ul>
      <button className="text-button" onClick={result.reload}>{pick('刷新来源状态','Refresh source status')}</button>
    </details>
  </div>;
}
