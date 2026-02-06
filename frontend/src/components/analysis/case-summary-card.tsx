"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { CaseSummary } from "@/lib/analysis-types";

const REC_CONFIG: Record<
  string,
  { label: string; variant: "default" | "destructive" | "secondary" | "outline" }
> = {
  proceed: { label: "調査続行", variant: "destructive" },
  hold: { label: "保留", variant: "outline" },
  dismiss: { label: "棄却", variant: "secondary" },
};

interface CaseSummaryCardProps {
  summary: CaseSummary;
}

export function CaseSummaryCard({ summary }: CaseSummaryCardProps) {
  const config = REC_CONFIG[summary.recommendation] || REC_CONFIG.hold;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>ケースサマリー</CardTitle>
          <Badge variant={config.variant} className="text-sm">
            {config.label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm">{summary.summary}</p>

        {summary.overall_confidence !== undefined && (
          <p className="text-sm text-muted-foreground">
            総合確信度: {(summary.overall_confidence * 100).toFixed(0)}%
          </p>
        )}

        {summary.best_claims && summary.best_claims.length > 0 && (
          <div>
            <h4 className="text-sm font-medium mb-1">有望な請求項</h4>
            <div className="flex gap-1">
              {summary.best_claims.map((cn) => (
                <Badge key={cn} variant="outline" className="text-xs">
                  請求項 {cn}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {summary.risks && summary.risks.length > 0 && (
          <div>
            <h4 className="text-sm font-medium mb-1">リスク</h4>
            <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
              {summary.risks.map((risk, i) => (
                <li key={i}>{risk}</li>
              ))}
            </ul>
          </div>
        )}

        {summary.next_steps && summary.next_steps.length > 0 && (
          <div>
            <h4 className="text-sm font-medium mb-1">次のステップ</h4>
            <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
              {summary.next_steps.map((step, i) => (
                <li key={i}>{step}</li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
