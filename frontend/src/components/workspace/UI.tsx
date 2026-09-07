import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import type { Context as ReactContext } from "react";
import { Link } from "react-router-dom";
import { request, send, safeURL, type RecordItem } from "../../api/knowledge";

const paths: Record<string, ReactNode> = {
  grid: (
    <>
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
      <rect x="14" y="14" width="7" height="7" rx="1.5" />
    </>
  ),
  news: (
    <>
      <rect x="3" y="4" width="18" height="16" rx="2" />
      <path d="M7 8h10M7 12h5M7 16h10M16 12h1" />
    </>
  ),
  search: (
    <>
      <circle cx="10.5" cy="10.5" r="6.5" />
      <path d="m16 16 5 5" />
    </>
  ),
  arrow: <path d="M4 12h15m-6-6 6 6-6 6" />,
  up: <path d="M6 18 18 6M6 6h12v12" />,
  bookmark: <path d="M6 4h12v17l-6-4-6 4V4Z" />,
  book: (
    <>
      <path d="M3 4h7l2 2 2-2h7v15h-7l-2 2-2-2H3V4ZM12 6v15" />
    </>
  ),
  compare: (
    <>
      <path d="M8 3v18M16 3v18M4 7h8M12 17h8M5 13H3v5h3M19 11h2V6h-3" />
    </>
  ),
  code: (
    <>
      <path d="m8 6-6 6 6 6m8-12 6 6-6 6m-2-15-4 18" />
    </>
  ),
  check: <path d="m5 12 4 4L19 6" />,
  close: <path d="m6 6 12 12M6 18 18 6" />,
  source: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18M12 3c5 5 5 13 0 18-5-5-5-13 0-18Z" />
    </>
  ),
  clock: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </>
  ),
  sun: (
    <>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1 1m12 12 1 1M5 19l1-1M18 6l1-1" />
    </>
  ),
  moon: <path d="M20 14A9 9 0 0 1 10 3a9 9 0 1 0 10 11Z" />,
  settings: (
    <>
      <path d="M4 7h16M4 17h16" />
      <circle cx="9" cy="7" r="3" />
      <circle cx="15" cy="17" r="3" />
    </>
  ),
  copy: (
    <>
      <rect x="8" y="8" width="12" height="13" rx="2" />
      <path d="M16 8V3H3v13h5" />
    </>
  ),
  download: (
    <>
      <path d="M12 3v12m-5-5 5 5 5-5M4 17v4h16v-4" />
    </>
  ),
  bell: (
    <>
      <path d="M5 17h14l-2-4V9a5 5 0 0 0-10 0v4l-2 4ZM10 21h4" />
    </>
  ),
  info: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v6M12 7v1" />
    </>
  ),
  flag: (
    <>
      <path d="M5 21V3h13l-3 5 3 5H5" />
    </>
  ),
  chevron: <path d="m9 5 7 7-7 7" />,
  user: (
    <>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21v-2a8 8 0 0 1 16 0v2" />
    </>
  ),
};
export function Icon({ name, size = 20 }: { name: string; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.65"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name] || paths.grid}
    </svg>
  );
}
export const TOPICS: Record<string, [string, string]> = {
  models: ["模型", "Models"],
  agents: ["Agent", "Agents"],
  research: ["研究", "Research"],
  engineering: ["开发", "Engineering"],
  business: ["商业", "Business"],
  vertical: ["垂直应用", "Applications"],
  learning: ["学习", "Learning"],
  data: ["数据", "Data"],
};
export const TYPES: Record<string, [string, string]> = {
  project: ["开源项目", "Open source"],
  event: ["动态", "News"],
  paper: ["论文", "Paper"],
  resource: ["资源", "Resource"],
  tool: ["工具", "Tool"],
  library: ["开发库", "Library"],
  model: ["模型", "Model"],
  api: ["API 服务", "API"],
  application: ["应用", "App"],
  dataset: ["数据集", "Dataset"],
  benchmark: ["评测基准", "Benchmark"],
  release: ["版本发布", "Release"],
  news: ["动态", "News"],
  other: ["资源", "Resource"],
};
type CollectionItem = {
  record_id: string;
  action: "save" | "follow";
  created_at: string;
};
interface WorkspaceContext {
  zh: boolean;
  toggleLang: () => void;
  dark: boolean;
  toggleTheme: () => void;
  pick: (zh: string, en: string) => string;
  collection: CollectionItem[];
  toggleCollection: (id: string, action?: "save" | "follow") => void;
  compare: string[];
  toggleCompare: (id: string) => void;
  clearCompare: () => void;
  notify: (message: string) => void;
}
const Context: ReactContext<WorkspaceContext> =
  import.meta.hot?.data.workspaceContext ??
  createContext<WorkspaceContext>(null!);
