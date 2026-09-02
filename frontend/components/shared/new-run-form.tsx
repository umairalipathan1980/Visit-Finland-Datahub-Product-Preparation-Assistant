"use client";

import { useCallback, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Plus, X, Upload, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { RunProgress } from "@/components/shared/run-progress";
import { createRun, type ProductType } from "@/lib/api";
import { trackActiveRun } from "@/lib/active-runs";
import { toast } from "sonner";

export function NewRunForm({ initialRunId = null }: { initialRunId?: string | null }) {
  const router = useRouter();
  const [productType, setProductType] = useState<ProductType>("accommodation");
  const [urls, setUrls] = useState<string[]>([""]);
  const [documents, setDocuments] = useState<File[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const openResult = useCallback((runId: string) => {
    router.push(`/runs/${runId}`);
  }, [router]);

  function updateUrl(index: number, value: string) {
    setUrls((prev) => prev.map((u, i) => (i === index ? value : u)));
  }

  function addUrlField() {
    setUrls((prev) => [...prev, ""]);
  }

  function removeUrlField(index: number) {
    setUrls((prev) => (prev.length === 1 ? prev : prev.filter((_, i) => i !== index)));
  }

  function onFilesSelected(fileList: FileList | null) {
    if (!fileList) return;
    setDocuments((prev) => [...prev, ...Array.from(fileList)]);
  }

  function removeDocument(index: number) {
    setDocuments((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const cleanUrls = urls.map((u) => u.trim()).filter(Boolean);
    if (cleanUrls.length === 0) {
      toast.error("At least one website URL is required.");
      return;
    }
    setSubmitting(true);
    try {
      const { run_id } = await createRun(productType, cleanUrls, documents);
      trackActiveRun(run_id);
      router.replace(`/?run=${encodeURIComponent(run_id)}`, { scroll: false });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not start the run.");
      setSubmitting(false);
    }
  }

  if (initialRunId) {
    return (
      <div className="space-y-4">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="gap-1.5"
          onClick={() => {
            router.replace("/", { scroll: false });
          }}
        >
          <ArrowLeft className="size-3.5" /> Back to home
        </Button>
        <RunProgress
          key={initialRunId}
          runId={initialRunId}
          onDone={() => openResult(initialRunId)}
        />
      </div>
    );
  }

  return (
    <Card className="border-border/60">
      <CardHeader>
        <CardTitle>New product preparation</CardTitle>
        <CardDescription>
          Choose the DataHub product type, provide one or more pages from the company&apos;s own
          website, and optionally add a brochure or price list.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="product-type">Product</Label>
            <Select value={productType} onValueChange={(value) => setProductType(value as ProductType)}>
              <SelectTrigger id="product-type" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="accommodation">Accommodation</SelectItem>
                <SelectItem value="shops">Shops</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Website URLs</Label>
            <div className="space-y-2">
              {urls.map((url, i) => (
                <div key={i} className="flex gap-2">
                  <Input
                    type="url"
                    placeholder={productType === "shops"
                      ? "https://example.fi/shop"
                      : "https://example.fi/accommodation"}
                    value={url}
                    onChange={(e) => updateUrl(i, e.target.value)}
                    required={i === 0}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => removeUrlField(i)}
                    disabled={urls.length === 1}
                    aria-label="Remove URL"
                  >
                    <X className="size-4" />
                  </Button>
                </div>
              ))}
            </div>
            <Button type="button" variant="outline" size="sm" onClick={addUrlField} className="gap-1.5">
              <Plus className="size-3.5" /> Add another URL
            </Button>
          </div>

          <div className="space-y-2">
            <Label>Documents (optional)</Label>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.docx"
              className="hidden"
              onChange={(e) => onFilesSelected(e.target.files)}
            />
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="gap-1.5"
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload className="size-3.5" /> Upload PDF or DOCX
            </Button>
            {documents.length > 0 && (
              <ul className="mt-2 space-y-1">
                {documents.map((doc, i) => (
                  <li key={i} className="flex items-center justify-between rounded-md border border-border/60 bg-secondary/40 px-3 py-1.5 text-sm">
                    <span className="truncate">{doc.name}</span>
                    <Button type="button" variant="ghost" size="icon" className="size-6" onClick={() => removeDocument(i)}>
                      <X className="size-3.5" />
                    </Button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <Button type="submit" disabled={submitting} className="w-full gap-2">
            {submitting && <Loader2 className="size-4 animate-spin" />}
            {submitting ? "Starting..." : "Start preparation"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
