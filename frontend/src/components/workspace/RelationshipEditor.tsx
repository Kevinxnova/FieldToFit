import { useState } from "react";
import { send } from "../../api/knowledge";
import { useWorkspace } from "./UI";
export default function RelationshipEditor() {
  const { pick, notify } = useWorkspace();
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [relation, setRelation] = useState("related");
  const [url, setUrl] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  return (
    <form
      className="ops-form"
      onSubmit={async (e) => {
        e.preventDefault();
        setBusy(true);
        setError("");
        try {
          await send(
            "/v1/admin/relations",
            { from_id: from, to_id: to, relation, evidence_url: url, note },
            "POST",
            true,
          );
          notify(
            pick("关联及变更记录已保存", "Relationship and history saved"),
          );
        } catch (e) {
          setError((e as Error).message);
        } finally {
          setBusy(false);
        }
      }}
    >
      <h2>
        {pick("维护有依据的关联", "Maintain source-linked relationships")}
      </h2>
      <label>
        {pick("起始资料 ID", "Source record ID")}
        <input
          required
          value={from}
          onChange={(e) => setFrom(e.target.value)}
        />
      </label>
      <label>
        {pick("关联资料 ID", "Related record ID")}
        <input required value={to} onChange={(e) => setTo(e.target.value)} />
      </label>
      <label>
        {pick("关系类型", "Relationship type")}
        <select value={relation} onChange={(e) => setRelation(e.target.value)}>
          {[
            ["related", "相关资料"],
            ["implementation", "实现"],
            ["dataset", "数据集"],
            ["model", "模型"],
            ["benchmark", "基准"],
            ["alternative", "替代"],
            ["dependency", "依赖"],
            ["integration", "集成"],
            ["release", "版本发布"],
          ].map(([v, cn]) => (
            <option key={v} value={v}>
              {pick(cn, v)}
            </option>
          ))}
        </select>
      </label>
      <label>
        {pick("原文依据", "Source URL")}
        <input
          type="url"
          required
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
      </label>
      <label>
        {pick("关系说明与作者身份依据", "Relationship and authorship evidence")}
        <textarea
          required
          value={note}
          onChange={(e) => setNote(e.target.value)}
        />
      </label>
      {error && <p role="alert">{error}</p>}
      <button className="button primary" disabled={busy}>
        {pick("保存关联", "Save relationship")}
      </button>
    </form>
  );
}
