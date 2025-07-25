# app.py
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from models.req_models import MCQRequest  # Import the MCQRequest model from models.py
import logging

# Import the generate_mcq function
from src.workflow import question_generation_workflow  

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Initialize the FastAPI app
app = FastAPI()

# Allow CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")



@app.get("/")
async def read_root():
    # Redirect to the static HTML file
    return RedirectResponse(url="/static/index.html")


# Define the endpoint to generate MCQs
@app.post("/generate_mcq", response_model=List[Dict[str, str]])
async def generate_mcq_endpoint(request: MCQRequest) -> JSONResponse:
    """
    Endpoint to generate multiple MCQs of various types.

    Args:
        request (MCQRequest): The request object containing text, fact, inference, and main_idea.

    Returns:
        JSONResponse: A JSON response containing the generated MCQs.
    """
    try:
        # Call the question generation workflow with the provided request data
        results = await question_generation_workflow(
            text=request.text,
            fact=request.fact,
            inference=request.inference,
            main_idea=request.main_idea,
            model="gpt-4o"
        )
        return JSONResponse(content=results)
    except ValueError as e:
        # Log and handle ValueError specifically
        logger.error(f"ValueError: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log unexpected errors and return a generic server error response
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")