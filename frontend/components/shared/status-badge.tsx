import { Badge } from "@/components/ui/badge";
import { STATUS_LABELS } from "@/lib/fields";
import { cn } from "@/lib/utils";

export function FieldStatusBadge({ status }: { status: string }) {
  const label = STATUS_LABELS[status] ?? status;
  if (status === "found") {
    return (
      <Badge className="bg-status-found text-status-found-foreground border-transparent">
        {label}
      </Badge>
    );
  }
  if (status === "review") {
    return (
      <Badge className="bg-status-review text-status-review-foreground border-transparent">
        {label}
      </Badge>
    );
  }
  if (status === "not_in_scope") {
    return <Badge variant="outline" className="text-muted-foreground">{label}</Badge>;
  }
  return <Badge variant="secondary">{label}</Badge>;
}

const RUN_STATUS_LABELS: Record<string, string> = {
  queued: "Queued",
  interrupted: "Interrupted",
  cancelled: "Cancelled",
  running: "Running",
  unknown: "Unknown",
  completed: "Completed",
  scope_ambiguous: "Scope ambiguous",
  no_usable_sources: "No usable sources",
  validation_failed: "Validation failed",
  execution_failed: "Execution failed",
  input_invalid: "Invalid request",
};

export function RunStatusBadge({ status, className }: { status: string; className?: string }) {
  const label = RUN_STATUS_LABELS[status] ?? status;
  if (status === "completed") {
    return (
      <Badge className={cn("bg-status-found text-status-found-foreground border-transparent", className)}>
        {label}
      </Badge>
    );
  }
  if (status === "running" || status === "queued") {
    return <Badge className={cn("bg-primary text-primary-foreground border-transparent", className)}>{label}</Badge>;
  }
  if (status === "scope_ambiguous") {
    return (
      <Badge className={cn("bg-status-review text-status-review-foreground border-transparent", className)}>
        {label}
      </Badge>
    );
  }
  if (["no_usable_sources", "validation_failed", "execution_failed", "input_invalid", "interrupted"].includes(status)) {
    return <Badge variant="destructive" className={className}>{label}</Badge>;
  }
  return <Badge variant="secondary" className={className}>{label}</Badge>;
}
