"""Financial goals management routes"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import Dict, Any
import uuid
from models.user import User
from utils.database import db
from utils.dependencies import require_auth

router = APIRouter(prefix="/goals", tags=["goals"])


@router.get("")
async def get_user_goals(user: User = Depends(require_auth)):
    """Get all financial goals for the user"""
    context = await db.user_context.find_one({"user_id": user.id})
    if not context or not context.get('liquidity_requirements'):
        return {"goals": []}
    return {"goals": context.get('liquidity_requirements', [])}


@router.post("")
async def add_goal(goal_data: Dict[str, Any], user: User = Depends(require_auth)):
    """Add a new financial goal"""
    # Generate goal_id if not provided
    if 'goal_id' not in goal_data:
        goal_data['goal_id'] = str(uuid.uuid4())
    
    # Calculate derived fields
    if 'target_amount' in goal_data and 'amount_saved' in goal_data:
        goal_data['amount_needed'] = goal_data['target_amount'] - goal_data['amount_saved']
        goal_data['progress_percentage'] = round((goal_data['amount_saved'] / goal_data['target_amount']) * 100, 2)
    
    # Add timestamps
    goal_data['created_at'] = datetime.now(timezone.utc).isoformat()
    goal_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    # Update context with new goal
    context = await db.user_context.find_one({"user_id": user.id})
    
    if not context:
        # Create new context with goal
        new_context = {
            "_id": str(uuid.uuid4()),
            "user_id": user.id,
            "liquidity_requirements": [goal_data],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        await db.user_context.insert_one(new_context)
        return {"success": True, "goal": goal_data}
    else:
        # Add to existing goals
        liquidity_requirements = context.get('liquidity_requirements', [])
        liquidity_requirements.append(goal_data)
        
        await db.user_context.update_one(
            {"user_id": user.id},
            {"$set": {
                "liquidity_requirements": liquidity_requirements,
                "updated_at": datetime.now(timezone.utc)
            }}
        )
        return {"success": True, "goal": goal_data}


@router.put("/{goal_id}")
async def update_goal(goal_id: str, goal_update: Dict[str, Any], user: User = Depends(require_auth)):
    """Update an existing financial goal"""
    context = await db.user_context.find_one({"user_id": user.id})
    
    if not context or not context.get('liquidity_requirements'):
        raise HTTPException(status_code=404, detail="No goals found")
    
    liquidity_requirements = context.get('liquidity_requirements', [])
    goal_found = False
    
    for i, goal in enumerate(liquidity_requirements):
        if goal.get('goal_id') == goal_id:
            # Update the goal
            liquidity_requirements[i].update(goal_update)
            
            # Recalculate derived fields
            if 'target_amount' in liquidity_requirements[i] and 'amount_saved' in liquidity_requirements[i]:
                liquidity_requirements[i]['amount_needed'] = liquidity_requirements[i]['target_amount'] - liquidity_requirements[i]['amount_saved']
                liquidity_requirements[i]['progress_percentage'] = round((liquidity_requirements[i]['amount_saved'] / liquidity_requirements[i]['target_amount']) * 100, 2)
            
            liquidity_requirements[i]['updated_at'] = datetime.now(timezone.utc).isoformat()
            goal_found = True
            break
    
    if not goal_found:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    await db.user_context.update_one(
        {"user_id": user.id},
        {"$set": {
            "liquidity_requirements": liquidity_requirements,
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    
    return {"success": True, "goal": liquidity_requirements[i]}


@router.delete("/{goal_id}")
async def delete_goal(goal_id: str, user: User = Depends(require_auth)):
    """Delete a financial goal"""
    context = await db.user_context.find_one({"user_id": user.id})
    
    if not context or not context.get('liquidity_requirements'):
        raise HTTPException(status_code=404, detail="No goals found")
    
    liquidity_requirements = context.get('liquidity_requirements', [])
    original_length = len(liquidity_requirements)
    liquidity_requirements = [g for g in liquidity_requirements if g.get('goal_id') != goal_id]
    
    if len(liquidity_requirements) == original_length:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    await db.user_context.update_one(
        {"user_id": user.id},
        {"$set": {
            "liquidity_requirements": liquidity_requirements,
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    
    return {"success": True, "message": "Goal deleted"}
