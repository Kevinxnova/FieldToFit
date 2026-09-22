import { Link, Navigate, useParams } from 'react-router-dom';
import { useRemote } from '../api/knowledge';
import { NewsReading, type NewsCollection } from '../components/workspace/NewsReading';
import { ContinuousWatch, type WatchCollection } from '../components/workspace/ContinuousWatch';
import { VisitReady } from '../components/workspace/SiteVisits';
import { useWorkspace } from '../components/workspace/UI';
import { contentPath, PageMetadata } from '../search';

export function PublishedDetail({kind}: {kind:'news'|'watch'}) {
  const {id = ''} = useParams();
  // A route change unmounts the prior request and its data immediately.
  return <Detail key={kind+'/'+id} kind={kind} id={id}/>;
}
function Detail({kind, id}: {kind:'news'|'watch';id:string}) {
  const {pick} = useWorkspace();
  const result = useRemote<NewsCollection | WatchCollection>(`/v1/platform/${kind}?id=${encodeURIComponent(id)}`);
  const item = !result.loading && !result.error ? result.data?.items[0] : null;
  const path = `/${kind}/${id}`;
  if (item && item.id !== id) return <Navigate to={contentPath(item.id)} replace/>;
  const title = item ? ('title' in item ? item.title : item.name) : pick('资料详情','Dossier');
  const description = item ? ('summary' in item ? item.summary : item.introduction) : '';
  return <div className="platform-page published-detail">
    {!result.loading && <PageMetadata title={item ? title+' · FieldToFit' : 'FieldToFit · '+title} description={description} path={path} index={!!item}/>}
    <VisitReady ready={!!item}/>
    <p><Link to="/for-you">← For you</Link></p>
    {result.loading && <p role="status">{pick('正在读取…','Loading…')}</p>}
    {result.error && <div role="alert"><p>{pick('这项资料已下架、不存在或暂时无法读取。','This item is unavailable, withdrawn or could not be loaded.')}</p><button className="button" onClick={result.reload}>{pick('重试','Retry')}</button></div>}
    {item && <><h1>{title}</h1>{kind === 'news'
      ? <NewsReading {...result} data={result.data as NewsCollection} standalone/>
      : <ContinuousWatch result={{...result,data:result.data as WatchCollection}} standalone/>}</>}
  </div>;
}
