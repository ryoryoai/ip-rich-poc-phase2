/**
 * Type definitions for analysis pipeline stage outputs.
 */

// Stage 10: Claim Element Extractor
export interface ClaimElement {
  element_no: number;
  quote_text: string;
  plain_description?: string;
  key_terms?: string[];
  term_construction_needed?: boolean;
  depends_on?: number[];
  errors?: string[];
}

export interface ClaimElementExtractorOutput {
  claim_id?: string;
  claim_no?: number;
  elements: ClaimElement[];
  errors?: string[];
}

// Stage 13: Element Assessment (batch)
export type AssessmentStatus =
  | "satisfied"
  | "not_satisfied"
  | "unknown"
  | "depends_on_construction";

export interface SupportingEvidence {
  evidence_id: string;
  quote: string;
  url: string | null;
}

export interface ElementAssessment {
  element_no: number;
  status: AssessmentStatus;
  confidence: number;
  rationale: string;
  supporting_evidence: SupportingEvidence[];
  missing_information: string[];
}

export interface ElementAssessmentOutput {
  assessments: ElementAssessment[];
  errors?: string[];
}

// Stage 14: Claim Decision Aggregator
export type ClaimDecisionStatus =
  | "pass"
  | "fail"
  | "needs_evidence"
  | "needs_construction";

export interface ClaimDecision {
  claim_id: string;
  claim_no?: number;
  decision: ClaimDecisionStatus;
  confidence: number;
  rationale: string;
  element_summary?: Array<{
    element_no: number;
    status: AssessmentStatus;
  }>;
  open_items?: string[];
  errors?: string[];
}

// Stage 15: Case Summary
export interface CaseSummary {
  recommendation: "proceed" | "hold" | "dismiss";
  summary: string;
  best_claims?: number[];
  risks?: string[];
  next_steps?: string[];
  overall_confidence?: number;
  errors?: string[];
}

// Stage 16: Investigation Tasks Generator
export interface InvestigationTask {
  task_id?: string;
  priority: "high" | "medium" | "low";
  category?: string;
  description: string;
  related_claims?: number[];
  related_elements?: number[];
  estimated_effort?: string;
}

export interface InvestigationTasksOutput {
  tasks: InvestigationTask[];
  errors?: string[];
}

// Parsed results structure (per-claim grouping)
export interface ParsedClaimData {
  claim_no: number;
  elements?: ClaimElementExtractorOutput;
  assessment?: ElementAssessmentOutput;
  decision?: ClaimDecision;
}

export interface ParsedResults {
  claims: ParsedClaimData[];
  caseSummary?: CaseSummary;
  investigationTasks?: InvestigationTasksOutput;
  otherStages: Array<{ stage: string; data: unknown }>;
}
