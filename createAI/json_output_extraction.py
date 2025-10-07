from typing import Any, List, Union, Dict, Optional, Tuple
import json
import re


_JSON_FENCE = re.compile(r"```json\s*(.*?)\s*```", re.IGNORECASE | re.DOTALL)
_ANY_FENCE  = re.compile(r"```\s*(.*?)\s*```", re.DOTALL)
_START_TOKEN = re.compile(r"[{\[]")

def _try_load_obj(snippet: str) -> Optional[Dict[str, Any]]:
    try:
        value = json.loads(snippet)
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        return None

def CREATEAI_extract_json_string(text: str) -> Dict[str, Any]:
    """
    Extract the first JSON object (dict) from noisy LLM output.
    Order:
      1) Try ```json fenced blocks
      2) Try any ``` fenced blocks
      3) Scan full text with JSONDecoder.raw_decode starting at each '{' or '['
         (continues scanning until it finds a JSON object)
    Raises ValueError if none is found.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a str")

    # Strip BOM / zero-width space that sometimes appear in LLM output
    text = text.lstrip("\ufeff").replace("\u200b", "")

    # 1) Prefer explicit JSON fences
    for m in _JSON_FENCE.finditer(text):
        obj = _try_load_obj(m.group(1).strip())
        if obj is not None:
            return obj

    # 2) Fall back to any fenced code block
    for m in _ANY_FENCE.finditer(text):
        obj = _try_load_obj(m.group(1).strip())
        if obj is not None:
            return obj

    # 3) Scan raw text, decoding from each '{' or '['; keep searching until a dict is found
    decoder = json.JSONDecoder()
    i, n = 0, len(text)
    while i < n:
        m = _START_TOKEN.search(text, i)
        if not m:
            break
        start = m.start()
        try:
            value, end = decoder.raw_decode(text, start)
        except json.JSONDecodeError:
            i = start + 1
            continue
        if isinstance(value, dict):
            return value
        i = end  # not an object; continue scanning after this JSON value

    raise ValueError("src.general report: No valid JSON object found in input.")  