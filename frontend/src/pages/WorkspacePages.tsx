import ResearchComparison, {
  type ResearchComparisonData,
} from "../components/workspace/ResearchComparison";
import { useEffect, useState, type FormEvent } from "react";
import { FollowingUpdates } from "./KnowledgeReading";
import { Link, useSearchParams } from "react-router-dom";
import {
  BASE,
  formatValue,
  request,
  send,
  useRemote,
  type Dossier,
  type RecordItem,
  type SearchResult,
  type Source,
  type Verification,
} from "../api/knowledge";
import {
  dateText,
  Icon,
  PageHeading,
  RecordCard,
  SourceLink,
  State,
  TOPICS,
  titleOf,
  useWorkspace,
} from "../components/workspace/UI";

export function Collection() {
  const { pick, collection, toggleCollection } = useWorkspace();
  const [view, setView] = useState("save");
  const entries = collection.filter((x) => x.action === view);
  const ids = entries
    .filter((x) => !x.record_id.startsWith("topic:"))
    .map((x) => x.record_id);
  const topics = entries
    .filter((x) => x.record_id.startsWith("topic:"))
    .map((x) => x.record_id.slice(6));
  const [items, setItems] = useState<RecordItem[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [reload, setReload] = useState(0);
  const key = ids.join(",");
  useEffect(() => {
    const controller = new AbortController();
    setError("");
    setItems([]);
    setLoading(!!key);
    if (!key) return;
    const chunks: string[][] = [];
    const all = key.split(",");
    for (let i = 0; i < all.length; i += 100)
      chunks.push(all.slice(i, i + 100));
    Promise.all(
      chunks.map((chunk) =>
        request<SearchResult>("/v1/records?limit=100&ids=" + chunk.join(","), {
          signal: controller.signal,
        }),
      ),
    )
      .then((results) => setItems(results.flatMap((r) => r.items)))
      .catch((e) => {
        if (!controller.signal.aborted) setError(e.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [key, reload]);
  return (
    <>
      <PageHeading
        eyebrow="YOUR KNOWLEDGE, CONNECTED"
        title={pick(
          "留住值得继续探索的事。",
          "Keep what sparks your curiosity.",
        )}
        description={pick(
          "收藏资料，关注变化。你的研究和实践，从这里继续。",
          "Save useful records and follow their progress. Pick up where you left off.",
        )}
      >
        <button className="button account-unavailable" type="button" disabled>
          <Icon name="user" size={17} />
          {pick("账户与同步", "Account & sync")}
          <small className="coming-soon-badge">
            {pick("待开放", "Coming soon")}
          </small>
        </button>
      </PageHeading>
      <div className="explore-tabs">
        <div>
          {[
            ["save", "我的收藏", "Saved"],
            ["follow", "关注更新", "Following"],
          ].map(([value, cn, en]) => (
            <button
              key={value}
              className={view === value ? "active" : ""}
              onClick={() => setView(value)}
            >
              {pick(cn, en)}{" "}
              <span className="count">
                {collection.filter((x) => x.action === value).length}
              </span>
            </button>
          ))}
        </div>
        <span className="muted">
          {pick("默认保存在当前浏览器", "Stored in this browser by default")}
        </span>
      </div>
      {!!topics.length && (
        <section className="followed-topics">
          <h2>{pick("关注的方向", "Topics you follow")}</h2>
          <div>
            {topics.map((topic) => (
              <div className="topic-tile" key={topic}>
                <Link to={`/information?topic=${topic}`}>
                  <Icon name="bell" size={18} />
                  {TOPICS[topic] ? pick(...TOPICS[topic]) : topic}
                  <Icon name="arrow" size={17} />
                </Link>
                <button
                  className="icon-button"
                  aria-label={pick("取消关注", "Unfollow")}
                  onClick={() => toggleCollection("topic:" + topic, "follow")}
                >
                  <Icon name="close" size={16} />
                </button>
              </div>
            ))}
          </div>
        </section>
      )}
      {view === "follow" && <FollowingUpdates />}
      <State
        loading={loading}
        error={error}
        retry={() => setReload((x) => x + 1)}
      >
        {!items.length && !topics.length ? (
          <div className="empty-state collection-empty">
            <span className="large-symbol">
              <Icon name="bookmark" size={32} />
            </span>
            <h2>
              {pick(
                "为下一个想法，留一个位置。",
                "Make room for your next idea.",
              )}
            </h2>
            <p>
              {pick(
                "在动态或资源卡片上点击收藏，资料就会出现在这里。",
                "Save a news item, paper or resource to find it here.",
              )}
            </p>
            <Link to="/apps" className="button primary">
              {pick("探索资源", "Explore resources")}
              <Icon name="arrow" size={17} />
            </Link>
          </div>
        ) : (
          <div className="record-grid">
            {items.map((item) => (
              <div key={item.id}>
                {view === "follow" && (
                  <p className="follow-update">
                    <Icon name="clock" size={14} />
                    {pick("资料最近变更", "Last record change")} ·{" "}
                    {dateText(item.updated_at)}
                  </p>
                )}
                <RecordCard record={item} />
              </div>
            ))}
          </div>
        )}
        {ids.length > items.length && !loading && (
          <p className="fine-print">
            {pick(
              "部分保存记录可能已下架，公开列表不再展示。",
              "Some saved records may have been withdrawn.",
            )}
          </p>
        )}
      </State>
    </>
  );
}

export function Compare() {
  const { zh, pick, notify } = useWorkspace();
  const [research, setResearch] = useState<ResearchComparisonData | null>(null);
  const [params] = useSearchParams();
  const key = params.get("ids") || "";
  const [items, setItems] = useState<Dossier[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    setItems([]);
    send<{ items: Dossier[]; research_comparison: ResearchComparisonData }>(
      "/v1/compare",
      { ids: key.split(",") },
    )
      .then((r) => {
        if (active) {
          setItems(r.items);
          setResearch(r.research_comparison);
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [key, revision]);
  const fields = [
    ["capabilities", "能力", "Capabilities"],
    ["limitations", "限制", "Limitations"],
    ["deployment", "使用与部署", "Deployment"],
    ["hardware", "硬件要求", "Hardware"],
    ["license", "许可证", "License"],
    ["cost", "费用", "Cost"],
    ["language", "语言", "Language"],
    ["dataset", "数据", "Dataset"],
    ["metric", "评测指标", "Metrics"],
    ["protocol", "评测设置", "Evaluation settings"],
  ];
  const copy = async () => {
    const text = [
      "# FieldToFit · " + pick("资源对比", "Resource comparison"),
      "",
      ...items.flatMap((item) => [
        "## " + titleOf(item, zh),
        item.canonical_url,
        `Version: ${item.version || "Unknown"} · Checked: ${item.checked_at || "Unknown"}`,
        ...fields.map(
          ([key, cn, en]) =>
            `${pick(cn, en)}: ${item.facts[key] ? formatValue(item.facts[key].value) + " [" + item.facts[key].status + "] " + (item.facts[key].source_url || "") : pick("未知", "Unknown")}`,
        ),
        "",
      ]),
    ].join("\n");
    try {
      await navigator.clipboard.writeText(text);
      notify(pick("带来源的对比已复制", "Comparison copied with sources"));
    } catch {
      notify(
        pick(
          "复制失败，请检查浏览器权限",
          "Copy failed; check browser permissions",
        ),
      );
    }
  };
  return (
    <>
      <PageHeading
        eyebrow="MAKE AN INFORMED CHOICE"
        title={pick("看清差异，再做选择。", "Understand the difference.")}
        description={pick(
          "把能力、条件与证据放在一起。缺失的信息保留为未知。",
          "Compare capabilities, conditions and evidence. Missing facts stay unknown.",
        )}
      >
        <button className="button" onClick={copy} disabled={!items.length}>
          <Icon name="copy" size={17} />
          {pick("复制对比", "Copy comparison")}
        </button>
      </PageHeading>
      <State
        loading={loading}
        error={error}
        retry={() => setRevision((r) => r + 1)}
      >
        {!!items.length && (
          <>
            <ResearchComparison data={research} />
            <div className="notice">
              <Icon name="info" />
              {pick(
                "来源热度与任务适配分别判断。比较论文或基准时，请确认数据、指标、版本和评测设置一致。",
                "Popularity and suitability are separate. Verify equivalent data, metrics, versions and evaluation settings.",
              )}
            </div>
            <div className="comparison-scroll">
              <table className="comparison-table">
                <thead>
                  <tr>
                    <th>{pick("对比维度", "Compare")}</th>
                    {items.map((item) => (
                      <th key={item.id}>
                        <span className="record-symbol">
                          <Icon name="code" />
                        </span>
                        <Link to={`/records/${item.id}`}>
                          {titleOf(item, zh)}
                        </Link>
                        <SourceLink url={item.canonical_url}>
                          {pick("原始来源", "Original source")}
                          <Icon name="up" size={14} />
                        </SourceLink>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <th>{pick("版本", "Version")}</th>
                    {items.map((item) => (
                      <td key={item.id}>
                        {item.version || (
                          <span className="unknown">
                            {pick("未知", "Unknown")}
                          </span>
                        )}
                      </td>
                    ))}
                  </tr>
                  {fields.map(([key, cn, en]) => (
                    <tr key={key}>
                      <th>{pick(cn, en)}</th>
                      {items.map((item) => (
                        <td key={item.id}>
                          {item.facts[key] ? (
                            <>
                              <p>{formatValue(item.facts[key].value)}</p>
                              <SourceLink
                                url={item.facts[key].source_url}
                                className="fact-source"
                              >
                                {item.facts[key].status}
                                <Icon name="up" size={12} />
                              </SourceLink>
                            </>
                          ) : (
                            <span className="unknown">
                              {pick("待核实", "Not yet verified")}
                            </span>
                          )}
                        </td>
                      ))}
                    </tr>
                  ))}
                  <tr>
                    <th>{pick("实测记录", "Verification")}</th>
                    {items.map((item) => (
                      <td key={item.id}>
                        {item.verifications.length
                          ? `${item.verifications.length} ${pick("项，详见记录", "scoped checks")}`
                          : pick("尚无实测记录", "No verification recorded")}
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          </>
        )}
      </State>
      <Link to="/apps" className="back-link">
        {pick("继续寻找资源", "Explore more resources")}
        <Icon name="arrow" size={16} />
      </Link>
    </>
  );
}

export function Sources() {
  const { zh, pick } = useWorkspace();
  const result = useRemote<{ items: Source[] }>("/v1/sources");
  const statusName = (s: string) =>
    s === "success"
      ? pick("最近采集成功", "Last run succeeded")
      : s === "running"
        ? pick("采集中", "Running")
        : s === "pending"
          ? pick("等待首次采集", "Awaiting first run")
          : s === "partial"
            ? pick("部分完成", "Partially completed")
            : pick("需要重试", "Needs attention");
  return (
    <>
      <PageHeading
        eyebrow="TRACEABLE BY DESIGN"
        title={pick("每一条资料，都有来处。", "Every record has a source.")}
        description={pick(
          "来源检查与更新周期统一为 1 天。这里展示实际接入状态和最近成功时间。",
          "Every source is checked once per day. See actual collection status and last successful updates.",
        )}
      />
      <div className="source-principles">
        {[
          [
            "01",
            "回到原始材料",
            "Go to the original",
            "官方公告、论文和项目文档支撑事实。",
            "Official announcements, papers and documentation support claims.",
          ],
          [
            "02",
            "保留未知与分歧",
            "Keep uncertainty visible",
            "采集失败、资料缺失和未经实测会明确标识。",
            "Failures, missing material and untested claims stay visible.",
          ],
          [
            "03",
            "每天继续更新",
            "Keep checking daily",
            "跟踪变化，并保留版本和历史依据。",
            "Track changes and retain versions and evidence.",
          ],
        ].map(([n, cn, en, dcn, den]) => (
          <div key={n}>
            <span>{n}</span>
            <h3>{pick(cn, en)}</h3>
            <p>{pick(dcn, den)}</p>
          </div>
        ))}
      </div>
      <State
        loading={result.loading}
        error={result.error}
        retry={result.reload}
      >
        <div className="source-list">
          {result.data?.items.map((s) => (
            <article className="source-row" key={s.id}>
              <span
                className={`record-symbol ${s.category === "research" ? "paper" : ""}`}
              >
                <Icon name="source" />
              </span>
              <div className="source-name">
                <SourceLink url={s.url}>
                  {s.name}
                  <Icon name="up" size={15} />
                </SourceLink>
                <span>
                  {s.category} · {pick("每 1 天", "Every 1 day")}
                </span>
              </div>
              <span className={`tag ${s.enabled ? s.status : "disabled"}`}>
                {s.enabled ? statusName(s.status) : pick("已停用", "Disabled")}
              </span>
              <div className="source-time">
                <small>{pick("最近成功", "Last success")}</small>
                <span>{dateText(s.last_success_at, zh)}</span>
              </div>
            </article>
          ))}
        </div>
      </State>
    </>
  );
}

export function Connect() {
  const { pick, notify } = useWorkspace();
  const [token, setToken] = useState("");
  const [testing, setTesting] = useState(false);
  const [connection, setConnection] = useState("");
  const endpoint = new URL(BASE + "/mcp", window.location.origin).href;
  const config = JSON.stringify(
    { mcpServers: { fieldtofit: { type: "http", url: endpoint } } },
    null,
    2,
  );
  const tools = [
    ["search", "查找动态、论文和资源", "Search news, papers and resources"],
    [
      "get_record",
      "读取档案、关系和验证状态",
      "Read dossiers and verification status",
    ],
    [
      "read_evidence",
      "按需读取详细原始材料",
      "Read original indexed materials",
    ],
    ["compare", "比较候选方案和使用条件", "Compare resources and conditions"],
    [
      "task_context",
      "按研究、学习和开发任务组织资料",
      "Organize context for a task",
    ],
    ["changes", "获取每日更新与变更记录", "Retrieve daily changes"],
    ["sources", "检查覆盖范围和更新时间", "Check coverage and freshness"],
  ];
  const test = async () => {
    setTesting(true);
    setConnection("");
    try {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
        Accept: "application/json, text/event-stream",
      };
      const saved = sessionStorage.getItem("fieldtofit-read-token");
      if (saved) headers.Authorization = "Bearer " + saved;
      const response = await fetch(endpoint, {
        method: "POST",
        headers,
        body: JSON.stringify({
          jsonrpc: "2.0",
          id: 1,
          method: "initialize",
          params: {
            protocolVersion: "2025-11-25",
            capabilities: {},
            clientInfo: { name: "fieldtofit-web-check", version: "1.0" },
          },
        }),
      });
      const r = await response.json();
      if (!response.ok || r.error)
        throw new Error(r.error?.message || r.error || "Connection failed");
      setConnection(
        pick("连接成功 · ", "Connected · ") +
          r.result.serverInfo.name +
          " " +
          r.result.serverInfo.version,
      );
    } catch (e) {
      setConnection((e as Error).message);
    } finally {
      setTesting(false);
    }
  };
  return (
    <>
      <PageHeading
        eyebrow="BUILT FOR PEOPLE. READY FOR AI."
        title={pick(
          "把 FieldToFit，带进你的 AI 工作流。",
          "Bring FieldToFit to your AI workflow.",
        )}
        description={pick(
          "通过 MCP 或查询接口，让 AI 读取同一套资料、来源与条件。",
          "Connect through MCP or the API to read the same records, evidence and conditions.",
        )}
      />
      <div className="connect-hero">
        <div>
          <span className="tag">MCP · STREAMABLE HTTP</span>
          <h2>
            {pick("让每一次回答，多一份依据。", "Give every answer a source.")}
          </h2>
          <p>
            {pick(
              "先找候选，再读档案，最后回到原文。AI 可以继续读取详细材料，识别版本和未知条件。",
              "Find candidates, read dossiers and follow original material. Keep versions and unknown conditions explicit.",
            )}
          </p>
          <button className="button inverted" onClick={test} disabled={testing}>
            {testing
              ? pick("正在检查…", "Checking…")
              : pick("测试 MCP 连接", "Test MCP connection")}
            <Icon name="arrow" size={17} />
          </button>
          {connection && (
            <p role="status" className="connection-result">
              {connection}
            </p>
          )}
        </div>
        <div className="connection-visual" aria-hidden="true">
          <span>m.</span>
          <i />
          <div>
            <Icon name="code" size={38} />
          </div>
        </div>
      </div>
      <div className="connect-layout">
        <section>
          <div className="section-title">
            <h2>{pick("连接配置", "Connection details")}</h2>
            <button
              className="text-button"
              onClick={() =>
                navigator.clipboard
                  .writeText(config)
                  .then(() =>
                    notify(pick("配置已复制", "Configuration copied")),
                  )
                  .catch(() =>
                    notify(pick("请手动复制配置", "Please copy manually")),
                  )
              }
            >
              <Icon name="copy" size={16} />
              {pick("复制", "Copy")}
            </button>
          </div>
          <p className="muted">
            {pick(
              "在支持 Streamable HTTP 的客户端中填写以下地址。配置示例的字段名称可能因客户端而异。",
              "Use this endpoint in a Streamable HTTP client. Configuration field names vary by client.",
            )}
          </p>
          <div className="endpoint-line">{endpoint}</div>
          <pre className="code-block">{config}</pre>
          <p className="fine-print">
            {pick(
              "私有部署需附带 Authorization: Bearer 读取令牌。读取权限不能进行管理或发送操作。",
              "Private deployments require an Authorization: Bearer read token. Read credentials cannot administer or send.",
            )}
          </p>
          <h3 className="spaced-heading">
            {pick("浏览器访问令牌", "Browser access token")}
          </h3>
          <form
            className="token-form"
            onSubmit={(e) => {
              e.preventDefault();
              if (token) sessionStorage.setItem("fieldtofit-read-token", token);
              else sessionStorage.removeItem("fieldtofit-read-token");
              notify(
                pick(
                  "设置已保存，请重新打开资料页",
                  "Settings saved. Reopen a records page.",
                ),
              );
              setToken("");
            }}
          >
            <input
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              autoComplete="off"
              aria-label={pick("读取令牌", "Read token")}
              placeholder={pick(
                "仅私有部署需要，留空可清除",
                "Private deployments only; empty to clear",
              )}
            />
            <button className="button">{pick("保存", "Save")}</button>
          </form>
        </section>
        <section>
          <h2>{pick("可调用的能力", "Available tools")}</h2>
          <div className="mcp-tool-list">
            {tools.map(([name, cn, en]) => (
              <div key={name}>
                <code>{name}</code>
                <p>{pick(cn, en)}</p>
                <span>READ ONLY</span>
              </div>
            ))}
          </div>
        </section>
      </div>
      <section className="example-prompts">
        <h2>{pick("从一个真实问题开始", "Start with a real question")}</h2>
        <div>
          {[
            [
              "研究者",
              "Researcher",
              "查找近期论文，比较方法和原文依据。",
              "Find recent papers and compare methods with citations.",
            ],
            [
              "工程师",
              "Engineer",
              "为本地 Python 项目找 PDF 工具，核查部署与许可证。",
              "Find PDF tools for local Python; check deployment and licensing.",
            ],
            [
              "研究生",
              "Graduate",
              "找到论文代码与数据，列出最小复现环境。",
              "Find a paper’s code and data and a minimal reproduction environment.",
            ],
            [
              "学生",
              "Student",
              "整理前置知识、官方教程和最小实践。",
              "Gather prerequisites, official tutorials and a minimal exercise.",
            ],
          ].map(([cn, en, qcn, qen]) => (
            <article key={en}>
              <span className="tag">{pick(cn, en)}</span>
              <p>{pick(qcn, qen)}</p>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}

export function Cases() {
  const { zh, pick } = useWorkspace();
  const result = useRemote<{ items: Verification[] }>("/v1/cases");
  return (
    <>
      <PageHeading
        eyebrow="FROM KNOWLEDGE TO PRACTICE"
        title={pick("每一次验证，都写清条件。", "Every result needs context.")}
        description={pick(
          "查看实际记录的环境、步骤、结果与限制。最小示例和完整实验复现分别说明。",
          "Inspect recorded environments, steps, outcomes and limitations. Minimal examples are distinct from full reproductions.",
        )}
      />
      <State
        loading={result.loading}
        error={result.error}
        retry={result.reload}
      >
        {result.data?.items.length ? (
          <div className="case-grid">
            {result.data.items.map((v) => (
              <article className="case-card" key={v.id}>
                <div>
                  <span className={`tag ${v.result}`}>
                    {v.result === "passed"
                      ? pick("指定检查通过", "Scoped check passed")
                      : v.result === "failed"
                        ? pick("检查失败", "Failed")
                        : pick("未运行", "Not run")}
                  </span>
                  <span className="muted">{dateText(v.checked_at, zh)}</span>
                </div>
                <h2>{v.title}</h2>
                <p>{v.environment}</p>
                <details>
                  <summary>{pick("过程与结果", "Steps & outcome")}</summary>
                  <pre>{v.steps}</pre>
                  <p>{v.output}</p>
                  <p className="notice">{v.limitations}</p>
                </details>
                <Link className="text-button" to={`/records/${v.record_id}`}>
                  {v.record_title || pick("关联资料", "Related dossier")}
                  <Icon name="arrow" size={16} />
                </Link>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <span className="large-symbol">
              <Icon name="check" size={30} />
            </span>
            <h2>
              {pick(
                "真实记录，从第一次验证开始。",
                "Real evidence starts with a recorded check.",
              )}
            </h2>
            <p>
              {pick(
                "当前还没有已记录案例。完成核验后，环境、步骤和结果会出现在这里。",
                "No cases are recorded yet. Environments, steps and outcomes will appear here.",
              )}
            </p>
            <Link className="button" to="/apps">
              {pick("先探索资源", "Explore resources")}
              <Icon name="arrow" size={16} />
            </Link>
          </div>
        )}
      </State>
    </>
  );
}

export function Account() {
  const { pick } = useWorkspace();
  return (
    <>
      <PageHeading
        eyebrow="YOUR PERSONAL LIBRARY"
        title={pick("我的账户", "My account")}
        description={pick(
          "账户功能准备中，暂未开放注册与登录。",
          "Accounts are coming soon. Registration and sign-in are not yet available.",
        )}
      />
      <section
        className="account-card account-coming-soon"
        aria-labelledby="account-coming-soon-title"
      >
        <span className="account-placeholder-icon">
          <Icon name="user" size={30} />
        </span>
        <h2 id="account-coming-soon-title">{pick("待开放", "Coming soon")}</h2>
        <p>
          {pick(
            "你可以直接浏览、检索和收藏资料。收藏与关注保存在当前浏览器，账户同步将在后续开放。",
            "Browse, search and save records without an account. Saves and follows stay in this browser; account sync will be available later.",
          )}
        </p>
        <Link className="button" to="/collection">
          <Icon name="bookmark" size={17} />
          {pick("查看我的收藏", "View my collection")}
          <Icon name="arrow" size={16} />
        </Link>
      </section>
    </>
  );
}

export function Manage() {
  const { pick, notify } = useWorkspace();
  const [authed, setAuthed] = useState(
    !!sessionStorage.getItem("fieldtofit-admin-password"),
  );
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const result = useRemote<{
    items: Source[];
    feedback: { id: number; category: string; content: string }[];
  }>(authed ? "/v1/admin/sources" : null, true);
  const [rid, setRid] = useState("");
  const [edit, setEdit] = useState("");
  const [reason, setReason] = useState("");
  const login = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await send("/admin/verify", { password });
      sessionStorage.setItem("fieldtofit-admin-password", password);
      setAuthed(true);
      setPassword("");
    } catch (e) {
      setError((e as Error).message);
    }
  };
  const run = async (sid: string) => {
    setBusy(sid);
    try {
      const r = await send<{ status: string }>(
        `/v1/admin/sources/${sid}/run`,
        {},
        "POST",
        true,
      );
      notify(pick("采集结果：", "Collection result: ") + r.status);
      result.reload();
    } catch (e) {
      notify((e as Error).message);
    } finally {
      setBusy("");
    }
  };
  const load = async () => {
    try {
      const d = await request<Dossier>("/v1/records/" + rid);
      setEdit(
        JSON.stringify(
          {
            title: d.title,
            title_zh: d.title_zh,
            summary: d.summary,
            summary_zh: d.summary_zh,
            topics: d.topics,
            facts: d.facts,
            version: d.version,
            completeness: d.completeness,
            status: d.status,
          },
          null,
          2,
        ),
      );
    } catch (e) {
      notify((e as Error).message);
    }
  };
  const save = async () => {
    try {
      await send(
        "/v1/admin/records/" + rid,
        { ...JSON.parse(edit), reason },
        "PATCH",
        true,
      );
      notify(
        pick("资料已更新，两端同步生效", "Dossier updated for people and AI"),
      );
    } catch (e) {
      notify((e as Error).message);
    }
  };
  return (
    <>
      <PageHeading
        eyebrow="KEEP THE KNOWLEDGE RELIABLE"
        title={pick("资料与运行管理", "Knowledge operations")}
        description={pick(
          "管理来源、检查采集结果、修正资料并查看用户反馈。",
          "Manage sources, inspect collection, correct records and review feedback.",
        )}
      >
        <Link className="button" to="/admin/curation">
          {pick("策展与简报", "Curation & newsletter")}
          <Icon name="arrow" size={17} />
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
              autoComplete="current-password"
              required
            />
          </label>
          {error && (
            <p className="error-text" role="alert">
              {error}
            </p>
          )}
          <button className="button primary">
            {pick("进入管理", "Sign in")}
          </button>
        </form>
      ) : (
        <>
          <div className="section-title">
            <h2>{pick("每日采集", "Daily collection")}</h2>
            <button
              className="text-button"
              onClick={() => {
                sessionStorage.removeItem("fieldtofit-admin-password");
                setAuthed(false);
              }}
            >
              {pick("退出管理", "Sign out")}
            </button>
          </div>
          <State
            loading={result.loading}
            error={result.error}
            retry={result.reload}
          >
            <div className="source-list">
              {result.data?.items.map((s) => (
                <article className="source-row" key={s.id}>
                  <div className="source-name">
                    <strong>{s.name}</strong>
                    <span>
                      {s.status} · {pick("每 1 天", "Every 1 day")}
                    </span>
                    {s.error && <small className="error-text">{s.error}</small>}
                  </div>
                  <button
                    className="button subtle"
                    onClick={() =>
                      send(
                        `/v1/admin/sources/${s.id}`,
                        { enabled: !s.enabled },
                        "PATCH",
                        true,
                      )
                        .then(result.reload)
                        .catch((e) => notify(e.message))
                    }
                  >
                    {s.enabled
                      ? pick("停用", "Disable")
                      : pick("启用", "Enable")}
                  </button>
                  <button
                    className="button"
                    disabled={!!busy || !s.enabled}
                    onClick={() => run(s.id)}
                  >
                    {busy === s.id
                      ? pick("采集中…", "Collecting…")
                      : pick("手动重试", "Retry now")}
                  </button>
                </article>
              ))}
            </div>
            <section className="editor-panel">
              <h2>{pick("事实纠错", "Correct a dossier")}</h2>
              <p className="muted">
                {pick(
                  "填写详情页中的稳定 ID。修改需要记录依据，事实字段保留来源与状态。",
                  "Use the stable ID from a dossier. Corrections require a reason and evidence.",
                )}
              </p>
              <div className="token-form">
                <input
                  value={rid}
                  onChange={(e) => setRid(e.target.value)}
                  placeholder={pick("资料 ID", "Record ID")}
                  aria-label={pick("资料 ID", "Record ID")}
                />
                <button className="button" onClick={load} disabled={!rid}>
                  {pick("读取", "Load")}
                </button>
                <button
                  className="button"
                  disabled={!rid || !!busy}
                  onClick={async () => {
                    setBusy("enrich");
                    try {
                      await send(
                        `/v1/admin/records/${rid}/enrich`,
                        {},
                        "POST",
                        true,
                      );
                      notify(
                        pick("详细材料已获取", "Source material retrieved"),
                      );
                    } catch (e) {
                      notify((e as Error).message);
                    } finally {
                      setBusy("");
                    }
                  }}
                >
                  {pick("获取原文", "Fetch material")}
                </button>
              </div>
              {edit && (
                <>
                  <textarea
                    className="record-editor"
                    value={edit}
                    onChange={(e) => setEdit(e.target.value)}
                    aria-label={pick("档案内容", "Dossier data")}
                  />
                  <label>
                    {pick("修改依据", "Reason for correction")}
                    <input
                      value={reason}
                      onChange={(e) => setReason(e.target.value)}
                      required
                    />
                  </label>
                  <button
                    className="button primary"
                    disabled={!reason.trim()}
                    onClick={save}
                  >
                    {pick("保存修改", "Save changes")}
                  </button>
                </>
              )}
            </section>
            <section className="feedback-inbox">
              <h2>{pick("用户反馈", "User feedback")}</h2>
              {result.data?.feedback.length ? (
                result.data.feedback.map((f) => (
                  <article key={f.id}>
                    <span className="tag">{f.category}</span>
                    <p>{f.content}</p>
                  </article>
                ))
              ) : (
                <p className="muted">
                  {pick("暂时没有反馈。", "No feedback yet.")}
                </p>
              )}
            </section>
          </State>
        </>
      )}
    </>
  );
}

export function Feedback() {
  const { pick, notify } = useWorkspace();
  const [content, setContent] = useState("");
  const [params] = useSearchParams();
  const [category, setCategory] = useState(["missing","correction"].includes(params.get("category")||"")?params.get("category")!:"use_case");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await send("/v1/feedback", { content, category });
      setContent("");
      notify(
        pick(
          "反馈已记录，谢谢你补充真实使用场景。",
          "Feedback recorded. Thank you for sharing your experience.",
        ),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <PageHeading
        eyebrow="BUILT AROUND REAL QUESTIONS"
        title={pick(
          "你遇到的问题，值得被解决。",
          "Tell us what you’re working on.",
        )}
        description={pick(
          "分享缺失的资料、发现的错误，或一次实际使用的结果。",
          "Share missing resources, corrections or a real task outcome.",
        )}
      />
      <form className="account-card feedback-card" onSubmit={submit}>
        <label>
          {pick("反馈类型", "Feedback type")}
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            {[
              ["use_case", "实际需求", "A real need"],
              ["missing", "推荐资源 / 缺失资料", "Recommend / missing resource"],
              ["correction", "事实错误", "Correction"],
              ["success", "成功使用", "Successful use"],
              ["failure", "遇到问题", "Something failed"],
              ["reuse", "再次使用", "Repeat use"],
            ].map(([v, cn, en]) => (
              <option value={v} key={v}>
                {pick(cn, en)}
              </option>
            ))}
          </select>
        </label>
        <label>
          {pick("具体情况", "Your experience")}
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            required
            maxLength={2000}
            placeholder={pick(
              "当时想完成什么？找到了什么，还缺少什么？",
              "What were you trying to do? What helped, and what was missing?",
            )}
          />
        </label>
        <p className="fine-print">
          {pick(
            "无需提供私人项目内容或任何凭证。",
            "No private project content or credentials are needed.",
          )}
        </p>
        {error && (
          <p className="error-text" role="alert">
            {error}
          </p>
        )}
        <button className="button primary" disabled={busy || !content.trim()}>
          {pick("提交反馈", "Send feedback")}
          <Icon name="arrow" size={17} />
        </button>
      </form>
    </>
  );
}
export function NotFound() {
  const { pick } = useWorkspace();
  return (
    <div className="empty-state">
      <span className="eyebrow">404</span>
      <h1>{pick("这一页暂时找不到。", "This page could not be found.")}</h1>
      <Link className="button primary" to="/information">
        {pick("回到信息页", "Back to information")}
      </Link>
    </div>
  );
}
