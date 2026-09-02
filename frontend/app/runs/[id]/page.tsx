"use client";

import { use, useCallback, useEffect, useState } from "react";
import { RunProgress } from "@/components/shared/run-progress";
import { ResultReviewForm } from "@/components/shared/result-review-form";
import { OutcomeCard } from "@/components/shared/outcome-card";
import { ScopeAmbiguousCard } from "@/components/shared/scope-ambiguous-card";
import { ScopeReviewCard } from "@/components/shared/scope-review-card";
import Link from "next/link";
import { getRun, getArtifact, getArtifactText, artifactDownloadUrl } from "@/lib/api";
import type { RunDetail, ExtractionResult, ScopeDecision, SourceCatalog, SourceReference } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Download } from "lucide-react";

// Filesystem-safe download filename: decompose accented characters (Finnish
// a/o + diaeresis, etc.) into base letter + combining mark via NFD, then
// drop the combining marks (U+0300-U+036F) and anything else non-ASCII.
function xlsxFilename(id: string, result: ExtractionResult): string {
  const name = result.fields.name as { fi?: { value?: unknown }; en?: { value?: unknown } } | undefined;
  const raw = (name?.fi?.value as string) || (name?.en?.value as string) || "";
  const slug = raw
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return `${slug || id}.xlsx`;
}

const OUTCOME_TITLES: Record<string, string> = {
  unknown: "The backend no longer has an active task for this run",
  interrupted: "The run was interrupted",
  cancelled: "The run was cancelled",
  no_usable_sources: "Nothing citable was retrieved",
  validation_failed: "Extraction did not pass validation",
  execution_failed: "The run broke before finishing",
  input_invalid: "The request was invalid",
};

export default function RunDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [detail, setDetail] = useState<RunDetail | null>(null);
  const [result, setResult] = useState<ExtractionResult | null>(null);
  const [sources, setSources] = useState<SourceReference[]>([]);
  const [scopeDecision, setScopeDecision] = useState<ScopeDecision | null>(null);
  const [report, setReport] = useState<string | null>(null);

  const refresh = useCallback(async (ignore: () => boolean) => {
    const d = await getRun(id);
    if (ignore()) return;
    setDetail(d);
    if (d.status === "completed" && d.artifacts.includes("result.json")) {
      const r = await getArtifact<ExtractionResult>(id, "result.json");
      if (!ignore()) setResult(r);
      if (d.artifacts.includes("sources.json")) {
        const catalog = await getArtifact<SourceCatalog>(id, "sources.json");
        if (!ignore()) setSources(catalog.sources);
      }
      if (d.artifacts.includes("scope-decision.json")) {
        const s = await getArtifact<ScopeDecision>(id, "scope-decision.json");
        if (!ignore()) setScopeDecision(s);
      }
    } else if (d.status === "scope_ambiguous" && d.artifacts.includes("scope-decision.json")) {
      const s = await getArtifact<ScopeDecision>(id, "scope-decision.json");
      if (!ignore()) setScopeDecision(s);
    } else if (d.artifacts.includes("review-report.md")) {
      const t = await getArtifactText(id, "review-report.md");
      if (!ignore()) setReport(t);
    }
  }, [id]);

  useEffect(() => {
    let ignored = false;
    void (async () => {
      await refresh(() => ignored);
    })();
    return () => {
      ignored = true;
    };
  }, [refresh]);

  if (!detail) {
    return <p className="text-sm text-muted-foreground">Loading…</p>;
  }

  if (detail.status === "running" || detail.status === "queued") {
    return (
      <div className="space-y-4">
        <Button variant="ghost" size="sm" className="gap-1.5" nativeButton={false} render={<Link href="/" />}>
          <ArrowLeft className="size-3.5" /> Back to home
        </Button>
        <RunProgress key={id} runId={id} onDone={() => refresh(() => false)} />
      </div>
    );
  }

  if (detail.status === "completed" && result) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              className="gap-1.5"
              nativeButton={false}
              render={<Link href="/runs" />}
            >
              <ArrowLeft className="size-3.5" /> Library
            </Button>
            <h1 className="text-lg font-semibold tracking-tight">
              Review the {result.product_type === "shops" ? "Shops" : "Accommodation"} record
            </h1>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5"
            nativeButton={false}
            render={<a href={artifactDownloadUrl(id, "result.xlsx")} download={xlsxFilename(id, result)} />}
          >
            <Download className="size-3.5" /> Download .xlsx
          </Button>
        </div>
        {scopeDecision?.status === "scope_ambiguous" && <ScopeReviewCard decision={scopeDecision} />}
        <ResultReviewForm runId={id} result={result} sources={sources} />
      </div>
    );
  }

  if (detail.status === "scope_ambiguous" && scopeDecision) {
    return (
      <div className="space-y-4">
        <Button variant="ghost" size="sm" className="gap-1.5" nativeButton={false} render={<Link href="/runs" />}>
          <ArrowLeft className="size-3.5" /> Library
        </Button>
        <ScopeAmbiguousCard decision={scopeDecision} productType={detail.product_type} />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Button variant="ghost" size="sm" className="gap-1.5" nativeButton={false} render={<Link href="/runs" />}>
        <ArrowLeft className="size-3.5" /> Library
      </Button>
      <OutcomeCard
        status={detail.status}
        errorCode={detail.error_code}
        report={report}
        title={OUTCOME_TITLES[detail.status] ?? detail.status}
      />
    </div>
  );
}


