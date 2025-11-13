# app.py
import os
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from typing import List, Dict
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from models.req_models import MCQRequest
import logging
import uuid
from dotenv import load_dotenv


# Import authentication utilities
from demo.utils.auth_utils import decode_token, TOKEN_COOKIE_NAME
from demo.utils.auth_middleware import AuthMiddleware

# Import the generate_mcq function
from src.workflow import question_generation_workflow

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

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

# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/pdf", StaticFiles(directory="pdf"), name="pdf")


@app.get("/")
async def read_root(request: Request, projectWebToken: str = None):
    return RedirectResponse(url="/static/index.html")


@app.get("/auth/user")
async def get_current_user(request: Request):
    """
    Get current authenticated user information.
    
    Returns:
        User claims from the JWT token
    """
    token = os.getenv("CREATEAI_API_KEY")
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
        session_id = str(uuid.uuid4())
        token = os.getenv("CREATEAI_API_KEY")
        logger.info(f"Generating MCQs for session_id: {session_id}")
        
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