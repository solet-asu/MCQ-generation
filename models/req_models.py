from pydantic import BaseModel

# Define a Pydantic model for the request body

class MCQRequest(BaseModel):
    text: str
    fact: int
    inference: int
    main_idea: int
