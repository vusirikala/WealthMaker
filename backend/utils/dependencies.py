"""FastAPI dependencies for authentication and authorization"""
from fastapi import Request, HTTPException, Depends
from typing import Optional
from datetime import datetime, timezone
from models.user import User
from utils.database import db


async def get_current_user(request: Request) -> Optional[User]:
    """Get current authenticated user from session token"""
    # Check session_token from cookie first
    session_token = request.cookies.get("session_token")
    
    # Fallback to Authorization header
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.replace("Bearer ", "")
    
    if not session_token:
        return None
    
    # Find session in database
    session = await db.user_sessions.find_one({"session_token": session_token})
    if not session:
        return None
    
    # Check if session expired
    expires_at = session["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return None
    
    # Get user
    user_doc = await db.users.find_one({"_id": session["user_id"]})
    if not user_doc:
        return None
    
    return User(**user_doc)


async def require_auth(user: Optional[User] = Depends(get_current_user)) -> User:
    """Require authentication, raise 401 if not authenticated"""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
