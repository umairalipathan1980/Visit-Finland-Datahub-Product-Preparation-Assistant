import { AlertTriangle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ScopeDecision } from "@/lib/api";

export function ScopeReviewCard({ decision }: { decision: ScopeDecision }) {
  return (
    <Card className="border-amber-300/70 bg-amber-50/60 dark:border-amber-800 dark:bg-amber-950/20">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm">
          <AlertTriangle className="size-4 text-amber-600" />
          Product scope needs review
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-1 text-sm text-muted-foreground">
        <p>{decision.reason || decision.error_code || "The product boundary could not be resolved confidently."}</p>
        <p>
          Extraction continued conservatively. Scope-dependent values are marked for review or left missing;
          facts from different candidate products were not combined.
        </p>
      </CardContent>
    </Card>
  );
}
