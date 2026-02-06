"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { ClaimDecision, ClaimDecisionStatus } from "@/lib/analysis-types";

const DECISION_CONFIG: Record<
  ClaimDecisionStatus,
  { label: string; variant: "default" | "destructive" | "secondary" | "outline" }
> = {
  pass: { label: "侵害の可能性あり", variant: "destructive" },
  fail: { label: "非侵害", variant: "secondary" },
  needs_evidence: { label: "証拠不足", variant: "outline" },
  needs_construction: { label: "解釈要", variant: "outline" },
};

interface ClaimDecisionCardProps {
  decision: ClaimDecision;
}

export function ClaimDecisionCard({ decision }: ClaimDecisionCardProps) {
  const config = DECISION_CONFIG[decision.decision] || DECISION_CONFIG.needs_evidence;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">
            請求項 {decision.claim_no ?? "?"}
          </CardTitle>
          <Badge variant={config.variant}>{config.label}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground mb-2">
          確信度: {(decision.confidence * 100).toFixed(0)}%
        </p>
        <p className="text-sm">{decision.rationale}</p>
        {decision.element_summary && decision.element_summary.length > 0 && (
          <div className="mt-2 flex gap-1 flex-wrap">
            {decision.element_summary.map((es) => (
              <span
                key={es.element_no}
                className={`text-xs px-1.5 py-0.5 rounded ${
                  es.status === "satisfied"
                    ? "bg-green-100 text-green-800"
                    : es.status === "not_satisfied"
                      ? "bg-red-100 text-red-800"
                      : es.status === "depends_on_construction"
                        ? "bg-purple-100 text-purple-800"
                        : "bg-yellow-100 text-yellow-800"
                }`}
              >
                E{es.element_no}
              </span>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
