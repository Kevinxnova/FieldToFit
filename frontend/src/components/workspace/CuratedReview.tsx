import { useEffect, useState } from "react";
import { request, send, type Dossier } from "../../api/knowledge";
import { useWorkspace } from "./UI";

type Role = { type: string; evidence_id: string; quote: string };
type Attention = { kind: string; explanation: string; evidence_id: string; quote: string; observed_at: string; platform?: string; value?: number; window?: string };
type Material = { evidence_id: string; kind: string; primary: boolean; note: string };
type Profile = { introduction: string; aliases: string[]; roles: Role[]; attention: Attention[]; materials: Material[] };
type Preview = {
  profile: Partial<Profile>; profile_revision: number; review_token: string;
  selection: { state: string; revision: number | null };
  gate: { ready: boolean; errors: string[] };
  object: { name: string; introduction: string; types: string[]; upstream_version: string | null; coverage: { registered_materials: number; readable_materials: number }; attention: { explanation: string; kind: string }[] };
};
const empty: Profile = { introduction: "", aliases: [], roles: [], attention: [], materials: [] };
const types = ["model", "tool", "agent", "skill", "harness", "research", "library", "dataset", "application"];
const states: Record<string, [string, string]> = {
  candidate: ["候选", "Candidate"], review: ["待审", "In review"], published: ["已精选发布", "Published selection"],
  needs_review: ["资料已变化，待复核", "Changed, needs review"], withdrawn: ["已撤回精选", "Withdrawn"],
};

