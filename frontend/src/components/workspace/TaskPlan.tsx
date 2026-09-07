import { useState } from "react";
import type { Verification } from "../../api/knowledge";
import { formatValue } from "../../api/knowledge";
import { SourceLink, useWorkspace } from "./UI";

type Reference = {
  record_id: string;
  field: string;
  value: unknown;
  source_url: string;
  version: string;
  status: string;
};
export type TaskPlanData = {
  brief: {
    inputs: string;
    outputs: string;
    success_criteria: string;
    input_kind: string;
    background: string;
    missing_fields: string[];
    applied_context: { reason: string }[];
  };
  paths: {
    path: string;
    title: string;
    status: string;
    instruction: string;
    check: string;
    gaps: string[];
    references: Reference[];
  }[];
  next_steps: string[];
  recipe: null | {
    title: string;
    version: string;
    resource_version: string;
    guide_url: string;
    code_url: string;
    blockers: string[];
    requirements: string[];
    success_criteria: string[];
    steps: {
      title: string;
      instruction: string;
      command: string;
      expected: string;
    }[];
    verification: {
      status: string;
      scope: string;
      observation: Verification | null;
    };
  };
};
const states: Record<string, [string, string]> = {
  documented: ["有版本依据", "Documented"],
  blocked: ["存在阻塞", "Blocked"],
  needs_evidence: ["缺少依据", "Needs evidence"],
  design_proposal: ["设计建议", "Design proposal"],
  example_design: ["附示例实现", "Example implementation"],
  passed: ["样本运行通过", "Example passed"],
  failed: ["最近运行失败", "Latest run failed"],
  stale: ["版本变化，待复验", "Stale result"],
  not_run: ["尚无运行记录", "Not run"],
};

export default function TaskPlan({ data }: { data: TaskPlanData }) {
  const { pick } = useWorkspace();
  const [active, setActive] = useState("mixed");
  const chosen = data.paths.find((p) => p.path === active) || data.paths[0];
  const recipe = data.recipe;
  const status = (value: string) =>
    states[value] ? pick(...states[value]) : value;
  return (
    <section
      className="task-plan"
      aria-label={pick("执行资料包", "Execution context")}
    >
      <div className="section-title">
        <h3>{pick("先明确怎样才算完成", "Define what done means")}</h3>
        <span className="tag">{pick("任务要求", "Task requirements")}</span>
      </div>
      <dl className="task-contract">
        <div>
          <dt>{pick("输入", "Input")}</dt>
          <dd>{data.brief.inputs || pick("待补充", "To specify")}</dd>
        </div>
        <div>
          <dt>{pick("输出", "Output")}</dt>
          <dd>{data.brief.outputs || pick("待补充", "To specify")}</dd>
        </div>
        <div>
          <dt>{pick("成功判据", "Success criteria")}</dt>
          <dd>
            {data.brief.success_criteria ||
              pick(
                "待补充；当前不能判断整个任务已完成",
                "Specify before judging task completion",
              )}
          </dd>
        </div>
      </dl>
      {data.brief.applied_context.map((h, i) => (
        <p className="muted" key={i}>
          {h.reason}
        </p>
      ))}
      <h3>{pick("选择采用路径", "Choose an adoption path")}</h3>
      <div
        className="task-path-tabs"
        role="group"
        aria-label={pick("采用路径", "Adoption paths")}
      >
        {data.paths.map((p) => (
          <button
            type="button"
            aria-pressed={chosen.path === p.path}
            className={chosen.path === p.path ? "active" : ""}
            key={p.path}
            onClick={() => setActive(p.path)}
          >
            {pick(
              p.title,
              (
                {
                  use: "Use",
                  extend: "Extend",
                  build: "Build",
                  mixed: "Combine",
                } as Record<string, string>
              )[p.path],
            )}
          </button>
        ))}
      </div>
      <article className="task-path-panel" aria-label={chosen.title}>
        <span className="tag">{status(chosen.status)}</span>
        <p>{chosen.instruction}</p>
        <p>
          <strong>{pick("检查方式：", "Acceptance: ")}</strong>
          {chosen.check}
        </p>
        {chosen.references.length > 0 && (
          <details>
            <summary>{pick("查看采用依据", "Read adoption evidence")}</summary>
            {chosen.references.map((r, i) => (
              <p key={i}>
                {formatValue(r.value)}{" "}
                <SourceLink url={r.source_url}>
                  {r.field} · {r.version}
                </SourceLink>
              </p>
            ))}
          </details>
        )}
        {!!chosen.gaps.length && (
          <ul className="missing-materials">
            {chosen.gaps.map((g, i) => (
              <li key={i}>{g}</li>
            ))}
          </ul>
        )}
      </article>
      {recipe && (
        <section className="task-recipe">
          <div className="section-title">
            <div>
              <p className="eyebrow">WORKED EXAMPLE · v{recipe.version}</p>
              <h3>{recipe.title}</h3>
            </div>
            <span className="tag">pypdf {recipe.resource_version}</span>
          </div>
          <p className="muted">
            {pick(
              "以下为固定样本的完整实践；自己的文件需要另行验证。",
              "A complete workflow for fixed samples. Validate your own files separately.",
            )}
          </p>
          {!!recipe.blockers.length && (
            <div className="notice error-text" role="status">
              {recipe.blockers.join(" ")}
            </div>
          )}
          <ul>
            {recipe.requirements.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
          <div className="button-row">
            <SourceLink url={recipe.guide_url}>
              {pick("复现说明", "Reproduction guide")}
            </SourceLink>
            <SourceLink url={recipe.code_url}>
              {pick("完整示例代码", "Complete example code")}
            </SourceLink>
          </div>
          <h4>{pick("案例成功判据", "Example acceptance criteria")}</h4>
          <ol>
            {recipe.success_criteria.map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ol>
          <details open={!recipe.blockers.length}>
            <summary>
              {pick("执行步骤与预期产物", "Steps and expected artifacts")}
            </summary>
            {recipe.steps.map((s, i) => (
              <article className="task-step" key={i}>
                <h4>
                  {i + 1}. {s.title}
                </h4>
                <p>{s.instruction}</p>
                <pre>
                  <code>{s.command}</code>
                </pre>
                <p className="muted">
                  {pick("预期：", "Expected: ")}
                  {s.expected}
                </p>
              </article>
            ))}
          </details>
          <div className="task-observation">
            <h4>{pick("真实运行记录", "Observed execution")}</h4>
            <span
              className={`tag condition-${recipe.verification.status === "passed" ? "satisfied" : "unknown"}`}
            >
              {status(recipe.verification.status)}
            </span>
            <p>{recipe.verification.scope}</p>
            {recipe.verification.observation && (
              <>
                <p className="muted">
                  {recipe.verification.observation.checked_at} ·{" "}
                  {recipe.verification.observation.environment} · pypdf{" "}
                  {recipe.verification.observation.version}
                </p>
                <details>
                  <summary>
                    {pick("查看实际输出与边界", "Inspect output and limits")}
                  </summary>
                  <p>{recipe.verification.observation.limitations}</p>
                  <pre>{recipe.verification.observation.output}</pre>
                </details>
              </>
            )}
          </div>
        </section>
      )}
      <details>
        <summary>{pick("接下来做什么", "Next actions")}</summary>
        <ol>
          {data.next_steps.map((s, i) => (
            <li key={i}>{s}</li>
          ))}
        </ol>
      </details>
    </section>
  );
}
