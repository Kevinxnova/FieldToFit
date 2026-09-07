import { useEffect, useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  send,
  useRemote,
  type Overview,
  type SearchResult,
  type Source,
  type TaskPack,
} from "../api/knowledge";
import {
  Icon,
  TOPICS,
  PageHeading,
  RecordCard,
  Pagination,
  State,
  useWorkspace,
  titleOf,
  summaryOf,
  dateText,
} from "../components/workspace/UI";

export default function Explore({
  mode,
}: {
  mode: "information" | "resource";
}) {
  const { zh, pick, collection, toggleCollection } = useWorkspace();
  const [params, setParams] = useSearchParams();
  const [query, setQuery] = useState(params.get("q") || "");
  const [persona, setPersona] = useState("engineer");
  const [deployment, setDeployment] = useState("");
  const [pack, setPack] = useState<TaskPack | null>(null);
  const [packError, setPackError] = useState("");
  const [packing, setPacking] = useState(false);
  const [advanced, setAdvanced] = useState(false);
  useEffect(() => {
    setQuery(params.get("q") || "");
    setPack(null);
    setPackError("");
  }, [params, mode]);
  const args = new URLSearchParams(params);
  args.set(
    "kind",
    mode === "resource" ? "resource" : params.get("kind") || "information",
  );
  args.set("limit", "24");
  const results = useRemote<SearchResult>("/v1/records?" + args);
  const overview = useRemote<Overview>("/v1/overview");
  const sources = useRemote<{ items: Source[] }>("/v1/sources");
  const information = mode === "information";
  const topic = params.get("topic") || "";
  const offset = Number(params.get("offset") || "0");
  const setFilter = (key: string, value: string) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    if (key !== "offset") next.delete("offset");
    setParams(next);
  };
  const submit = (event: FormEvent) => {
    event.preventDefault();
    setFilter("q", query.trim());
  };
  const buildPack = async () => {
    setPacking(true);
    setPackError("");
    try {
      setPack(
        await send<TaskPack>("/v1/task", {
          goal: query,
          persona,
          constraints: deployment ? { deployment } : {},
        }),
      );
    } catch (error) {
      setPackError((error as Error).message);
    } finally {
      setPacking(false);
    }
  };
  const first = results.data?.items[0];
  const feature =
    information &&
    !params.get("q") &&
    !topic &&
    !offset &&
    !params.get("kind") &&
    !!first;
  return (
    <>
      <PageHeading
        eyebrow={information ? "THE DAILY PERSPECTIVE" : "THE RESOURCE LIBRARY"}
        title={
          information
            ? pick("看清变化，找到下一步。", "Make sense of what’s next.")
            : pick(
                "从一个问题，找到可用的资源。",
                "Find the right starting point.",
              )
        }
        description={
          information
            ? pick(
                "连接 AI 动态、研究和实践。每天更新，沿着来源继续探索。",
                "Connect AI news, research and practice. Updated daily, grounded in sources.",
              )
            : pick(
                "模型、工具、数据与开源项目。看清能力、条件与依据，再做选择。",
                "Models, tools, datasets and open-source projects. Explore capabilities and conditions before choosing.",
              )
        }
      >
        <div className="edition-mark">
          <span>{information ? "01" : "02"}</span>
          <small>{information ? "INFORMATION" : "APPLICATIONS"}</small>
        </div>
      </PageHeading>

      <div className="workspace-shortcuts">
        <Link
          className="button"
          to={information ? "/briefs" : "/tasks?q=" + encodeURIComponent(query)}
        >
          <Icon name={information ? "news" : "book"} size={17} />
          {information
            ? pick("每日重点与历史简报", "Daily editions")
            : pick("打开任务工作台", "Open task workbench")}
          <Icon name="arrow" size={15} />
        </Link>
      </div>
      <section
        className={`search-panel ${information ? "" : "resource-search"}`}
        aria-label={pick("检索资料", "Search records")}
      >
        {!information && (
          <div className="persona-row">
            {[
              ["engineer", "工程开发", "Engineering"],
              ["researcher", "研究探索", "Research"],
              ["graduate", "论文复现", "Reproduction"],
              ["student", "学习实践", "Learning"],
            ].map(([id, cn, en]) => (
              <button
                key={id}
                onClick={() => setPersona(id)}
                className={persona === id ? "active" : ""}
                aria-pressed={persona === id}
              >
                {pick(cn, en)}
              </button>
            ))}
          </div>
        )}
        <form className="search-form" onSubmit={submit}>
          <Icon name="search" size={23} />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label={pick("搜索关键词或任务", "Search keywords or a task")}
            placeholder={
              information
                ? pick(
                    "搜索一个方向、项目或你关心的问题…",
                    "Search a topic, project or question…",
                  )
                : pick(
                    "例如：为本地 Python 项目寻找 PDF 处理工具",
                    "Try: PDF processing for a local Python project",
                  )
            }
            maxLength={500}
          />
          {query && (
            <button
              type="button"
              className="icon-button"
              aria-label={pick("清空搜索", "Clear search")}
              onClick={() => {
                setQuery("");
                setFilter("q", "");
              }}
            >
              <Icon name="close" size={17} />
            </button>
          )}
          <button className="button primary" type="submit">
            {pick("搜索", "Search")}
            <Icon name="arrow" size={17} />
          </button>
        </form>
        <div className="search-bottom">
          <div className="suggestions">
            <span>{pick("试试看", "Explore")}</span>
            {(information
              ? ["Agent", "模型", "研究"]
              : ["PDF", "Agent", "数据集", "开源"]
            ).map((value) => (
              <button key={value} onClick={() => setFilter("q", value)}>
                {value}
              </button>
            ))}
          </div>
          {!information && (
            <button
              className="text-button"
              onClick={() => setAdvanced(!advanced)}
              aria-expanded={advanced}
            >
              <Icon name="settings" size={15} />
              {pick("按任务整理", "Task context")}
            </button>
          )}
        </div>
        {advanced && !information && (
          <div className="task-builder">
            <label>
              {pick("部署条件", "Deployment")}
              <select
                value={deployment}
                onChange={(e) => setDeployment(e.target.value)}
              >
                <option value="">
                  {pick("不限 / 尚未确定", "Any / undecided")}
                </option>
                <option value="local">{pick("本地运行", "Local")}</option>
                <option value="cloud">{pick("云端服务", "Cloud")}</option>
                <option value="self-hosted">
                  {pick("自行部署", "Self-hosted")}
                </option>
              </select>
            </label>
            <p>
              {pick(
                "未知条件会单独列出。任务资料帮助你继续核查候选方案。",
                "Unknown conditions stay explicit. Use the task context to review each candidate.",
              )}
            </p>
            <button
              className="button primary"
              disabled={!query.trim() || packing}
              onClick={buildPack}
            >
              {packing
                ? pick("正在整理…", "Preparing…")
                : pick("整理任务资料", "Build task context")}
            </button>
          </div>
        )}
      </section>
      {packError && (
        <div className="notice danger" role="alert">
          {packError}
        </div>
      )}
      {pack && (
        <section className="task-result">
          <div className="section-title">
            <h2>{pick("任务资料", "Task context")}</h2>
            <button
              className="icon-button"
              onClick={() => setPack(null)}
              aria-label={pick("关闭", "Close")}
            >
              <Icon name="close" />
            </button>
          </div>
          <p>{pack.goal}</p>
          <div className="notice">
            <Icon name="info" />
            {pick(
              `当前收录范围内找到 ${pack.total_candidates} 项相关资料。以下为检索候选，采用前仍需核查条件与原文。`,
              `${pack.total_candidates} indexed candidates. Review the conditions and original evidence before adopting.`,
            )}
          </div>
          {pack.candidates.map((item) => (
            <div className="task-candidate" key={item.id}>
              <Link to={`/records/${item.id}`}>
                {titleOf(item, zh)}
                <Icon name="up" size={15} />
              </Link>
              <div>
                {item.constraint_matches?.map((m) => (
                  <span className={`tag ${m.state}`} key={m.condition}>
                    {String(m.requested)} ·{" "}
                    {m.state === "satisfied"
                      ? pick("来源声明支持", "Source states support")
                      : m.state === "unmet"
                        ? pick("不满足", "Unmet")
                        : pick("待核实", "Unknown")}
                  </span>
                ))}
              </div>
            </div>
          ))}
          {!pack.candidates.length && (
            <p>
              {pick(
                "未找到相关记录，可以减少条件或提交缺失资料反馈。",
                "No candidates found. Try fewer conditions or submit missing resources.",
              )}
            </p>
          )}
        </section>
      )}

      <div className="explore-tabs">
        <div role="group" aria-label={pick("资料分类", "Record type")}>
          {information ? (
            [
              ["", "全部信息", "All information"],
              ["event", "行业动态", "News"],
              ["paper", "研究论文", "Papers"],
            ].map(([value, cn, en]) => (
              <button
                key={value}
                className={(params.get("kind") || "") === value ? "active" : ""}
                onClick={() => setFilter("kind", value)}
              >
                {pick(cn, en)}
              </button>
            ))
          ) : (
            <span className="tab-title">
              {pick("应用与研究资源", "Applications & research resources")}
            </span>
          )}
        </div>
        <Link to="/sources" className="text-button">
          <span className="status-dot" />
          {pick("每 1 天更新", "Updated every day")}
          <Icon name="chevron" size={14} />
        </Link>
      </div>
      <div className="filters">
        <div className="topic-filters">
          <button
            className={!topic ? "active" : ""}
            onClick={() => setFilter("topic", "")}
          >
            {pick("全部领域", "All topics")}
          </button>
          {Object.entries(TOPICS).map(([value, names]) => (
            <button
              key={value}
              className={topic === value ? "active" : ""}
              onClick={() => setFilter("topic", value)}
            >
              {pick(...names)}
            </button>
          ))}
        </div>
        <div className="filter-selects">
          <select
            aria-label={pick("来源筛选", "Filter by source")}
            value={params.get("source") || ""}
            onChange={(e) => setFilter("source", e.target.value)}
          >
            <option value="">{pick("所有来源", "All sources")}</option>
            {sources.data?.items.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
          <input
            aria-label={pick("最早发布日期", "Published since")}
            type="date"
            value={params.get("since") || ""}
            onChange={(e) => setFilter("since", e.target.value)}
          />
          {!information && (
            <select
              aria-label={pick("资源类型", "Resource type")}
              value={params.get("object_type") || ""}
              onChange={(e) => setFilter("object_type", e.target.value)}
            >
              <option value="">{pick("所有类型", "All types")}</option>
              {[
                ["project", "开源项目", "Open source"],
                ["model", "模型", "Models"],
                ["tool", "工具", "Tools"],
                ["library", "开发库", "Libraries"],
                ["dataset", "数据集", "Datasets"],
                ["application", "应用", "Apps"],
              ].map(([value, cn, en]) => (
                <option value={value} key={value}>
                  {pick(cn, en)}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>
      {params.get("since") && (
        <p className="filter-note">
          {pick(
            "按原始发布日期筛选；发布时间未知的记录不在此结果中。",
            "Filtered by original publication date; records with unknown dates are excluded.",
          )}
        </p>
      )}
      {topic && (
        <div className="topic-follow">
          <span>{pick("持续跟踪这个方向", "Keep track of this topic")}</span>
          <button
            className="text-button"
            onClick={() => toggleCollection("topic:" + topic, "follow")}
          >
            <Icon name="bell" size={16} />
            {collection.some(
              (x) => x.record_id === "topic:" + topic && x.action === "follow",
            )
              ? pick("取消关注", "Unfollow")
              : pick("关注主题", "Follow topic")}
          </button>
        </div>
      )}

      <State
        loading={results.loading}
        error={results.error}
        empty={results.data?.items.length === 0}
        retry={results.reload}
      >
        {feature && first && (
          <div className="featured-layout">
            <article className="lead-story">
              <div className="lead-top">
                <span className="eyebrow">
                  {pick("从这里开始阅读", "START READING")}
                </span>
                <span className="tag">
                  {first.kind === "paper"
                    ? pick("研究论文", "RESEARCH")
                    : pick("领域动态", "PERSPECTIVE")}
                </span>
              </div>
              <div className="lead-orbit" aria-hidden="true">
                <div />
                <div />
                <div />
                <span>m.</span>
              </div>
              <div className="lead-content">
                <div className="tiny-topic">
                  {first.topics
                    .slice(0, 2)
                    .map((x) => (TOPICS[x] ? pick(...TOPICS[x]) : x))
                    .join(" / ")}
                </div>
                <h2>
                  <Link to={`/records/${first.id}`}>{titleOf(first, zh)}</Link>
                </h2>
                <p>
                  {summaryOf(first, zh) ||
                    pick(
                      "查看来源与详情，继续了解这条动态。",
                      "Follow the original source to explore this update.",
                    )}
                </p>
                <Link to={`/records/${first.id}`} className="lead-link">
                  {pick("阅读详情与依据", "Read the story & sources")}
                  <Icon name="arrow" size={18} />
                </Link>
              </div>
            </article>
            <aside className="perspective-card">
              <div className="eyebrow">THE BIGGER PICTURE</div>
              <h2>
                {pick("把关注，变成积累。", "Turn curiosity into knowledge.")}
              </h2>
              <p>
                {pick(
                  "一条动态连接一份资料。找到研究、工具和下一次实践的起点。",
                  "Every update can lead to a useful resource, a research question, or your next experiment.",
                )}
              </p>
              <div className="stat-pair">
                <div>
                  <strong>{overview.data?.counts.paper ?? "—"}</strong>
                  <span>{pick("研究资料", "Research papers")}</span>
                </div>
                <div>
                  <strong>{overview.data?.counts.resource ?? "—"}</strong>
                  <span>{pick("应用与资源", "Resources")}</span>
                </div>
              </div>
              <Link to="/apps">
                {pick("探索应用与资源", "Explore the library")}
                <Icon name="arrow" size={19} />
              </Link>
              <div className="fine-print">
                {pick("最近成功采集", "Last successful collection")} ·{" "}
                {dateText(overview.data?.last_update, zh)}
              </div>
            </aside>
          </div>
        )}
        <div className="section-title">
          <h2>
            {params.get("q")
              ? pick("检索结果", "Search results")
              : information
                ? pick("继续探索", "Keep exploring")
                : pick("资源目录", "The library")}
          </h2>
          <span>
            {pick(
              `${results.data?.total ?? 0} 项资料`,
              `${results.data?.total ?? 0} records`,
            )}
          </span>
        </div>
        <div className="record-grid">
          {(feature ? results.data?.items.slice(1) : results.data?.items)?.map(
            (record) => (
              <RecordCard key={record.id} record={record} />
            ),
          )}
        </div>
        {results.data && (
          <Pagination
            offset={offset}
            next={results.data.next_offset}
            total={results.data.total}
            onPage={(value) => {
              setFilter("offset", String(value));
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
          />
        )}
      </State>
    </>
  );
}
