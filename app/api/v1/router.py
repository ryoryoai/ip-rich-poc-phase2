"""API v1 router."""

from fastapi import APIRouter, Depends

from app.api.deps import require_approved_user
from app.api.v1.endpoints import (
    analysis,
    cases,
    collection,
    companies,
    cron,
    evidence,
    health,
    ingest,
    jobs,
    jp_index,
    keywords,
    links,
    matches,
    patents,
    products,
    research,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(
    patents.router,
    prefix="/v1/patents",
    tags=["patents"],
    dependencies=[Depends(require_approved_user)],
)
api_router.include_router(
    analysis.router,
    prefix="/v1/analysis",
    tags=["analysis"],
    dependencies=[Depends(require_approved_user)],
)
api_router.include_router(
    research.router,
    prefix="/v1/research",
    tags=["research"],
    dependencies=[Depends(require_approved_user)],
)
api_router.include_router(
    companies.router,
    prefix="/v1/companies",
    tags=["companies"],
    dependencies=[Depends(require_approved_user)],
)
api_router.include_router(
    products.router,
    prefix="/v1/products",
    tags=["products"],
    dependencies=[Depends(require_approved_user)],
)
api_router.include_router(
    links.router,
    prefix="/v1/links",
    tags=["links"],
    dependencies=[Depends(require_approved_user)],
)
api_router.include_router(
    evidence.router,
    prefix="/v1/evidence",
    tags=["evidence"],
    dependencies=[Depends(require_approved_user)],
)
api_router.include_router(
    ingest.router,
    prefix="/v1/ingest",
    tags=["ingest"],
    dependencies=[Depends(require_approved_user)],
)
api_router.include_router(
    jobs.router,
    prefix="/v1/jobs",
    tags=["jobs"],
    dependencies=[Depends(require_approved_user)],
)
api_router.include_router(
    keywords.router,
    prefix="/v1/keywords",
    tags=["keywords"],
    dependencies=[Depends(require_approved_user)],
)
api_router.include_router(
    jp_index.router,
    prefix="/v1/jp-index",
    tags=["jp-index"],
    dependencies=[Depends(require_approved_user)],
)
api_router.include_router(
    collection.router,
    prefix="/v1/collection",
    tags=["collection"],
    dependencies=[Depends(require_approved_user)],
)
api_router.include_router(
    cases.router,
    prefix="/v1/cases",
    tags=["cases"],
    dependencies=[Depends(require_approved_user)],
)
api_router.include_router(
    matches.router,
    prefix="/v1/matches",
    tags=["matches"],
    dependencies=[Depends(require_approved_user)],
)
api_router.include_router(cron.router, prefix="/api/cron", tags=["cron"])
