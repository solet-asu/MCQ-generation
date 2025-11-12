# app.py
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from models.req_models import MCQRequest
from src.workflow import question_generation_workflow
from typing import List, Dict
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from models.req_models import MCQRequest
import logging, os

# Import authentication utilities
from utils.auth_utils import decode_token, TOKEN_COOKIE_NAME
from utils.auth_middleware import AuthMiddleware

# Import the generate_mcq function
from src.workflow import question_generation_workflow

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize the FastAPI app
app = FastAPI()

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware
app.add_middleware(AuthMiddleware)

# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/pdf", StaticFiles(directory="pdf"), name="pdf")


@app.get("/")
async def read_root(request: Request, projectWebToken: str = None):
    """
    Root endpoint that handles both:
    1. SSO callback with projectWebToken parameter
    2. Normal app access for authenticated users
    """
    # Check if this is a callback from ASU SSO with a token
    if projectWebToken:
        logger.info("Received token from ASU SSO, validating and setting cookie")
        
        # Validate the token
        claims = decode_token(projectWebToken)
        if not claims:
            logger.error("Invalid token received from ASU SSO")
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        logger.info(f"User authenticated successfully: {claims.get('sub', 'unknown')}")
        
        # Create redirect response to clean URL (remove token from URL)
        redirect_response = RedirectResponse(url="/", status_code=302)
        
        # Set the token as an HTTP-only cookie
        redirect_response.set_cookie(
            key=TOKEN_COOKIE_NAME,
            value=projectWebToken,
            httponly=True,  
            secure=True,  
            samesite="lax",
            max_age=86400, 
        )        
        return redirect_response
    
    # Normal access - user already has valid token (checked by middleware)
    # Redirect to the main application page
    return FileResponse("static/index.html")


@app.get("/auth/user")
async def get_current_user(request: Request):
    """
    Get current authenticated user information.
    
    Returns:
        User claims from the JWT token
    """
    token = request.state.token
    claims = decode_token(token)
    
    if not claims:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return JSONResponse(content=claims)


@app.post("/auth/logout")
async def logout(response: Response):
    """
    Logout endpoint - clears the authentication cookie.
    """
    response = JSONResponse(content={"message": "Logged out successfully"})
    response.delete_cookie(key=TOKEN_COOKIE_NAME)
    return response


@app.post("/generate_mcq", response_model=List[Dict[str, str]])
async def generate_mcq_endpoint(request: MCQRequest, req: Request) -> JSONResponse:
    """
    Endpoint to generate multiple MCQs of various types. Protected by authentication.
    
    Args:
        request: The request object containing text, fact, inference, and main_idea
        req: FastAPI Request object (contains auth token in state)
        
    Returns:
        JSONResponse: A JSON response containing the generated MCQs
    """
    try:
        session_id = req.headers.get('x-session-id', 'unknown')
        token = req.state.token
        logger.debug(f"Generating MCQs for authenticated user")
        
        # Call the question generation workflow with the provided request data
        results = await question_generation_workflow(
            session_id=session_id,
            api_token=token,
            text=request.text,
            fact=request.fact,
            inference=request.inference,
            main_idea=request.main_idea,
            model="gpt-4o",
            quality_first=request.quality_first,
        )
        return JSONResponse(content=results)
    except ValueError as e:
        logger.error(f"ValueError: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/health")
async def health_check():
    """Health check endpoint (public, no auth required)"""
    return {"status": "healthy"}




#Keep it at the end of the file
#Mount the static files directory
app.mount("/", StaticFiles(directory="static", html=True), name="static")