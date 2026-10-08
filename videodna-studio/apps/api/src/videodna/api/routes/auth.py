from __future__ import annotations

from fastapi import APIRouter, Request
from sqlalchemy import select

from videodna.api import schemas as s
from videodna.api.deps import DbDep, RuntimeDep, UserDep, _limiter
from videodna.api.security import create_access_token, hash_password, verify_password
from videodna.db import models as m
from videodna.errors import AppError, ErrorCode

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=s.TokenResponse, status_code=201)
def register(
    req: s.RegisterRequest, db: DbDep, runtime: RuntimeDep, request: Request
) -> s.TokenResponse:
    _limiter().hit(f"auth:{request.client.host if request.client else 'na'}", 20)
    email = req.email.lower()
    if db.scalar(select(m.User).where(m.User.email == email)):
        raise AppError(
            ErrorCode.CONFLICT,
            "Já existe uma conta com este e-mail. Clique em “Entrar” e use sua senha.",
        )
    user = m.User(
        email=email, password_hash=hash_password(req.password), display_name=req.display_name
    )
    db.add(user)
    db.commit()
    return s.TokenResponse(
        access_token=create_access_token(user.id, runtime.settings),
        user=s.UserOut.model_validate(user),
    )


@router.post("/login", response_model=s.TokenResponse)
def login(req: s.LoginRequest, db: DbDep, runtime: RuntimeDep, request: Request) -> s.TokenResponse:
    _limiter().hit(f"auth:{request.client.host if request.client else 'na'}", 20)
    user = db.scalar(select(m.User).where(m.User.email == req.email.lower()))
    if user is None or not verify_password(req.password, user.password_hash):
        raise AppError(
            ErrorCode.UNAUTHORIZED, "E-mail ou senha não conferem. Confira e tente de novo."
        )
    return s.TokenResponse(
        access_token=create_access_token(user.id, runtime.settings),
        user=s.UserOut.model_validate(user),
    )


@router.get("/me", response_model=s.UserOut)
def me(user: UserDep) -> s.UserOut:
    return s.UserOut.model_validate(user)
