"use client";

import { useEffect, useState } from "react";
import { eventsUrl, getRun, type ProgressEvent } from "@/lib/api";

export const STAGE_ORDER: string[] = [
  "stage_0_bootstrap",
  "stage_1",
  "stage_2",
  "stage_3",
  "stage_4",
  "stage_5",
  "stage_6",
  "stage_7",
];

export const STAGE_LABELS: Record<string, string> = {
  stage_0_bootstrap: "Starting",
  stage_1: "Validating request",
  stage_2: "Parsing documents",
  stage_3: "Retrieving pages",
  stage_4: "Determining product scope",
  stage_5: "Extracting fields",
  stage_6: "Validating extraction",
  stage_7: "Building outputs",
};

interface RunEventsState {
  stage: string | null;
  done: (ProgressEvent & { type: "done" }) | null;
  connected: boolean;
  backendUnavailable: boolean;
}

/** Consumes GET /runs/{id}/events (SSE). Reconnects are not needed: the
 * endpoint replays full history to a fresh connection, so a dropped
 * EventSource can simply be recreated by the browser's own retry logic. */
export function useRunEvents(runId: string | null): RunEventsState {
  const [state, setState] = useState<RunEventsState>({
    stage: null,
    done: null,
    connected: false,
    backendUnavailable: false,
  });
  useEffect(() => {
    if (!runId) return;

    const source = new EventSource(eventsUrl(runId));
    const poll = async () => {
      try {
        const detail = await getRun(runId);
        setState((s) => ({ ...s, backendUnavailable: false }));
        if (detail.status !== "running" && detail.status !== "queued") {
          setState((s) => ({
            ...s,
            done: s.done ?? { type: "done", status: detail.status, error_code: detail.error_code },
          }));
          source.close();
        }
      } catch {
        setState((s) => ({ ...s, connected: false, backendUnavailable: true }));
      }
    };
    const pollTimer = window.setInterval(() => void poll(), 5000);
    void poll();
    source.onopen = () => setState((s) => ({ ...s, connected: true, backendUnavailable: false }));
    source.onmessage = (message) => {
      const event = JSON.parse(message.data) as ProgressEvent;
      setState((s) => {
        if (event.type === "stage") {
          return { ...s, stage: event.stage };
        }
        if (event.type === "done") {
          return { ...s, done: event };
        }
        return s;
      });
      if (event.type === "done") source.close();
    };
    source.onerror = () => {
      setState((s) => ({ ...s, connected: false }));
    };

    return () => {
      window.clearInterval(pollTimer);
      source.close();
    };
  }, [runId]);

  return state;
}


