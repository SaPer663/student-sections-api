from fastapi import APIRouter

from app.api.v1.endpoints import auth, sections, students

api_router = APIRouter()

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)

api_router.include_router(
    students.router,
    prefix="/students",
    tags=["Students"],
)

api_router.include_router(
    sections.router,
    prefix="/sections",
    tags=["Sections"],
)
