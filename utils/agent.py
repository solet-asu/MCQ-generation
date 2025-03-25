import json
import logging
import os
import re
from datetime import datetime, timedelta

from openai import OpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Agent(BaseModel):

    model: str | None = None
    system_prompt: str | None = None
    user_prompt: str | None = None
    most_recent_completion: str | None = None
    most_recent_extraction: dict | None = None
    most_recent_execution_time: timedelta | None = None
    task: str | None = None
    require_json_output: bool = True

    def get_metadata(self) -> dict:
        return {
            "task": self.task,
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
            "model": self.model,
            "completion": self.most_recent_completion,
            "extraction": self.most_recent_extraction,
            "execution_time": str(self.most_recent_execution_time),
        }


    def completion_generation(self):
        start_time = datetime.now()
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self.user_prompt},
        ]

        response = client.chat.completions.create(model=self.model, messages=messages)

        completion = response.choices[0].message.content
        self.most_recent_completion = completion
        if completion is None:
            logger.warning("Received empty completion.")
            extraction = None
        else:
            extraction = {"content": completion}
        self.most_recent_execution_time = datetime.now() - start_time
        return extraction
