import OperationsOverview, { type Operations } from "../components/workspace/OperationsOverview";
import DuplicateReview, { type DuplicatePair } from "../components/workspace/DuplicateReview";
import RelationshipEditor from "../components/workspace/RelationshipEditor";
import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import {
  request,
  send,
  useRemote,
  type Dossier,
  type Fact,
  type Source,
} from "../api/knowledge";
import {
  PageHeading,
  State,
  TOPICS,
  dateText,
  useWorkspace,
} from "../components/workspace/UI";

type Job = {
  record_id: string;
  title: string;
  stage: string;
  status: string;
  error: string;
  finished_at: string;
};
type Model = {
  api_style?: "responses" | "chat_completions";
  enabled: boolean;
  model: string;
  base_url: string;
  key_env: string;
  credential_configured?: boolean;
  timeout_seconds: number;
};
type Conflict = {
  id: string;
  record_id: string;
  field: string;
  alternatives: Fact[];
};
type Feedback = {
  id: number;
  category: string;
  content: string;
  handling_status: string;
  resolution: string | null;
};
type Queue = {
  records: Dossier[];
  total: number;
  next_offset: number | null;
  conflicts: Conflict[];
  actions: { id: string; reason: string; status: string }[];
  feedback: Feedback[];
};
const facts = [
  "capabilities",
  "limitations",
  "deployment",
  "language",
  "platform",
  "license",
  "cost",
  "hardware",
  "hardware_vram_gb",
  "cost_monthly_usd",
  "usage",
  "extension",
  "dependencies",
  "prerequisites",
  "method",
  "experiments",
  "dataset",
  "dataset_version",
  "split",
  "metric",
  "protocol",
  "model_version",
];
function values(text: string) {
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export default function KnowledgeOps() {
  const { pick, notify } = useWorkspace();
  const [password, setPassword] = useState("");
  const [authed, setAuthed] = useState(
    !!sessionStorage.getItem("metis-admin-password"),
  );
  const [tab, setTab] = useState("records");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const [query, setQuery] = useState("");
  const [reviewNeed, setReviewNeed] = useState("");
  const [reviewStatus, setReviewStatus] = useState("");
  const [offset, setOffset] = useState(0);
  const operations = useRemote<Operations>(authed ? "/v1/admin/operations" : null, true);
  const duplicates = useRemote<{items: DuplicatePair[]}>(authed && tab === "relations" ? "/v1/admin/duplicates" : null, true);
  const queue = useRemote<Queue>(
    authed ? "/v1/admin/records?" + new URLSearchParams({q: query, need: reviewNeed, status: reviewStatus, offset: String(offset)}) : null,
    true,
  );
  const sources = useRemote<{
    items: (Source & { adapter: string; config: Record<string, unknown> })[];
  }>(authed ? "/v1/admin/sources" : null, true);
  const processing = useRemote<{
    jobs: Job[];
    counts: { stage: string; status: string; count: number }[];
    model: Model;
  }>(authed ? "/v1/admin/processing" : null, true);
  const [record, setRecord] = useState<Dossier | null>(null);
  const [reason, setReason] = useState("");
  const [factKey, setFactKey] = useState("capabilities");
  const [factValue, setFactValue] = useState("");
  const [factSource, setFactSource] = useState("");
  const [factStatus, setFactStatus] = useState("documented");
  const [factVersion, setFactVersion] = useState("");
  const [factConditions, setFactConditions] = useState("");
  const [source, setSource] = useState({
    id: "",
    name: "",
    url: "",
    category: "official",
    adapter: "rss",
    config: "{}",
  });
  const [model, setModel] = useState<Model | null>(null);
  const [mergeIds, setMergeIds] = useState("");
  const [target, setTarget] = useState("");
  const [mergeReason, setMergeReason] = useState("");
  const [resolution, setResolution] = useState("");
  const [since, setSince] = useState("");
  const run = async (name: string, fn: () => Promise<unknown>) => {
    setBusy(name);
    setError("");
    try {
      const result = await fn();
      const partial = result && typeof result === "object" && "status" in result && result.status === "partial";
      notify(partial ? pick("本批处理结束，仍有待处理或失败项", "Batch finished; unfinished or failed work remains") : pick("操作已完成", "Done"));
      queue.reload();
      sources.reload();
      processing.reload();
      operations.reload();
      duplicates.reload();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  };
  const login = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const r = await send<{ ok: boolean }>("/admin/verify", { password });
      if (!r.ok) throw Error("登录失败");
      sessionStorage.setItem("metis-admin-password", password);
      setAuthed(true);
    } catch (e) {
      setError((e as Error).message);
    }
  };
  const selectRecord = async (id: string) => {
    await run("read", async () => {
      setRecord(await request<Dossier>("/v1/admin/records/" + id, {}, true));
      setReason("");
    });
  };
  const saveRecord = async () => {
    if (!record) return;
    await run("save", () =>
      send(
        "/v1/admin/records/" + record.id,
        {
          title: record.title,
          title_zh: record.title_zh,
          summary_zh: record.summary_zh,
          object_type: record.object_type,
          status: record.status,
          topics: record.topics,
          facts: record.facts,
          reason,
        },
        "PATCH",
        true,
      ),
    );
  };
  const addFact = () => {
    if (!record || !factValue || !factSource) return;
    setRecord({
      ...record,
      facts: {
        ...record.facts,
        [factKey]: {
          value: values(factValue),
          source_url: factSource,
          status: factStatus,
          version: factVersion,
          checked_at: new Date().toISOString(),
          ...(factKey === "hardware_vram_gb"
            ? { unit: "GB", conditions: factConditions }
            : factKey === "cost_monthly_usd"
              ? { unit: "USD/month", conditions: factConditions }
              : {}),
        },
      },
    });
    setFactValue("");
  };
  const currentModel = model || processing.data?.model;
  return (
    <>
      <PageHeading
        eyebrow="KNOWLEDGE OPERATIONS"
        title={pick("让资料持续可靠。", "Keep the knowledge reliable.")}
        description={pick(
          "管理来源、处理积压、整理内容、核对分歧，并回应实际需求。",
          "Manage sources, processing, evidence conflicts and real user needs.",
        )}
      >
        <Link className="button" to="/admin/curation">
          {pick("原策展后台", "Curation")}
        </Link>
      </PageHeading>
      {!authed ? (
        <form className="account-card" onSubmit={login}>
          <h2>{pick("管理员登录", "Administrator sign in")}</h2>
          <label>
            {pick("管理密码", "Admin password")}
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </label>
          <button className="button primary">
            {pick("进入管理", "Sign in")}
          </button>
        </form>
      ) : (
        <>
          <div className="ops-tabs">
            {[
              ["records", "资料审核", "Records"],
              ["sources", "来源配置", "Sources"],
              ["processing", "处理进度", "Processing"],
              ["model", "生成模型", "Model"],
              ["relations", "归并与分歧", "Grouping"],
              ["feedback", "需求反馈", "Feedback"],
            ].map(([v, cn, en]) => (
              <button
                key={v}
                className={"button " + (tab === v ? "primary" : "subtle")}
                onClick={() => setTab(v)}
              >
                {pick(cn, en)}
              </button>
            ))}
            <button
              className="text-button"
              onClick={() => {
                sessionStorage.removeItem("metis-admin-password");
                setAuthed(false);
              }}
            >
              {pick("退出", "Sign out")}
            </button>
          </div>
          {busy && (
            <p className="notice" role="status">
              {pick("正在处理，请稍候…", "Working…")}
            </p>
          )}
          {tab === "records" && (
            <>
              <input
                value={query}
                onChange={(e) => { setQuery(e.target.value); setOffset(0); }}
                placeholder={pick(
                  "查找资料，包括待整理和已下架内容",
                  "Search all records, including pending and withdrawn",
                )}
                aria-label={pick("查找资料", "Find records")}
              />
              <div className="button-row">
                <select aria-label={pick("审核状态", "Review status")} value={reviewStatus} onChange={e => {setReviewStatus(e.target.value);setOffset(0);}}>
                  <option value="">{pick("所有状态", "All states")}</option>
                  {[["published","已展示"],["pending","待发布"],["withdrawn","已下架"],["basic","基础资料"],["full","完整资料"]].map(([v,label]) => <option key={v} value={v}>{pick(label,v)}</option>)}
                </select>
                <select aria-label={pick("审核事项", "Review need")} value={reviewNeed} onChange={e => {setReviewNeed(e.target.value);setOffset(0);}}>
                  <option value="">{pick("所有审核事项", "All review needs")}</option>
                  {[["unorganized","未整理"],["missing_evidence","缺少原文"],["conflict","事实分歧"],["failed","处理失败"]].map(([v,label]) => <option key={v} value={v}>{pick(label,v)}</option>)}
                </select>
                <span>{pick("符合条件", "Matching")}: {queue.data?.total ?? "…"}</span>
                <button className="button" disabled={!offset || queue.loading} onClick={() => setOffset(Math.max(0,offset-30))}>{pick("上一页", "Previous")}</button>
                <button className="button" disabled={queue.data?.next_offset == null || queue.loading} onClick={() => setOffset(queue.data?.next_offset ?? 0)}>{pick("下一页", "Next")}</button>
              </div>
              <div className="ops-grid">
                <State
                  loading={queue.loading}
                  error={queue.error}
                  retry={queue.reload}
                >
                  <div>
                    {queue.data?.records.map((r) => (
                      <article className="ops-item" key={r.id}>
                        <h3>{r.title_zh || r.title}</h3>
                        <p>
                          {r.status} · {r.completeness} ·{" "}
                          {r.version || pick("版本未知", "Unknown version")}
                        </p>
                        <button
                          className="button subtle"
                          disabled={!!busy}
                          onClick={() => selectRecord(r.id)}
                        >
                          {pick("编辑与审核", "Review")}
                        </button>
                      </article>
                    ))}
                  </div>
                </State>
                {record && (
                  <section className="ops-form">
                    <h2>{pick("编辑资料", "Edit record")}</h2>
                    <label>
                      {pick("名称", "Title")}
                      <input
                        value={record.title}
                        onChange={(e) =>
                          setRecord({ ...record, title: e.target.value })
                        }
                      />
                    </label>
                    <label>
                      {pick("中文名称", "Chinese title")}
                      <input
                        value={record.title_zh}
                        onChange={(e) =>
                          setRecord({ ...record, title_zh: e.target.value })
                        }
                      />
                    </label>
                    <label>
                      {pick("中文摘要", "Chinese summary")}
                      <textarea
                        value={record.summary_zh}
                        onChange={(e) =>
                          setRecord({ ...record, summary_zh: e.target.value })
                        }
                      />
                    </label>
                    <label>
                      {pick("发布状态", "Publication")}
                      <select
                        value={record.status}
                        onChange={(e) =>
                          setRecord({ ...record, status: e.target.value })
                        }
                      >
                        {["published", "pending", "withdrawn"].map((v) => (
                          <option key={v}>{v}</option>
                        ))}
                      </select>
                    </label>
                    <label>
                      {pick("对象类型", "Object type")}
                      <select
                        value={record.object_type}
                        onChange={(e) =>
                          setRecord({ ...record, object_type: e.target.value })
                        }
                      >
                        {[
                          "project",
                          "tool",
                          "library",
                          "model",
                          "api",
                          "application",
                          "dataset",
                          "benchmark",
                          "paper",
                          "news",
                          "release",
                        ].map((v) => (
                          <option key={v}>{v}</option>
                        ))}
                      </select>
                    </label>
                    <div className="condition-matches">
                      {Object.entries(TOPICS).map(([v, l]) => (
                        <label className="inline-field" key={v}>
                          <input
                            type="checkbox"
                            checked={record.topics.includes(v)}
                            onChange={() =>
                              setRecord({
                                ...record,
                                topics: record.topics.includes(v)
                                  ? record.topics.filter((t) => t !== v)
                                  : [...record.topics, v],
                              })
                            }
                          />
                          {pick(...l)}
                        </label>
                      ))}
                    </div>
                    <h3>{pick("事实与依据", "Facts and evidence")}</h3>
                    {Object.entries(record.facts).map(([k, f]) => (
                      <div className="ops-item" key={k}>
                        <strong>{k}</strong>
                        <p>{JSON.stringify(f.value)}</p>
                        <small>{f.source_url}</small>
                        <div>
                          <button
                            className="text-button"
                            onClick={() => {
                              setFactKey(k);
                              setFactValue(JSON.stringify(f.value));
                              setFactSource(f.source_url || "");
                              setFactStatus(f.status);
                              setFactVersion(f.version || "");
                            }}
                          >
                            {pick("编辑", "Edit")}
                          </button>
                          <button
                            className="text-button"
                            onClick={() => {
                              const next = { ...record.facts };
                              delete next[k];
                              setRecord({ ...record, facts: next });
                            }}
                          >
                            {pick("移除", "Remove")}
                          </button>
                        </div>
                      </div>
                    ))}
                    <label>
                      {pick("条件字段", "Fact field")}
                      <select
                        value={factKey}
                        onChange={(e) => setFactKey(e.target.value)}
                      >
                        {facts.map((v) => (
                          <option key={v}>{v}</option>
                        ))}
                      </select>
                    </label>
                    <label>
                      {pick("具体内容", "Value")}
                      <textarea
                        value={factValue}
                        onChange={(e) => setFactValue(e.target.value)}
                      />
                    </label>
                    <label>
                      {pick("依据链接", "Evidence URL")}
                      <input
                        type="url"
                        value={factSource}
                        onChange={(e) => setFactSource(e.target.value)}
                      />
                    </label>
                    <label>
                      {pick("适用版本", "Applicable version")}
                      <input
                        value={factVersion}
                        onChange={(e) => setFactVersion(e.target.value)}
                      />
                    </label>
                    <label>
                      {pick("依据类型", "Evidence status")}
                      <select
                        value={factStatus}
                        onChange={(e) => setFactStatus(e.target.value)}
                      >
                        {[
                          "documented",
                          "official_claim",
                          "reported",
                          "inferred",
                          "unknown",
                        ].map((v) => (
                          <option key={v}>{v}</option>
                        ))}
                      </select>
                    </label>
                    {["hardware_vram_gb", "cost_monthly_usd"].includes(
                      factKey,
                    ) && (
                      <label>
                        {pick("数值适用条件", "Conditions for this number")}
                        <input
                          value={factConditions}
                          onChange={(e) => setFactConditions(e.target.value)}
                        />
                      </label>
                    )}
                    <button
                      className="button"
                      onClick={addFact}
                      disabled={!factValue || !factSource}
                    >
                      {pick("加入当前编辑", "Add to this edit")}
                    </button>
                    <label>
                      {pick("修改依据", "Reason for correction")}
                      <textarea
                        value={reason}
                        onChange={(e) => setReason(e.target.value)}
                      />
                    </label>
                    <div className="button-row">
                      <button
                        className="button primary"
                        disabled={!reason || !!busy}
                        onClick={saveRecord}
                      >
                        {pick("保存修正", "Save correction")}
                      </button>
                      <button
                        className="button"
                        disabled={!!busy}
                        onClick={() =>
                          run("organize", () =>
                            send(
                              "/v1/admin/processing",
                              { record_id: record.id, force: true },
                              "POST",
                              true,
                            ),
                          )
                        }
                      >
                        {pick("重新获取与整理", "Retrieve and organize")}
                      </button>
                    </div>
                  </section>
                )}
              </div>
            </>
          )}
          {tab === "sources" && (
            <div className="ops-grid">
              <State
                loading={sources.loading}
                error={sources.error}
                retry={sources.reload}
              >
                <div>
                  {sources.data?.items.map((s) => (
                    <article className="ops-item" key={s.id}>
                      <h3>{s.name}</h3>
                      <p>
                        {s.status} · {pick("每 1 天", "Every 1 day")} ·{" "}
                        {dateText(s.last_success_at)}
                      </p>
                      {s.error && <p className="error-text">{s.error}</p>}
                      <div className="button-row">
                        <button
                          className="button subtle"
                          onClick={() =>
                            setSource({
                              id: s.id,
                              name: s.name,
                              url: s.url,
                              adapter: s.adapter,
                              category: s.category,
                              config: JSON.stringify(s.config, null, 2),
                            })
                          }
                        >
                          {pick("配置", "Configure")}
                        </button>
                        <button
                          className="button"
                          disabled={!!busy}
                          onClick={() =>
                            run("source", () =>
                              send(
                                "/v1/admin/sources/" + s.id + "/run",
                                {},
                                "POST",
                                true,
                              ),
                            )
                          }
                        >
                          {pick("重试采集", "Retry")}
                        </button>
                        <button
                          className="text-button"
                          onClick={() =>
                            run("enable", () =>
                              send(
                                "/v1/admin/sources/" + s.id,
                                { enabled: !s.enabled },
                                "PATCH",
                                true,
                              ),
                            )
                          }
                        >
                          {s.enabled
                            ? pick("停用", "Disable")
                            : pick("启用", "Enable")}
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              </State>
              <section className="ops-form">
                <h2>
                  {source.id
                    ? pick("编辑来源", "Edit source")
                    : pick("添加来源", "Add source")}
                </h2>
                <label>
                  {pick("来源名称", "Name")}
                  <input
                    value={source.name}
                    onChange={(e) =>
                      setSource({ ...source, name: e.target.value })
                    }
                  />
                </label>
                <label>
                  {pick("公开地址", "Public URL")}
                  <input
                    type="url"
                    value={source.url}
                    onChange={(e) =>
                      setSource({ ...source, url: e.target.value })
                    }
                  />
                </label>
                <label>
                  {pick("来源类别", "Category")}
                  <input
                    value={source.category}
                    onChange={(e) =>
                      setSource({ ...source, category: e.target.value })
                    }
                  />
                </label>
                <label>
                  {pick("采集类型", "Collector type")}
                  <select
                    value={source.adapter}
                    onChange={(e) =>
                      setSource({ ...source, adapter: e.target.value })
                    }
                  >
                    {[
                      "rss",
                      "pages",
                      "arxiv",
                      "huggingface",
                      "openreview",
                      "github_releases",
                      "github_skills",
                      "github_projects",
                    ].map((v) => (
                      <option key={v}>{v}</option>
                    ))}
                  </select>
                </label>
                <details>
                  <summary>
                    {pick("高级采集参数", "Advanced collection settings")}
                  </summary>
                  <textarea
                    value={source.config}
                    onChange={(e) =>
                      setSource({ ...source, config: e.target.value })
                    }
                  />
                </details>
                <p className="fine-print">
                  {pick(
                    "检查周期固定为 1 天。仓库、会议、主题和分页范围可在高级参数中指定。",
                    "Checks run every 1 day. Advanced settings specify repositories, venues and page scope.",
                  )}
                </p>
                <button
                  className="button primary"
                  disabled={!!busy || !source.name || !source.url}
                  onClick={() =>
                    run("source-save", () =>
                      send(
                        "/v1/admin/sources" +
                          (source.id ? "/" + source.id : ""),
                        {
                          name: source.name,
                          url: source.url,
                          category: source.category,
                          adapter: source.adapter,
                          config: JSON.parse(source.config),
                          interval_days: 1,
                        },
                        source.id ? "PATCH" : "POST",
                        true,
                      ),
                    )
                  }
                >
                  {pick("保存来源", "Save source")}
                </button>
                {source.id && (
                  <>
                    <label>
                      {pick("历史补采起点", "Backfill from")}
                      <input
                        type="date"
                        value={since}
                        onChange={(e) => setSince(e.target.value)}
                      />
                    </label>
                    <button
                      className="button"
                      disabled={!since || !!busy}
                      onClick={() =>
                        run("backfill", () =>
                          send(
                            "/v1/admin/sources/" + source.id + "/backfill",
                            { since },
                            "POST",
                            true,
                          ),
                        )
                      }
                    >
                      {pick("安排历史补采", "Queue backfill")}
                    </button>
                  </>
                )}
                <button
                  className="text-button"
                  onClick={() =>
                    setSource({
                      id: "",
                      name: "",
                      url: "",
                      category: "official",
                      adapter: "rss",
                      config: "{}",
                    })
                  }
                >
                  {pick("新建另一来源", "Add another source")}
                </button>
              </section>
            </div>
          )}
          {tab === "processing" && (
            <>
            <State loading={operations.loading} error={operations.error} retry={operations.reload}>{operations.data && <OperationsOverview data={operations.data} />}</State>
            <State
              loading={processing.loading}
              error={processing.error}
              retry={processing.reload}
            >
              <div className="button-row">
                <button
                  className="button primary"
                  disabled={!!busy}
                  onClick={() =>
                    run("batch", () =>
                      send("/v1/admin/processing", { limit: 5 }, "POST", true),
                    )
                  }
                >
                  {pick("继续整理 5 项", "Process 5 records")}
                </button>
                <button
                  className="button"
                  onClick={() =>
                    run("brief", () =>
                      send("/v1/admin/briefs", {}, "POST", true),
                    )
                  }
                >
                  {pick("更新今日简报", "Update daily edition")}
                </button>
              </div>
              <div className="ops-status">
                {processing.data?.counts.map((c) => (
                  <span key={c.stage + c.status}>
                    {c.stage} · {c.status} <strong>{c.count}</strong>
                  </span>
                ))}
              </div>
              <table className="ops-table">
                <thead>
                  <tr>
                    <th>{pick("资料", "Record")}</th>
                    <th>{pick("阶段", "Stage")}</th>
                    <th>{pick("状态与说明", "Status")}</th>
                  </tr>
                </thead>
                <tbody>
                  {processing.data?.jobs.map((j) => (
                    <tr key={j.record_id + j.stage}>
                      <td>{j.title}</td>
                      <td>{j.stage}</td>
                      <td>
                        {j.status}
                        <p>{j.error}</p>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </State>
            </>
          )}
          {tab === "model" && currentModel && (
            <section className="ops-form">
              <h2>{pick("生成服务配置", "Generation service")}</h2>
              <label className="inline-field">
                <input
                  type="checkbox"
                  checked={currentModel.enabled}
                  onChange={(e) =>
                    setModel({ ...currentModel, enabled: e.target.checked })
                  }
                />
                {pick("启用自动整理", "Enable organization")}
              </label>
              {(["base_url", "model", "key_env"] as const).map((key) => (
                <label key={key}>
                  {key === "base_url"
                    ? pick("服务地址", "Service URL")
                    : key === "model"
                      ? pick("模型名称", "Model name")
                      : pick("服务器凭证变量名", "Server credential variable")}
                  <input
                    value={currentModel[key]}
                    onChange={(e) =>
                      setModel({ ...currentModel, [key]: e.target.value })
                    }
                  />
                </label>
              ))}
              <label>
                {pick("接口类型", "API style")}
                <select
                  value={currentModel.api_style || "chat_completions"}
                  onChange={(e) =>
                    setModel({
                      ...currentModel,
                      api_style: e.target.value as Model["api_style"],
                    })
                  }
                >
                  <option value="responses">OpenAI Responses</option>
                  <option value="chat_completions">Chat Completions</option>
                </select>
              </label>
              <p className="fine-print">
                {pick(
                  "密钥保存在服务器环境配置中，不会通过页面读取或导出。",
                  "Credentials stay in the server environment and are never returned or exported.",
                )}{" "}
                ·{" "}
                {currentModel.credential_configured
                  ? pick("已配置凭证", "Credential configured")
                  : pick("尚未配置凭证", "Credential missing")}
              </p>
              <div className="button-row">
                <button
                  className="button primary"
                  disabled={!!busy}
                  onClick={() =>
                    run("model-save", () =>
                      send(
                        "/v1/admin/model",
                        {
                          enabled: currentModel.enabled,
                          model: currentModel.model,
                          base_url: currentModel.base_url,
                          key_env: currentModel.key_env,
                          timeout_seconds: currentModel.timeout_seconds,
                          api_style:
                            currentModel.api_style || "chat_completions",
                        },
                        "PATCH",
                        true,
                      ),
                    )
                  }
                >
                  {pick("保存配置", "Save configuration")}
                </button>
                <button
                  className="button"
                  disabled={!!busy}
                  onClick={() =>
                    run("model-test", () =>
                      send("/v1/admin/model", {}, "POST", true),
                    )
                  }
                >
                  {pick("测试已保存配置", "Test saved configuration")}
                </button>
              </div>
            </section>
          )}
          {tab === "relations" && (
            <>
              <RelationshipEditor />
              <State loading={duplicates.loading} error={duplicates.error} retry={duplicates.reload}>
                {duplicates.data && <DuplicateReview items={duplicates.data.items} choose={(primary,other) => {setTarget(primary);setMergeIds(other);setMergeReason("");notify(pick("已选择，请在下方填写判断依据后归并", "Selected. Add a reason in the form below before grouping."));}} />}
              </State>
              <section className="ops-form">
                <h2>
                  {pick(
                    "归并同一事件或对象",
                    "Group identical events or objects",
                  )}
                </h2>
                <p className="muted">
                  {pick(
                    "保留所有原始资料和链接。只有类型与版本一致的记录可以归并，操作可撤销。",
                    "Original records and links are retained. Group matching types and versions; grouping can be undone.",
                  )}
                </p>
                <label>
                  {pick("主记录 ID", "Primary record ID")}
                  <input
                    value={target}
                    onChange={(e) => setTarget(e.target.value)}
                  />
                </label>
                <label>
                  {pick(
                    "其他记录 ID，用逗号分隔",
                    "Other record IDs, comma-separated",
                  )}
                  <input
                    value={mergeIds}
                    onChange={(e) => setMergeIds(e.target.value)}
                  />
                </label>
                <label>
                  {pick("判断依据", "Evidence for grouping")}
                  <textarea
                    value={mergeReason}
                    onChange={(e) => setMergeReason(e.target.value)}
                  />
                </label>
                <button
                  className="button primary"
                  disabled={!target || !mergeIds || !mergeReason || !!busy}
                  onClick={() =>
                    run("merge", () =>
                      send(
                        "/v1/admin/merge",
                        {
                          target_id: target,
                          record_ids: mergeIds
                            .split(",")
                            .map((x) => x.trim())
                            .filter(Boolean),
                          reason: mergeReason,
                        },
                        "POST",
                        true,
                      ),
                    )
                  }
                >
                  {pick("确认归并", "Group records")}
                </button>
              </section>
              <label>
                {pick("分歧处理或撤销依据", "Reason for resolution or undo")}
                <input
                  value={resolution}
                  onChange={(e) => setResolution(e.target.value)}
                />
              </label>
              {queue.data?.conflicts.map((c) => (
                <article className="ops-item" key={c.id}>
                  <h3>
                    {c.field} · {c.record_id}
                  </h3>
                  {c.alternatives.map((a, i) => (
                    <div key={i}>
                      <p>
                        {JSON.stringify(a.value)} · {a.source_url}
                      </p>
                      <button
                        className="button"
                        disabled={!resolution || !!busy}
                        onClick={() =>
                          run("resolve", () =>
                            send(
                              "/v1/admin/conflicts/" + c.id + "/resolve",
                              { choice: i, reason: resolution },
                              "POST",
                              true,
                            ),
                          )
                        }
                      >
                        {pick("采用这项依据", "Use this evidence")}
                      </button>
                    </div>
                  ))}
                </article>
              ))}
              {queue.data?.actions
                .filter((a) => a.status === "applied")
                .map((a) => (
                  <article className="ops-item" key={a.id}>
                    <p>{a.reason}</p>
                    <button
                      className="button"
                      disabled={!resolution || !!busy}
                      onClick={() =>
                        run("undo", () =>
                          send(
                            "/v1/admin/actions/" + a.id + "/undo",
                            { reason: resolution },
                            "POST",
                            true,
                          ),
                        )
                      }
                    >
                      {pick("撤销归并 / 拆分", "Undo grouping")}
                    </button>
                  </article>
                ))}
            </>
          )}
          {tab === "feedback" && (
            <>
              <label>
                {pick("处理结果与依据", "Resolution and evidence")}
                <textarea
                  value={resolution}
                  onChange={(e) => setResolution(e.target.value)}
                />
              </label>
              {queue.data?.feedback.map((f) => (
                <article className="ops-item" key={f.id}>
                  <span className="tag">
                    {f.category} · {f.handling_status}
                  </span>
                  <p>{f.content}</p>
                  {f.resolution && <p>{f.resolution}</p>}
                  <div className="button-row">
                    {[
                      ["reviewing", "处理中", "Reviewing"],
                      ["resolved", "已解决", "Resolved"],
                      ["declined", "暂不处理", "Declined"],
                    ].map(([v, cn, en]) => (
                      <button
                        key={v}
                        className="button"
                        disabled={!resolution || !!busy}
                        onClick={() =>
                          run("feedback", () =>
                            send(
                              "/v1/admin/feedback/" + f.id,
                              { status: v, resolution },
                              "PATCH",
                              true,
                            ),
                          )
                        }
                      >
                        {pick(cn, en)}
                      </button>
                    ))}
                  </div>
                </article>
              ))}
            </>
          )}
        </>
      )}
      {error && (
        <p className="notice error-text" role="alert">
          {error}
        </p>
      )}
    </>
  );
}
