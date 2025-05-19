import json
import logging
import os
import re
from datetime import datetime, timedelta

from openai import OpenAI
from pydantic import BaseModel
import tiktoken  

from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()


logger = logging.getLogger(__name__)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.error("OPENAI_API_KEY is not set.")
    raise ValueError("OPENAI_API_KEY is not set.")

# TODO # add answer and answer extraction method
class Agent(BaseModel):
    model: str | None = None
    system_prompt: str | None = None
    user_prompt: str | None = None
    most_recent_completion: str | None = None
    most_recent_execution_time: timedelta | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None

    def get_metadata(self) -> dict:
        return {
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
            "model": self.model,
            "completion": self.most_recent_completion,
            "execution_time": str(self.most_recent_execution_time),
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }
    

    def calculate_tokens(self, text: str) -> int:
        # Initialize the tokenizer for the specific model
        tokenizer = tiktoken.encoding_for_model(self.model)
        # Tokenize the text and return the number of tokens
        return len(tokenizer.encode(text))

    def completion_generation(self):
        start_time = datetime.now()
        client = OpenAI(api_key=api_key)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self.user_prompt},
        ]

        # Calculate input tokens
        self.input_tokens = sum(self.calculate_tokens(message["content"]) for message in messages)

        response = client.chat.completions.create(model=self.model, messages=messages)

        completion = response.choices[0].message.content
        self.most_recent_completion = completion

        # Calculate output tokens
        self.output_tokens = self.calculate_tokens(completion)

        if completion is None:
            logger.warning("Received empty completion.")
 
        self.most_recent_execution_time = datetime.now() - start_time
        return completion

