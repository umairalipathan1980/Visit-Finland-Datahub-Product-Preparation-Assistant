import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { RunStatusBadge } from "@/components/shared/status-badge";

export function OutcomeCard({
  status, errorCode, report, title,
}: {
  status: string;
  errorCode: string | null;
  report: string | null;
  title: string;
}) {
  return (
    <Card className="border-border/60">
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle>{title}</CardTitle>
          {errorCode && <CardDescription className="mt-1">{errorCode}</CardDescription>}
        </div>
        <RunStatusBadge status={status} />
      </CardHeader>
      {report && (
        <CardContent>
          <div className="rounded-md border border-border/60 bg-secondary/30 p-4 text-sm whitespace-pre-wrap">
            {report}
          </div>
        </CardContent>
      )}
    </Card>
  );
}
