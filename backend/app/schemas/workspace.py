from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class WorkspaceCurrentOut(BaseModel):
    organization_id: int
    name: str
    slug: str
    domain: str | None = None
    role: str
    is_default: bool = False


class WorkspaceMemberOut(BaseModel):
    user_id: int
    login: str
    email: EmailStr
    name: str | None = None
    company: str | None = None
    role: str
    is_active: bool
    joined_at: datetime
    is_current_user: bool


class WorkspaceMemberRoleUpdateIn(BaseModel):
    role: str = Field(..., min_length=3, max_length=32)


class WorkspaceInviteCreateIn(BaseModel):
    email: EmailStr
    role: str = Field(..., min_length=3, max_length=32)
    expires_in_hours: int = Field(default=72, ge=1, le=24 * 14)


class WorkspaceInviteOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    status: str
    expires_at: datetime
    invited_by_user_id: int | None = None
    created_at: datetime


class WorkspaceInviteCreateOut(BaseModel):
    invitation: WorkspaceInviteOut
    email_sent: bool


class WorkspaceCreateIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    domain: str | None = Field(default=None, max_length=120)


class WorkspaceUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    domain: str | None = Field(default=None, max_length=120)


class IncomingWorkspaceInviteOut(BaseModel):
    id: int
    organization_id: int
    organization_name: str
    organization_slug: str
    organization_domain: str | None = None
    role: str
    status: str
    invited_by_user_id: int | None = None
    invited_by_login: str | None = None
    invited_by_email: str | None = None
    expires_at: datetime
    created_at: datetime


class WorkspaceOwnerTransferIn(BaseModel):
    new_owner_user_id: int = Field(..., ge=1)


class WorkspaceDeleteIn(BaseModel):
    confirm_name: str = Field(..., min_length=1, max_length=120)
