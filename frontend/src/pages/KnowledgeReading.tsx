import { useState } from "react";
import { Link } from "react-router-dom";
import { useRemote, type Dossier } from "../api/knowledge";
import {
  Icon,
  PageHeading,
  SourceLink,
  State,
  dateText,
  useWorkspace,
} from "../components/workspace/UI";
import { saveText } from "./TaskWorkbench";

type Editorial = {
  human: { zh: Record<string, string>; en: Record<string, string> };
  citations: {
    evidence_id: string;
    source_url: string;
    quote: string;
    locator: string;
  }[];
  review_status: string;
  model: string;
  generated_at: string;
};
export function StructuredReading({ record }: { record: Dossier }) {
  const { pick, zh } = useWorkspace();
  const editorial = record.metadata.editorial as Editorial | undefined;
  const conflicts = record.conflicts || [];
  return (
    <>
      {editorial && (
        <div className="structured-reading">
          <span className="tag">
            {pick("AI 整理 · 可回查来源", "AI organized · source linked")}
          </span>
          {[
            ["what", "发生了什么", "What happened"],
            ["changes", "关键变化", "Key changes"],
            ["why", "为什么值得关注", "Why it matters"],
            ["audience", "适用人群", "Who it helps"],
            ["limitations", "限制与未知", "Limitations"],
            ["next_step", "下一步", "Next step"],
          ].map(([key, cn, en]) => (
            <section key={key}>
              <h3>{pick(cn, en)}</h3>
              <p>{editorial.human[zh ? "zh" : "en"]?.[key]}</p>
            </section>
          ))}
          <details>
            <summary>
              {pick("查看整理依据", "Review supporting evidence")}
            </summary>
            {editorial.citations.map((c, i) => (
              <blockquote key={i}>
                <p>{c.quote}</p>
                <SourceLink url={c.source_url}>
                  {c.locator || pick("原文", "Source")}
                </SourceLink>
              </blockquote>
            ))}
          </details>
        </div>
      )}
      {conflicts.length > 0 && (
        <div className="notice">
          <Icon name="flag" />
          <div>
            <strong>
              {pick("部分来源存在分歧", "Some source claims conflict")}
            </strong>
            {conflicts.map((c) => (
              <div key={c.id}>
                <p>{c.field}</p>
                {c.alternatives.map((a, i) => (
                  <p key={i}>
                    {JSON.stringify(a.value)}{" "}
                    <SourceLink url={a.source_url}>
                      {pick("依据", "Evidence")}
                    </SourceLink>
                  </p>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
      {!!record.grouped_sources?.length && (
        <section className="grouped-sources">
          <h3>{pick("同一事件的其他来源", "More sources for this event")}</h3>
          {record.grouped_sources.map((s) => (
            <Link key={s.id} to={`/records/${s.id}`}>
              {s.title}
              <Icon name="arrow" size={14} />
            </Link>
          ))}
        </section>
      )}
    </>
  );
}

type Brief = {
  date: string;
  generated_at: string;
  scope: string;
  items: {
    id: string;
    title: string;
    title_zh: string;
    summary_zh: string;
    summary_en: string;
    source_url: string;
    reason: { reason_zh: string; reason_en: string };
  }[];
};
export function DailyBriefs() {
  const { pick, zh } = useWorkspace();
  const result = useRemote<{ items: Brief[] }>("/v1/briefs");
  const [selected, setSelected] = useState("");
  const brief =
    result.data?.items.find((x) => x.date === selected) ||
    result.data?.items[0];
  return (
    <>
      <PageHeading
        eyebrow="THE DAILY EDITION"
        title={pick(
          "每天，读懂值得关注的变化。",
          "A clearer view of each day.",
        )}
        description={pick(
          "按发布日期整理重点，保留选择理由与原文。自动整理内容均明确标注。",
          "Daily highlights by publication date, with selection reasons and original sources.",
        )}
      >
        <Link className="button" to="/information">
          {pick("全部信息", "All information")}
        </Link>
      </PageHeading>
      <State
        loading={result.loading}
        error={result.error}
        retry={result.reload}
      >
        {brief ? (
          <>
            <div className="brief-controls">
              <label>
                {pick("简报日期", "Edition date")}
                <select
                  value={brief.date}
                  onChange={(e) => setSelected(e.target.value)}
                >
                  {result.data?.items.map((b) => (
                    <option key={b.date}>{b.date}</option>
                  ))}
                </select>
              </label>
              <button
                className="button"
                onClick={() =>
                  saveText(
                    `fieldtofit-${brief.date}.md`,
                    `# FieldToFit ${brief.date}\n\nAI 整理 · ${brief.scope}\n` +
                      brief.items
                        .map(
                          (i) =>
                            `\n## ${i.title_zh || i.title}\n${i.summary_zh}\n\n${i.reason.reason_zh}\n\n来源：${i.source_url}\n`,
                        )
                        .join(""),
                  )
                }
              >
                {pick("导出简报", "Export edition")}
              </button>
            </div>
            <p className="fine-print">
              {pick(
                "AI 整理，尚需结合原文判断。整理时间：",
                "AI organized. Review original sources. Generated: ",
              )}
              {dateText(brief.generated_at)}
            </p>
            {brief.items.length ? (
              brief.items.map((item, i) => (
                <article className="brief-item" key={item.id}>
                  <span className="brief-number">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <div>
                    <Link to={`/records/${item.id}`}>
                      <h2>{zh ? item.title_zh || item.title : item.title}</h2>
                    </Link>
                    <p>{zh ? item.summary_zh : item.summary_en}</p>
                    <div className="brief-reason">
                      <strong>{pick("关注理由", "Why selected")}</strong>
                      <p>
                        {zh ? item.reason.reason_zh : item.reason.reason_en}
                      </p>
                    </div>
                    <SourceLink url={item.source_url}>
                      {pick("查看原文", "Original source")}
                      <Icon name="up" size={14} />
                    </SourceLink>
                  </div>
                </article>
              ))
            ) : (
              <div className="empty-state">
                <h2>
                  {pick(
                    "这一天还没有整理完成的重点",
                    "No organized highlights for this day",
                  )}
                </h2>
                <p>
                  {pick(
                    "原始信息仍可浏览，简报会在内容整理完成后补充。",
                    "Original records remain available. Highlights appear after organization.",
                  )}
                </p>
              </div>
            )}
          </>
        ) : (
          <div className="empty-state">
            <Icon name="news" size={28} />
            <h2>
              {pick("每日简报准备中", "Daily editions are being prepared")}
            </h2>
            <p>
              {pick(
                "先浏览已经收录的信息，简报将在资料整理完成后出现。",
                "Browse indexed information while the daily edition is prepared.",
              )}
            </p>
            <Link className="button" to="/information">
              {pick("浏览信息", "Browse information")}
            </Link>
          </div>
        )}
      </State>
    </>
  );
}

type Change = {
  seq: number;
  record_id: string;
  action: string;
  changed_at: string;
  reason: string;
  snapshot: {
    title?: string;
    title_zh?: string;
    status?: string;
    version?: string;
  };
};
type Changes = {
  items: Change[];
  next_cursor: number;
  latest_cursor: number;
  has_more: boolean;
};
export function FollowingUpdates() {
  const { pick, collection } = useWorkspace();
  const [read, setRead] = useState(() =>
    Number(localStorage.getItem("fieldtofit-follow-read-cursor") || 0),
  );
  const [offset, setOffset] = useState(read);
  const [all, setAll] = useState(false);
  const ids = collection
    .filter((x) => x.action === "follow" && !x.record_id.startsWith("topic:"))
    .map((x) => x.record_id);
  const topics = collection
    .filter((x) => x.action === "follow" && x.record_id.startsWith("topic:"))
    .map((x) => x.record_id.slice(6));
  const params = new URLSearchParams({
    record_ids: ids.join(","),
    topics: topics.join(","),
    after: String(all ? offset : Math.max(offset, read)),
    limit: "50",
  });
  const result = useRemote<Changes>("/v1/changes?" + params);
  const [previous, setPrevious] = useState<Change[]>([]);
  const rows = [...previous, ...(result.data?.items || [])].filter(
    (x, i, a) => a.findIndex((y) => y.seq === x.seq) === i,
  );
  const mark = () => {
    const value = result.data?.latest_cursor || read;
    localStorage.setItem("fieldtofit-follow-read-cursor", String(value));
    setRead(value);
    setOffset(value);
    setPrevious([]);
  };
  const actionLabels: Record<string, [string, string]> = {
    relationship_updated: ["关联依据更新", "Relationship updated"],
    created: ["新收录", "New record"],
    updated: ["内容变化", "Record changed"],
    evidence_added: ["来源材料更新", "Source material added"],
    grouped: ["报道归并", "Grouped coverage"],
    ungrouped: ["报道拆分", "Coverage separated"],
  };
  return (
    <section className="following-updates">
      <div className="section-title">
        <h2>{pick("关注范围内的变化", "Changes you follow")}</h2>
        <div className="button-row">
          <button
            className="button subtle"
            onClick={() => {
              setAll(!all);
              setOffset(all ? read : 0);
              setPrevious([]);
            }}
          >
            {pick(
              all ? "只看未读" : "查看历史",
              all ? "Unread only" : "View history",
            )}
          </button>
          <button
            className="button"
            onClick={mark}
            disabled={!rows.length || result.data?.has_more}
          >
            {pick("标记已读", "Mark as read")}
          </button>
        </div>
      </div>
      <State
        loading={result.loading}
        error={result.error}
        retry={result.reload}
      >
        {!rows.length ? (
          <div className="notice">
            {pick(
              "暂时没有新的关注变化。关注主题或资源后，在这里继续查看。",
              "No new changes in your followed scope. Follow topics or records to see updates here.",
            )}
          </div>
        ) : (
          <div className="change-list">
            {rows.map((c) => (
              <article key={c.seq}>
                <span className="tag">
                  {actionLabels[c.action]
                    ? pick(...actionLabels[c.action])
                    : c.action}
                </span>
                <time>{dateText(c.changed_at)}</time>
                {c.snapshot.status === "published" ? (
                  <Link to={`/records/${c.record_id}`}>
                    <h3>{c.snapshot.title_zh || c.snapshot.title}</h3>
                  </Link>
                ) : (
                  <h3>
                    {pick(
                      "资料已下架或不可用",
                      "Record withdrawn or unavailable",
                    )}
                  </h3>
                )}
                <p>{c.reason}</p>
                {c.snapshot.version && <small>{c.snapshot.version}</small>}
              </article>
            ))}
          </div>
        )}
        {result.data?.has_more && (
          <button
            className="button"
            onClick={() => {
              setPrevious(rows);
              setOffset(result.data!.next_cursor);
            }}
          >
            {pick("继续读取变化", "Read more changes")}
          </button>
        )}
      </State>
    </section>
  );
}
