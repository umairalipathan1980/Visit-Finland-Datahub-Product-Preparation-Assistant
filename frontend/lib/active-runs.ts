"use client";

import { useEffect, useState } from "react";

const STORAGE_KEY = "visit-finland-active-runs";
const CHANGE_EVENT = "visit-finland-active-runs-changed";
const RUN_ID_PATTERN = /^[a-f0-9]{12}$/;

function readActiveRuns(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const value = JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? "[]");
    return Array.isArray(value)
      ? value.filter((item): item is string => typeof item === "string" && RUN_ID_PATTERN.test(item))
      : [];
  } catch {
    return [];
  }
}

function writeActiveRuns(runIds: string[]) {
  if (typeof window === "undefined") return;
  const uniqueRunIds = [...new Set(runIds.filter((id) => RUN_ID_PATTERN.test(id)))];
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(uniqueRunIds));
  window.dispatchEvent(new Event(CHANGE_EVENT));
}

export function trackActiveRun(runId: string) {
  if (!RUN_ID_PATTERN.test(runId)) return;
  writeActiveRuns([...readActiveRuns(), runId]);
}

export function untrackActiveRun(runId: string) {
  writeActiveRuns(readActiveRuns().filter((id) => id !== runId));
}

export function useActiveRunIds(): string[] {
  const [runIds, setRunIds] = useState<string[]>([]);

  useEffect(() => {
    const refresh = () => setRunIds(readActiveRuns());
    const onStorage = (event: StorageEvent) => {
      if (event.key === STORAGE_KEY) refresh();
    };

    refresh();
    window.addEventListener(CHANGE_EVENT, refresh);
    window.addEventListener("storage", onStorage);
    return () => {
      window.removeEventListener(CHANGE_EVENT, refresh);
      window.removeEventListener("storage", onStorage);
    };
  }, []);

  return runIds;
}
