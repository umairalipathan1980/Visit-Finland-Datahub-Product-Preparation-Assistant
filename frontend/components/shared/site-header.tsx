"use client";

import Link from "next/link";
import { Layers3, Loader2 } from "lucide-react";
import { useActiveRunIds } from "@/lib/active-runs";

export function SiteHeader() {
  const activeRunIds = useActiveRunIds();
  const activeRunHref = activeRunIds.length === 1
    ? `/?run=${activeRunIds[0]}`
    : "/runs";

  return (
    <header className="border-b border-border/60">
      <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-4 sm:px-6">
        <Link href="/" aria-label="DataHub Studio home" className="group flex items-center gap-6">
          <span className="grid size-[5rem] place-items-center rounded-xl bg-gradient-to-br from-primary to-primary/70 text-primary-foreground shadow-sm ring-1 ring-primary/15 transition-transform group-hover:-rotate-3">
            <Layers3 className="size-10" strokeWidth={2.25} />
          </span>
          <span className="leading-none">
            <span className="block text-[2.5rem] font-semibold tracking-tight text-foreground">
              DataHub <span className="font-normal text-primary">Studio</span>
            </span>
            <span className="mt-2 hidden text-[1.3rem] font-medium uppercase tracking-[0.18em] text-muted-foreground sm:block">
              Product preparation
            </span>
          </span>
        </Link>
        <nav className="flex items-center gap-3 text-sm sm:gap-5">
          {activeRunIds.length > 0 && (
            <Link
              href={activeRunHref}
              className="flex items-center gap-1.5 font-medium text-primary transition-colors hover:text-primary/80"
            >
              <Loader2 className="size-3.5 animate-spin" />
              {activeRunIds.length === 1 ? "Run in progress" : `${activeRunIds.length} runs in progress`}
            </Link>
          )}
          <Link href="/" className="text-muted-foreground transition-colors hover:text-foreground">
            New run
          </Link>
          <Link href="/runs" className="text-muted-foreground transition-colors hover:text-foreground">
            Library
          </Link>
        </nav>
      </div>
    </header>
  );
}
