/**
 * API client for Phase2 backend
 */

const API_BASE = "/api";

export interface ResolveResponse {
  country: string;
  doc_number: string;
  kind: string | null;
  normalized: string;
}

export interface ClaimResponse {
  patent_id: string;
  claim_no: number;
  claim_text: string;
}

export interface ApiError {
  detail: string;
}

export async function resolvePatentNumber(
  input: string
): Promise<ResolveResponse> {
  const response = await fetch(
    `${API_BASE}/v1/patents/resolve?input=${encodeURIComponent(input)}`
  );
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail);
  }
  return response.json();
}

export async function getClaim(
  patentId: string,
  claimNo: number
): Promise<ClaimResponse> {
  const response = await fetch(
    `${API_BASE}/v1/patents/${encodeURIComponent(patentId)}/claims/${claimNo}`
  );
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail);
  }
  return response.json();
}

export async function checkHealth(): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE}/healthz`);
  if (!response.ok) {
    throw new Error("API is not healthy");
  }
  return response.json();
}

// Analysis API types
export interface StartAnalysisRequest {
  patent_id: string;
  target_product?: string;
  pipeline: "A" | "B" | "C" | "full";
}

export interface StartAnalysisResponse {
  job_id: string;
  status: string;
  patent_id: string;
  pipeline: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: string;
  patent_id: string;
  pipeline: string;
  current_stage: string | null;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface StageResult {
  stage: string;
  output_data: Record<string, unknown> | unknown[] | null;  // list added for Phase1 compatibility
  llm_model: string | null;
  tokens_input: number | null;
  tokens_output: number | null;
  latency_ms: number | null;
  created_at: string;
}

export interface JobResultsResponse {
  job_id: string;
  status: string;
  results: StageResult[];
}

export async function startAnalysis(
  request: StartAnalysisRequest
): Promise<StartAnalysisResponse> {
  const response = await fetch(`${API_BASE}/v1/analysis/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail);
  }
  return response.json();
}

export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  const response = await fetch(`${API_BASE}/v1/analysis/${jobId}`);
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail);
  }
  return response.json();
}

export async function getJobResults(jobId: string): Promise<JobResultsResponse> {
  const response = await fetch(`${API_BASE}/v1/analysis/${jobId}/results`);
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail);
  }
  return response.json();
}

// Deep Research integration
export interface DeepResearchRequest {
  patent_number: string;
  claim_text: string;
  company_name?: string;
  product_name?: string;
}

export interface DeepResearchResponse {
  job_id: string;
  status: string;
  existing?: boolean;
}

export async function startDeepResearch(
  request: DeepResearchRequest
): Promise<DeepResearchResponse> {
  const response = await fetch(`${API_BASE}/v1/research/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail);
  }
  return response.json();
}

// Job list
export interface JobListItem {
  id: string;
  status: string;
  patent_id: string;
  pipeline: string;
  created_at: string;
  completed_at: string | null;
  infringement_score: number | null;
}

export interface JobListResponse {
  jobs: JobListItem[];
  total: number;
  page: number;
  per_page: number;
}

export async function getJobList(
  page: number = 1,
  perPage: number = 20
): Promise<JobListResponse> {
  const response = await fetch(
    `${API_BASE}/v1/analysis/list?page=${page}&per_page=${perPage}`
  );
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail);
  }
  return response.json();
}

// Retry job
export async function retryJob(jobId: string): Promise<{ job_id: string; status: string }> {
  const response = await fetch(`${API_BASE}/v1/analysis/${jobId}/retry`, {
    method: "POST",
  });
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail);
  }
  return response.json();
}
