from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from models.req_models import MCQRequest
from src.workflow import question_generation_workflow
from typing import List, Dict
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#
@app.post("/generate_mcq", response_model=List[Dict[str, str]])
async def generate_mcq_endpoint(request: MCQRequest) -> JSONResponse:
    logger.info("POST /generate_mcq called")
    try:
        results = await question_generation_workflow(
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


app.mount("/", StaticFiles(directory="static", html=True), name="static")
