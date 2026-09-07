import { formatValue } from "../../api/knowledge";
import { useWorkspace } from "./UI";

export type ResearchComparisonData = {
  comparable: boolean;
  missing_settings: string[];
  different_settings: string[];
  items: { id: string; title: string; settings: Record<string, unknown> }[];
};
export default function ResearchComparison({
  data,
}: {
  data?: ResearchComparisonData | null;
}) {
  const { pick } = useWorkspace();
  if (!data || data.items.length < 2) return null;
  const fields = [
    ["dataset", "数据集", "Dataset"],
    ["dataset_version", "数据版本", "Data version"],
    ["split", "数据划分", "Split"],
    ["metric", "指标", "Metric"],
    ["protocol", "评测流程", "Protocol"],
    ["model_version", "模型版本", "Model version"],
    ["hardware", "硬件条件", "Hardware"],
  ];
  const names = (keys: string[]) =>
    fields
      .filter(([key]) => keys.includes(key))
      .map(([, cn, en]) => pick(cn, en))
      .join("、");
  return (
    <section className="research-comparison">
      <h2>{pick("实验条件核对", "Experimental conditions")}</h2>
      <p className="notice">
        {data.comparable
          ? pick(
              "已记录的条件一致，可以继续核对指标定义和实验结果。",
              "Recorded settings align; check metric definitions and results next.",
            )
          : pick(
              "当前结果不能直接比较优劣。",
              "These results cannot be ranked directly.",
            )}
      </p>
      {!!data.missing_settings.length && (
        <p>
          {pick("缺少依据：", "Missing evidence: ")}
          {names(data.missing_settings)}
        </p>
      )}
      {!!data.different_settings.length && (
        <p>
          {pick("存在差异：", "Different settings: ")}
          {names(data.different_settings)}
        </p>
      )}
      <div className="comparison-scroll">
        <table className="comparison-table">
          <thead>
            <tr>
              <th>{pick("实验条件", "Condition")}</th>
              {data.items.map((i) => (
                <th key={i.id}>{i.title}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {fields.map(([key, cn, en]) => (
              <tr key={key}>
                <th>{pick(cn, en)}</th>
                {data.items.map((i) => (
                  <td key={i.id}>
                    {i.settings[key] == null
                      ? pick("未知或有分歧", "Unknown or conflicting")
                      : formatValue(i.settings[key])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
