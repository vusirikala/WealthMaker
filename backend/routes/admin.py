"""
Admin routes for managing shared assets database
These should be protected with admin authentication in production
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional
from models.user import User
from utils.dependencies import require_auth
from services.shared_assets_db import shared_assets_service
import logging

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


@router.post("/initialize-database")
async def initialize_assets_database(
    background_tasks: BackgroundTasks,
    symbols: Optional[List[str]] = None,
    user: User = Depends(require_auth)
):
    """
    Initialize the shared assets database
    This is a one-time operation that fetches 3 years of historical data
    
    ⚠️ WARNING: This can take 5-10 minutes for all assets
    
    Args:
        symbols: Optional list of specific symbols to initialize. 
                 If None, initializes top 50 S&P 500 + crypto + commodities
    
    Use background_tasks for long-running initialization
    """
    # Get current database stats
    stats = await shared_assets_service.get_database_stats()
    
    if stats["status"] == "active" and stats["total_assets"] > 0:
        return {
            "message": "Database already initialized",
            "stats": stats,
            "hint": "Use /admin/update-live-data to refresh live data, or provide specific symbols to add more assets"
        }
    
    # Start initialization in background
    background_tasks.add_task(shared_assets_service.initialize_database, symbols)
    
    return {
        "message": "Database initialization started",
        "status": "processing",
        "note": "This will take 5-10 minutes. Check /admin/database-stats for progress"
    }


@router.post("/update-live-data")
async def update_live_data(
    background_tasks: BackgroundTasks,
    symbols: Optional[List[str]] = None,
    user: User = Depends(require_auth)
):
    """
    Update live data (prices, news, events) for all assets
    Should be run 2x daily - morning (9 AM) and afternoon (4 PM)
    
    Args:
        symbols: Optional list of specific symbols to update. If None, updates all
    """
    # Start update in background
    background_tasks.add_task(shared_assets_service.update_live_data, symbols)
    
    return {
        "message": "Live data update started",
        "status": "processing",
        "note": "Updates running in background. Check /admin/database-stats for completion"
    }


@router.get("/database-stats")
async def get_database_stats(user: User = Depends(require_auth)):
    """
    Get statistics about the shared assets database
    Shows total assets, breakdown by type, last update time
    """
    stats = await shared_assets_service.get_database_stats()
    return stats


@router.post("/add-asset")
async def add_single_asset(
    symbol: str,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_auth)
):
    """
    Add a single new asset to the shared database
    Useful for adding stocks that aren't in the initial set
    """
    symbol = symbol.upper()
    
    # Check if already exists
    existing = await shared_assets_service.get_single_asset(symbol)
    if existing:
        return {
            "message": f"{symbol} already exists in database",
            "asset": existing
        }
    
    # Initialize this single asset
    background_tasks.add_task(shared_assets_service.initialize_database, [symbol])
    
    return {
        "message": f"Adding {symbol} to shared database",
        "status": "processing"
    }


@router.delete("/remove-asset/{symbol}")
async def remove_asset(
    symbol: str,
    user: User = Depends(require_auth)
):
    """
    Remove an asset from the shared database
    ⚠️ WARNING: This will affect all users tracking this asset
    """
    from utils.database import db
    
    symbol = symbol.upper()
    
    result = await db.shared_assets.delete_one({"symbol": symbol})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")
    
    return {
        "message": f"Removed {symbol} from shared database",
        "deleted": True
    }


@router.get("/list-assets")
async def list_all_assets(
    asset_type: Optional[str] = None,
    user: User = Depends(require_auth)
):
    """
    List all assets in the shared database
    
    Args:
        asset_type: Filter by type (stock, crypto, commodity)
    """
    from utils.database import db
    
    query = {}
    if asset_type:
        query["assetType"] = asset_type
    
    cursor = db.shared_assets.find(
        query,
        {"symbol": 1, "name": 1, "assetType": 1, "lastUpdated": 1}
    ).sort("symbol", 1)
    
    assets = []
    async for doc in cursor:
        assets.append({
            "symbol": doc.get("symbol"),
            "name": doc.get("name"),
            "assetType": doc.get("assetType"),
            "lastUpdated": doc.get("lastUpdated")
        })
    
    return {
        "count": len(assets),
        "assets": assets
    }
