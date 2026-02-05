--
-- PostgreSQL database dump
--


-- Dumped from database version 17.6
-- Dumped by pg_dump version 18.1


--
-- Name: phase2; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA IF NOT EXISTS phase2;




--
-- Name: alembic_version; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: analysis_jobs; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.analysis_jobs (
    id uuid NOT NULL,
    status character varying(20) NOT NULL,
    progress integer,
    error_message text,
    patent_id character varying(30) NOT NULL,
    claim_text text,
    company_name text,
    product_name text,
    pipeline character varying(20),
    current_stage character varying(50),
    openai_response_id text,
    input_prompt text,
    research_results json,
    requirements json,
    compliance_results json,
    summary json,
    priority integer,
    scheduled_for timestamp with time zone,
    retry_count integer,
    max_retries integer,
    batch_id text,
    search_type text,
    infringement_score double precision,
    revenue_estimate json,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    queued_at timestamp with time zone,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    context_json json,
    user_id uuid,
    ip_address text,
    company_id uuid,
    product_id uuid
);


--
-- Name: analysis_results; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.analysis_results (
    id uuid NOT NULL,
    job_id uuid NOT NULL,
    stage character varying(50) NOT NULL,
    input_data json,
    output_data json,
    llm_model character varying(50),
    tokens_input integer,
    tokens_output integer,
    latency_ms integer,
    created_at timestamp with time zone
);


