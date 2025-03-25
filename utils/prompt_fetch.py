import functools
import importlib.resources
import json
import logging
from collections.abc import Iterable
import yaml
import utils
logger = logging.getLogger(__name__)


@functools.cache
def get_prompts(filename: str = "prompts.yaml") -> dict[str, str]:
    resources_dir = importlib.resources.files(utils)
    prompt_path = resources_dir / filename
    with open(prompt_path, encoding="utf-8") as f:
        prompts = yaml.safe_load(f)
    return prompts


def test():
    return "test!!!"