import ResearchComparison, {
  type ResearchComparisonData,
} from "../components/workspace/ResearchComparison";
import { useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  send,
  useRemote,
  formatValue,
  type TaskPack,
  type RecordItem,
  type Evidence,
} from "../api/knowledge";
import {
  Icon,
  PageHeading,
  SourceLink,
  useWorkspace,
} from "../components/workspace/UI";

type Packet = {
  record_id: string;
  title: string;
  version: string;
  steps: {
    type: string;
    instruction: unknown;
    source_url: string;
    status: string;
    version_matches: boolean;
  }[];
  materials: Evidence[];
  missing_materials: string[];
};
type DetailedPack = TaskPack & {
  research_comparison?: ResearchComparisonData;
  constraints: Record<string, unknown>;
  interpretation: { retrieval_mode: string; warning: string };
  material_packets: Packet[];
  deliverables: string[];
  generated_at: string;
  background: string;
};
type Reading = {
  comparison?: ResearchComparisonData;
  goal: string;
  items: {
    id: string;
    title: string;
    title_zh: string;
    source_url: string;
    research: Record<string, unknown>;
    bibtex: string;
  }[];
  bibtex: string;
  outline: {
    sections: {
      title: string;
      points: { text: string; source_url: string; locator: string }[];
    }[];
  } | null;
  scope: string;
};
const labels: Record<string, string> = {
  deployment: "部署方式",
  language: "语言",
  platform: "平台",
  hardware_vram_gb: "显存",
  cost_monthly_usd: "每月费用",
  license: "许可证",
  usage: "使用步骤",
  extension: "扩展入口",
  dependencies: "依赖",
  method: "方法",
  experiments: "实验",
  limitations: "局限",
  hardware: "运行环境",
  dataset: "数据",
  protocol: "评测条件",
  prerequisites: "前置知识",
  capabilities: "能力",
};
export function saveText(name: string, text: string, type = "text/markdown") {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function printable(pack: DetailedPack) {
  return (
    `# ${pack.goal}\n\n${pack.scope}\n\n${JSON.stringify(pack.constraints)}\n\n背景：${pack.background}\n\n${pack.deliverables.map((d) => "- " + d).join("\n")}\n` +
    pack.material_packets
      .map(
        (p) =>
          `\n## ${p.title}\n版本：${p.version || "未知"}\n` +
          p.steps
            .map(
              (s) =>
                `- ${labels[s.type] || s.type}：${formatValue(s.instruction)}\n  来源：${s.source_url}`,
            )
            .join("\n") +
          "\n" +
          p.materials
            .map(
              (m) => `- [${m.title}](${m.url}) · ${m.locator} · ${m.coverage}`,
            )
            .join("\n") +
          `\n缺失材料：${p.missing_materials.join("、")}\n`,
      )
      .join("\n")
  );
}

export default function TaskWorkbench() {
  const { pick, notify } = useWorkspace();
  const [params] = useSearchParams();
  const [goal, setGoal] = useState(params.get("q") || "");
  const [persona, setPersona] = useState("engineer");
  const [background, setBackground] = useState("");
  const [deployment, setDeployment] = useState("");
  const [language, setLanguage] = useState("");
  const [platform, setPlatform] = useState("");
  const [vram, setVram] = useState("");
  const [cost, setCost] = useState("");
  const [enhanced, setEnhanced] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [pack, setPack] = useState<DetailedPack | null>(null);
  const [reading, setReading] = useState<Reading | null>(null);
  const capabilities = useRemote<{ generation_available: boolean }>(
    "/v1/capabilities",
  );
  const build = async (e?: FormEvent, offset = 0) => {
    e?.preventDefault();
    setBusy(true);
    setError("");
    setReading(null);
    const constraints: Record<string, unknown> = {};
    if (deployment) constraints.deployment = deployment;
    if (language) constraints.language = language;
    if (platform) constraints.platform = platform;
    if (vram) constraints.hardware_vram_gb = { max: Number(vram), unit: "GB" };
    if (cost)
      constraints.cost_monthly_usd = { max: Number(cost), unit: "USD/month" };
    try {
      setPack(
        await send<DetailedPack>("/v1/task", {
          goal,
          persona,
          background,
          constraints,
          enhanced,
          offset,
        }),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  const makeReading = async () => {
    if (!pack) return;
    setBusy(true);
    setError("");
    try {
      setReading(
        await send<Reading>("/v1/research", {
          goal: pack.goal,
          background: pack.background,
          ids: pack.candidates
            .filter((x) => x.kind === "paper")
            .slice(0, 20)
            .map((x) => x.id),
          enhanced,
        }),
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
        eyebrow="FROM QUESTION TO PRACTICE"
        title={pick(
          "把问题，变成有依据的下一步。",
          "Turn your question into an informed next step.",
        )}
        description={pick(
          "描述目标和条件，查看候选、原文材料与行动步骤。未知条件会明确保留。",
          "Describe a goal and constraints. Review candidates, source materials and steps, with unknowns kept visible.",
        )}
      />
      <form className="task-form" onSubmit={build}>
        <div className="persona-row">
          {[
            ["engineer", "工程开发", "Engineering"],
            ["researcher", "研究探索", "Research"],
            ["graduate", "论文复现", "Reproduction"],
            ["student", "学习实践", "Learning"],
          ].map(([v, cn, en]) => (
            <button
              type="button"
              key={v}
              className={persona === v ? "active" : ""}
              onClick={() => setPersona(v)}
            >
              {pick(cn, en)}
            </button>
          ))}
        </div>
        <label>
          {pick("想完成什么？", "What do you want to accomplish?")}
          <textarea
            required
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            maxLength={2000}
            placeholder={pick(
              "例如：为本地 Python 项目选择中文 PDF 处理方案",
              "For example: choose Chinese PDF processing tools for a local Python project",
            )}
          />
        </label>
        <label>
          {pick("已有基础和环境", "Background and environment")}
          <input
            value={background}
            onChange={(e) => setBackground(e.target.value)}
            maxLength={3000}
            placeholder={pick(
              "例如：熟悉 Python，已有一批扫描件，使用 Mac",
              "For example: familiar with Python, scanned documents, on a Mac",
            )}
          />
        </label>
        <div className="constraint-grid">
          <label>
            {pick("部署", "Deployment")}
            <select
              value={deployment}
              onChange={(e) => setDeployment(e.target.value)}
            >
              <option value="">{pick("不限定", "Any")}</option>
              <option value="local">{pick("本地", "Local")}</option>
              <option value="cloud">{pick("云端", "Cloud")}</option>
            </select>
          </label>
          <label>
            {pick("内容语言", "Content language")}
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              <option value="">{pick("不限定", "Any")}</option>
              <option value="chinese">中文</option>
              <option value="english">English</option>
            </select>
          </label>
          <label>
            {pick("平台", "Platform")}
            <select
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
            >
              <option value="">{pick("不限定", "Any")}</option>
              {["macos", "windows", "linux"].map((v) => (
                <option key={v}>{v}</option>
              ))}
            </select>
          </label>
          <label>
            {pick("显存上限 GB", "VRAM limit GB")}
            <input
              type="number"
              min="0"
              step="0.5"
              value={vram}
              onChange={(e) => setVram(e.target.value)}
            />
          </label>
          <label>
            {pick("每月预算 USD", "Monthly budget USD")}
            <input
              type="number"
              min="0"
              step="0.01"
              value={cost}
              onChange={(e) => setCost(e.target.value)}
            />
          </label>
        </div>
        <div className="task-form-footer">
          <label className="check-label">
            <input
              type="checkbox"
              checked={enhanced}
              disabled={!capabilities.data?.generation_available}
              onChange={(e) => setEnhanced(e.target.checked)}
            />
            {pick("使用 AI 扩展任务检索", "Use AI to expand task retrieval")}
            {!capabilities.data?.generation_available && (
              <small>{pick("当前未配置", "Not configured")}</small>
            )}
          </label>
          <button className="button primary" disabled={busy}>
            {busy
              ? pick("整理中…", "Working…")
              : pick("整理任务资料", "Build task context")}
            <Icon name="arrow" size={17} />
          </button>
        </div>
      </form>
      {error && (
        <div className="notice error-text" role="alert">
          {error}
        </div>
      )}
      {pack && (
        <section className="task-results">
          <div className="section-title">
            <div>
              <h2>{pack.goal}</h2>
              <p className="muted">
                {pick(
                  `找到 ${pack.total_candidates} 项候选，匹配依据与材料如下。`,
                  `${pack.total_candidates} candidates with matching evidence and materials.`,
                )}
              </p>
            </div>
            <button
              className="button"
              onClick={() => saveText("metis-task.md", printable(pack))}
            >
              <Icon name="download" size={17} />
              {pick("导出资料包", "Export context")}
            </button>
          </div>
          <div className="notice">
            <Icon name="info" />
            <div>
              {pack.conclusion === "not_found_in_scope"
                ? pick(
                    "当前收录范围内未找到候选，可反馈缺失资料。",
                    "No candidates in the indexed collection. You can report missing resources.",
                  )
                : pack.conclusion === "known_candidates_unmet"
                  ? pick(
                      "已找到的候选均有不满足的条件，请核对约束。",
                      "Known candidates have unmet conditions. Review your constraints.",
                    )
                  : pick(
                      "请核对条件和版本，再选择实践范围。资料完整不代表已经运行验证。",
                      "Check constraints and versions before choosing a scoped task. Documentation does not imply runtime verification.",
                    )}
              <p>{pack.interpretation.warning}</p>
            </div>
          </div>
          <ResearchComparison data={pack.research_comparison} />
          <div className="deliverable-list">
            {pack.deliverables.map((d, i) => (
              <span key={d}>
                <b>{i + 1}</b>
                {d}
              </span>
            ))}
          </div>
          <details className="task-conditions">
            <summary>
              {pick("查看识别出的条件", "Review interpreted conditions")}
            </summary>
            <pre>{JSON.stringify(pack.constraints, null, 2)}</pre>
          </details>
          {pack.candidates.map((item: RecordItem, i) => (
            <article className="task-candidate" key={item.id}>
              <div className="section-title">
                <Link to={`/records/${item.id}`}>
                  <h3>{item.title_zh || item.title}</h3>
                </Link>
                <span className="mono">
                  {item.version || pick("版本未知", "Version unknown")}
                </span>
              </div>
              <div className="condition-matches">
                {item.constraint_matches?.map((m) => (
                  <span
                    className={`tag condition-${m.state}`}
                    key={m.condition}
                  >
                    {labels[m.condition] || m.condition} ·{" "}
                    {m.state === "satisfied"
                      ? pick("有依据支持", "Documented match")
                      : m.state === "unmet"
                        ? pick("不满足", "Unmet")
                        : pick("待核实", "Unknown")}
                  </span>
                ))}
              </div>
              <p>{item.summary_zh || item.summary}</p>
              {pack.material_packets[i]?.steps.map((s, j) => (
                <div className="task-step" key={j}>
                  <strong>{labels[s.type] || s.type}</strong>
                  <p>{formatValue(s.instruction)}</p>
                  <SourceLink url={s.source_url}>
                    {pick("查看依据", "Read evidence")}
                    <Icon name="up" size={13} />
                  </SourceLink>
                  {!s.version_matches && (
                    <span className="tag">
                      {pick("版本待核对", "Version mismatch")}
                    </span>
                  )}
                </div>
              ))}
              <details>
                <summary>{pick("展开原文与章节材料", "Read source documents and sections")}</summary>
                <div className="task-materials">
                {pack.material_packets[i]?.materials.map((m) => (
                  <SourceLink key={m.id} url={m.url}>
                    <Icon name="book" size={15} />
                    {m.locator || m.title}
                    <small>{m.coverage}</small>
                  </SourceLink>
                ))}
                </div>
              </details>
              {!!pack.material_packets[i]?.missing_materials.length && (
                <p className="missing-materials">
                  {pick("还缺少：", "Still missing: ")}
                  {pack.material_packets[i].missing_materials
                    .map((k) => labels[k] || k)
                    .join("、")}
                </p>
              )}
            </article>
          ))}
          <div className="button-row">
            {pack.next_offset !== null && (
              <button
                className="button"
                disabled={busy}
                onClick={() => void build(undefined, pack.next_offset!)}
              >
                {pick("下一页候选", "Next candidates")}
              </button>
            )}
            {pack.candidates.some((r) => r.kind === "paper") && (
              <button
                className="button primary"
                disabled={busy}
                onClick={makeReading}
              >
                {pick("组织研究阅读材料", "Organize research materials")}
              </button>
            )}
          </div>
        </section>
      )}
      {reading && (
        <section className="reading-workbench">
          <div className="section-title">
            <h2>{pick("研究阅读材料", "Research reading materials")}</h2>
            <button
              className="button"
              onClick={() => {
                saveText("metis-references.bib", reading.bibtex, "text/plain");
                notify(pick("引用已导出", "References exported"));
              }}
            >
              {pick("导出引用", "Export citations")}
            </button>
            <button
              className="button"
              onClick={() =>
                saveText(
                  "metis-research.md",
                  `# ${reading.goal}\n\n${reading.scope}\n` +
                    reading.items
                      .map(
                        (r) =>
                          `\n## ${r.title_zh || r.title}\n来源：${r.source_url}\n` +
                          Object.entries(r.research || {})
                            .filter(([, v]) => typeof v === "string")
                            .map(
                              ([k, v]) => `- ${labels[k] || k}: ${String(v)}`,
                            )
                            .join("\n"),
                      )
                      .join("\n"),
                )
              }
            >
              {pick("导出阅读材料", "Export reading notes")}
            </button>
          </div>
          <ResearchComparison data={reading.comparison} />
          {reading.outline?.sections.map((s, i) => (
            <article key={i}>
              <h3>{s.title}</h3>
              {s.points.map((p, j) => (
                <p key={j}>
                  {p.text}{" "}
                  <SourceLink url={p.source_url}>
                    {p.locator || pick("原文", "Source")}
                  </SourceLink>
                </p>
              ))}
            </article>
          ))}
          {reading.items.map((r) => (
            <article key={r.id}>
              <Link to={`/records/${r.id}`}>
                <h3>{r.title_zh || r.title}</h3>
              </Link>
              {Object.entries(r.research || {})
                .filter(([, v]) => typeof v === "string" && v)
                .map(([key, value]) => (
                  <p key={key}>
                    <strong>{labels[key] || key}：</strong>
                    {String(value)}
                  </p>
                ))}
            </article>
          ))}
        </section>
      )}
    </>
  );
}
