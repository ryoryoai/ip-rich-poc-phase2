# Data Model Reference

All tables reside in PostgreSQL schema `phase2`. Migrations in `supabase/migrations/`.

## Entity Groups

### 1. Patent Data

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `patents` | Internal patent identity | `internal_patent_id`, jurisdiction, application/publication/registration_no, `tenant_id` |
| `patent_number_sources` | Number normalization sources | patent_id, source_number, number_type |
| `patent_versions` | Version history per patent | patent_id, raw_file_id, kind, publication_date |
| `patent_claims` | Claims per version | version_id, claim_no, text_raw, text_norm |
| `patent_spec_sections` | Specification sections | version_id, section_type, text |
| `documents` | Patent document metadata | country, doc_number, kind, `tenant_id` |
| `document_texts` | Long-form text storage | document_id, text_type, content |
| `claims` | Legacy claim storage | document_id, claim_no, claim_text |
| `claim_elements` | Claim element decomposition | claim_id, element_no, quote_text, `approval_status`, `synonyms`, `claim_set_id` |
| `claim_sets` | Versioned claim sets | patent_id, version_label, source, effective_date |

### 2. Company & Product

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `companies` | Company master | name, corporate_number, `tenant_id` |
| `company_aliases` | Alternative names | company_id, alias |
| `company_identifiers` | External IDs | company_id, id_type, id_value |
| `products` | Product master | company_id, name, model_number, `tenant_id` |
| `product_identifiers` | External IDs | product_id, id_type, id_value |
| `product_versions` | Version history | product_id, version_name |
| `product_facts` | Product attributes | product_id, fact_type, fact_value |
| `tech_keywords` | Technical keywords | keyword, language, domain |

### 3. Evidence & Links

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `evidence` | Evidence from web/docs | url, source_type, quote_text, content_hash |
| `company_evidence_links` | Company-evidence links | company_id, evidence_id |
| `product_evidence_links` | Product-evidence links | product_id, evidence_id |
| `company_product_links` | Company-product relationships | company_id, product_id, link_type |
| `patent_company_links` | Patent-company relationships | document_id, company_id, link_type |

### 4. Analysis Pipeline

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `analysis_jobs` | Pipeline execution job | patent_id, pipeline, status, `claim_nos`, `tenant_id` |
| `analysis_results` | Per-stage output | job_id, stage, output_data, llm_model |
| `analysis_runs` | Legacy Phase1 runs | document_id, status |
| `element_assessments` | Element satisfaction results | claim_element_id, product_id, status |
| `element_assessment_evidence` | Assessment-evidence links | assessment_id, evidence_id |

### 5. Case Management (Phase 1B)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `investigation_cases` | Investigation case | title, status, patent_id, `tenant_id` |
| `case_targets` | Case investigation targets | case_id, target_type, target_id |
| `match_candidates` | Patent x Product candidates | patent_id, product_id, score_total, status, `tenant_id` |
| `case_matches` | Case-candidate links | case_id, match_candidate_id |

### 6. Multi-Tenant & Audit

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `tenants` | Organisation/tenant | name, slug, settings |
| `audit_logs` | Generic operation audit | tenant_id, action, entity_type, entity_id, diff |

### 7. JP Index (Japan Patent Office)

| Table | Purpose |
|-------|---------|
| `jp_cases` | JP patent case master |
| `jp_documents` | JP publication documents |
| `jp_number_aliases` | Number normalization |
| `jp_applicants` | Applicant entities |
| `jp_case_applicants` | Case-applicant links |
| `jp_classifications` | IPC/FI/F-term classifications |
| `jp_status_events` | Legal status events |
| `jp_status_snapshots` | Derived status snapshots |
| `jp_search_documents` | Full-text search index |
| `jp_audit_logs` | JP-specific audit logs |
| `jp_ingest_batches` | Ingestion batch tracking |
| `jp_ingest_batch_files` | Batch file tracking |

### 8. Infrastructure

| Table | Purpose |
|-------|---------|
| `raw_files` | Raw file (ZIP/XML) metadata |
| `ingest_runs` | Ingest run history |
| `ingestion_jobs` | Background ingestion jobs |
| `ingestion_job_items` | Items within ingestion jobs |
| `collection_jobs` | Auto-collection jobs |
| `collection_items` | Collection job items |

## Key Relationships

```
Patent (1) --< PatentVersion (n) --< PatentClaim (n)
Patent (1) --< ClaimSet (n) --< ClaimElement (n)
Company (1) --< Product (n) --< ProductFact (n)
Patent (1) --< MatchCandidate (n) >-- Product (1)
InvestigationCase (1) --< CaseMatch (n) >-- MatchCandidate (1)
InvestigationCase (1) --< CaseTarget (n)
```
