"use client";

import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { ClaimElement } from "@/lib/analysis-types";

interface ClaimElementsTableProps {
  elements: ClaimElement[];
}

export function ClaimElementsTable({ elements }: ClaimElementsTableProps) {
  if (!elements || elements.length === 0) {
    return <p className="text-sm text-muted-foreground">要素データなし</p>;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-12">No.</TableHead>
          <TableHead>引用テキスト</TableHead>
          <TableHead>解釈</TableHead>
          <TableHead>キーワード</TableHead>
          <TableHead className="w-20">用語解釈</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {elements.map((el) => (
          <TableRow key={el.element_no}>
            <TableCell className="font-mono text-xs">
              {el.element_no}
            </TableCell>
            <TableCell className="text-sm max-w-xs">
              <p className="line-clamp-3">{el.quote_text}</p>
            </TableCell>
            <TableCell className="text-sm max-w-xs">
              <p className="line-clamp-2 text-muted-foreground">
                {el.plain_description || "-"}
              </p>
            </TableCell>
            <TableCell>
              <div className="flex flex-wrap gap-1">
                {(el.key_terms || []).map((term) => (
                  <Badge key={term} variant="secondary" className="text-xs">
                    {term}
                  </Badge>
                ))}
              </div>
            </TableCell>
            <TableCell>
              {el.term_construction_needed ? (
                <Badge variant="outline" className="text-xs text-amber-600 border-amber-400">
                  要
                </Badge>
              ) : (
                <span className="text-xs text-muted-foreground">-</span>
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
