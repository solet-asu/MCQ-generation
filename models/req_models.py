from pydantic import BaseModel

# Define a Pydantic model for the request body

class MCQRequest(BaseModel):
    text: str
    facts: int
    inferences: int
    main_idea: int
