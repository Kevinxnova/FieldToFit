import { dateText, useWorkspace } from "./UI";

export type Operations = {
  organization_pending: number;
  oldest_pending_days: number | null;
  organized_last_day: number;
  publication_to_collection: { p95_days: number | null; sample_count: number };
  collection_to_organization: { p95_days: number | null; sample_count: number };
  successful_daily_dates_utc: string[];
  runs: { id: number; kind: string; status: string; started_at: string; duration_days: number | null }[];
  source_progress: { source_id: string; state: Record<string, unknown> }[];
};

export default function OperationsOverview({ data }: { data: Operations }) {
  const { pick } = useWorkspace();
  const days = (n: number | null) => n === null ? pick("暂无样本", "No samples") : `${n} ${pick("天", "days")}`;
  return <section className="operations-overview">
    <h2>{pick("每日运行与积压", "Daily operations and backlog")}</h2>
    <div className="ops-status">
      <span>{pick("待整理资料", "Unorganized records")} <strong>{data.organization_pending}</strong></span>
      <span>{pick("最长等待", "Oldest wait")} <strong>{days(data.oldest_pending_days)}</strong></span>
      <span>{pick("近 1 天整理成功", "Organized in 1 day")} <strong>{data.organized_last_day}</strong></span>
      <span>{pick("发布到采集 P95", "Publication to collection P95")} <strong>{days(data.publication_to_collection.p95_days)}</strong> ({data.publication_to_collection.sample_count})</span>
      <span>{pick("采集到整理 P95", "Collection to organization P95")} <strong>{days(data.collection_to_organization.p95_days)}</strong> ({data.collection_to_organization.sample_count})</span>
    </div>
    <p className="muted">{pick("检查和更新周期均为 1 天；括号内为有效延迟样本数。完整流程成功日期按 UTC 去重，同日重试不算多个日周期，仍需逐日核对来源和内容质量。", "Checks and updates run every 1 day. Parentheses show latency sample counts. Successful full-workflow dates are distinct UTC dates; retries do not count as additional days. Review sources and content separately.")}</p>
    <p>{pick("完整流程成功日期", "Successful full-workflow dates")}: {data.successful_daily_dates_utc.slice(0, 7).join(", ") || pick("尚无记录", "None recorded")}</p>
    <div className="table-scroll"><table className="ops-table"><thead><tr>
      <th>{pick("运行", "Run")}</th><th>{pick("开始时间", "Started")}</th><th>{pick("状态", "Status")}</th><th>{pick("耗时", "Duration")}</th>
    </tr></thead><tbody>{data.runs.map(r => <tr key={r.id}><td>{r.kind} #{r.id}</td><td>{dateText(r.started_at)}</td><td>{r.status}</td><td>{days(r.duration_days)}</td></tr>)}</tbody></table></div>
    <details><summary>{pick("来源续采位置", "Source continuation positions")}</summary>
      {data.source_progress.map(p => <div key={p.source_id}><strong>{p.source_id}</strong><pre>{JSON.stringify(p.state, null, 2)}</pre></div>)}
    </details>
  </section>;
}
