"""
Rate Limiting Middleware
Prevents 429 errors by limiting requests per user
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class RateLimiter(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiter
    
    Limits:
    - 100 requests per minute per IP
    - 1000 requests per hour per IP
    """
    
    def __init__(self, app, requests_per_minute: int = 100, requests_per_hour: int = 1000):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        
        # Store request timestamps per IP
        self.minute_requests = defaultdict(list)  # IP -> [timestamps]
        self.hour_requests = defaultdict(list)
        
        # Last cleanup time
        self.last_cleanup = datetime.now()
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/api/health"]:
            return await call_next(request)
        
        now = datetime.now()
        
        # Cleanup old entries every 5 minutes
        if (now - self.last_cleanup) > timedelta(minutes=5):
            self.cleanup_old_entries()
            self.last_cleanup = now
        
        # Check minute limit
        minute_timestamps = self.minute_requests[client_ip]
        minute_timestamps = [t for t in minute_timestamps if (now - t) < timedelta(minutes=1)]
        
        if len(minute_timestamps) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded (per minute) for IP: {client_ip}")
            raise HTTPException(
                status_code=429,
                detail=f"Too many requests. Limit: {self.requests_per_minute} requests per minute. Please slow down."
            )
        
        # Check hour limit
        hour_timestamps = self.hour_requests[client_ip]
        hour_timestamps = [t for t in hour_timestamps if (now - t) < timedelta(hours=1)]
        
        if len(hour_timestamps) >= self.requests_per_hour:
            logger.warning(f"Rate limit exceeded (per hour) for IP: {client_ip}")
            raise HTTPException(
                status_code=429,
                detail=f"Too many requests. Limit: {self.requests_per_hour} requests per hour. Please try again later."
            )
        
        # Record this request
        minute_timestamps.append(now)
        hour_timestamps.append(now)
        self.minute_requests[client_ip] = minute_timestamps
        self.hour_requests[client_ip] = hour_timestamps
        
        # Process request
        response = await call_next(request)
        return response
    
    def cleanup_old_entries(self):
        """Remove old timestamps to prevent memory leak"""
        now = datetime.now()
        
        # Clean minute requests
        for ip in list(self.minute_requests.keys()):
            timestamps = self.minute_requests[ip]
            timestamps = [t for t in timestamps if (now - t) < timedelta(minutes=5)]
            if timestamps:
                self.minute_requests[ip] = timestamps
            else:
                del self.minute_requests[ip]
        
        # Clean hour requests
        for ip in list(self.hour_requests.keys()):
            timestamps = self.hour_requests[ip]
            timestamps = [t for t in timestamps if (now - t) < timedelta(hours=2)]
            if timestamps:
                self.hour_requests[ip] = timestamps
            else:
                del self.hour_requests[ip]
        
        logger.info(f"Rate limiter cleanup complete. Tracking {len(self.minute_requests)} IPs")