--
-- Name: analysis_runs; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.analysis_runs (
    id uuid NOT NULL,
    job_id uuid,
    document_id uuid,
    claim_id uuid,
    model text,
    ruleset_version text,
    raw_output json,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: claim_elements; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.claim_elements (
    id uuid NOT NULL,
    claim_id uuid NOT NULL,
    element_no integer NOT NULL,
    quote_text text NOT NULL,
    normalized_text text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: claims; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.claims (
    id uuid NOT NULL,
    document_id uuid NOT NULL,
    claim_no integer NOT NULL,
    claim_text text NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: companies; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.companies (
    id uuid NOT NULL,
    name text NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    corporate_number character varying(13),
    country character varying(2),
    legal_type character varying(50),
    normalized_name text,
    address_raw text,
    address_pref character varying(20),
    address_city character varying(50),
    status character varying(20),
    is_listed boolean,
    has_jp_entity boolean,
    website_url text,
    contact_url text
);


--
-- Name: company_aliases; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.company_aliases (
    id uuid NOT NULL,
    company_id uuid NOT NULL,
    alias text NOT NULL,
    created_at timestamp with time zone,
    alias_type character varying(30),
    language character varying(8),
    source_evidence_id uuid
);


--
-- Name: company_evidence_links; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.company_evidence_links (
    id uuid NOT NULL,
    company_id uuid NOT NULL,
    evidence_id uuid NOT NULL,
    purpose character varying(50),
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: company_identifiers; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.company_identifiers (
    id uuid NOT NULL,
    company_id uuid NOT NULL,
    id_type character varying(30) NOT NULL,
    value character varying(100) NOT NULL,
    source_evidence_id uuid,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: company_product_links; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.company_product_links (
    id uuid NOT NULL,
    company_id uuid NOT NULL,
    product_id uuid NOT NULL,
    role character varying(30) NOT NULL,
    link_type character varying(20) NOT NULL,
    confidence_score double precision,
    evidence_json jsonb,
    verified_by text,
    verified_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    review_status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    review_note text
);


--
-- Name: documents; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.documents (
    id uuid NOT NULL,
    country character varying(2) NOT NULL,
    doc_number character varying(20) NOT NULL,
    kind character varying(10),
    publication_date date,
    title text,
    abstract text,
    assignee text,
    filing_date character varying(20),
    raw_file_id uuid,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: element_assessment_evidence; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.element_assessment_evidence (
    id uuid NOT NULL,
    assessment_id uuid NOT NULL,
    evidence_id uuid NOT NULL,
    created_at timestamp with time zone
);


--
-- Name: element_assessments; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.element_assessments (
    id uuid NOT NULL,
    analysis_run_id uuid NOT NULL,
    claim_element_id uuid NOT NULL,
    product_version_id uuid NOT NULL,
    status text NOT NULL,
    confidence double precision,
    rationale text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: evidence; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.evidence (
    id uuid NOT NULL,
    url text NOT NULL,
    title text,
    quote_text text,
    retrieved_at timestamp with time zone,
    raw json,
    created_at timestamp with time zone,
    source_type character varying(50),
    captured_at timestamp with time zone,
    content_hash character varying(64),
    content_type character varying(100),
    storage_path text
);


--
-- Name: ingest_runs; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.ingest_runs (
    id uuid NOT NULL,
    run_type character varying(20) NOT NULL,
    started_at timestamp with time zone,
    finished_at timestamp with time zone,
    status character varying(20) NOT NULL,
    detail_json json
);


--
-- Name: jp_applicants; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.jp_applicants (
    id uuid NOT NULL,
    name_raw text NOT NULL,
    name_norm text,
    normalize_confidence double precision,
    source character varying(20),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone
);


--
-- Name: jp_audit_logs; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.jp_audit_logs (
    id uuid NOT NULL,
    action character varying(50) NOT NULL,
    resource_id character varying(64),
    request_path text,
    method character varying(10),
    client_ip character varying(64),
    user_agent text,
    payload_json jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: jp_case_applicants; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.jp_case_applicants (
    id uuid NOT NULL,
    case_id uuid NOT NULL,
    applicant_id uuid NOT NULL,
    role character varying(20) DEFAULT 'applicant'::character varying NOT NULL,
    is_primary boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: jp_cases; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.jp_cases (
    id uuid NOT NULL,
    country character varying(2) DEFAULT 'JP'::character varying NOT NULL,
    application_number_raw character varying(40),
    application_number_norm character varying(40),
    filing_date date,
    title text,
    abstract text,
    current_status character varying(20),
    status_updated_at timestamp with time zone,
    last_update_date date,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone
);


--
-- Name: jp_classifications; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.jp_classifications (
    id uuid NOT NULL,
    case_id uuid NOT NULL,
    type character varying(10) NOT NULL,
    code character varying(64) NOT NULL,
    version character varying(20),
    is_primary boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: jp_documents; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.jp_documents (
    id uuid NOT NULL,
    case_id uuid NOT NULL,
    doc_type character varying(20) NOT NULL,
    publication_number_raw character varying(40),
    publication_number_norm character varying(40),
    patent_number_raw character varying(40),
    patent_number_norm character varying(40),
    kind character varying(10),
    publication_date date,
    raw_file_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone
);


--
-- Name: jp_ingest_batch_files; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.jp_ingest_batch_files (
    id uuid NOT NULL,
    batch_id uuid NOT NULL,
    raw_file_id uuid,
    file_sha256 character varying(64),
    original_name character varying(255),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: jp_ingest_batches; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.jp_ingest_batches (
    id uuid NOT NULL,
    source character varying(50) NOT NULL,
    run_type character varying(20) NOT NULL,
    update_date date,
    batch_key character varying(100) NOT NULL,
    status character varying(20) DEFAULT 'running'::character varying NOT NULL,
    started_at timestamp with time zone,
    finished_at timestamp with time zone,
    counts_json jsonb,
    metadata_json jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: jp_number_aliases; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.jp_number_aliases (
    id uuid NOT NULL,
    case_id uuid NOT NULL,
    document_id uuid,
    number_type character varying(20) NOT NULL,
    number_raw character varying(40),
    number_norm character varying(40) NOT NULL,
    country character varying(2) DEFAULT 'JP'::character varying NOT NULL,
    kind character varying(10),
    is_primary boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: jp_search_documents; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.jp_search_documents (
    id uuid NOT NULL,
    case_id uuid NOT NULL,
    document_id uuid,
    title text,
    abstract text,
    applicants_text text,
    classifications_text text,
    status character varying(20),
    publication_date date,
    tsv tsvector,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone
);


--
-- Name: jp_status_events; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.jp_status_events (
    id uuid NOT NULL,
    case_id uuid NOT NULL,
    event_date date,
    event_type character varying(40) NOT NULL,
    source character varying(40),
    payload_json jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: jp_status_snapshots; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.jp_status_snapshots (
    id uuid NOT NULL,
    case_id uuid NOT NULL,
    status character varying(20) NOT NULL,
    derived_at timestamp with time zone DEFAULT now() NOT NULL,
    logic_version character varying(20) DEFAULT 'v1'::character varying NOT NULL,
    basis_event_ids jsonb,
    reason text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: patent_company_links; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.patent_company_links (
    id uuid NOT NULL,
    document_id uuid,
    patent_ref character varying(40),
    company_id uuid NOT NULL,
    role character varying(30) NOT NULL,
    link_type character varying(20) NOT NULL,
    confidence_score double precision,
    evidence_json jsonb,
    verified_by text,
    verified_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    review_status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    review_note text
);


--
-- Name: patent_sources; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.patent_sources (
    id uuid NOT NULL,
    document_id uuid NOT NULL,
    source text NOT NULL,
    payload json,
    retrieved_at timestamp with time zone,
    created_at timestamp with time zone
);


--
-- Name: product_evidence_links; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.product_evidence_links (
    id uuid NOT NULL,
    product_id uuid NOT NULL,
    product_version_id uuid,
    evidence_id uuid NOT NULL,
    purpose character varying(50),
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: product_facts; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.product_facts (
    id uuid NOT NULL,
    product_version_id uuid NOT NULL,
    fact_text text NOT NULL,
    evidence_id uuid,
    created_at timestamp with time zone
);


--
-- Name: product_identifiers; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.product_identifiers (
    id uuid NOT NULL,
    product_id uuid NOT NULL,
    id_type character varying(30) NOT NULL,
    value character varying(100) NOT NULL,
    source_evidence_id uuid,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: product_versions; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.product_versions (
    id uuid NOT NULL,
    product_id uuid NOT NULL,
    version_name text,
    start_date character varying(20),
    end_date character varying(20),
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: products; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.products (
    id uuid NOT NULL,
    company_id uuid NOT NULL,
    name text NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    model_number text,
    category_path text,
    description text,
    sale_region text,
    normalized_name text,
    status character varying(20)
);


--
-- Name: raw_files; Type: TABLE; Schema: phase2; Owner: -
--

CREATE TABLE IF NOT EXISTS phase2.raw_files (
    id uuid NOT NULL,
    source character varying(50) NOT NULL,
    original_name character varying(255) NOT NULL,
    sha256 character varying(64) NOT NULL,
    stored_path text NOT NULL,
    acquired_at timestamp with time zone,
    metadata_json json,
    created_at timestamp with time zone
);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: analysis_jobs analysis_jobs_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.analysis_jobs
    ADD CONSTRAINT analysis_jobs_pkey PRIMARY KEY (id);


--
-- Name: analysis_results analysis_results_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.analysis_results
    ADD CONSTRAINT analysis_results_pkey PRIMARY KEY (id);


--
-- Name: analysis_runs analysis_runs_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.analysis_runs
    ADD CONSTRAINT analysis_runs_pkey PRIMARY KEY (id);


--
-- Name: claim_elements claim_elements_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.claim_elements
    ADD CONSTRAINT claim_elements_pkey PRIMARY KEY (id);


--
-- Name: claims claims_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.claims
    ADD CONSTRAINT claims_pkey PRIMARY KEY (id);


--
-- Name: companies companies_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.companies
    ADD CONSTRAINT companies_pkey PRIMARY KEY (id);


--
-- Name: company_aliases company_aliases_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.company_aliases
    ADD CONSTRAINT company_aliases_pkey PRIMARY KEY (id);


--
-- Name: company_evidence_links company_evidence_links_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.company_evidence_links
    ADD CONSTRAINT company_evidence_links_pkey PRIMARY KEY (id);


--
-- Name: company_identifiers company_identifiers_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.company_identifiers
    ADD CONSTRAINT company_identifiers_pkey PRIMARY KEY (id);


--
-- Name: company_product_links company_product_links_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.company_product_links
    ADD CONSTRAINT company_product_links_pkey PRIMARY KEY (id);


--
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);


--
-- Name: element_assessment_evidence element_assessment_evidence_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.element_assessment_evidence
    ADD CONSTRAINT element_assessment_evidence_pkey PRIMARY KEY (id);


--
-- Name: element_assessments element_assessments_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.element_assessments
    ADD CONSTRAINT element_assessments_pkey PRIMARY KEY (id);


--
-- Name: evidence evidence_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.evidence
    ADD CONSTRAINT evidence_pkey PRIMARY KEY (id);


--
-- Name: ingest_runs ingest_runs_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.ingest_runs
    ADD CONSTRAINT ingest_runs_pkey PRIMARY KEY (id);


--
-- Name: jp_applicants jp_applicants_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_applicants
    ADD CONSTRAINT jp_applicants_pkey PRIMARY KEY (id);


--
-- Name: jp_audit_logs jp_audit_logs_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_audit_logs
    ADD CONSTRAINT jp_audit_logs_pkey PRIMARY KEY (id);


--
-- Name: jp_case_applicants jp_case_applicants_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_case_applicants
    ADD CONSTRAINT jp_case_applicants_pkey PRIMARY KEY (id);


--
-- Name: jp_cases jp_cases_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_cases
    ADD CONSTRAINT jp_cases_pkey PRIMARY KEY (id);


--
-- Name: jp_classifications jp_classifications_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_classifications
    ADD CONSTRAINT jp_classifications_pkey PRIMARY KEY (id);


--
-- Name: jp_documents jp_documents_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_documents
    ADD CONSTRAINT jp_documents_pkey PRIMARY KEY (id);


--
-- Name: jp_ingest_batch_files jp_ingest_batch_files_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_ingest_batch_files
    ADD CONSTRAINT jp_ingest_batch_files_pkey PRIMARY KEY (id);


--
-- Name: jp_ingest_batches jp_ingest_batches_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_ingest_batches
    ADD CONSTRAINT jp_ingest_batches_pkey PRIMARY KEY (id);


--
-- Name: jp_number_aliases jp_number_aliases_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_number_aliases
    ADD CONSTRAINT jp_number_aliases_pkey PRIMARY KEY (id);


--
-- Name: jp_search_documents jp_search_documents_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_search_documents
    ADD CONSTRAINT jp_search_documents_pkey PRIMARY KEY (id);


--
-- Name: jp_status_events jp_status_events_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_status_events
    ADD CONSTRAINT jp_status_events_pkey PRIMARY KEY (id);


--
-- Name: jp_status_snapshots jp_status_snapshots_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_status_snapshots
    ADD CONSTRAINT jp_status_snapshots_pkey PRIMARY KEY (id);


--
-- Name: patent_company_links patent_company_links_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.patent_company_links
    ADD CONSTRAINT patent_company_links_pkey PRIMARY KEY (id);


--
-- Name: patent_sources patent_sources_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.patent_sources
    ADD CONSTRAINT patent_sources_pkey PRIMARY KEY (id);


--
-- Name: product_evidence_links product_evidence_links_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.product_evidence_links
    ADD CONSTRAINT product_evidence_links_pkey PRIMARY KEY (id);


--
-- Name: product_facts product_facts_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.product_facts
    ADD CONSTRAINT product_facts_pkey PRIMARY KEY (id);


--
-- Name: product_identifiers product_identifiers_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.product_identifiers
    ADD CONSTRAINT product_identifiers_pkey PRIMARY KEY (id);


--
-- Name: product_versions product_versions_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.product_versions
    ADD CONSTRAINT product_versions_pkey PRIMARY KEY (id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- Name: raw_files raw_files_pkey; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.raw_files
    ADD CONSTRAINT raw_files_pkey PRIMARY KEY (id);


--
-- Name: raw_files raw_files_sha256_key; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.raw_files
    ADD CONSTRAINT raw_files_sha256_key UNIQUE (sha256);


--
-- Name: claim_elements uq_claim_elements_claim_element_no; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.claim_elements
    ADD CONSTRAINT uq_claim_elements_claim_element_no UNIQUE (claim_id, element_no);


--
-- Name: claims uq_claims_document_claim_no; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.claims
    ADD CONSTRAINT uq_claims_document_claim_no UNIQUE (document_id, claim_no);


--
-- Name: companies uq_companies_corporate_number; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.companies
    ADD CONSTRAINT uq_companies_corporate_number UNIQUE (corporate_number);


--
-- Name: companies uq_companies_name; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.companies
    ADD CONSTRAINT uq_companies_name UNIQUE (name);


--
-- Name: company_aliases uq_company_aliases_company_alias; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.company_aliases
    ADD CONSTRAINT uq_company_aliases_company_alias UNIQUE (company_id, alias);


--
-- Name: company_evidence_links uq_company_evidence_links; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.company_evidence_links
    ADD CONSTRAINT uq_company_evidence_links UNIQUE (company_id, evidence_id, purpose);


--
-- Name: company_identifiers uq_company_identifiers; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.company_identifiers
    ADD CONSTRAINT uq_company_identifiers UNIQUE (company_id, id_type, value);


--
-- Name: company_product_links uq_company_product_links_company_product_role; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.company_product_links
    ADD CONSTRAINT uq_company_product_links_company_product_role UNIQUE (company_id, product_id, role);


--
-- Name: documents uq_documents_country_number_kind; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.documents
    ADD CONSTRAINT uq_documents_country_number_kind UNIQUE (country, doc_number, kind);


--
-- Name: element_assessment_evidence uq_element_assessment_evidence_assessment_evidence; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.element_assessment_evidence
    ADD CONSTRAINT uq_element_assessment_evidence_assessment_evidence UNIQUE (assessment_id, evidence_id);


--
-- Name: element_assessments uq_element_assessments_run_element_version; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.element_assessments
    ADD CONSTRAINT uq_element_assessments_run_element_version UNIQUE (analysis_run_id, claim_element_id, product_version_id);


--
-- Name: jp_case_applicants uq_jp_case_applicants_case_app_role; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_case_applicants
    ADD CONSTRAINT uq_jp_case_applicants_case_app_role UNIQUE (case_id, applicant_id, role);


--
-- Name: jp_classifications uq_jp_classifications_case_type_code; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_classifications
    ADD CONSTRAINT uq_jp_classifications_case_type_code UNIQUE (case_id, type, code);


--
-- Name: jp_ingest_batch_files uq_jp_ingest_batch_files_batch_raw; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_ingest_batch_files
    ADD CONSTRAINT uq_jp_ingest_batch_files_batch_raw UNIQUE (batch_id, raw_file_id);


--
-- Name: jp_ingest_batches uq_jp_ingest_batches_batch_key; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_ingest_batches
    ADD CONSTRAINT uq_jp_ingest_batches_batch_key UNIQUE (batch_key);


--
-- Name: jp_number_aliases uq_jp_number_aliases_type_norm; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_number_aliases
    ADD CONSTRAINT uq_jp_number_aliases_type_norm UNIQUE (number_type, number_norm);


--
-- Name: jp_search_documents uq_jp_search_documents_case; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_search_documents
    ADD CONSTRAINT uq_jp_search_documents_case UNIQUE (case_id);


--
-- Name: jp_status_events uq_jp_status_events_case; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_status_events
    ADD CONSTRAINT uq_jp_status_events_case UNIQUE (case_id, event_type, event_date, source);


--
-- Name: patent_company_links uq_patent_company_links_doc_patent_company_role; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.patent_company_links
    ADD CONSTRAINT uq_patent_company_links_doc_patent_company_role UNIQUE (document_id, patent_ref, company_id, role);


--
-- Name: product_evidence_links uq_product_evidence_links; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.product_evidence_links
    ADD CONSTRAINT uq_product_evidence_links UNIQUE (product_id, product_version_id, evidence_id);


--
-- Name: product_identifiers uq_product_identifiers; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.product_identifiers
    ADD CONSTRAINT uq_product_identifiers UNIQUE (product_id, id_type, value);


--
-- Name: products uq_products_company_name; Type: CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.products
    ADD CONSTRAINT uq_products_company_name UNIQUE (company_id, name);


--
-- Name: idx_analysis_jobs_batch; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_analysis_jobs_batch ON phase2.analysis_jobs USING btree (batch_id);


--
-- Name: idx_analysis_jobs_company_id; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_analysis_jobs_company_id ON phase2.analysis_jobs USING btree (company_id);


--
-- Name: idx_analysis_jobs_created_at; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_analysis_jobs_created_at ON phase2.analysis_jobs USING btree (created_at);


--
-- Name: idx_analysis_jobs_product_id; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_analysis_jobs_product_id ON phase2.analysis_jobs USING btree (product_id);


--
-- Name: idx_analysis_jobs_queue; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_analysis_jobs_queue ON phase2.analysis_jobs USING btree (status, priority, scheduled_for);


--
-- Name: idx_analysis_jobs_status; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_analysis_jobs_status ON phase2.analysis_jobs USING btree (status);


--
-- Name: idx_analysis_jobs_user_id; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_analysis_jobs_user_id ON phase2.analysis_jobs USING btree (user_id);


--
-- Name: idx_analysis_runs_job; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_analysis_runs_job ON phase2.analysis_runs USING btree (job_id);


--
-- Name: idx_companies_corporate_number; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_companies_corporate_number ON phase2.companies USING btree (corporate_number);


--
-- Name: idx_companies_normalized_name; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_companies_normalized_name ON phase2.companies USING btree (normalized_name);


--
-- Name: idx_company_aliases_alias; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_company_aliases_alias ON phase2.company_aliases USING btree (alias);


--
-- Name: idx_company_evidence_links_company; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_company_evidence_links_company ON phase2.company_evidence_links USING btree (company_id);


--
-- Name: idx_company_identifiers_value; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_company_identifiers_value ON phase2.company_identifiers USING btree (value);


--
-- Name: idx_company_product_links_company; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_company_product_links_company ON phase2.company_product_links USING btree (company_id);


--
-- Name: idx_company_product_links_product; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_company_product_links_product ON phase2.company_product_links USING btree (product_id);


--
-- Name: idx_element_assessments_status; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_element_assessments_status ON phase2.element_assessments USING btree (status);


--
-- Name: idx_evidence_content_hash; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_evidence_content_hash ON phase2.evidence USING btree (content_hash);


--
-- Name: idx_evidence_url; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_evidence_url ON phase2.evidence USING btree (url);


--
-- Name: idx_jp_applicants_name_norm; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_jp_applicants_name_norm ON phase2.jp_applicants USING btree (name_norm);


--
-- Name: idx_jp_audit_logs_action; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_jp_audit_logs_action ON phase2.jp_audit_logs USING btree (action);


--
-- Name: idx_jp_audit_logs_created_at; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_jp_audit_logs_created_at ON phase2.jp_audit_logs USING btree (created_at);


--
-- Name: idx_jp_case_applicants_case; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_jp_case_applicants_case ON phase2.jp_case_applicants USING btree (case_id);


--
-- Name: idx_jp_cases_application_number_norm; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_jp_cases_application_number_norm ON phase2.jp_cases USING btree (application_number_norm);


--
-- Name: idx_jp_cases_last_update_date; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_jp_cases_last_update_date ON phase2.jp_cases USING btree (last_update_date);


--
-- Name: idx_jp_cases_status; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_jp_cases_status ON phase2.jp_cases USING btree (current_status);


--
-- Name: idx_jp_classifications_type_code; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_jp_classifications_type_code ON phase2.jp_classifications USING btree (type, code);


--
-- Name: idx_jp_documents_patent_number_norm; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_jp_documents_patent_number_norm ON phase2.jp_documents USING btree (patent_number_norm);


--
-- Name: idx_jp_documents_publication_number_norm; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_jp_documents_publication_number_norm ON phase2.jp_documents USING btree (publication_number_norm);


--
-- Name: idx_jp_ingest_batch_files_raw_file; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_jp_ingest_batch_files_raw_file ON phase2.jp_ingest_batch_files USING btree (raw_file_id);


--
-- Name: idx_jp_ingest_batches_update_date; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_jp_ingest_batches_update_date ON phase2.jp_ingest_batches USING btree (update_date);


--
-- Name: idx_jp_number_aliases_number_norm; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_jp_number_aliases_number_norm ON phase2.jp_number_aliases USING btree (number_norm);


--
-- Name: idx_jp_search_documents_status; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_jp_search_documents_status ON phase2.jp_search_documents USING btree (status);


--
-- Name: idx_jp_search_documents_tsv; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_jp_search_documents_tsv ON phase2.jp_search_documents USING gin (tsv);


--
-- Name: idx_jp_status_events_case_date; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_jp_status_events_case_date ON phase2.jp_status_events USING btree (case_id, event_date);


--
-- Name: idx_jp_status_snapshots_case; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_jp_status_snapshots_case ON phase2.jp_status_snapshots USING btree (case_id);


--
-- Name: idx_patent_company_links_company; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_patent_company_links_company ON phase2.patent_company_links USING btree (company_id);


--
-- Name: idx_patent_company_links_document; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_patent_company_links_document ON phase2.patent_company_links USING btree (document_id);


--
-- Name: idx_patent_sources_document; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_patent_sources_document ON phase2.patent_sources USING btree (document_id);


--
-- Name: idx_product_evidence_links_product; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_product_evidence_links_product ON phase2.product_evidence_links USING btree (product_id);


--
-- Name: idx_product_facts_version; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_product_facts_version ON phase2.product_facts USING btree (product_version_id);


--
-- Name: idx_product_identifiers_value; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_product_identifiers_value ON phase2.product_identifiers USING btree (value);


--
-- Name: idx_product_versions_product; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_product_versions_product ON phase2.product_versions USING btree (product_id);


--
-- Name: idx_products_model_number; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_products_model_number ON phase2.products USING btree (model_number);


--
-- Name: idx_products_normalized_name; Type: INDEX; Schema: phase2; Owner: -
--

CREATE INDEX IF NOT EXISTS idx_products_normalized_name ON phase2.products USING btree (normalized_name);


--
-- Name: analysis_results analysis_results_job_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.analysis_results
    ADD CONSTRAINT analysis_results_job_id_fkey FOREIGN KEY (job_id) REFERENCES phase2.analysis_jobs(id);


--
-- Name: analysis_runs analysis_runs_claim_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.analysis_runs
    ADD CONSTRAINT analysis_runs_claim_id_fkey FOREIGN KEY (claim_id) REFERENCES phase2.claims(id);


--
-- Name: analysis_runs analysis_runs_document_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.analysis_runs
    ADD CONSTRAINT analysis_runs_document_id_fkey FOREIGN KEY (document_id) REFERENCES phase2.documents(id);


--
-- Name: analysis_runs analysis_runs_job_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.analysis_runs
    ADD CONSTRAINT analysis_runs_job_id_fkey FOREIGN KEY (job_id) REFERENCES phase2.analysis_jobs(id);


--
-- Name: claim_elements claim_elements_claim_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.claim_elements
    ADD CONSTRAINT claim_elements_claim_id_fkey FOREIGN KEY (claim_id) REFERENCES phase2.claims(id);


--
-- Name: claims claims_document_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.claims
    ADD CONSTRAINT claims_document_id_fkey FOREIGN KEY (document_id) REFERENCES phase2.documents(id);


--
-- Name: company_aliases company_aliases_company_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.company_aliases
    ADD CONSTRAINT company_aliases_company_id_fkey FOREIGN KEY (company_id) REFERENCES phase2.companies(id);


--
-- Name: company_evidence_links company_evidence_links_company_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.company_evidence_links
    ADD CONSTRAINT company_evidence_links_company_id_fkey FOREIGN KEY (company_id) REFERENCES phase2.companies(id);


--
-- Name: company_evidence_links company_evidence_links_evidence_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.company_evidence_links
    ADD CONSTRAINT company_evidence_links_evidence_id_fkey FOREIGN KEY (evidence_id) REFERENCES phase2.evidence(id);


--
-- Name: company_identifiers company_identifiers_company_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.company_identifiers
    ADD CONSTRAINT company_identifiers_company_id_fkey FOREIGN KEY (company_id) REFERENCES phase2.companies(id);


--
-- Name: company_identifiers company_identifiers_source_evidence_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.company_identifiers
    ADD CONSTRAINT company_identifiers_source_evidence_id_fkey FOREIGN KEY (source_evidence_id) REFERENCES phase2.evidence(id);


--
-- Name: company_product_links company_product_links_company_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.company_product_links
    ADD CONSTRAINT company_product_links_company_id_fkey FOREIGN KEY (company_id) REFERENCES phase2.companies(id);


--
-- Name: company_product_links company_product_links_product_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.company_product_links
    ADD CONSTRAINT company_product_links_product_id_fkey FOREIGN KEY (product_id) REFERENCES phase2.products(id);


--
-- Name: documents documents_raw_file_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.documents
    ADD CONSTRAINT documents_raw_file_id_fkey FOREIGN KEY (raw_file_id) REFERENCES phase2.raw_files(id);


--
-- Name: element_assessment_evidence element_assessment_evidence_assessment_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.element_assessment_evidence
    ADD CONSTRAINT element_assessment_evidence_assessment_id_fkey FOREIGN KEY (assessment_id) REFERENCES phase2.element_assessments(id);


--
-- Name: element_assessment_evidence element_assessment_evidence_evidence_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.element_assessment_evidence
    ADD CONSTRAINT element_assessment_evidence_evidence_id_fkey FOREIGN KEY (evidence_id) REFERENCES phase2.evidence(id);


--
-- Name: element_assessments element_assessments_analysis_run_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.element_assessments
    ADD CONSTRAINT element_assessments_analysis_run_id_fkey FOREIGN KEY (analysis_run_id) REFERENCES phase2.analysis_runs(id);


--
-- Name: element_assessments element_assessments_claim_element_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.element_assessments
    ADD CONSTRAINT element_assessments_claim_element_id_fkey FOREIGN KEY (claim_element_id) REFERENCES phase2.claim_elements(id);


--
-- Name: element_assessments element_assessments_product_version_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.element_assessments
    ADD CONSTRAINT element_assessments_product_version_id_fkey FOREIGN KEY (product_version_id) REFERENCES phase2.product_versions(id);


--
-- Name: analysis_jobs fk_analysis_jobs_company; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.analysis_jobs
    ADD CONSTRAINT fk_analysis_jobs_company FOREIGN KEY (company_id) REFERENCES phase2.companies(id);


--
-- Name: analysis_jobs fk_analysis_jobs_product; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.analysis_jobs
    ADD CONSTRAINT fk_analysis_jobs_product FOREIGN KEY (product_id) REFERENCES phase2.products(id);


--
-- Name: company_aliases fk_company_aliases_source_evidence; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.company_aliases
    ADD CONSTRAINT fk_company_aliases_source_evidence FOREIGN KEY (source_evidence_id) REFERENCES phase2.evidence(id);


--
-- Name: jp_case_applicants jp_case_applicants_applicant_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_case_applicants
    ADD CONSTRAINT jp_case_applicants_applicant_id_fkey FOREIGN KEY (applicant_id) REFERENCES phase2.jp_applicants(id);


--
-- Name: jp_case_applicants jp_case_applicants_case_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_case_applicants
    ADD CONSTRAINT jp_case_applicants_case_id_fkey FOREIGN KEY (case_id) REFERENCES phase2.jp_cases(id);


--
-- Name: jp_classifications jp_classifications_case_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_classifications
    ADD CONSTRAINT jp_classifications_case_id_fkey FOREIGN KEY (case_id) REFERENCES phase2.jp_cases(id);


--
-- Name: jp_documents jp_documents_case_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_documents
    ADD CONSTRAINT jp_documents_case_id_fkey FOREIGN KEY (case_id) REFERENCES phase2.jp_cases(id);


--
-- Name: jp_documents jp_documents_raw_file_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_documents
    ADD CONSTRAINT jp_documents_raw_file_id_fkey FOREIGN KEY (raw_file_id) REFERENCES phase2.raw_files(id);


--
-- Name: jp_ingest_batch_files jp_ingest_batch_files_batch_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_ingest_batch_files
    ADD CONSTRAINT jp_ingest_batch_files_batch_id_fkey FOREIGN KEY (batch_id) REFERENCES phase2.jp_ingest_batches(id);


--
-- Name: jp_ingest_batch_files jp_ingest_batch_files_raw_file_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_ingest_batch_files
    ADD CONSTRAINT jp_ingest_batch_files_raw_file_id_fkey FOREIGN KEY (raw_file_id) REFERENCES phase2.raw_files(id);


--
-- Name: jp_number_aliases jp_number_aliases_case_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_number_aliases
    ADD CONSTRAINT jp_number_aliases_case_id_fkey FOREIGN KEY (case_id) REFERENCES phase2.jp_cases(id);


--
-- Name: jp_number_aliases jp_number_aliases_document_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_number_aliases
    ADD CONSTRAINT jp_number_aliases_document_id_fkey FOREIGN KEY (document_id) REFERENCES phase2.jp_documents(id);


--
-- Name: jp_search_documents jp_search_documents_case_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_search_documents
    ADD CONSTRAINT jp_search_documents_case_id_fkey FOREIGN KEY (case_id) REFERENCES phase2.jp_cases(id);


--
-- Name: jp_search_documents jp_search_documents_document_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_search_documents
    ADD CONSTRAINT jp_search_documents_document_id_fkey FOREIGN KEY (document_id) REFERENCES phase2.jp_documents(id);


--
-- Name: jp_status_events jp_status_events_case_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_status_events
    ADD CONSTRAINT jp_status_events_case_id_fkey FOREIGN KEY (case_id) REFERENCES phase2.jp_cases(id);


--
-- Name: jp_status_snapshots jp_status_snapshots_case_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.jp_status_snapshots
    ADD CONSTRAINT jp_status_snapshots_case_id_fkey FOREIGN KEY (case_id) REFERENCES phase2.jp_cases(id);


--
-- Name: patent_company_links patent_company_links_company_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.patent_company_links
    ADD CONSTRAINT patent_company_links_company_id_fkey FOREIGN KEY (company_id) REFERENCES phase2.companies(id);


--
-- Name: patent_company_links patent_company_links_document_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.patent_company_links
    ADD CONSTRAINT patent_company_links_document_id_fkey FOREIGN KEY (document_id) REFERENCES phase2.documents(id);


--
-- Name: patent_sources patent_sources_document_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.patent_sources
    ADD CONSTRAINT patent_sources_document_id_fkey FOREIGN KEY (document_id) REFERENCES phase2.documents(id);


--
-- Name: product_evidence_links product_evidence_links_evidence_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.product_evidence_links
    ADD CONSTRAINT product_evidence_links_evidence_id_fkey FOREIGN KEY (evidence_id) REFERENCES phase2.evidence(id);


--
-- Name: product_evidence_links product_evidence_links_product_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.product_evidence_links
    ADD CONSTRAINT product_evidence_links_product_id_fkey FOREIGN KEY (product_id) REFERENCES phase2.products(id);


--
-- Name: product_evidence_links product_evidence_links_product_version_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.product_evidence_links
    ADD CONSTRAINT product_evidence_links_product_version_id_fkey FOREIGN KEY (product_version_id) REFERENCES phase2.product_versions(id);


--
-- Name: product_facts product_facts_evidence_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.product_facts
    ADD CONSTRAINT product_facts_evidence_id_fkey FOREIGN KEY (evidence_id) REFERENCES phase2.evidence(id);


--
-- Name: product_facts product_facts_product_version_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.product_facts
    ADD CONSTRAINT product_facts_product_version_id_fkey FOREIGN KEY (product_version_id) REFERENCES phase2.product_versions(id);


--
-- Name: product_identifiers product_identifiers_product_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.product_identifiers
    ADD CONSTRAINT product_identifiers_product_id_fkey FOREIGN KEY (product_id) REFERENCES phase2.products(id);


--
-- Name: product_identifiers product_identifiers_source_evidence_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.product_identifiers
    ADD CONSTRAINT product_identifiers_source_evidence_id_fkey FOREIGN KEY (source_evidence_id) REFERENCES phase2.evidence(id);


--
-- Name: product_versions product_versions_product_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.product_versions
    ADD CONSTRAINT product_versions_product_id_fkey FOREIGN KEY (product_id) REFERENCES phase2.products(id);


--
-- Name: products products_company_id_fkey; Type: FK CONSTRAINT; Schema: phase2; Owner: -
--

ALTER TABLE ONLY phase2.products
    ADD CONSTRAINT products_company_id_fkey FOREIGN KEY (company_id) REFERENCES phase2.companies(id);


--
-- PostgreSQL database dump complete
--


