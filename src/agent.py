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


class Agent(BaseModel):
    question_type: str | None = None
    model: str | None = None
    system_prompt: str | None = None
    user_prompt: str | None = None
    most_recent_completion: str | None = None
    most_recent_extraction: str | None = None
    most_recent_execution_time: timedelta | None = None
    require_json_output: bool = True
    input_tokens: int | None = None
    output_tokens: int | None = None

    def get_metadata(self) -> dict:
        return {
            "question_type": self.question_type,
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
            "model": self.model,
            "completion": self.most_recent_completion,
            "extraction": self.most_recent_extraction,
            "execution_time": str(self.most_recent_execution_time),
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }
    
    def extract_output(self, input_str: str) -> str | None:
        # Use regex to extract content within <MCQ> and </MCQ> tags
        pattern = re.compile(r"<MCQ>(.*?)</MCQ>", re.DOTALL)
        match = pattern.search(input_str)
        if match:
            target_str = match.group(1).strip()

            # Replace escaped newlines and tabs that are within the string
            target_str = target_str.replace("\\n", "\n").replace("\\t", "\t")

            # Store the most recent extraction as a string
            self.most_recent_extraction = target_str

            return target_str
        else:
            logger.error(f"No <MCQ> tags found in '{input_str}'.")
            return None

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
            extraction = ""
        else:
            extraction = self.extract_output(completion)
        self.most_recent_execution_time = datetime.now() - start_time
        return extraction
