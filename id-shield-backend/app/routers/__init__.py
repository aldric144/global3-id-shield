from app.routers.auth import router as auth_router
from app.routers.agencies import router as agencies_router
from app.routers.cases import router as cases_router
from app.routers.evidence import router as evidence_router
from app.routers.analysis import router as analysis_router
from app.routers.reports import router as reports_router
from app.routers.bootstrap import router as bootstrap_router
from app.routers.admissibility import router as admissibility_router

__all__ = [
    "auth_router",
    "agencies_router",
    "cases_router",
    "evidence_router",
    "analysis_router",
    "reports_router",
    "bootstrap_router",
    "admissibility_router"
]
