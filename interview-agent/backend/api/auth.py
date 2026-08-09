"""
Simple email-based authentication.
Demo-grade: no passwords, no email verification.
Production would use OAuth2 / JWT with email verification.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["auth"])

# In-memory session store (demo — not persistent across restarts)
_sessions: dict[str, dict] = {}
_users_by_email: dict[str, dict] = {}


class LoginRequest(BaseModel):
    email: str
    name: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    token: str


@router.post("/login", response_model=UserResponse)
async def login(req: LoginRequest):
    email = req.email.strip().lower()
    name = req.name.strip()

    if not email or "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")
    if len(name) < 2:
        raise HTTPException(status_code=400, detail="Please enter your full name (min 2 characters).")

    # Get or create user
    if email in _users_by_email:
        user = _users_by_email[email]
        user["name"] = name
    else:
        user = {
            "id": f"usr_{uuid.uuid4().hex[:12]}",
            "email": email,
            "name": name,
            "created_at": datetime.utcnow().isoformat(),
            "interview_count": 0,
        }
        _users_by_email[email] = user

    # Issue session token
    token = uuid.uuid4().hex
    user["token"] = token
    _sessions[token] = user

    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        token=token,
    )


@router.get("/me")
async def health():
    return {"status": "ok"}
