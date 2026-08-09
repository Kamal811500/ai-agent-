"""Authentication routes."""
from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
async def login():
    """Login endpoint."""
    return {"token": "placeholder"}

@router.post("/logout")
async def logout():
    """Logout endpoint."""
    return {"status": "logged out"}