if (import.meta.hot) import.meta.hot.data.workspaceContext = Context;
function local<T>(key: string, fallback: T): T {
  try {
    return JSON.parse(localStorage.getItem(key) || "null") ?? fallback;
  } catch {
    return fallback;
  }
}
export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [zh, setZh] = useState(() => local("metis-workspace-zh", true));
  const [dark, setDark] = useState(() => local("metis-workspace-dark", false));
  const [collection, setCollection] = useState<CollectionItem[]>(() =>
    local("metis-collection", []),
  );
  const [collectionKey, setCollectionKey] = useState("metis-collection");
  const [compare, setCompare] = useState<string[]>([]);
  const [toast, setToast] = useState("");
  const [signedIn, setSignedIn] = useState(false);
  const pick = (cn: string, en: string) => (zh ? cn : en);
  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    localStorage.setItem("metis-workspace-dark", JSON.stringify(dark));
  }, [dark]);
  useEffect(() => {
    document.documentElement.lang = zh ? "zh-CN" : "en";
    localStorage.setItem("metis-workspace-zh", JSON.stringify(zh));
  }, [zh]);
  useEffect(() => {
    localStorage.setItem(collectionKey, JSON.stringify(collection));
  }, [collection, collectionKey]);
  useEffect(() => {
    if (!toast) return;
    const id = setTimeout(() => setToast(""), 4200);
    return () => clearTimeout(id);
  }, [toast]);
  useEffect(() => {
    request<{ user: { id: string } | null }>("/v1/account")
      .then(async (r) => {
        if (!r.user) return;
        setSignedIn(true);
        const saved = await request<{ items: CollectionItem[] }>(
          "/v1/collection",
        );
        setCollectionKey("metis-collection:" + r.user.id);
        setCollection(saved.items);
      })
      .catch(() => {});
  }, []);
  const toggleCollection = (id: string, action: "save" | "follow" = "save") => {
    const exists = collection.some(
      (x) => x.record_id === id && x.action === action,
    );
    setCollection((items) =>
      exists
        ? items.filter((x) => !(x.record_id === id && x.action === action))
        : [
            ...items,
            { record_id: id, action, created_at: new Date().toISOString() },
          ],
    );
    setToast(
      exists
        ? pick("已移除", "Removed")
        : pick(
            action === "save" ? "已加入收藏" : "已关注，每日更新可在收藏页查看",
            action === "save"
              ? "Saved to your collection"
              : "Following. Check your collection for daily updates.",
          ),
    );
    if (signedIn)
      send(
        "/v1/collection",
        { record_id: id, action },
        exists ? "DELETE" : "POST",
      ).catch(() =>
        setToast(
          pick(
            "已保存在本机，账户同步失败",
            "Saved locally; account sync failed",
          ),
        ),
      );
  };
  const toggleCompare = (id: string) => {
    if (compare.includes(id)) setCompare(compare.filter((x) => x !== id));
    else if (compare.length < 4) setCompare([...compare, id]);
    else setToast(pick("一次最多对比 4 项", "Compare up to 4 items"));
  };
  return (
    <Context.Provider
      value={{
        zh,
        dark,
        pick,
        toggleLang: () => setZh(!zh),
        toggleTheme: () => setDark(!dark),
        collection,
        toggleCollection,
        compare,
        toggleCompare,
        clearCompare: () => setCompare([]),
        notify: setToast,
      }}
    >
      {children}
      {toast && (
        <div className="toast" role="status">
          <Icon name="check" size={17} />
          {toast}
          <button
            aria-label={pick("关闭", "Dismiss")}
            onClick={() => setToast("")}
          >
            <Icon name="close" size={16} />
          </button>
        </div>
      )}
    </Context.Provider>
  );
}
export function useWorkspace() {
  return useContext(Context);
}
export function titleOf(record: RecordItem, zh: boolean) {
  return record.kind !== "resource" && zh && record.title_zh
    ? record.title_zh
    : record.title;
}
export function summaryOf(record: RecordItem, zh: boolean) {
  return zh && record.summary_zh ? record.summary_zh : record.summary;
}
export function dateText(date: string | null | undefined, zh = true) {
  if (!date) return zh ? "尚未记录" : "Not recorded";
  const value = new Date(date);
  return Number.isNaN(value.getTime())
    ? date.slice(0, 10)
    : value.toLocaleDateString(zh ? "zh-CN" : "en-GB", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
}
export function SourceLink({
  url,
  children,
  className = "",
}: {
  url?: string;
  children: ReactNode;
  className?: string;
}) {
  const href = safeURL(url);
  return href ? (
    <a
      href={href}
      className={className}
      target="_blank"
      rel="noopener noreferrer"
    >
      {children}
    </a>
  ) : (
    <span className={className}>{children}</span>
  );
}
export function PageHeading({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow: string;
  title: string;
  description: string;
  children?: ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {children}
    </div>
  );
}
export function State({
  loading,
  error,
  empty,
  retry,
  children,
}: {
  loading?: boolean;
  error?: string;
  empty?: boolean;
  retry?: () => void;
  children?: ReactNode;
}) {
  const { pick } = useWorkspace();
  if (loading)
    return (
      <div
        className="skeleton-list"
        aria-label={pick("正在加载", "Loading")}
        aria-busy="true"
      >
        {[1, 2, 3].map((i) => (
          <div className="skeleton" key={i} />
        ))}
      </div>
    );
  if (error)
    return (
      <div className="empty-state" role="alert">
        <Icon name="info" size={28} />
        <h3>{pick("暂时无法读取资料", "Unable to load records")}</h3>
        <p>{error}</p>
        <div className="button-row">
          {retry && (
            <button className="button" onClick={retry}>
              {pick("重试", "Try again")}
            </button>
          )}
          <Link className="button subtle" to="/connect">
            {pick("检查连接", "Connection settings")}
          </Link>
        </div>
      </div>
    );
  if (empty)
    return (
      <div className="empty-state">
        <Icon name="search" size={28} />
        <h3>{pick("当前范围内还没有结果", "No results in this collection")}</h3>
        <p>
          {pick(
            "试试更具体的关键词，或减少筛选条件。未收录不代表不存在。",
            "Try a different keyword or fewer filters. Missing records do not prove absence.",
          )}
        </p>
      </div>
    );
  return <>{children}</>;
}
export function RecordCard({
  record,
  compact = false,
}: {
  record: RecordItem;
  compact?: boolean;
}) {
  const { zh, pick, collection, toggleCollection, compare, toggleCompare } =
    useWorkspace();
  const saved = collection.some(
    (x) => x.record_id === record.id && x.action === "save",
  );
  const type =
    TYPES[record.kind === "resource" ? record.object_type : record.kind] ||
    TYPES.resource;
  let domain = record.source_id;
  try {
    domain = new URL(record.canonical_url).hostname.replace("www.", "");
  } catch {
    /* Display the source ID if URL is unavailable. */
  }
  return (
    <article className={`record-card ${compact ? "compact" : ""}`}>
      <div className="record-top">
        <span className={`record-symbol ${record.kind}`}>
          <Icon
            name={
              record.kind === "paper"
                ? "book"
                : record.kind === "event"
                  ? "news"
                  : "code"
            }
            size={21}
          />
        </span>
        <span className="record-domain">{domain}</span>
        <button
          className={`icon-button ${saved ? "selected" : ""}`}
          aria-label={pick(
            saved ? "取消收藏" : "收藏",
            saved ? "Unsave" : "Save",
          )}
          aria-pressed={saved}
          onClick={() => toggleCollection(record.id)}
        >
          <Icon name="bookmark" size={18} />
        </button>
      </div>
      <div className="record-labels">
        <span className={`tag kind-${record.kind}`}>{pick(...type)}</span>
        {record.topics.slice(0, 2).map((topic) => (
          <span className="tiny-topic" key={topic}>
            {TOPICS[topic] ? pick(...TOPICS[topic]) : topic}
          </span>
        ))}
      </div>
      <Link className="record-title" to={`/records/${record.id}`}>
        {titleOf(record, zh)}
      </Link>
      <p className="record-summary">
        {summaryOf(record, zh) ||
          pick(
            "已收录来源入口，详细说明待补充。",
            "Source indexed. Detailed documentation is not yet available.",
          )}
      </p>
      <div className="record-footer">
        <span className="record-date">
          {record.published_at
            ? dateText(record.published_at, zh)
            : pick("发布时间未知", "Publication date unknown")}
        </span>
        {record.kind === "resource" ? (
          <button
            className={`text-button ${compare.includes(record.id) ? "selected" : ""}`}
            onClick={() => toggleCompare(record.id)}
            aria-pressed={compare.includes(record.id)}
          >
            <Icon name="compare" size={15} />
            {pick(
              compare.includes(record.id) ? "已选对比" : "对比",
              compare.includes(record.id) ? "Selected" : "Compare",
            )}
          </button>
        ) : (
          <Link
            className="round-arrow"
            aria-label={pick("查看详情", "Read details")}
            to={`/records/${record.id}`}
          >
            <Icon name="arrow" size={17} />
          </Link>
        )}
      </div>
    </article>
  );
}
export function Pagination({
  offset,
  next,
  total,
  onPage,
}: {
  offset: number;
  next: number | null;
  total: number;
  onPage: (offset: number) => void;
}) {
  const { pick } = useWorkspace();
  return (
    <div className="pagination">
      <span>
        {pick(
          `共 ${total} 项 · 第 ${Math.floor(offset / 24) + 1} 页`,
          `${total} records · Page ${Math.floor(offset / 24) + 1}`,
        )}
      </span>
      <div>
        <button
          className="button subtle"
          disabled={!offset}
          onClick={() => onPage(Math.max(0, offset - 24))}
        >
          {pick("上一页", "Previous")}
        </button>
        <button
          className="button subtle"
          disabled={next === null}
          onClick={() => next !== null && onPage(next)}
        >
          {pick("下一页", "Next")}
        </button>
      </div>
    </div>
  );
}
