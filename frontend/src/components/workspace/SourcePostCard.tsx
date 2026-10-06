import { useEffect, useState } from 'react';
import { SourceLink, useWorkspace } from './UI';
import type { SourcePost } from './codexData';
const roles={primary:['主公告','Announcement'],supplement:['补充说明','Supplement'],reply:['回复','Reply'],correction:['更正','Correction']} as const;
export function SourcePosts({posts}:{posts?:SourcePost[]}){
 const {pick}=useWorkspace();if(!posts?.length)return null;
 const primary=posts.find(p=>p.kind==='primary');const others=posts.filter(p=>p!==primary);
 return <div className="codex-source-posts">{primary&&<Post post={primary}/>} {!!others.length&&<details className="codex-related-posts"><summary>{pick(`另有${others.length}条相关原帖`,`${others.length} related original posts`)}</summary>{others.map(post=><Post key={post.url} post={post}/>)}</details>}</div>;
}
function Post({post}:{post:SourcePost}){
 const {pick,zh}=useWorkspace();const [failed,setFailed]=useState(false);useEffect(()=>setFailed(false),[post.avatar?.url]);
 const date=new Date(post.announced_at).toLocaleString(zh?'zh-CN':'en-GB',{timeZone:'Asia/Shanghai',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false});
 return <aside className="codex-source-post" aria-label={pick('Tibo原帖','Tibo original post')}><header><div className="codex-post-author">{post.avatar&&!failed&&<img key={post.avatar.url} src={post.avatar.url} width="48" height="48" alt={pick('Tibo的X头像','Tibo’s X avatar')} onError={()=>setFailed(true)} loading="lazy"/>}<div><SourceLink url={'https://x.com/'+post.author_handle}>{post.author_name}</SourceLink><small>@{post.author_handle}</small></div></div><span>{pick(roles[post.kind][0],roles[post.kind][1])}</span></header>
  <div className="codex-post-text"><small>{zh?pick(post.text_scope==='excerpt'?'中文摘译':'中文译文',''):post.text_scope==='excerpt'?'Original excerpt':'Original post'}</small><p lang={zh?'zh':'en'}>{zh?post.translation_zh:post.text_en}</p></div>
  {post.context&&<blockquote className="codex-post-context"><small>{pick(post.context.kind==='reply'?'回复':'引用',post.context.kind==='reply'?'Replying to':'Quoting')} <SourceLink url={post.context.url}>{post.context.author_name} · @{post.context.author_handle}</SourceLink></small><p lang={zh?'zh':'en'}>{zh?post.context.translation_zh:post.context.text_en}</p></blockquote>}
  <footer><time dateTime={post.announced_at}>{date} · {pick('北京时间','Beijing time')}</time><SourceLink url={post.url}>{pick('在X查看','View on X')} ↗</SourceLink></footer>
  <details className="codex-post-original"><summary>{zh?pick(post.text_scope==='excerpt'?'英文原文摘录':'英文原文',''):pick('',post.text_scope==='excerpt'?'Chinese translation of excerpt':'Chinese translation')}</summary><p lang={zh?'en':'zh'}>{zh?post.text_en:post.translation_zh}</p>{post.context&&<blockquote><small>@{post.context.author_handle} · {pick(post.context.kind==='reply'?'回复对象':'引用帖',post.context.kind==='reply'?'Reply context':'Quoted post')}</small><p lang={zh?'en':'zh'}>{zh?post.context.text_en:post.context.translation_zh}</p></blockquote>}<p className="codex-post-evidence"><SourceLink url={post.evidence_url}>{pick(post.retrieval_method==='official_embed'?'原帖嵌入依据':'原帖读取依据',post.retrieval_method==='official_embed'?'Original embed evidence':'Source evidence')}</SourceLink> · {post.checked_at}{post.timestamp_basis==='post_id_derived'&&pick(' · 时刻由原帖ID推导',' · Time derived from post ID')}{post.avatar&&<> · <SourceLink url={post.avatar.evidence_url}>{pick('头像出处','Avatar provenance')}</SourceLink></>}</p></details>
 </aside>;
}
