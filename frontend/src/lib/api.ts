/**
 * API client for Phase2 backend
 */

import { supabase } from "@/lib/supabase/client";

const API_BASE = "/api";

async function getAuthHeaders(): Promise<Record<string, string>> {
  if (!supabase) return {};
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

async function fetchApi(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers ?? {});
  const authHeaders = await getAuthHeaders();
  if (authHeaders.Authorization && !headers.has("Authorization")) {
    headers.set("Authorization", authHeaders.Authorization);
  }
  return fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
  });
}

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
  text_raw: string | null;
  text_norm: string | null;
}

export interface ApiError {
  detail: string;
}

export async function resolvePatentNumber(
  input: string
): Promise<ResolveResponse> {
  const response = await fetchApi(
    `/v1/patents/resolve?input=${encodeURIComponent(input)}`
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
  const response = await fetchApi(
    `/v1/patents/${encodeURIComponent(patentId)}/claims/${claimNo}`
  );
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail);
  }
  return response.json();
}

export interface ClaimListResponse {
  patent_id: string;
  version_id: string | null;
  claims: ClaimResponse[];
}

export async function getPatentClaims(
  patentId: string
): Promise<ClaimListResponse> {
  const response = await fetchApi(
    `/v1/patents/${encodeURIComponent(patentId)}/claims`
  );
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail);
  }
  return response.json();
}

export async function checkHealth(): Promise<{ status: string }> {
  const response = await fetchApi("/healthz");
  if (!response.ok) {
    throw new Error("API is not healthy");
  }
  return response.json();
}

// JP Patent Index API
export interface JpIndexNumberAlias {
  type: string;
  number: string;
  is_primary: boolean;
}

export interface JpIndexSearchItem {
  case_id: string;
  application_number: string | null;
  title: string | null;
  status: string | null;
  rights_status?: string | null;
  registration_date?: string | null;
  patent_numbers?: string[];
  last_update_date: string | null;
  numbers: JpIndexNumberAlias[];
}

export interface JpIndexSearchResponse {
  total: number;
  page: number;
  page_size: number;
  items: JpIndexSearchItem[];
}

export interface JpIndexResolveResponse {
  input: string;
  normalized: string;
  number_type: string;
  case_id: string | null;
}

export interface JpIndexCaseDetail {
  case: {
    case_id: string;
    application_number_raw: string | null;
    application_number_norm: string | null;
    filing_date: string | null;
    title: string | null;
    abstract: string | null;
    current_status: string | null;
    rights_status?: string | null;
    status_updated_at: string | null;
    last_update_date: string | null;
    registration_date?: string | null;
    patent_numbers?: string[];
  };
  numbers: Array<{
    type: string;
    number_raw: string | null;
    number_norm: string;
    kind: string | null;
    is_primary: boolean;
  }>;
  documents: Array<{
    doc_type: string;
    publication_number_raw: string | null;
    publication_number_norm: string | null;
    patent_number_raw: string | null;
    patent_number_norm: string | null;
    kind: string | null;
    publication_date: string | null;
  }>;
  applicants: Array<{
    name_raw: string;
    name_norm: string | null;
    role: string;
    is_primary: boolean;
  }>;
  classifications: Array<{
    type: string;
    code: string;
    version: string | null;
    is_primary: boolean;
  }>;
  status_events: Array<{
    event_type: string;
    event_date: string | null;
    source: string | null;
  }>;
  status_snapshots: Array<{
    status: string;
    derived_at: string | null;
    logic_version: string;
    reason: string | null;
  }>;
}

export interface JpIndexChangesResponse {
  from_date: string;
  count: number;
  items: Array<{
    case_id: string;
    application_number: string | null;
    title: string | null;
    status: string | null;
    last_update_date: string | null;
  }>;
}

export interface JpIndexIngestRun {
  batch_id: string;
  source: string;
  run_type: string;
  update_date: string | null;
  status: string;
  started_at: string | null;
  finished_at: string | null;
  counts: Record<string, number> | null;
}

export interface JpIndexIngestRunsResponse {
  items: JpIndexIngestRun[];
}

export async function searchJpIndex(params: {
  q?: string;
  number?: string;
  applicant?: string;
  classification?: string;
  status?: string;
  from_date?: string;
  to_date?: string;
  page?: number;
  page_size?: number;
  sort?: string;
}): Promise<JpIndexSearchResponse> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      query.append(key, String(value));
    }
  });
  const response = await fetchApi(`/v1/jp-index/search?${query.toString()}`);
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail);
  }
  return response.json();
}

