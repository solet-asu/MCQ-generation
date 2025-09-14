from __future__ import annotations



import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field
import tiktoken
from openai import AsyncOpenAI

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Retrieve API key from environment variables
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.error("OPENAI_API_KEY is not set.")
    raise ValueError("OPENAI_API_KEY is not set.")

class Agent(BaseModel):
    # Required
    model: str = Field(..., description="Model name, e.g., 'gpt-4o'")

    # Optional
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    most_recent_completion: Optional[str] = None
    most_recent_execution_time: Optional[timedelta] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None

    def get_metadata(self) -> Dict[str, Any]:
        """Return metadata about the most recent completion."""
        return {
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
            "model": self.model,
            "completion": self.most_recent_completion,
            "execution_time": (
                str(self.most_recent_execution_time)
                if self.most_recent_execution_time is not None
                else None
            ),
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }

    # --- Tokenization helpers -------------------------------------------------

    def _tokenizer(self):
        """Get a tokenizer for the configured model, with a safe fallback."""
        try:
            return tiktoken.encoding_for_model(self.model)
        except Exception:
            return tiktoken.get_encoding("cl100k_base")

    def calculate_tokens(self, text: Optional[str]) -> int:
        """Calculate the number of tokens in the given text."""
        if not text:
            return 0
        tokenizer = self._tokenizer()
        try:
            return len(tokenizer.encode(text))
        except Exception:
            # Fallback proxy if tokenizer fails for any reason
            return len(text.encode("utf-8"))

   # --- Generation -----------------------------------------------------------

    async def completion_generation(
        self,
        *,
        response_format: Optional[Dict[str, Any]] = None,  # <-- NEW (optional)
    ) -> str:
        """Generate a completion using the OpenAI API."""
        if not (self.system_prompt or self.user_prompt):
            raise ValueError(
                "At least one of 'system_prompt' or 'user_prompt' must be provided."
            )

        start_time = datetime.now()
        client = AsyncOpenAI(api_key=api_key)

        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        if self.user_prompt:
            messages.append({"role": "user", "content": self.user_prompt})

        # Calculate input tokens
        self.input_tokens = sum(self.calculate_tokens(m["content"]) for m in messages)

        try:
            # Build kwargs so we only include response_format when it's provided
            kwargs: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
            }
            if response_format is not None:
                kwargs["response_format"] = response_format
                logger.info("Using response_format: %s", response_format.get("type"))

            response = await client.chat.completions.create(**kwargs)

            completion = (response.choices[0].message.content or "").strip()
            self.most_recent_completion = completion

            self.output_tokens = self.calculate_tokens(completion)
            self.most_recent_execution_time = datetime.now() - start_time

            if not completion:
                logger.warning("Received empty completion.")

            return completion

        except Exception as e:
            self.most_recent_execution_time = datetime.now() - start_time
            logger.error("Error during async completion: %s", e)
            raise
