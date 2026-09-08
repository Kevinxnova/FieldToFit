import { SourceLink, useWorkspace } from "./UI";

export default function SkillDetails({ value }: { value: unknown }) {
  const { pick } = useWorkspace();
  if (!value || typeof value !== "object") return null;
  const skill = value as { name: string; description: string; compatibility?: string; license?: string; entrypoint: string; path: string; files?: { path: string; url: string }[]; files_total?: number; files_truncated?: boolean };
  if (typeof skill.name !== "string" || typeof skill.description !== "string" || typeof skill.entrypoint !== "string") return null;
  const files = Array.isArray(skill.files) ? skill.files.filter(f => f && typeof f.path === "string" && typeof f.url === "string") : [];
  return <section className="skill-details">
    <div className="section-title"><h2>{pick("Skill 使用资料", "Skill materials")}</h2><span className="tag">{pick("未运行验证", "Not execution-tested")}</span></div>
    <p>{skill.description}</p>
    <dl className="skill-conditions">
      <div><dt>{pick("适用环境", "Compatibility")}</dt><dd>{typeof skill.compatibility === "string" ? skill.compatibility : pick("来源未说明", "Not specified by source")}</dd></div>
      <div><dt>{pick("许可证说明", "License statement")}</dt><dd>{typeof skill.license === "string" ? skill.license : pick("待核实", "Unknown")}</dd></div>
      <div><dt>{pick("仓库目录", "Directory")}</dt><dd>{typeof skill.path === "string" ? skill.path : "—"}</dd></div>
    </dl>
    <SourceLink className="button" url={skill.entrypoint}>{pick("查看该版本的 SKILL.md", "Read this version of SKILL.md")}</SourceLink>
    <p className="filter-note">{pick("按来源说明核对适用客户端和依赖。收录材料不表示安装成功或执行通过。", "Check the source for client compatibility and dependencies. Indexed material does not establish successful installation or execution.")}</p>
    {!!files.length && <details><summary>{pick(`附属文件（${skill.files_total ?? files.length}）`, `Supporting files (${skill.files_total ?? files.length})`)}</summary><ul>{files.map(f => <li key={f.path}><SourceLink url={f.url}>{f.path}</SourceLink></li>)}</ul>{skill.files_truncated && <p>{pick("这里只列出前 100 项，请在原仓库查看全部文件。", "First 100 entries; open the source repository for the complete tree.")}</p>}</details>}
  </section>;
}