export async function resolveJpIndexNumber(input: string): Promise<JpIndexResolveResponse> {
  const response = await fetchApi(
    `/v1/jp-index/resolve?input=${encodeURIComponent(input)}`
  );
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail);
  }
  return response.json();
}

export async function getJpIndexCase(caseId: string): Promise<JpIndexCaseDetail> {
  const response = await fetchApi(`/v1/jp-index/patents/${caseId}`);
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail);
  }
  return response.json();
}

export async function getJpIndexChanges(fromDate: string): Promise<JpIndexChangesResponse> {
  const response = await fetchApi(`/v1/jp-index/changes?from_date=${fromDate}`);
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail);
  }
  return response.json();
}

export async function getJpIndexIngestRuns(limit: number = 50): Promise<JpIndexIngestRunsResponse> {
  const response = await fetchApi(`/v1/jp-index/ingest/runs?limit=${limit}`);
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail);
  }
  return response.json();
}

// Analysis API types
export interface StartAnalysisRequest {
  patent_id: string;
  target_product?: string;
  company_id?: string;
  product_id?: string;
  pipeline: "A" | "B" | "C" | "full";
  claim_nos?: number[];
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
  claim_nos: number[] | null;
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
  const response = await fetchApi(`/v1/analysis/start`, {
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
  const response = await fetchApi(`/v1/analysis/${jobId}`);
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail);
  }
  return response.json();
}

export async function getJobResults(jobId: string): Promise<JobResultsResponse> {
  const response = await fetchApi(`/v1/analysis/${jobId}/results`);
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
  const response = await fetchApi(`/v1/research/start`, {
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
  const response = await fetchApi(
    `/v1/analysis/list?page=${page}&per_page=${perPage}`
  );
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail);
  }
  return response.json();
}

// Retry job
export async function retryJob(jobId: string): Promise<{ job_id: string; status: string }> {
  const response = await fetchApi(`/v1/analysis/${jobId}/retry`, {
    method: "POST",
  });
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail);
  }
  return response.json();
}

// Company/Product master data
export interface CompanyCreateRequest {
  name: string;
  corporate_number?: string;
  country?: string;
  legal_type?: string;
  address_raw?: string;
  address_pref?: string;
  address_city?: string;
  status?: string;
  business_description?: string;
  primary_products?: string;
  market_regions?: string;
  is_listed?: boolean;
  has_jp_entity?: boolean;
  website_url?: string;
  contact_url?: string;
  aliases?: string[];
}

export interface CompanyCreateResponse {
  company_id: string;
  name: string;
  corporate_number: string | null;
  normalized_name: string | null;
  existing: boolean;
}

export interface CompanySearchResult {
  company_id: string;
  name: string;
  corporate_number: string | null;
  normalized_name: string | null;
}

export async function createCompany(
  request: CompanyCreateRequest
): Promise<CompanyCreateResponse> {
  const response = await fetchApi(`/v1/companies`, {
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

export async function searchCompanies(query: string): Promise<CompanySearchResult[]> {
  if (!query) return [];
  const response = await fetchApi(
    `/v1/companies/search?q=${encodeURIComponent(query)}`
  );
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail);
  }
  const data = await response.json();
  return data.results as CompanySearchResult[];
}

export interface ProductCreateRequest {
  company_id: string;
  name: string;
  model_number?: string;
  brand_name?: string;
  category_path?: string;
  description?: string;
  sale_region?: string;
  status?: string;
}

export interface ProductCreateResponse {
  product_id: string;
  name: string;
  model_number: string | null;
  normalized_name: string | null;
  existing: boolean;
}

export interface ProductSearchResult {
  product_id: string;
  company_id: string;
  name: string;
  model_number: string | null;
  normalized_name: string | null;
}

export async function createProduct(
  request: ProductCreateRequest
): Promise<ProductCreateResponse> {
  const response = await fetchApi(`/v1/products`, {
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

export async function searchProducts(query: string): Promise<ProductSearchResult[]> {
  if (!query) return [];
  const response = await fetchApi(
    `/v1/products/search?q=${encodeURIComponent(query)}`
  );
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail);
  }
  const data = await response.json();
  return data.results as ProductSearchResult[];
}

// Review queue
export interface ReviewQueueItem {
  link_id: string;
  company_id: string;
  product_id?: string;
  document_id?: string;
  patent_ref?: string;
  role: string;
  link_type: string;
  confidence_score: number | null;
  review_status?: string;
}

export interface ReviewQueueResponse {
  patent_company_links: ReviewQueueItem[];
  company_product_links: ReviewQueueItem[];
}

export async function fetchReviewQueue(): Promise<ReviewQueueResponse> {
  const response = await fetchApi(`/v1/links/review-queue`);
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail);
  }
  return response.json();
}

