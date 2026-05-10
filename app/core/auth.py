from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, Header, HTTPException, status

from app.core.config import settings

Role = str


def get_actor_role(
    x_user_role: str | None = Header(default=None, alias="X-User-Role"),
    x_role_token: str | None = Header(default=None, alias="X-Role-Token"),
) -> Role:
    role = x_user_role or "viewer"
    allowed = {"owner", "marketing_manager", "staff", "viewer"}
    if role not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="허용되지 않은 역할입니다.")

    if settings.app_env != "local" and role != "viewer" and x_role_token != settings.role_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="역할 토큰 검증에 실패했습니다.")

    return role


ROLE_RANK = {
    "viewer": 0,
    "staff": 1,
    "marketing_manager": 2,
    "owner": 3,
}


def require_roles(*roles: Role) -> Callable[[Role], Role]:
    def dependency(actor_role: Role = Depends(get_actor_role)) -> Role:
        if actor_role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
        return actor_role

    return dependency


def require_min_role(min_role: Role) -> Callable[[Role], Role]:
    def dependency(actor_role: Role = Depends(get_actor_role)) -> Role:
        if ROLE_RANK.get(actor_role, -1) < ROLE_RANK[min_role]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
        return actor_role

    return dependency
