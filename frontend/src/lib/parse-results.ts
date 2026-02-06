/**
 * Parse raw StageResult[] into structured ParsedResults.
 * Handles both new `:claim_N` suffixed stages and legacy single-claim format.
 */

import type { StageResult } from "@/lib/api";
import type {
  ParsedResults,
  ParsedClaimData,
  ClaimElementExtractorOutput,
  ElementAssessmentOutput,
  ClaimDecision,
  CaseSummary,
  InvestigationTasksOutput,
} from "@/lib/analysis-types";

const CLAIM_SUFFIX_RE = /:claim_(\d+)$/;

function getOrCreateClaim(
  claimsMap: Map<number, ParsedClaimData>,
  claimNo: number
): ParsedClaimData {
  let claim = claimsMap.get(claimNo);
  if (!claim) {
    claim = { claim_no: claimNo };
    claimsMap.set(claimNo, claim);
  }
  return claim;
}

export function parseResults(results: StageResult[]): ParsedResults {
  const claimsMap = new Map<number, ParsedClaimData>();
  let caseSummary: CaseSummary | undefined;
  let investigationTasks: InvestigationTasksOutput | undefined;
  const otherStages: Array<{ stage: string; data: unknown }> = [];

  for (const result of results) {
    const { stage, output_data } = result;
    if (!output_data) continue;

    const data = output_data as Record<string, unknown>;

    // Check for :claim_N suffix
    const suffixMatch = stage.match(CLAIM_SUFFIX_RE);
    const baseName = suffixMatch ? stage.replace(CLAIM_SUFFIX_RE, "") : stage;
    const claimNo = suffixMatch ? parseInt(suffixMatch[1], 10) : null;

    if (baseName.includes("10_claim_element_extractor")) {
      const cn = claimNo ?? (data.claim_no as number | undefined) ?? 1;
      const claim = getOrCreateClaim(claimsMap, cn);
      claim.elements = data as unknown as ClaimElementExtractorOutput;
    } else if (baseName.includes("13_element_assessment")) {
      const cn = claimNo ?? 1;
      const claim = getOrCreateClaim(claimsMap, cn);
      claim.assessment = data as unknown as ElementAssessmentOutput;
    } else if (baseName.includes("14_claim_decision_aggregator")) {
      const cn = claimNo ?? (data.claim_no as number | undefined) ?? 1;
      const claim = getOrCreateClaim(claimsMap, cn);
      claim.decision = data as unknown as ClaimDecision;
    } else if (baseName.includes("15_case_summary")) {
      caseSummary = data as unknown as CaseSummary;
    } else if (baseName.includes("16_investigation_tasks_generator")) {
      investigationTasks = data as unknown as InvestigationTasksOutput;
    } else if (
      baseName.includes("11_evidence_query_builder") ||
      baseName.includes("12_product_fact_extractor")
    ) {
      // Skip intermediate stages from display (data is used internally)
    } else {
      otherStages.push({ stage, data });
    }
  }

  // Sort claims by claim_no
  const claims = Array.from(claimsMap.values()).sort(
    (a, b) => a.claim_no - b.claim_no
  );

  return {
    claims,
    caseSummary,
    investigationTasks,
    otherStages,
  };
}
