"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, CheckCircle2, ExternalLink, Plus, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Card, CardContent, CardHeader, CardTitle, CardFooter,
} from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { FieldStatusBadge } from "@/components/shared/status-badge";
import { getFieldSpecs, type FieldSpec } from "@/lib/fields";
import type { CategoryOption, ExtractionResult, FieldEnvelope, FieldEvidence, SourceReference } from "@/lib/api";
import { approveRun, getCategoryTaxonomy } from "@/lib/api";
import { toast } from "sonner";

function asEnvelope(v: unknown): FieldEnvelope {
  return (v as FieldEnvelope) ?? { status: "missing" };
}

type DisplayEvidence = FieldEvidence & {
  locale?: string;
  alternative?: boolean;
};

function envelopeEvidence(
  envelope: FieldEnvelope,
  locale?: string,
): DisplayEvidence[] {
  const direct = (envelope.evidence ?? []).map((entry) => ({ ...entry, locale }));
  const alternatives = (envelope.alternatives ?? []).flatMap((alternative) =>
    alternative.evidence.map((entry) => ({ ...entry, locale, alternative: true })),
  );
  return [...direct, ...alternatives];
}

function fieldEvidence(spec: FieldSpec, raw: unknown): DisplayEvidence[] {
  if (spec.kind !== "localized-text") return envelopeEvidence(asEnvelope(raw));
  const localized = (raw ?? {}) as Record<string, FieldEnvelope>;
  return ["fi", "en"].flatMap((locale) =>
    envelopeEvidence(asEnvelope(localized[locale]), locale),
  );
}

function sourceLabel(source: SourceReference | undefined, sourceId: string): string {
  if (!source) return sourceId;
  return source.title || source.file_name || source.url || sourceId;
}

