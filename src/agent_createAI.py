from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import requests
import json
import httpx
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


api_url = os.getenv("API_URL")
if not api_url:
    logger.error("API_URL is not set.")
    raise ValueError("API_URL is not set.")


class Agent(BaseModel):
    model: str = Field(..., description="Model name, e.g., 'gpt-4o'")
    session_id: str = Field(..., description="Session identifier for the API")
    api_token: Optional[str] = Field(None, description="API token for authentication")
    response_format: Dict[str, Any] = Field(..., description="Desired response format")

    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    model_provider: Optional[str] = "openai"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None

    most_recent_completion: Optional[str] = None
    most_recent_execution_time: Optional[timedelta] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None

    class Config:
        arbitrary_types_allowed = True

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "api_token": self.api_token,
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



    # ---------------- asynchronous ----------------
    async def completion_generation(
        self,
        *,
        timeout_seconds: float = 100.0,
    ) -> str:
        if not self.api_token:
            logger.info("api_token is not provided by the user. Defaulting to lcoal environment variable.")
            self.api_token = os.getenv("CreateAI_KEY")

            if not self.api_token:
                logger.error("CreateAI_KEY is not set.")
                raise ValueError("CreateAI_KEY is not set.")

        if not (self.system_prompt or self.user_prompt):
            raise ValueError("At least one of 'system_prompt' or 'user_prompt' must be provided.")

        start_time = datetime.now()

        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        if self.user_prompt:
            messages.append({"role": "user", "content": self.user_prompt})

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "session_id": self.session_id,
            "query": json.dumps(messages),
            "model_provider": self.model_provider,
            "model_name": self.model,
            "response_format": self.response_format,
        }
        if self.temperature is not None:
            payload["temperature"] = self.temperature
        if self.max_tokens is not None:
            payload["max_tokens"] = self.max_tokens

        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            try:
                resp = await client.post(api_url, json=payload, headers=headers)
                self.most_recent_execution_time = datetime.now() - start_time

                if resp.status_code != 200:
                    logger.error("Async API request failed with status code %s: %s", resp.status_code, resp.text)
                    raise ValueError(f"API request failed with status code {resp.status_code}: {resp.text}")

                output_all = resp.json()
                self.most_recent_completion = output_all.get("response", "")

                usage = output_all.get("metadata", {}).get("usage_metric", {}) or {}
                self.input_tokens = usage.get("input_token_count", 0)
                self.output_tokens = usage.get("output_token_count", 0)

                if not self.most_recent_completion:
                    logger.warning("Received empty output from API (async).")

                return self.most_recent_completion

            except httpx.RequestError as e:
                logger.error("Error during async API request: %s", e)
                self.most_recent_execution_time = datetime.now() - start_time
                raise



    # # ---------------- synchronous ----------------
    # def completion_generation(self) -> str:
    #     if not (self.system_prompt or self.user_prompt):
    #         raise ValueError("At least one of 'system_prompt' or 'user_prompt' must be provided.")

    #     start_time = datetime.now()

    #     messages = []
    #     if self.system_prompt:
    #         messages.append({"role": "system", "content": self.system_prompt})
    #     if self.user_prompt:
    #         messages.append({"role": "user", "content": self.user_prompt})

    #     headers = {
    #         "Authorization": f"Bearer {api_key}",
    #         "Content-Type": "application/json",
    #     }

    #     payload = {
    #         "session_id": self.session_id,
    #         "query": json.dumps(messages),
    #         "model_provider": self.model_provider,
    #         "model_name": self.model,
    #         "response_format": self.response_format,
    #         "temperature": self.temperature,
    #     }
    #     if self.temperature is not None:
    #         payload["temperature"] = self.temperature
    #     if self.max_tokens is not None:
    #         payload["max_tokens"] = self.max_tokens

    #     try:
    #         resp = requests.post(api_url, json=payload, headers=headers, timeout=30)
    #         self.most_recent_execution_time = datetime.now() - start_time

    #         if resp.status_code != 200:
    #             logger.error("API request failed with status code %s: %s", resp.status_code, resp.text)
    #             raise ValueError(f"API request failed with status code {resp.status_code}: {resp.text}")

    #         output_all = resp.json()

    #         # primary content
    #         self.most_recent_completion = output_all.get("response", "")

    #         # read token counts from metadata (CreateAI provides these)
    #         usage = output_all.get("metadata", {}).get("usage_metric", {}) or {}
    #         self.input_tokens = usage.get("input_token_count", 0)
    #         self.output_tokens = usage.get("output_token_count", 0)

    #         if not self.most_recent_completion:
    #             logger.warning("Received empty output from API.")

    #         return self.most_recent_completion

    #     except requests.RequestException as e:
    #         logger.error("Error during API request: %s", e)
    #         self.most_recent_execution_time = datetime.now() - start_time
    #         raise