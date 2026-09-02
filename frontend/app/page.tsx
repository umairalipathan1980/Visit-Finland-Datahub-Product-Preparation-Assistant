import { NewRunForm } from "@/components/shared/new-run-form";

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ run?: string | string[] }>;
}) {
  const params = await searchParams;
  const requestedRunId = typeof params.run === "string" ? params.run : null;
  const initialRunId = requestedRunId && /^[a-f0-9]{12}$/.test(requestedRunId)
    ? requestedRunId
    : null;

  return (
    <div className="space-y-8">
      <div className="space-y-1.5">
        <h1 className="text-2xl font-semibold tracking-tight">Prepare a DataHub product record</h1>
        <p className="text-sm text-muted-foreground">
          Evidence-grounded extraction for the Visit Finland DataHub — nothing is invented, and
          anything ambiguous is left for you to confirm.
        </p>
      </div>
      <NewRunForm initialRunId={initialRunId} />
    </div>
  );
}
