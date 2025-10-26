import { Requirement } from './patent';

export interface ComplianceResult {
  requirementId: string;
  requirement: string;
  compliance: '○' | '×';
  reason: string;
  evidence: string;
  urls: string[];
}

export interface AnalysisSummary {
  totalRequirements: number;
  compliantRequirements: number;
  complianceRate: number;
  infringementPossibility: '○' | '×';
}

export interface AnalysisResult {
  patentNumber: string;
  companyName: string;
  productName: string;
  timestamp: string;
  requirements: Requirement[];
  complianceResults: ComplianceResult[];
  summary: AnalysisSummary;
}
