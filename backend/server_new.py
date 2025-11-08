"""
WealthMaker Backend - Modular FastAPI Application
Main application file that imports and registers all route modules
"""
from fastapi import FastAPI, APIRouter
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the main app
app = FastAPI(title="WealthMaker API", version="1.0.0")

# Create API router with /api prefix
api_router = APIRouter(prefix="/api")

# Import and include all route modules
from routes import auth, context, goals, portfolios, chat, news

# Register all routers
api_router.include_router(auth.router)
api_router.include_router(context.router)
api_router.include_router(goals.router)
api_router.include_router(portfolios.router)
api_router.include_router(chat.router)
api_router.include_router(news.router)

# Include the API router in the main app
app.include_router(api_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "WealthMaker API", "version": "1.0.0", "status": "active"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.on_event("shutdown")
async def shutdown_db_client():
    """Close database connections on shutdown"""
    from utils.database import client
    client.close()
    logger.info("Database connection closed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
