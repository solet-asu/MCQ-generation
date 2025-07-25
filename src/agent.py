import json
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Dict, Optional

from openai import AsyncOpenAI
from pydantic import BaseModel
import tiktoken

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Retrieve API key from environment variables
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.error("OPENAI_API_KEY is not set.")
    raise ValueError("OPENAI_API_KEY is not set.")

class Agent(BaseModel):
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    most_recent_completion: Optional[str] = None
    most_recent_execution_time: Optional[timedelta] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None

    def get_metadata(self) -> Dict[str, Optional[str]]:
        """Return metadata about the most recent completion."""
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
        """Calculate the number of tokens in the given text."""
        tokenizer = tiktoken.encoding_for_model(self.model)
        return len(tokenizer.encode(text))

    async def completion_generation(self) -> str:
        """Generate a completion using the OpenAI API."""
        start_time = datetime.now()
        client = AsyncOpenAI(api_key=api_key)

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self.user_prompt},
        ]

        # Calculate input tokens
        self.input_tokens = sum(self.calculate_tokens(m["content"]) for m in messages)

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
            completion = response.choices[0].message.content
            self.most_recent_completion = completion

            self.output_tokens = self.calculate_tokens(completion or "")
            self.most_recent_execution_time = datetime.now() - start_time

            if not completion:
                logger.warning("Received empty completion.")

            return completion

        except Exception as e:
            logger.error(f"Error during async completion: {e}")
            raise