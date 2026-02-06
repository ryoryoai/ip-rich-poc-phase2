"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import type { ElementAssessment, AssessmentStatus } from "@/lib/analysis-types";

const STATUS_CONFIG: Record<
  AssessmentStatus,
  { label: string; bg: string; text: string }
> = {
  satisfied: { label: "充足", bg: "bg-green-100", text: "text-green-800" },
  not_satisfied: { label: "不充足", bg: "bg-red-100", text: "text-red-800" },
  unknown: { label: "不明", bg: "bg-yellow-100", text: "text-yellow-800" },
  depends_on_construction: {
    label: "解釈次第",
    bg: "bg-purple-100",
    text: "text-purple-800",
  },
};

interface AssessmentHeatmapProps {
  assessments: ElementAssessment[];
}

export function AssessmentHeatmap({ assessments }: AssessmentHeatmapProps) {
  if (!assessments || assessments.length === 0) {
    return <p className="text-sm text-muted-foreground">判定データなし</p>;
  }

  return (
    <TooltipProvider>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12">要素</TableHead>
            <TableHead className="w-24">判定</TableHead>
            <TableHead className="w-20">確信度</TableHead>
            <TableHead>理由</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {assessments.map((a) => {
            const config = STATUS_CONFIG[a.status] || STATUS_CONFIG.unknown;
            return (
              <TableRow key={a.element_no}>
                <TableCell className="font-mono text-xs">
                  {a.element_no}
                </TableCell>
                <TableCell>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span
                        className={`inline-block px-2 py-1 rounded text-xs font-medium ${config.bg} ${config.text}`}
                      >
                        {config.label}
                      </span>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>{a.status}</p>
                    </TooltipContent>
                  </Tooltip>
                </TableCell>
                <TableCell className="text-sm">
                  {(a.confidence * 100).toFixed(0)}%
                </TableCell>
                <TableCell className="text-sm max-w-md">
                  <p className="line-clamp-2">{a.rationale}</p>
                  {a.missing_information && a.missing_information.length > 0 && (
                    <p className="text-xs text-amber-600 mt-1">
                      不足情報: {a.missing_information.join(", ")}
                    </p>
                  )}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </TooltipProvider>
  );
}
