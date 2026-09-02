"use client";

import { useEffect, useState } from "react";
import { Check, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { useRunEvents, STAGE_ORDER, STAGE_LABELS } from "@/hooks/use-run-events";
import { cn } from "@/lib/utils";
import { cancelRun } from "@/lib/api";
import { trackActiveRun, untrackActiveRun } from "@/lib/active-runs";
import { Button } from "@/components/ui/button";

export function RunProgress({ runId, onDone }: { runId: string; onDone: () => void }) {
  const { stage, done, backendUnavailable } = useRunEvents(runId);
  const [cancelling, setCancelling] = useState(false);
  const [cancelError, setCancelError] = useState(false);
  const currentIndex = stage ? STAGE_ORDER.indexOf(stage) : -1;

  useEffect(() => {
    trackActiveRun(runId);
  }, [runId]);

  useEffect(() => {
    if (done) {
      untrackActiveRun(runId);
      onDone();
    }
  }, [done, onDone, runId]);

  const cancel = async () => {
    setCancelling(true);
    setCancelError(false);
    try {
      await cancelRun(runId);
      untrackActiveRun(runId);
      onDone();
    } catch {
      setCancelError(true);
    } finally {
      setCancelling(false);
    }
  };

  return (
    <Card className="border-border/60">
      <CardHeader>
        <div className="flex items-center justify-between gap-4">
          <CardTitle>Working on it</CardTitle>
          <Button variant="outline" size="sm" onClick={() => void cancel()} disabled={cancelling}>
            {cancelling ? "Cancelling..." : "Cancel run"}
          </Button>
        </div>
        <CardDescription>
          This runs unattended. You can follow each stage below.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {backendUnavailable && (
          <p role="alert" className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
            The backend is currently unreachable. Progress will resume automatically when the connection returns.
          </p>
        )}
        {cancelError && (
          <p role="alert" className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
            The run could not be cancelled. Check the backend connection and try again.
          </p>
        )}
        <ol className="space-y-2">
          {STAGE_ORDER.slice(1).map((stageName, index) => {
            const stageIndex = index + 1;
            const isDone = currentIndex > stageIndex || (currentIndex === stageIndex && !!done);
            const isCurrent = currentIndex === stageIndex && !done;
            return (
              <li key={stageName} className="flex items-center gap-3 text-sm">
                <span
                  className={cn(
                    "flex size-5 shrink-0 items-center justify-center rounded-full border text-[10px]",
                    isDone && "border-status-found bg-status-found text-status-found-foreground",
                    isCurrent && "border-primary text-primary",
                    !isDone && !isCurrent && "border-border text-muted-foreground",
                  )}
                >
                  {isDone
                    ? <Check className="size-3" />
                    : isCurrent
                      ? <Loader2 className="size-3 animate-spin" />
                      : stageIndex}
                </span>
                <span
                  className={cn(
                    isDone && "text-foreground",
                    isCurrent && "font-medium text-foreground",
                    !isDone && !isCurrent && "text-muted-foreground",
                  )}
                >
                  {STAGE_LABELS[stageName]}
                </span>
              </li>
            );
          })}
        </ol>
      </CardContent>
    </Card>
  );
}
