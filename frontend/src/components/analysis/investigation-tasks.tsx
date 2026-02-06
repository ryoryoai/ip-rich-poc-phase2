"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { InvestigationTask } from "@/lib/analysis-types";

const PRIORITY_CONFIG: Record<
  string,
  { label: string; variant: "default" | "destructive" | "secondary" | "outline" }
> = {
  high: { label: "高", variant: "destructive" },
  medium: { label: "中", variant: "outline" },
  low: { label: "低", variant: "secondary" },
};

interface InvestigationTasksProps {
  tasks: InvestigationTask[];
}

export function InvestigationTasks({ tasks }: InvestigationTasksProps) {
  if (!tasks || tasks.length === 0) {
    return <p className="text-sm text-muted-foreground">調査タスクなし</p>;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>調査タスク</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {tasks.map((task, i) => {
            const config = PRIORITY_CONFIG[task.priority] || PRIORITY_CONFIG.medium;
            return (
              <div
                key={task.task_id || i}
                className="flex items-start gap-3 p-3 rounded-md border"
              >
                <Badge variant={config.variant} className="text-xs shrink-0 mt-0.5">
                  {config.label}
                </Badge>
                <div className="flex-1 min-w-0">
                  <p className="text-sm">{task.description}</p>
                  <div className="flex gap-2 mt-1 flex-wrap">
                    {task.category && (
                      <span className="text-xs text-muted-foreground">
                        {task.category}
                      </span>
                    )}
                    {task.related_claims && task.related_claims.length > 0 && (
                      <span className="text-xs text-muted-foreground">
                        関連請求項: {task.related_claims.join(", ")}
                      </span>
                    )}
                    {task.estimated_effort && (
                      <span className="text-xs text-muted-foreground">
                        {task.estimated_effort}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
