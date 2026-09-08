import { Link } from "react-router-dom";
import { type Dossier } from "../../api/knowledge";
import { SourceLink, useWorkspace } from "./UI";

export type DuplicatePair = { left: Dossier; right: Dossier; similarity: number };
export default function DuplicateReview({ items, choose }: { items: DuplicatePair[]; choose: (primary: string, other: string) => void }) {
  const { pick } = useWorkspace();
  return <section><h2>{pick("待审核的重复候选", "Possible duplicates to review")}</h2>
    <p className="muted">{pick("仅对最近 500 条事件按标题、发布日期和版本提出候选。逐条核对原文，选择主记录并填写下方判断依据后才能归并。", "Suggestions compare titles, publication dates and versions among the latest 500 events. Check original sources, select a primary record and supply a reason in the form below.")}</p>
    {!items.length && <p>{pick("当前范围内没有重复候选", "No candidates in the current scope")}</p>}
    {items.map(p => <article className="ops-item" key={p.left.id+p.right.id}>
      <p>{pick("标题相似度", "Title similarity")}: {Math.round(p.similarity*100)}%</p>
      {[p.left,p.right].map((r,i) => <div key={r.id}><Link to={`/records/${r.id}`}>{r.title_zh || r.title}</Link><p>{r.summary_zh || r.summary}</p>
        <SourceLink url={r.canonical_url}>{pick("核对原文", "Read source")}</SourceLink>{" "}
        <button className="button subtle" onClick={() => choose(r.id, i ? p.left.id : p.right.id)}>{pick("选择为主记录", "Select as primary")}</button>
      </div>)}
    </article>)}
  </section>;
}
