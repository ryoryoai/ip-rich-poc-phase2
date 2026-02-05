"""Analysis service for running patent infringement investigation pipelines."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core import get_logger
from app.db.models import AnalysisJob, AnalysisResult, Document, Claim, ClaimElement
from app.llm import get_llm_provider, PromptManager

logger = get_logger(__name__)


# Pipeline stage definitions
PIPELINE_STAGES = {
    "A": [
        "01_fetch_planner",
        "02_status_normalizer",
        "03_grant_info_normalizer",
        "04_citations_normalizer",
        "05_documents_metadata_normalizer",
        "06_number_reference_normalizer",
        "07_poll_state_updater",
    ],
    "B": [
        "08_search_seed_generator",
        "09_candidate_ranker",
    ],
    "C": [
        "10_claim_element_extractor",
        "11_evidence_query_builder",
        "12_product_fact_extractor",
        "13_element_assessment",
        "14_claim_decision_aggregator",
        "15_case_summary",
        "16_investigation_tasks_generator",
    ],
}


class AnalysisService:
    """Service for managing and executing analysis pipelines."""

    def __init__(self, db: Session):
        self.db = db
        self.prompt_manager = PromptManager()
        self._llm_provider = None

    @property
    def llm_provider(self):
        """Lazy load LLM provider."""
        if self._llm_provider is None:
            self._llm_provider = get_llm_provider()
        return self._llm_provider

    def create_job(
        self,
        patent_id: str,
        pipeline: str,
        target_product: str | None = None,
        company_id: uuid.UUID | None = None,
        product_id: uuid.UUID | None = None,
    ) -> AnalysisJob:
        """Create a new analysis job."""
        if pipeline not in ["A", "B", "C", "full"]:
            raise ValueError(f"Invalid pipeline: {pipeline}")

        job = AnalysisJob(
            patent_id=patent_id,
            target_product=target_product,
            pipeline=pipeline,
            status="pending",
            context_json={},
            company_id=company_id,
            product_id=product_id,
        )
        self.db.add(job)
        self.db.flush()

        logger.info(
            "Created analysis job",
            job_id=str(job.id),
            patent_id=patent_id,
            pipeline=pipeline,
        )
        return job

    def get_job(self, job_id: uuid.UUID) -> AnalysisJob | None:
        """Get an analysis job by ID."""
        return self.db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()

    def get_job_results(self, job_id: uuid.UUID) -> list[AnalysisResult]:
        """Get all results for a job."""
        return (
            self.db.query(AnalysisResult)
            .filter(AnalysisResult.job_id == job_id)
            .order_by(AnalysisResult.created_at)
            .all()
        )

    def run_job(self, job_id: uuid.UUID) -> AnalysisJob:
        """Run an analysis job synchronously."""
        job = self.get_job(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        if job.status not in ["pending", "failed"]:
            raise ValueError(f"Job cannot be run in status: {job.status}")

        # Mark as running
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        self.db.flush()

        try:
            # Get stages for the pipeline
            stages = self._get_pipeline_stages(job.pipeline)

            # Initialize context
            context = job.context_json or {}
            context = self._initialize_context(job, context)

            for stage in stages:
                job.current_stage = stage
                self.db.flush()

                logger.info("Running stage", job_id=str(job_id), stage=stage)

                try:
                    result = self._run_stage(job, stage, context)

                    # Save result
                    analysis_result = AnalysisResult(
                        job_id=job.id,
                        stage=stage,
                        input_data=result.get("input"),
                        output_data=result.get("output"),
                        llm_model=result.get("model"),
                        tokens_input=result.get("tokens_input"),
                        tokens_output=result.get("tokens_output"),
                        latency_ms=result.get("latency_ms"),
                    )
                    self.db.add(analysis_result)

                    # Update context with output
                    if result.get("output"):
                        context[stage] = result["output"]
                        job.context_json = context

                    # Persist structured outputs when available
                    if stage == "10_claim_element_extractor":
                        self._persist_claim_elements(result.get("output"), context)

                    self.db.flush()

                    # Check for errors
                    if result.get("output", {}).get("errors"):
                        logger.warning(
                            "Stage returned errors",
                            job_id=str(job_id),
                            stage=stage,
                            errors=result["output"]["errors"],
                        )

                except Exception as e:
                    logger.exception("Stage failed", job_id=str(job_id), stage=stage)
                    job.status = "failed"
                    job.error_message = f"Stage {stage} failed: {str(e)}"
                    self.db.flush()
                    return job

            # Mark as completed
            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            job.current_stage = None
            self.db.flush()

            logger.info("Job completed", job_id=str(job_id))

        except Exception as e:
            logger.exception("Job failed", job_id=str(job_id))
            job.status = "failed"
            job.error_message = str(e)
            self.db.flush()

        return job

    def _get_pipeline_stages(self, pipeline: str) -> list[str]:
        """Get the stages for a pipeline."""
        if pipeline == "full":
            return PIPELINE_STAGES["A"] + PIPELINE_STAGES["B"] + PIPELINE_STAGES["C"]
        return PIPELINE_STAGES.get(pipeline, [])

    def _initialize_context(self, job: AnalysisJob, context: dict) -> dict:
        """Initialize context with patent data from database."""
        # Get patent document
        from app.api.v1.endpoints.patents import normalize_patent_number
        from app.jp_index.normalize import normalize_number as normalize_jp_number
        from app.db.models import (
            JpNumberAlias,
            JpCase,
            JpCaseApplicant,
            JpApplicant,
            JpClassification,
        )

        try:
            resolved = normalize_patent_number(job.patent_id)
            doc = (
                self.db.query(Document)
                .filter(
                    Document.country == resolved.country,
                    Document.doc_number == resolved.doc_number,
                )
                .first()
            )

            if doc:
                # Get claims
                claims = (
                    self.db.query(Claim)
                    .filter(Claim.document_id == doc.id)
                    .order_by(Claim.claim_no)
                    .all()
                )

                context["patent_info"] = {
                    "patent_id": job.patent_id,
                    "country": doc.country,
                    "doc_number": doc.doc_number,
                    "kind": doc.kind,
                    "publication_date": str(doc.publication_date) if doc.publication_date else None,
                    "title": doc.title,
                    "abstract": doc.abstract,
                    "assignee": doc.assignee,
                    "filing_date": doc.filing_date,
                }

                context["claims"] = [
                    {"claim_id": str(c.id), "claim_no": c.claim_no, "claim_text": c.claim_text}
                    for c in claims
                ]
        except Exception as e:
            logger.warning("Could not load patent from DB", error=str(e))
            context["patent_info"] = {"patent_id": job.patent_id}
            context["claims"] = []

        # Enrich with JP index metadata (applicants, classifications, status)
        try:
            normalized = normalize_jp_number(job.patent_id)
            if normalized:
                alias = (
                    self.db.query(JpNumberAlias)
                    .filter(
                        JpNumberAlias.number_type == normalized.number_type,
                        JpNumberAlias.number_norm == normalized.number_norm,
                    )
                    .first()
                )
                if not alias and normalized.number_base:
                    alias = (
                        self.db.query(JpNumberAlias)
                        .filter(
                            JpNumberAlias.number_type == normalized.number_type,
                            JpNumberAlias.number_norm.like(f"{normalized.number_base}%"),
                        )
                        .first()
                    )

                if alias:
                    case = (
                        self.db.query(JpCase)
                        .filter(JpCase.id == alias.case_id)
                        .first()
                    )
                else:
                    case = None

                if case:
                    applicants = (
                        self.db.query(JpApplicant, JpCaseApplicant)
                        .join(JpCaseApplicant, JpCaseApplicant.applicant_id == JpApplicant.id)
                        .filter(JpCaseApplicant.case_id == case.id)
                        .all()
                    )
                    classifications = (
                        self.db.query(JpClassification)
                        .filter(JpClassification.case_id == case.id)
                        .all()
                    )

                    context["applicants"] = [
                        {
                            "name": app.name_raw,
                            "role": link.role,
                            "is_primary": link.is_primary,
                        }
                        for app, link in applicants
                    ]
                    context["classifications"] = [
                        {
                            "type": c.type,
                            "code": c.code,
                            "version": c.version,
                            "is_primary": c.is_primary,
                        }
                        for c in classifications
                    ]

                    patent_info = context.get("patent_info", {})
                    if case.title and not patent_info.get("title"):
                        patent_info["title"] = case.title
                    if case.abstract and not patent_info.get("abstract"):
                        patent_info["abstract"] = case.abstract
                    if case.filing_date:
                        patent_info["filing_date"] = case.filing_date.isoformat()
                    patent_info["application_number"] = case.application_number_norm
                    patent_info["status"] = case.current_status
                    context["patent_info"] = patent_info
        except Exception as e:
            logger.warning("Could not load JP index metadata", error=str(e))

        # Load company/product master data if provided
        try:
            from app.db.models import Company, Product, ProductVersion, ProductFact

            if job.company_id:
                company = (
                    self.db.query(Company)
                    .filter(Company.id == job.company_id)
                    .first()
                )
                if company:
                    context["company_profile"] = {
                        "company_id": str(company.id),
                        "name": company.name,
                        "country": company.country,
                        "legal_type": company.legal_type,
                        "business_description": company.business_description,
                        "primary_products": company.primary_products,
                        "market_regions": company.market_regions,
                        "website_url": company.website_url,
                        "contact_url": company.contact_url,
                        "has_jp_entity": company.has_jp_entity,
                    }

            if job.product_id:
                product = (
                    self.db.query(Product)
                    .filter(Product.id == job.product_id)
                    .first()
                )
                if product:
                    context["product_profile"] = {
                        "product_id": str(product.id),
                        "company_id": str(product.company_id),
                        "name": product.name,
                        "brand_name": product.brand_name,
                        "model_number": product.model_number,
                        "category_path": product.category_path,
                        "description": product.description,
                        "sale_region": product.sale_region,
                        "status": product.status,
                    }

                    latest_version = (
                        self.db.query(ProductVersion)
                        .filter(ProductVersion.product_id == product.id)
                        .order_by(ProductVersion.created_at.desc())
                        .first()
                    )
                    if latest_version:
                        facts = (
                            self.db.query(ProductFact)
                            .filter(ProductFact.product_version_id == latest_version.id)
                            .all()
                        )
                        context["product_facts"] = [
                            {"fact_text": fact.fact_text} for fact in facts
                        ]
        except Exception as e:
            logger.warning("Could not load company/product master data", error=str(e))

        if context.get("product_profile") or context.get("company_profile"):
            context["target_product"] = {
                "name": job.target_product,
                "product": context.get("product_profile"),
                "company": context.get("company_profile"),
            }
        else:
            context["target_product"] = job.target_product
        context["today"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        return context

    def _persist_claim_elements(self, output: dict | None, context: dict) -> None:
        """Persist extracted claim elements to the database."""
        if not output or not isinstance(output, dict):
            return

        elements = output.get("elements") or []
        if not isinstance(elements, list) or not elements:
            return

        claim_id = output.get("claim_id")
        if not claim_id:
            claims = context.get("claims") or []
            if claims and isinstance(claims, list):
                claim_id = claims[0].get("claim_id")

        if not claim_id:
            return

        try:
            claim_uuid = uuid.UUID(str(claim_id))
        except ValueError:
            logger.warning("Invalid claim_id in element output", claim_id=claim_id)
            return

        for element in elements:
            if not isinstance(element, dict):
                continue
            try:
                element_no = int(element.get("element_no") or 0)
            except (TypeError, ValueError):
                continue
            quote_text = str(element.get("quote_text") or "")
            normalized_text = element.get("plain_description") or element.get("normalized_text")

            metadata = {
                "plain_description": element.get("plain_description"),
                "key_terms": element.get("key_terms"),
                "term_construction_needed": element.get("term_construction_needed"),
                "depends_on": element.get("depends_on"),
                "errors": element.get("errors"),
            }

            existing = (
                self.db.query(ClaimElement)
                .filter(
                    ClaimElement.claim_id == claim_uuid,
                    ClaimElement.element_no == element_no,
                )
                .first()
            )

            if existing:
                if quote_text:
                    existing.quote_text = quote_text
                if normalized_text:
                    existing.normalized_text = str(normalized_text)
                existing.metadata_json = metadata
                existing.updated_at = datetime.now(timezone.utc)
            else:
                self.db.add(
                    ClaimElement(
                        claim_id=claim_uuid,
                        element_no=element_no,
                        quote_text=quote_text or "",
                        normalized_text=str(normalized_text) if normalized_text else None,
                        metadata_json=metadata,
                    )
                )

    def _run_stage(
        self,
        job: AnalysisJob,
        stage: str,
        context: dict,
    ) -> dict[str, Any]:
        """Run a single stage of the pipeline."""
        # Prepare variables for the prompt
        variables = self._prepare_stage_variables(stage, context)

        # Render prompt
        system_prompt, user_prompt = self.prompt_manager.render(stage, variables)

        # Call LLM
        response = self.llm_provider.call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.0,
        )

        return {
            "input": variables,
            "output": response.parsed_json or {"raw": response.content, "errors": ["JSON parse failed"]},
            "model": response.model,
            "tokens_input": response.tokens_input,
            "tokens_output": response.tokens_output,
            "latency_ms": response.latency_ms,
        }

    def _prepare_stage_variables(self, stage: str, context: dict) -> dict[str, Any]:
        """Prepare variables for a specific stage prompt."""
        variables: dict[str, Any] = {}

        # Common variables
        variables["today"] = context.get("today", "")

        # Stage-specific variable mapping
        if stage == "01_fetch_planner":
            variables["patent_case"] = context.get("patent_info", {})
            variables["poll_state"] = context.get("poll_state", {})
            variables["quota_remaining"] = 100

        elif stage in ["02_status_normalizer", "03_grant_info_normalizer",
                       "04_citations_normalizer", "05_documents_metadata_normalizer",
                       "06_number_reference_normalizer"]:
            variables["raw_response_meta"] = context.get("raw_response_meta", {})
            variables["raw_payload"] = context.get("raw_payload", {})

        elif stage == "07_poll_state_updater":
            variables["current_poll_state"] = context.get("poll_state", {})
            variables["fetch_results"] = context.get("fetch_results", {})

        elif stage == "08_search_seed_generator":
            variables["patent_summary"] = context.get("patent_info", {})
            variables["claim_texts"] = context.get("claims", [])
            variables["classifications"] = context.get("classifications", [])

        elif stage == "09_candidate_ranker":
            variables["target_patent"] = context.get("patent_info", {})
            variables["candidates"] = context.get("candidates", [])

        elif stage == "10_claim_element_extractor":
            # Use claim 1 by default
            claims = context.get("claims", [])
            claim = claims[0] if claims else {"claim_no": 1, "claim_text": ""}
            variables["claim"] = claim

        elif stage == "11_evidence_query_builder":
            variables["claim_elements"] = context.get("10_claim_element_extractor", {}).get("elements", [])
            variables["target_product"] = context.get("target_product", "")

        elif stage == "12_product_fact_extractor":
            variables["evidence_documents"] = context.get("evidence_documents", [])
            variables["target_elements"] = context.get("10_claim_element_extractor", {}).get("elements", [])

        elif stage == "13_element_assessment":
            elements = context.get("10_claim_element_extractor", {}).get("elements", [])
            variables["claim_element"] = elements[0] if elements else {}
            variables["product_facts"] = context.get("12_product_fact_extractor", {}).get("product_facts", [])

        elif stage == "14_claim_decision_aggregator":
            variables["claim_id"] = f"{context.get('patent_info', {}).get('patent_id', '')}_claim1"
            variables["element_assessments"] = context.get("element_assessments", [])

        elif stage == "15_case_summary":
            variables["case_context"] = context.get("patent_info", {})
            variables["claim_decisions"] = context.get("claim_decisions", [])

        elif stage == "16_investigation_tasks_generator":
            variables["open_items"] = context.get("open_items", [])

        return variables
