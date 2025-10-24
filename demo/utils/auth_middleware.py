# auth_middleware.py
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from .auth_utils import is_token_valid, ASU_SSO_LOGIN_URL, TOKEN_COOKIE_NAME
import logging

logger = logging.getLogger(__name__)



class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to check authentication for all routes except public ones.
    """
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Special handling for root path with projectWebToken parameter (SSO callback)
        if path == "/" and "projectWebToken" in request.query_params:
            # Allow this request through - the endpoint will handle token validation and cookie setting
            return await call_next(request)
        
        # Get token from cookies
        token = request.cookies.get(TOKEN_COOKIE_NAME)
        
        # Check if token is valid
        if not is_token_valid(token):
            logger.warning(f"Invalid or missing token for path: {path}")
            # Redirect to ASU SSO login
            return RedirectResponse(url=ASU_SSO_LOGIN_URL, status_code=302)
        
        # Token is valid, proceed with the request
        # Attach token to request state for use in endpoints
        request.state.token = token
        return await call_next(request)