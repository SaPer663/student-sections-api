from app.schemas.auth import LoginRequest, Token, TokenData
from app.schemas.common import (
    PaginatedResponse,
    PaginationParams,
    SectionFilterParams,
    SortOrder,
    SortParams,
    StudentFilterParams,
)
from app.schemas.role import RoleCreate, RoleResponse, RoleUpdate
from app.schemas.section import (
    SectionCreate,
    SectionDetailResponse,
    SectionResponse,
    SectionUpdate,
    StudentInSectionInfo,
)
from app.schemas.student import (
    EnrollmentRequest,
    StudentCreate,
    StudentDetailResponse,
    StudentResponse,
    StudentSectionInfo,
    StudentUpdate,
)
from app.schemas.user import UserCreate, UserCreateByAdmin, UserInDB, UserResponse, UserUpdate

__all__ = (
    # Auth
    "LoginRequest",
    "Token",
    "TokenData",
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserInDB",
    "UserCreateByAdmin",
    # Role
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",
    # Student
    "StudentCreate",
    "StudentUpdate",
    "StudentResponse",
    "StudentDetailResponse",
    "EnrollmentRequest",
    "StudentSectionInfo",
    # Section
    "SectionCreate",
    "SectionUpdate",
    "SectionResponse",
    "SectionDetailResponse",
    "StudentInSectionInfo",
    # Common
    "PaginationParams",
    "SortParams",
    "SortOrder",
    "PaginatedResponse",
    "StudentFilterParams",
    "SectionFilterParams",
)