function EvidenceReferences({
  evidence,
  sourcesById,
}: {
  evidence: DisplayEvidence[];
  sourcesById: Map<string, SourceReference>;
}) {
  if (evidence.length === 0) return null;
  return (
    <div className="space-y-2 border-t border-border/60 pt-3">
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Evidence</p>
      {evidence.map((entry, index) => {
        const source = sourcesById.get(entry.source_id);
        return (
          <div key={`${entry.source_id}-${entry.locator}-${index}`} className="rounded-md bg-secondary/40 p-3 text-xs">
            <blockquote className="text-foreground">&ldquo;{entry.excerpt}&rdquo;</blockquote>
            <div className="mt-1.5 flex flex-wrap items-center gap-x-2 text-muted-foreground">
              {source?.url ? (
                <a
                  href={source.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 font-medium text-primary hover:underline"
                >
                  {sourceLabel(source, entry.source_id)}
                  <ExternalLink className="size-3" />
                </a>
              ) : (
                <span className="font-medium">{sourceLabel(source, entry.source_id)}</span>
              )}
              <span>{entry.source_id}</span>
              {entry.locale && <span>{entry.locale.toUpperCase()}</span>}
              {entry.alternative && <span>Alternative</span>}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function SourcesCard({ sources }: { sources: SourceReference[] }) {
  if (sources.length === 0) return null;
  return (
    <Card className="border-border/60">
      <CardHeader>
        <CardTitle className="text-sm font-medium">Sources used</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2">
          {sources.map((source) => (
            <li key={source.source_id} className="flex items-start justify-between gap-4 text-sm">
              <div className="min-w-0">
                {source.url ? (
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 break-all font-medium text-primary hover:underline"
                  >
                    {sourceLabel(source, source.source_id)}
                    <ExternalLink className="size-3 shrink-0" />
                  </a>
                ) : (
                  <span className="font-medium">{sourceLabel(source, source.source_id)}</span>
                )}
                {source.url && source.title && (
                  <p className="break-all text-xs text-muted-foreground">{source.url}</p>
                )}
              </div>
              <span className="shrink-0 text-xs text-muted-foreground">
                {source.source_id} · {source.citation_count} citation{source.citation_count === 1 ? "" : "s"}
              </span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

type EditableValue = Record<string, unknown>;

const LEGACY_CATEGORY_NAMESPACES = new Set(["accommodation", "amenity", "shops"]);

function plainTaxonomyValue(value: string): string {
  const separator = value.indexOf(".");
  if (separator < 0 || !LEGACY_CATEGORY_NAMESPACES.has(value.slice(0, separator))) return value;
  return value.slice(separator + 1);
}

function normalizeArrayValues(spec: FieldSpec, values: string[]): string[] {
  if (spec.key !== "categories" && spec.key !== "amenities") return values;
  return Array.from(new Set(values.map(plainTaxonomyValue)));
}

function initialState(result: ExtractionResult, fieldSpecs: FieldSpec[]): Record<string, EditableValue> {
  const state: Record<string, EditableValue> = {};
  for (const spec of fieldSpecs) {
    const raw = result.fields[spec.key];
    if (spec.kind === "localized-text") {
      const localized = (raw ?? {}) as Record<string, FieldEnvelope>;
      state[spec.key] = {
        fi: (localized.fi?.value as string) ?? "",
        en: (localized.en?.value as string) ?? "",
      };
    } else if (spec.kind === "object") {
      const env = asEnvelope(raw);
      const value = (env.value as Record<string, unknown>) ?? {};
      const obj: EditableValue = {};
      for (const sub of spec.subfields ?? []) obj[sub.key] = value[sub.key] ?? (sub.type === "boolean" ? false : "");
      state[spec.key] = obj;
    } else if (spec.kind === "array") {
      const env = asEnvelope(raw);
      const values = normalizeArrayValues(spec, (env.value as string[]) ?? []);
      state[spec.key] = { value: spec.key === "categories" ? values : values.join(", ") };
    } else if (spec.kind === "json") {
      const env = asEnvelope(raw);
      state[spec.key] = {
        value: env.value == null ? "" : JSON.stringify(env.value, null, 2),
      };
    } else {
      const env = asEnvelope(raw);
      state[spec.key] = { value: (env.value as string) ?? "" };
    }
  }
  return state;
}

function buildApprovalPayload(
  state: Record<string, EditableValue>,
  fieldSpecs: FieldSpec[],
): Record<string, unknown> {
  const payload: Record<string, unknown> = {};
  for (const spec of fieldSpecs) {
    if (spec.key === "images") continue; // never in scope, never approved
    const entry = state[spec.key];
    if (spec.kind === "localized-text") {
      const out: Record<string, string> = {};
      if (entry.fi) out.fi = String(entry.fi);
      if (entry.en) out.en = String(entry.en);
      if (Object.keys(out).length > 0) payload[spec.key] = out;
    } else if (spec.kind === "object") {
      const out: Record<string, unknown> = {};
      for (const sub of spec.subfields ?? []) {
        const v = entry[sub.key];
        if (sub.type === "boolean") out[sub.key] = Boolean(v);
        else if (sub.type === "number") { if (v !== "" && v != null) out[sub.key] = Number(v); }
        else if (v) out[sub.key] = v;
      }
      if (Object.keys(out).length > 0) payload[spec.key] = out;
    } else if (spec.kind === "array") {
      const rawItems = Array.isArray(entry.value)
        ? entry.value.map(String)
        : String(entry.value ?? "").split(",").map((s) => s.trim()).filter(Boolean);
      const items = normalizeArrayValues(spec, rawItems);
      if (items.length > 0) payload[spec.key] = items;
    } else if (spec.kind === "json") {
      const value = String(entry.value ?? "").trim();
      if (value) payload[spec.key] = JSON.parse(value);
    } else {
      if (entry.value) payload[spec.key] = entry.value;
    }
  }
  return payload;
}

function categoryLabel(category: CategoryOption): string {
  if (category.label_fi && category.label_fi !== category.label_en) {
    return `${category.label_en} / ${category.label_fi}`;
  }
  return category.label_en;
}

function CategoryEditor({
  value, options, loading, error, onChange,
}: {
  value: EditableValue;
  options: CategoryOption[];
  loading: boolean;
  error: string | null;
  onChange: (next: EditableValue) => void;
}) {
  const selected = Array.isArray(value.value) ? value.value.map(String) : [];
  const [pendingCategory, setPendingCategory] = useState<string | null>(null);
  const optionsById = new Map(options.map((option) => [option.id, option]));
  const available = options.filter((option) => !selected.includes(option.id));
  const hasUnknown = !loading && !error && selected.some((id) => !optionsById.has(id));

  function addCategory() {
    if (!pendingCategory || selected.includes(pendingCategory)) return;
    onChange({ value: [...selected, pendingCategory] });
    setPendingCategory(null);
  }

  return (
    <div className="space-y-3">
      <div className="flex min-h-7 flex-wrap gap-2">
        {selected.length === 0 && (
          <p className="text-sm text-muted-foreground">No categories selected.</p>
        )}
        {selected.map((id) => {
          const option = optionsById.get(id);
          const isUnknown = !loading && !error && !option;
          return (
            <Badge key={id} variant={isUnknown ? "destructive" : "secondary"} className="h-7 gap-1.5 pr-1">
              {option ? categoryLabel(option) : id}
              <button
                type="button"
                aria-label={`Remove ${option ? categoryLabel(option) : id}`}
                className="rounded-full p-0.5 hover:bg-foreground/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                onClick={() => onChange({ value: selected.filter((categoryId) => categoryId !== id) })}
              >
                <X className="size-3" />
              </button>
            </Badge>
          );
        })}
      </div>

      <div className="flex max-w-xl gap-2">
        <Select
          value={pendingCategory}
          onValueChange={setPendingCategory}
          disabled={loading || Boolean(error) || available.length === 0}
        >
          <SelectTrigger className="w-full">
            <SelectValue
              placeholder={loading
                ? "Loading categories..."
                : available.length === 0
                  ? "All categories selected"
                  : "Select a category"}
            />
          </SelectTrigger>
          <SelectContent>
            {available.map((option) => (
              <SelectItem key={option.id} value={option.id}>{categoryLabel(option)}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button type="button" variant="outline" onClick={addCategory} disabled={!pendingCategory}>
          <Plus className="size-4" /> Add
        </Button>
      </div>

      {error && <p className="text-xs text-destructive">{error}</p>}
      {hasUnknown && (
        <p className="text-xs text-destructive">
          Remove unknown legacy categories before approving this record.
        </p>
      )}
    </div>
  );
}

function FieldEditor({
  spec, value, categoryOptions, categoryLoading, categoryError, onChange,
}: {
  spec: FieldSpec;
  value: EditableValue;
  categoryOptions: CategoryOption[];
  categoryLoading: boolean;
  categoryError: string | null;
  onChange: (next: EditableValue) => void;
}) {
  if (spec.key === "categories") {
    return (
      <CategoryEditor
        value={value}
        options={categoryOptions}
        loading={categoryLoading}
        error={categoryError}
        onChange={onChange}
      />
    );
  }
  if (spec.kind === "object") {
    return (
      <div className="grid grid-cols-2 gap-3">
        {spec.subfields!.map((sub) => (
          <div key={sub.key} className="space-y-1">
            <Label className="text-xs text-muted-foreground">{sub.label}</Label>
            {sub.type === "boolean" ? (
              <Select
                value={value[sub.key] ? "yes" : "no"}
                onValueChange={(v) => onChange({ ...value, [sub.key]: v === "yes" })}
              >
                <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="yes">Yes</SelectItem>
                  <SelectItem value="no">No</SelectItem>
                </SelectContent>
              </Select>
            ) : (
              <Input
                type={sub.type === "number" ? "number" : "text"}
                value={value[sub.key] as string | number}
                onChange={(e) => onChange({ ...value, [sub.key]: e.target.value })}
              />
            )}
          </div>
        ))}
      </div>
    );
  }
  if (spec.kind === "enum") {
    return (
      <Select value={String(value.value)} onValueChange={(v) => onChange({ value: v })}>
        <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
        <SelectContent>
          {spec.options!.map((opt) => <SelectItem key={opt} value={opt}>{opt}</SelectItem>)}
        </SelectContent>
      </Select>
    );
  }
  if (spec.kind === "localized-text") {
    return (
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <Label className="text-xs text-muted-foreground">Finnish</Label>
          <Input value={value.fi as string} onChange={(e) => onChange({ ...value, fi: e.target.value })} />
        </div>
        <div className="space-y-1">
          <Label className="text-xs text-muted-foreground">English</Label>
          <Input value={value.en as string} onChange={(e) => onChange({ ...value, en: e.target.value })} />
        </div>
      </div>
    );
  }
  if (spec.kind === "json") {
    return (
      <Textarea
        value={String(value.value ?? "")}
        rows={12}
        className="font-mono text-xs"
        onChange={(e) => onChange({ value: e.target.value })}
      />
    );
  }
  if (spec.key === "images") {
    return <p className="text-sm text-muted-foreground">Out of scope for this release.</p>;
  }
  return (
    <Input
      value={value.value as string}
      placeholder={spec.kind === "array" ? "Comma-separated" : undefined}
      onChange={(e) => onChange({ value: e.target.value })}
    />
  );
}

export function ResultReviewForm({
  runId,
  result,
  sources,
}: {
  runId: string;
  result: ExtractionResult;
  sources: SourceReference[];
}) {
  const router = useRouter();
  const fieldSpecs = getFieldSpecs(result.product_type);
  const sourcesById = new Map(sources.map((source) => [source.source_id, source]));
  const [state, setState] = useState(() => initialState(result, fieldSpecs));
  const [submitting, setSubmitting] = useState(false);
  const [approved, setApproved] = useState(false);
  const [categoryOptions, setCategoryOptions] = useState<CategoryOption[]>([]);
  const [categoryLoading, setCategoryLoading] = useState(true);
  const [categoryError, setCategoryError] = useState<string | null>(null);

  useEffect(() => {
    let ignored = false;
    void getCategoryTaxonomy(result.product_type)
      .then((taxonomy) => {
        if (!ignored) setCategoryOptions(taxonomy.categories);
      })
      .catch((error: unknown) => {
        if (!ignored) {
          setCategoryOptions([]);
          setCategoryError(error instanceof Error ? error.message : "Could not load category options.");
        }
      })
      .finally(() => {
        if (!ignored) setCategoryLoading(false);
      });
    return () => {
      ignored = true;
    };
  }, [result.product_type]);

  const selectedCategories = Array.isArray(state.categories?.value)
    ? state.categories.value.map(String)
    : [];
  const hasUnknownCategory = !categoryLoading
    && !categoryError
    && selectedCategories.some((id) => !categoryOptions.some((option) => option.id === id));

  async function handleApprove() {
    setSubmitting(true);
    try {
      await approveRun(runId, buildApprovalPayload(state, fieldSpecs));
      setApproved(true);
      toast.success("Saved as the approved record.");
      router.refresh();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not save the approval.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-4">
      <SourcesCard sources={sources} />
      {fieldSpecs.map((spec) => {
        const raw = result.fields[spec.key];
        const envelope = spec.kind === "localized-text"
          ? asEnvelope((raw as Record<string, FieldEnvelope>)?.fi ?? (raw as Record<string, FieldEnvelope>)?.en)
          : asEnvelope(raw);
        const evidence = fieldEvidence(spec, raw);

        return (
          <Card key={spec.key} className="border-border/60">
            <CardHeader className="flex-row items-center justify-between space-y-0 pb-3">
              <CardTitle className="text-sm font-medium">{spec.label}</CardTitle>
              <FieldStatusBadge status={envelope.status} />
            </CardHeader>
            <CardContent className="space-y-2">
              <FieldEditor
                spec={spec}
                value={state[spec.key]}
                categoryOptions={categoryOptions}
                categoryLoading={categoryLoading}
                categoryError={categoryError}
                onChange={(next) => setState((prev) => ({ ...prev, [spec.key]: next }))}
              />
              <EvidenceReferences evidence={evidence} sourcesById={sourcesById} />
              {envelope.notes && (
                <p className="text-xs text-muted-foreground italic">{envelope.notes}</p>
              )}
            </CardContent>
          </Card>
        );
      })}

      <Card className="border-border/60 bg-secondary/30">
        <CardFooter className="flex items-center justify-between pt-6">
          <p className="text-sm text-muted-foreground">
            {approved
              ? "Approved — saved as approved-product.json for this run."
              : "Review the fields above, correct anything needed, then approve to save the final record."}
          </p>
          <Button onClick={handleApprove} disabled={submitting || hasUnknownCategory} className="gap-2">
            {submitting ? <Loader2 className="size-4 animate-spin" /> : <CheckCircle2 className="size-4" />}
            {approved ? "Re-approve" : "Approve and save"}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
