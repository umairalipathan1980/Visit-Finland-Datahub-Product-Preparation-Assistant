import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { RunStatusBadge } from "@/components/shared/status-badge";
import type { ProductType, ScopeDecision } from "@/lib/api";

// The model writes this field freeform (it isn't schema-validated) -- across
// runs it has been seen as a plain string and as { pages, summary }. Both are
// rendered as prose; a string identifier or unrecognized shape falls back to
// stringifying so nothing is silently dropped.
function candidateSummary(candidate: unknown): { summary: string; pages?: string[] } {
  if (typeof candidate === "string") return { summary: candidate };
  if (candidate && typeof candidate === "object" && "summary" in candidate) {
    const c = candidate as { summary: string; pages?: string[] };
    return { summary: c.summary, pages: c.pages };
  }
  return { summary: JSON.stringify(candidate) };
}

export function ScopeAmbiguousCard({
  decision,
  productType,
}: {
  decision: ScopeDecision;
  productType: ProductType;
}) {
  const count = decision.additional_products?.length ?? 0;
  const productLabel = productType === "shops" ? "Shops" : "Accommodation";
  const topSummary =
    decision.product?.summary ??
    decision.summary ??
    // The model leaves `product` null (rather than naming one) when nothing
    // stands out as the natural single candidate -- genuinely N options,
    // not "one plus alternatives". Say that plainly instead of showing nothing.
    `Found ${count} candidate ${productLabel} product${count === 1 ? "" : "s"} with no single one standing out as the intended target.`;

  return (
    <div className="space-y-4">
      <Card className="border-border/60">
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle>More than one {productLabel} product found</CardTitle>
            <CardDescription className="mt-1">{decision.error_code}</CardDescription>
          </div>
          <RunStatusBadge status="scope_ambiguous" />
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">{topSummary}</p>
        </CardContent>
      </Card>

      {decision.additional_products?.length > 0 && (
        <Card className="border-border/60">
          <CardHeader>
            <CardTitle className="text-sm font-medium">Candidate products</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3 text-sm">
              {decision.additional_products.map((p, i) => {
                const { summary, pages } = candidateSummary(p);
                return (
                  <li key={i} className="rounded-md border border-border/60 bg-secondary/30 p-3">
                    <p>{summary}</p>
                    {pages && pages.length > 0 && (
                      <p className="mt-1.5 text-xs text-muted-foreground">
                        Pages: {pages.join(", ")}
                      </p>
                    )}
                  </li>
                );
              })}
            </ul>
          </CardContent>
        </Card>
      )}

      <p className="text-sm text-muted-foreground">
        Start a new run with a URL scoped to a single one of these products to get a record for it.
      </p>
    </div>
  );
}
