# auth_utils.py
from jose import jwt, JWTError
from datetime import datetime
from typing import Optional, Dict
import logging
import os
from urllib.parse import quote

logger = logging.getLogger(__name__)

# Environment-based configuration
ASU_SSO_BASE_URL = os.getenv(
    "ASU_SSO_BASE_URL",
    "https://weblogin.asu.edu/cas/login?service=https://auth-main-poc.aiml.asu.edu/app/?aid=g1WGR674bvIeL7bVgfXIAU%26eid=583b207b6a94d5c1776f5b8b5990d102%26redirect="
)
APP_DOMAIN = os.getenv("APP_DOMAIN", "http://127.0.0.1:8000")

# Build the complete SSO login URL with the app domain
ASU_SSO_LOGIN_URL = f"{ASU_SSO_BASE_URL}{quote(APP_DOMAIN, safe='')}"

TOKEN_COOKIE_NAME = "asu_auth_token"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # production, staging, development


def decode_token(token: str) -> Optional[Dict]:
    """
    Decode and validate the JWT token without verification.
    Returns the token claims if valid, None if expired or invalid.
    
    Args:
        token: JWT token string
        
    Returns:
        Dictionary containing token claims or None
    """
    try:
        payload = jwt.decode(
            token,
            key="",  # required even if not verifying
            options={
                "verify_signature": False,  
                "verify_exp": True,         
            }
        )
        
        # Check if token is expired manually
        exp = payload.get("exp")
        if exp:
            exp_datetime = datetime.fromtimestamp(exp)
            if datetime.now() > exp_datetime:
                logger.warning("Token has expired")
                return None
        
        logger.info(f"Token decoded successfully for user: {payload.get('sub', 'unknown')}")
        return payload
        
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error decoding token: {e}")
        return None


def is_token_valid(token: Optional[str]) -> bool:
    """
    Check if a token exists and is valid.
    
    Args:
        token: JWT token string or None
        
    Returns:
        Boolean indicating if token is valid
    """
    if not token:
        return False
    
    claims = decode_token(token)
    return claims is not None