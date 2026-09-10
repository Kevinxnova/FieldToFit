import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useRemote } from '../../api/knowledge';
import { dateText, useWorkspace } from './UI';

type Event = { id:number; kind:string; published_at:string; from_revision:number|null; to_revision:number|null; availability:string; changed_fields:string[] };
type History = { revision:number; items:Event[]; total:number; next_cursor:string|null; previous_cursor:string|null; offset:number };

export function PublicationHistory({id, revision}: {id:string; revision:number}) {
  const {pick, zh} = useWorkspace();
  const [cursor, setCursor] = useState('');
  const [params] = useSearchParams();
  const link = (toRevision:number) => {const next=new URLSearchParams(params);next.set('object',id);next.set('revision',String(toRevision));return '/for-you?' + next;};
  const query = new URLSearchParams({revision:String(revision),limit:'5'});
  if (cursor) query.set('cursor',cursor);
  const result = useRemote<History>(`/v1/platform/objects/${encodeURIComponent(id)}/history?${query}`);
  const kinds:Record<string,string> = {added:pick('首次精选','First publication'),updated:pick('资料修订','Revision'),needs_review:pick('进入待复核','Needs review'),withdrawn:pick('撤回','Withdrawn')};
  const fields:Record<string,string> = {name:pick('名称','Name'),aliases:pick('别名','Aliases'),roles:pick('角色依据','Role evidence'),facts:pick('公开事实','Facts'),materials:pick('材料清单','Materials'),attention:pick('关注依据','Attention evidence'),introduction:pick('介绍','Introduction'),types:pick('类型','Types'),upstream_version:pick('上游版本','Upstream version'),official_url:pick('官方入口','Official URL'),source_id:pick('采集来源','Collection source')};
  return <section className="platform-panel" aria-label={pick('公开修订历史','Public publication history')}>
    <div className="platform-section-heading"><h2>{pick('这份资料如何变化','How this dossier changed')}</h2><span>r{revision}</span></div>
    <p className="muted">{pick('只展示截至所选发布修订的公开记录，较新记录可到“给 AI 用”查看。以下版本号是 FieldToFit 内部修订，不是上游软件版本。','Public events through the selected publication only. See For your AI for newer changes. These are FieldToFit revisions, not upstream software versions.')}</p>
    {result.loading && <p role="status">{pick('正在读取历史…','Loading history…')}</p>}
    {result.error && <div role="alert"><p>{result.error}</p><button className="button" onClick={()=>{setCursor('');result.reload();}}>{pick('重新读取历史','Restart history')}</button></div>}
    {result.data && <><p>{result.data.total} {pick('条公开记录','public events')}</p><ol className="platform-change-list">{result.data.items.map(e=><li key={e.id}>
      <div className="platform-section-heading"><strong>{kinds[e.kind] || e.kind}</strong><span>{dateText(e.published_at,zh)}</span></div>
      <p>{pick('记录','Event')} {e.id} · {e.from_revision === null?'—':`r${e.from_revision}`} → {e.to_revision === null?'—':`r${e.to_revision}`}</p>
      {!!e.changed_fields.length && <p>{pick('变化字段：','Changed fields: ')}{e.changed_fields.map(f=>fields[f] || f).join('、')}</p>}
      {e.availability !== 'readable' ? <p>{pick('此前正文已不可用，仅保留公开变化通知。','Previous text is unavailable; only a public event notice remains.')}</p> : e.to_revision === revision ? <span>{pick('当前查看版本','Viewing this revision')}</span> : e.to_revision && <Link to={link(e.to_revision)}>{pick('打开此修订的资料','Open this publication')}</Link>}
    </li>)}</ol><div className="platform-actions"><button className="button" disabled={!result.data.previous_cursor || result.loading} onClick={()=>setCursor(result.data!.previous_cursor!)}>{pick('较新记录','Newer events')}</button><button className="button" disabled={!result.data.next_cursor || result.loading} onClick={()=>setCursor(result.data!.next_cursor!)}>{pick('更早记录','Older events')}</button></div></>}
  </section>;
}
