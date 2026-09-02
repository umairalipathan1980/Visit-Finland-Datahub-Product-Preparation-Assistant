"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, CheckCircle2, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogClose,
} from "@/components/ui/dialog";
import { RunStatusBadge } from "@/components/shared/status-badge";
import { listRuns, deleteRun, type RunSummary } from "@/lib/api";
import { untrackActiveRun } from "@/lib/active-runs";

export default function LibraryPage() {
  const [runs, setRuns] = useState<RunSummary[] | null>(null);
  const [pendingDelete, setPendingDelete] = useState<RunSummary | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    let disposed = false;
    const refresh = async () => {
      try {
        const result = await listRuns();
        if (!disposed) setRuns(result.runs);
      } catch {
        // Keep the last successful list; the next poll may recover.
      }
    };

    void refresh();
    const timer = window.setInterval(() => void refresh(), 5000);
    return () => {
      disposed = true;
      window.clearInterval(timer);
    };
  }, []);

  async function confirmDelete() {
    const target = pendingDelete;
    if (!target) return;
    setDeleting(true);
    try {
      await deleteRun(target.run_id);
      untrackActiveRun(target.run_id);
      setRuns((prev) => prev?.filter((r) => r.run_id !== target.run_id) ?? prev);
      toast.success("Run deleted.");
      setPendingDelete(null);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not delete the run.");
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className="space-y-6">
      <Button
        variant="ghost"
        size="sm"
        className="gap-1.5"
        nativeButton={false}
        render={<Link href="/" />}
      >
        <ArrowLeft className="size-3.5" /> Back
      </Button>

      <div className="space-y-1.5">
        <h1 className="text-2xl font-semibold tracking-tight">Library</h1>
        <p className="text-sm text-muted-foreground">Every preparation run, newest first.</p>
      </div>

      {runs === null && <p className="text-sm text-muted-foreground">Loading…</p>}
      {runs?.length === 0 && (
        <p className="text-sm text-muted-foreground">
          Nothing here yet — <Link href="/" className="text-primary underline underline-offset-2">start a run</Link>.
        </p>
      )}

      <div className="grid gap-3">
        {runs?.map((run) => (
          <Card key={run.run_id} className="border-border/60 transition-colors hover:border-primary/40">
            <CardContent className="flex items-center justify-between py-4">
              <Link href={`/runs/${run.run_id}`} className="min-w-0 flex-1 space-y-1">
                <p className="truncate text-sm font-medium">
                  {run.product_name || run.website_urls[0] || "(unnamed run)"}
                </p>
                <p className="text-xs text-muted-foreground">
                  {run.product_type === "shops" ? "Shops" : "Accommodation"} · {new Date(run.created_at).toLocaleString()}
                </p>
              </Link>
              <div className="flex shrink-0 items-center gap-2">
                {run.approved && <CheckCircle2 className="size-4 text-status-found" />}
                <RunStatusBadge status={run.status} />
                <Button
                  variant="ghost"
                  size="icon-sm"
                  className="text-muted-foreground hover:text-destructive"
                  onClick={() => setPendingDelete(run)}
                >
                  <Trash2 className="size-3.5" />
                  <span className="sr-only">Delete run</span>
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Dialog open={pendingDelete !== null} onOpenChange={(open) => !open && setPendingDelete(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete this run?</DialogTitle>
            <DialogDescription>
              This permanently removes {pendingDelete?.product_name || pendingDelete?.website_urls[0] || "this run"} and every file produced for
              it. This cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <DialogClose render={<Button variant="outline" />}>Cancel</DialogClose>
            <Button variant="destructive" onClick={confirmDelete} disabled={deleting}>
              {deleting ? "Deleting…" : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
