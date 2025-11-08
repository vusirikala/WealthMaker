"""Authentication routes"""
from fastapi import APIRouter, HTTPException, Request, Response, Depends
from datetime import datetime, timezone, timedelta
import httpx
import logging
from models.user import User
from utils.database import db
from utils.dependencies import require_auth

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.get("/me")
async def get_me(user: User = Depends(require_auth)):
    """Get current authenticated user"""
    return user


@router.post("/session")
async def process_session(request: Request, response: Response):
    """Process Emergent authentication session"""
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        logger.error("No session ID in request")
        raise HTTPException(status_code=400, detail="Session ID required")
    
    logger.info(f"Processing session ID: {session_id[:10]}...")
    
    # Call Emergent auth service
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": session_id}
            )
            resp.raise_for_status()
            session_data = resp.json()
            logger.info(f"Successfully got session data for user: {session_data.get('email')}")
        except Exception as e:
            logger.error(f"Failed to get session data: {e}")
            raise HTTPException(status_code=400, detail="Invalid session")
    
    # Check if user exists
    existing_user = await db.users.find_one({"_id": session_data["id"]})
    if not existing_user:
        # Create new user
        user_doc = {
            "_id": session_data["id"],
            "email": session_data["email"],
            "name": session_data["name"],
            "picture": session_data.get("picture"),
            "created_at": datetime.now(timezone.utc)
        }
        await db.users.insert_one(user_doc)
        logger.info(f"Created new user: {session_data['email']}")
    else:
        logger.info(f"User already exists: {session_data['email']}")
    
    # Create session
    session_token = session_data["session_token"]
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    session_doc = {
        "user_id": session_data["id"],
        "session_token": session_token,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc)
    }
    await db.user_sessions.insert_one(session_doc)
    logger.info(f"Created session for user: {session_data['email']}")
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=7 * 24 * 60 * 60,
        path="/"
    )
    logger.info(f"Set cookie for user: {session_data['email']}")
    
    return {"success": True, "user": session_data}


@router.post("/logout")
async def logout(response: Response, user: User = Depends(require_auth)):
    """Logout user and clear session"""
    # Delete all sessions for user
    await db.user_sessions.delete_many({"user_id": user.id})
    
    # Clear cookie
    response.delete_cookie("session_token", path="/")
    
    return {"success": True}
