"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { getRun } from "@/lib/api";
import { untrackActiveRun, useActiveRunIds } from "@/lib/active-runs";

const POLL_INTERVAL_MS = 5000;

function isViewingRun(runId: string): boolean {
  const params = new URLSearchParams(window.location.search);
  return (
    window.location.pathname === `/runs/${runId}`
    || (window.location.pathname === "/" && params.get("run") === runId)
  );
}

export function RunMonitor() {
  const runIds = useActiveRunIds();
  const router = useRouter();

  useEffect(() => {
    if (runIds.length === 0) return;
    let disposed = false;
    let checking = false;

    const checkRuns = async () => {
      if (checking) return;
      checking = true;
      try {
        await Promise.all(runIds.map(async (runId) => {
          try {
            const run = await getRun(runId);
            if (run.status === "running" || run.status === "queued") return;

            untrackActiveRun(runId);
            if (disposed || isViewingRun(runId)) return;

            const notification = {
              description: run.status === "completed"
                ? "The prepared record is ready in the Library."
                : "The run has finished. Open the Library to review its outcome.",
              action: {
                label: "View Library",
                onClick: () => router.push("/runs"),
              },
              duration: 15000,
            };
            if (run.status === "completed") {
              toast.success("Preparation completed", notification);
            } else {
              toast.info("Preparation finished", notification);
            }
          } catch (error) {
            if (error instanceof Error && error.message.startsWith("404 ")) {
              untrackActiveRun(runId);
            }
            // A temporary backend outage must not discard the active run.
          }
        }));
      } finally {
        checking = false;
      }
    };

    void checkRuns();
    const timer = window.setInterval(() => void checkRuns(), POLL_INTERVAL_MS);
    return () => {
      disposed = true;
      window.clearInterval(timer);
    };
  }, [router, runIds]);

  return null;
}
