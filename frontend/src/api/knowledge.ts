import { useEffect, useState } from "react";

export const BASE = (import.meta.env.VITE_API_URL || "") + "/api";
export type Kind = "event" | "paper" | "resource";
export interface Fact {
  value: unknown;
  status: string;
  source_url?: string;
  version?: string;
  checked_at?: string;
  exhaustive?: boolean;
}
export interface Evidence {
  id: string;
  title: string;
  url: string;
  coverage: string;
  version: string;
  locator: string;
  characters: number;
  retrieved_at: string;
}
export interface Verification {
  id: string;
  record_id: string;
  record_title?: string;
  title: string;
  method: string;
  environment: string;
  version: string;
  steps: string;
  expected: string;
  result: string;
  output: string;
  limitations: string;
  checked_at: string;
}
export interface RecordItem {
  id: string;
  kind: Kind;
  canonical_url: string;
  title: string;
  title_zh: string;
  summary: string;
  summary_zh: string;
  object_type: string;
  topics: string[];
  source_id: string;
  published_at: string | null;
  collected_at: string;
  checked_at: string | null;
  updated_at: string;
  version: string;
  completeness: string;
  status: string;
  freshness: string;
  facts: Record<string, Fact>;
  metadata: Record<string, unknown>;
  match_score?: number;
  constraint_matches?: {
    condition: string;
    requested: unknown;
    state: string;
    evidence: Fact;
  }[];
}
export interface Dossier extends RecordItem {
  conflicts?: { id: string; field: string; alternatives: Fact[] }[];
  grouped_sources?: {
    id: string;
    title: string;
    url: string;
    source_id: string;
  }[];
  evidence: Evidence[];
  verifications: Verification[];
  verification_status: string;
  relations: {
    id: string;
    related_id: string;
    related_title: string;
    relation: string;
    note: string;
    evidence_url: string;
  }[];
  history: {
    seq: number;
    action: string;
    reason: string;
    changed_at: string;
  }[];
  history_truncated: boolean;
}
export interface SearchResult {
  items: RecordItem[];
  total: number;
  offset: number;
  next_offset: number | null;
  scope: string;
  expanded_terms: string[];
}
export interface Overview {
  counts: Record<string, number>;
  complete: number;
  verified: number;
  sources: number;
  last_update: string | null;
  interval_days: number;
  topics: Record<string, string>;
}
export interface Source {
  id: string;
  name: string;
  category: string;
  url: string;
  enabled: boolean;
  interval_days: number;
  status: string;
  last_success_at: string | null;
  last_attempt_at: string | null;
  error?: string;
}
export interface TaskPack {
  goal: string;
  persona: string;
  candidates: RecordItem[];
  total_candidates: number;
  next_offset: number | null;
  conclusion: string;
  scope: string;
}

export function readToken() {
  try {
    return sessionStorage.getItem("metis-read-token") || "";
  } catch {
    return "";
  }
}
export async function request<T>(
  path: string,
  options: RequestInit = {},
  admin = false,
): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body) headers.set("Content-Type", "application/json");
  const token = readToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (admin)
    headers.set(
      "X-Admin-Password",
      sessionStorage.getItem("metis-admin-password") || "",
    );
  const response = await fetch(BASE + path, {
    ...options,
    headers,
    credentials: "include",
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      error.detail || error.error || `Request failed (${response.status})`,
    );
  }
  return response.json();
}
export function send<T>(
  path: string,
  data: unknown,
  method = "POST",
  admin = false,
) {
  return request<T>(path, { method, body: JSON.stringify(data) }, admin);
}
export function useRemote<T>(path: string | null, admin = false) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(!!path);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setData(null);
    setError("");
    setLoading(!!path);
    if (path)
      request<T>(path, { signal: controller.signal }, admin)
        .then(setData)
        .catch((e) => {
          if (!controller.signal.aborted) setError(e.message);
        })
        .finally(() => {
          if (!controller.signal.aborted) setLoading(false);
        });
    return () => controller.abort();
  }, [path, revision, admin]);
  return { data, error, loading, reload: () => setRevision((r) => r + 1) };
}
export async function downloadRecord(
  id: string,
  format: "markdown" | "bibtex" | "json" = "markdown",
) {
  const headers = new Headers();
  if (readToken()) headers.set("Authorization", `Bearer ${readToken()}`);
  const response = await fetch(
    `${BASE}/v1/records/${id}/export?format=${format}`,
    { headers, credentials: "include" },
  );
  if (!response.ok) throw new Error("Export failed");
  const url = URL.createObjectURL(await response.blob());
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `metis-${id}.${format === "markdown" ? "md" : format === "bibtex" ? "bib" : "json"}`;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export function safeURL(url?: string) {
  try {
    const parsed = new URL(url || "");
    return ["http:", "https:"].includes(parsed.protocol)
      ? parsed.href
      : undefined;
  } catch {
    return undefined;
  }
}
export function formatValue(value: unknown): string {
  return Array.isArray(value)
    ? value.map(formatValue).join(" · ")
    : value && typeof value === "object"
      ? JSON.stringify(value, null, 2)
      : String(value ?? "—");
}