export async function reviewCompanyProductLink(
  linkId: string,
  decision: "approve" | "reject",
  reviewedBy?: string,
  note?: string
): Promise<{ link_id: string; review_status: string; link_type: string }> {
  const response = await fetchApi(
    `/v1/links/company-product/${linkId}/review`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision, reviewed_by: reviewedBy, note }),
    }
  );
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail);
  }
  return response.json();
}

export async function reviewPatentCompanyLink(
  linkId: string,
  decision: "approve" | "reject",
  reviewedBy?: string,
  note?: string
): Promise<{ link_id: string; review_status: string; link_type: string }> {
  const response = await fetchApi(
    `/v1/links/patent-company/${linkId}/review`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision, reviewed_by: reviewedBy, note }),
    }
  );
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail);
  }
  return response.json();
}

// Tech keywords
export interface KeywordCreateRequest {
  term: string;
  language?: string;
  synonyms?: string[];
  abbreviations?: string[];
  domain?: string;
  notes?: string;
  source_evidence_id?: string;
}

export interface KeywordCreateResponse {
  keyword_id: string;
  term: string;
  language: string;
  normalized_term: string | null;
  existing: boolean;
}

export interface KeywordSearchResult {
  keyword_id: string;
  term: string;
  language: string;
  synonyms: string[];
  abbreviations: string[];
  domain: string | null;
}

export async function createKeyword(
  request: KeywordCreateRequest
): Promise<KeywordCreateResponse> {
  const response = await fetchApi(`/v1/keywords`, {
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

export async function searchKeywords(
  query: string,
  language?: string
): Promise<KeywordSearchResult[]> {
  if (!query) return [];
  const params = new URLSearchParams({ q: query });
  if (language) {
    params.append("language", language);
  }
  const response = await fetchApi(`/v1/keywords/search?${params.toString()}`);
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail);
  }
  const data = await response.json();
  return data.results as KeywordSearchResult[];
}

// =============================================================================
// Case Management API
// =============================================================================

export interface CaseItem {
  id: string;
  title: string;
  description: string | null;
  status: string;
  assignee_id: string | null;
  patent_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface CaseListResponse {
  cases: CaseItem[];
  total: number;
  page: number;
  per_page: number;
}

export interface CaseTarget {
  id: string;
  target_type: string;
  target_id: string;
  created_at: string;
}

export interface CaseMatchItem {
  id: string;
  match_candidate_id: string;
  reviewer_note: string | null;
  score_total: number | null;
  product_name: string | null;
  company_name: string | null;
  status: string | null;
  created_at: string;
}

export interface CaseDetailResponse {
  case: CaseItem;
  targets: CaseTarget[];
  matches: CaseMatchItem[];
}

export async function getCases(params: {
  status?: string;
  page?: number;
  per_page?: number;
} = {}): Promise<CaseListResponse> {
  const query = new URLSearchParams();
  if (params.status) query.append("status", params.status);
  if (params.page) query.append("page", String(params.page));
  if (params.per_page) query.append("per_page", String(params.per_page));
  const response = await fetchApi(`/v1/cases?${query.toString()}`);
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail);
  }
  return response.json();
}

export async function getCase(caseId: string): Promise<CaseDetailResponse> {
  const response = await fetchApi(`/v1/cases/${caseId}`);
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail);
  }
  return response.json();
}

export async function createCase(request: {
  title: string;
  description?: string;
  patent_id?: string;
}): Promise<CaseItem> {
  const response = await fetchApi("/v1/cases", {
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

export async function updateCase(
  caseId: string,
  request: { title?: string; description?: string; status?: string }
): Promise<CaseItem> {
  const response = await fetchApi(`/v1/cases/${caseId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail);
  }
  return response.json();
}

// =============================================================================
// Match Candidate API
// =============================================================================

export interface MatchItem {
  id: string;
  patent_id: string;
  product_id: string | null;
  company_id: string | null;
  product_name: string | null;
  company_name: string | null;
  score_total: number | null;
  score_coverage: number | null;
  score_evidence_quality: number | null;
  score_blackbox_penalty: number | null;
  score_legal_status: number | null;
  logic_version: string | null;
  analysis_job_id: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface MatchListResponse {
  matches: MatchItem[];
  total: number;
  page: number;
  per_page: number;
}

export async function getMatches(params: {
  patent_id?: string;
  product_id?: string;
  company_id?: string;
  status?: string;
  page?: number;
  per_page?: number;
} = {}): Promise<MatchListResponse> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined) query.append(key, String(value));
  });
  const response = await fetchApi(`/v1/matches?${query.toString()}`);
  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail);
  }
  return response.json();
}
