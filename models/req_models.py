from pydantic import BaseModel

# Define a Pydantic model for the request body

class MCQRequest(BaseModel):
    text: str
    question_type: str
    num_questions: int = 1