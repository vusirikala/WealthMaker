"""User context routes"""
from fastapi import APIRouter, Depends
from datetime import datetime, timezone
from typing import Dict, Any
import uuid
from models.user import User
from utils.database import db
from utils.dependencies import require_auth

router = APIRouter(prefix="/context", tags=["context"])


@router.get("")
async def get_user_context(user: User = Depends(require_auth)):
    """Get user context/profile"""
    context = await db.user_context.find_one({"user_id": user.id})
    if not context:
        # Create default context
        default_context = {
            "_id": str(uuid.uuid4()),
            "user_id": user.id,
            "portfolio_type": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        await db.user_context.insert_one(default_context)
        return default_context
    return context


@router.put("")
async def update_user_context(context_update: Dict[str, Any], user: User = Depends(require_auth)):
    """Update user context/profile"""
    context = await db.user_context.find_one({"user_id": user.id})
    
    if not context:
        # Create new context
        context_update["_id"] = str(uuid.uuid4())
        context_update["user_id"] = user.id
        context_update["created_at"] = datetime.now(timezone.utc)
        context_update["updated_at"] = datetime.now(timezone.utc)
        await db.user_context.insert_one(context_update)
        return context_update
    else:
        # Update existing context
        context_update["updated_at"] = datetime.now(timezone.utc)
        await db.user_context.update_one(
            {"user_id": user.id},
            {"$set": context_update}
        )
        updated_context = await db.user_context.find_one({"user_id": user.id})
        return updated_context
