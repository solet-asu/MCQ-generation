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
from src.mcq_generation import generate_mcq  

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
@app.post("/generate_mcq", response_model=Dict[str,str])
async def generate_mcq_endpoint(request: MCQRequest) -> JSONResponse:
    """
    Endpoint to generate multiple-choice questions (MCQs).

    Args:
        request (MCQRequest): The request containing text, question type, and number of questions.

    Returns:
        JSONResponse: A JSON response containing the generated MCQ and its answer.
    """

    try:
        # Call the generate_mcq function
        question_meta = generate_mcq(request.text, request.facts, request.inferences, request.main_idea)
        mcq = question_meta.get("mcq", "Sorry, I couldn't generate the MCQ.")
        mcq_answer = question_meta.get("mcq_answer", "Sorry, the answer is not available.")
        response = {
            "mcq": mcq,
            "mcq_answer": mcq_answer
        }
        return JSONResponse(content=response)
    except ValueError as e:
        logger.error(f"ValueError: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")