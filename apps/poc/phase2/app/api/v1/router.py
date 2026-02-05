"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    health,
    patents,
    analysis,
    cron,
    research,
    companies,
    products,
    links,
    evidence,
    ingest,
    jobs,
    jp_index,
    keywords,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(patents.router, prefix="/v1/patents", tags=["patents"])
api_router.include_router(analysis.router, prefix="/v1/analysis", tags=["analysis"])
api_router.include_router(research.router, prefix="/v1/research", tags=["research"])
api_router.include_router(companies.router, prefix="/v1/companies", tags=["companies"])
api_router.include_router(products.router, prefix="/v1/products", tags=["products"])
api_router.include_router(links.router, prefix="/v1/links", tags=["links"])
api_router.include_router(evidence.router, prefix="/v1/evidence", tags=["evidence"])
api_router.include_router(ingest.router, prefix="/v1/ingest", tags=["ingest"])
api_router.include_router(jobs.router, prefix="/v1/jobs", tags=["jobs"])
api_router.include_router(keywords.router, prefix="/v1/keywords", tags=["keywords"])
api_router.include_router(jp_index.router, prefix="/v1/jp-index", tags=["jp-index"])
api_router.include_router(cron.router, prefix="/api/cron", tags=["cron"])