export default function CuratedReview({ record }: { record: Dossier }) {
  const { pick } = useWorkspace();
  const [preview, setPreview] = useState<Preview | null>(null);
  const [profile, setProfile] = useState<Profile>(empty);
  const [reason, setReason] = useState("");
  const [aliases, setAliases] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [dirty, setDirty] = useState(false);
  const path = "/v1/admin/platform/objects/" + record.id;
  const accept = (data: Preview) => { setPreview(data); setProfile({ ...empty, ...data.profile }); setAliases((data.profile.aliases || []).join(", ")); setDirty(false); };
  useEffect(() => {
    let active = true;
    setPreview(null); setError(""); setReason(""); setDirty(false);
    request<Preview>(path, {}, true).then(data => { if (active) accept(data); }).catch(e => { if (active) setError(e.message); });
    return () => { active = false; };
  }, [path]);
  const change = (next: Profile) => { setProfile(next); setDirty(true); };
  const act = async (action: "save" | "review" | "published" | "withdrawn" | "reload") => {
    if (!preview && action !== "reload") return;
    setBusy(true); setError("");
    try {
      const result = action === "reload" ? await request<Preview>(path, {}, true)
        : action === "save" ? await send<Preview>(path, { profile, expected_revision: preview!.profile_revision, reason }, "PATCH", true)
        : await send<Preview>(path + "/transition", { state: action, review_token: preview!.review_token, reason }, "POST", true);
      accept(result);
    } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  };
  const evidenceOptions = record.evidence.map(e => <option key={e.id} value={e.id}>{e.title} · {e.locator || e.coverage}</option>);
  const state = preview?.selection.state || "candidate";
  return <section className="ops-form curated-review" aria-label={pick("精选审核", "Curated review")}>
    <h2>{pick("精选审核", "Curated review")}</h2>
    <p>{pick("收录与精选分开。先保存资料中的事实和引文，再整理此处的介绍、关注依据与材料清单。", "Collection and selection are separate. Save source facts and quotes first, then review this profile.")}</p>
    {error && <p role="alert" className="error-text">{error}</p>}
    {!preview ? <button className="button" disabled={busy} onClick={() => act("reload")}>{pick("重新载入审核资料", "Reload review")}</button> : <>
      <p aria-live="polite"><strong>{pick(...(states[state] || [state, state]))}</strong> · {pick("草稿版本", "Draft revision")} {preview.profile_revision}</p>
      <fieldset disabled={busy} style={{ border: 0, padding: 0, minWidth: 0 }}>
        <label>{pick("给人看的介绍", "Structured introduction")}<textarea value={profile.introduction} onChange={e => change({ ...profile, introduction: e.target.value })} /></label>
        <label>{pick("别名（逗号分隔）", "Aliases (comma separated)")}<input value={aliases} onChange={e => { setAliases(e.target.value); change({ ...profile, aliases: e.target.value.split(/[,，]/).map(s => s.trim()).filter(Boolean) }); }} /></label>
        <h3>{pick("对象类型及原文依据", "Types and original evidence")}</h3>
        {profile.roles.map((role, i) => <div className="ops-item" key={i}>
          <label>{pick("类型", "Type")}<select value={role.type} onChange={e => change({ ...profile, roles: profile.roles.map((r, j) => j === i ? { ...r, type: e.target.value } : r) })}>{types.map(t => <option key={t}>{t}</option>)}</select></label>
          <label>{pick("类型依据材料", "Type evidence")}<select value={role.evidence_id} onChange={e => change({ ...profile, roles: profile.roles.map((r, j) => j === i ? { ...r, evidence_id: e.target.value } : r) })}><option value="">{pick("选择原文", "Choose source")}</option>{evidenceOptions}</select></label>
          <label>{pick("类型依据原句", "Type source quote")}<textarea value={role.quote} onChange={e => change({ ...profile, roles: profile.roles.map((r, j) => j === i ? { ...r, quote: e.target.value } : r) })} /></label>
          <button className="text-button" onClick={() => change({ ...profile, roles: profile.roles.filter((_, j) => j !== i) })}>{pick("移除此类型", "Remove type")}</button>
        </div>)}
        <button className="button" onClick={() => change({ ...profile, roles: [...profile.roles, { type: "tool", evidence_id: "", quote: "" }] })}>{pick("添加类型", "Add type")}</button>
        <h3>{pick("为什么收录", "Why include this object")}</h3>
        {profile.attention.map((signal, i) => <div className="ops-item" key={i}>
          <small>{signal.kind} · {signal.observed_at}{signal.kind === "metric" && ` · ${signal.platform} / ${signal.value} / ${signal.window}`}</small>
          <label>{pick("收录理由", "Reason for inclusion")}<textarea value={signal.explanation} onChange={e => change({ ...profile, attention: profile.attention.map((s, j) => j === i ? { ...s, explanation: e.target.value } : s) })} /></label>
          <label>{pick("理由依据材料", "Reason evidence")}<select value={signal.evidence_id} onChange={e => change({ ...profile, attention: profile.attention.map((s, j) => j === i ? { ...s, evidence_id: e.target.value } : s) })}><option value="">{pick("选择原文", "Choose source")}</option>{evidenceOptions}</select></label>
          <label>{pick("理由依据原句", "Reason source quote")}<textarea value={signal.quote} onChange={e => change({ ...profile, attention: profile.attention.map((s, j) => j === i ? { ...s, quote: e.target.value } : s) })} /></label>
          <button className="text-button" onClick={() => change({ ...profile, attention: profile.attention.filter((_, j) => j !== i) })}>{pick("移除此理由", "Remove reason")}</button>
        </div>)}
        <button className="button" onClick={() => change({ ...profile, attention: [...profile.attention, { kind: "editorial", explanation: "", evidence_id: "", quote: "", observed_at: new Date().toISOString() }] })}>{pick("添加编辑选择理由", "Add editorial reason")}</button>
        <h3>{pick("交给 AI 的材料", "Materials for AI")}</h3>
        {record.evidence.map(e => {
          const selected = profile.materials.find(m => m.evidence_id === e.id);
          return <div className="ops-item" key={e.id}>
            <label className="inline-field"><input type="checkbox" checked={!!selected} onChange={() => change({ ...profile, materials: selected ? profile.materials.filter(m => m.evidence_id !== e.id) : [...profile.materials, { evidence_id: e.id, kind: "document", primary: false, note: "" }] })} />{e.title} · {e.locator || e.coverage}</label>
            <p><a href={e.url} target="_blank" rel="noreferrer">{pick("查看原始来源", "Open original source")}</a> · {e.coverage} · {e.characters} {pick("字符", "characters")} · {e.version || pick("版本未知", "Version unknown")}</p>
            {selected && <>
              <label className="inline-field"><input type="checkbox" checked={selected.primary} onChange={ev => change({ ...profile, materials: profile.materials.map(m => m.evidence_id === e.id ? { ...m, primary: ev.target.checked } : m) })} />{pick("主要材料", "Primary material")}</label>
              <label>{pick("覆盖说明或缺口", "Coverage note or missing content")}<input value={selected.note} onChange={ev => change({ ...profile, materials: profile.materials.map(m => m.evidence_id === e.id ? { ...m, note: ev.target.value } : m) })} /></label>
            </>}
          </div>;
        })}
        <label>{pick("本次审核依据", "Review reason")}<textarea value={reason} onChange={e => setReason(e.target.value)} /></label>
      </fieldset>
      <div className="ops-item" aria-live="polite">
        <h3>{pick("已保存内容的发布检查", "Publication checks for saved content")}</h3>
        {dirty && <p>{pick("有未保存修改；保存后重新检查。", "Unsaved changes; save to recheck.")}</p>}
        <strong>{preview.object.name}</strong><p>{preview.object.introduction}</p>
        <p>{preview.object.types.join(" · ")} · {pick("可读材料", "Readable materials")} {preview.object.coverage.readable_materials}/{preview.object.coverage.registered_materials}</p>
        {preview.gate.ready ? <p>{pick("基础门槛通过；发布前请核对介绍含义与原文。", "Basic checks passed. Review meaning against the original before publishing.")}</p> : <ul>{preview.gate.errors.map((e, i) => <li key={i}>{e}</li>)}</ul>}
      </div>
      <div className="button-row">
        <button className="button" disabled={busy || !reason.trim() || !dirty} onClick={() => act("save")}>{pick("保存精选草稿", "Save selection draft")}</button>
        <button className="button" disabled={busy || dirty || !reason.trim() || state === "review" || state === "published"} onClick={() => act("review")}>{pick("提交审核", "Submit for review")}</button>
        <button className="button primary" disabled={busy || dirty || !reason.trim() || state !== "review" || !preview.gate.ready} onClick={() => act("published")}>{pick("发布到精选", "Publish selection")}</button>
        <button className="button" disabled={busy || dirty || !reason.trim() || state === "withdrawn"} onClick={() => act("withdrawn")}>{pick("撤回精选", "Withdraw selection")}</button>
        <button className="text-button" disabled={busy} onClick={() => act("reload")}>{pick("重新读取服务端内容", "Reload saved content")}</button>
      </div>
    </>}
  </section>;
}
