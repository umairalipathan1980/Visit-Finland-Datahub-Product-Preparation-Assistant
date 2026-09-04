const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8010";

export type ProductType = "accommodation" | "shops";

export interface CategoryOption {
  id: string;
  group: "accommodation" | "shops";
  label_en: string;
  label_fi?: string;
}

export interface CategoryTaxonomy {
  taxonomy_version: string | null;
  product_type: ProductType;
  categories: CategoryOption[];
}

export type RunStatus =
  | "queued"
  | "interrupted"
  | "cancelled"
  | "running"
  | "unknown"
  | "completed"
  | "scope_ambiguous"
  | "no_usable_sources"
  | "validation_failed"
  | "execution_failed"
  | "input_invalid";

export interface RunSummary {
  run_id: string;
  product_type: ProductType;
  product_name: string | null;
  website_urls: string[];
  status: RunStatus;
  error_code: string | null;
  approved: boolean;
  created_at: string;
}

export interface RunDetail {
  run_id: string;
  product_type: ProductType;
  status: RunStatus;
  error_code: string | null;
  stage_reached: string | null;
  artifacts: string[];
}

export interface FieldEvidence {
  source_id: string;
  locator: string;
  excerpt: string;
  quote_verified?: boolean;
}

export interface SourceReference {
  source_id: string;
  source_type: "website" | "document" | "unknown";
  title?: string;
  url?: string;
  retrieved_at?: string;
  file_name?: string;
  parsing_method?: string;
  citation_count: number;
}

export interface SourceCatalog {
  sources: SourceReference[];
}

export interface FieldEnvelope {
  status: "found" | "review" | "missing" | "not_in_scope";
  value?: unknown;
  evidence?: FieldEvidence[];
  alternatives?: { value: unknown; evidence: FieldEvidence[]; reason: string }[];
  notes?: string;
}

export interface ExtractionResult {
  run_metadata: Record<string, unknown>;
  product_type: ProductType;
  fields: Record<string, FieldEnvelope | Record<string, FieldEnvelope>>;
  validation: { valid: boolean; errors: unknown[]; warnings: unknown[] };
}

export interface ScopeDecision {
  status: "resolved" | "scope_ambiguous";
  error_code: string | null;
  reason?: string;
  product: { pages: string[]; summary: string } | null;
  summary?: string;
  additional_products: unknown[];
  excluded: string[];
  out_of_type_facilities: string[];
}

export type ProgressEvent =
  | { type: "stage"; stage: string }
  | { type: "reasoning"; text: string }
  | { type: "tool_use"; tool: string; detail?: string }
  | { type: "done"; status: RunStatus; error_code: string | null; [key: string]: unknown };

async function asJson<T>(resp: Response): Promise<T> {
  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      const body = await resp.json();
      const responseDetail = body.detail;
      detail = typeof responseDetail === "string"
        ? responseDetail
        : JSON.stringify(responseDetail ?? body);
    } catch {
      // response body wasn't JSON; fall back to statusText
    }
    throw new Error(`${resp.status} ${detail}`);
  }
  return resp.json() as Promise<T>;
}

export async function createRun(
  productType: ProductType,
  websiteUrls: string[],
  documents: File[],
): Promise<{ run_id: string }> {
  const form = new FormData();
  form.append("product_type", productType);
  for (const url of websiteUrls) form.append("website_urls", url);
  for (const doc of documents) form.append("documents", doc);
  const resp = await fetch(`${API_BASE}/runs`, { method: "POST", body: form });
  return asJson(resp);
}

export async function getRun(runId: string): Promise<RunDetail> {
  const resp = await fetch(`${API_BASE}/runs/${runId}`, { cache: "no-store" });
  return asJson(resp);
}

export async function listRuns(): Promise<{ runs: RunSummary[] }> {
  const resp = await fetch(`${API_BASE}/runs`, { cache: "no-store" });
  return asJson(resp);
}

export async function getCategoryTaxonomy(productType: ProductType): Promise<CategoryTaxonomy> {
  const params = new URLSearchParams({ product_type: productType });
  const resp = await fetch(`${API_BASE}/taxonomy/categories?${params}`, { cache: "no-store" });
  return asJson(resp);
}

export async function getArtifact<T>(runId: string, name: string): Promise<T> {
  const resp = await fetch(`${API_BASE}/runs/${runId}/artifacts/${name}`, { cache: "no-store" });
  return asJson(resp);
}

export async function getArtifactText(runId: string, name: string): Promise<string> {
  const resp = await fetch(`${API_BASE}/runs/${runId}/artifacts/${name}`, { cache: "no-store" });
  if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
  return resp.text();
}

export function artifactDownloadUrl(runId: string, name: string): string {
  return `${API_BASE}/runs/${runId}/artifacts/${name}`;
}

export async function approveRun(runId: string, fields: Record<string, unknown>): Promise<{ status: string }> {
  const resp = await fetch(`${API_BASE}/runs/${runId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fields }),
  });
  return asJson(resp);
}

export async function cancelRun(
  runId: string,
): Promise<{ run_id: string; status: RunStatus; error_code: string | null }> {
  const resp = await fetch(`${API_BASE}/runs/${runId}/cancel`, { method: "POST" });
  return asJson(resp);
}

export async function deleteRun(runId: string): Promise<void> {
  const resp = await fetch(`${API_BASE}/runs/${runId}`, { method: "DELETE" });
  if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
}

export function eventsUrl(runId: string): string {
  return `${API_BASE}/runs/${runId}/events`;
}
