from __future__ import annotations

import sys
import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List, Tuple
from urllib.parse import urlparse, quote_plus
from json.decoder import WHITESPACE

import websockets
from websockets.exceptions import InvalidStatusCode, ConnectionClosedError
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Use selector event loop on Windows (avoids proactor cleanup crash)
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()
logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.DEBUG)  # enable during debugging

API_URL = os.getenv("API_URL")
if not API_URL:
    raise ValueError("API_URL is not set in environment")


class Agent(BaseModel):
    model: str = Field(..., description="Model name, e.g., 'gpt-4o'")
    session_id: str = Field(..., description="Session identifier for the API")
    api_token: Optional[str] = Field(None, description="API token for authentication")
    response_format: Optional[Dict[str, Any]] = Field(None, description="Desired response format")
    model_provider: Optional[str] = Field(None, description="Model provider, e.g., 'openai'")

    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None

    most_recent_completion: Optional[str] = None
    most_recent_execution_time: Optional[timedelta] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None

    class Config:
        arbitrary_types_allowed = True

    async def completion_generation(
        self,
        *,
        timeout_seconds: float = 300.0,
        ping_interval: Optional[float] = None,
        auth_preference: str = "auto",  # "auto" | "header" | "query"
        origin: Optional[str] = None,
        subprotocols: Optional[List[str]] = None,
        extra_headers: Optional[List[Tuple[str, str]]] = None,
        eos_marker: str = "<EOS>",
    ) -> str:
        """
        Streaming completion over WebSocket with robust incremental parsing and finalization.

        Returns the final assembled string. If the assembled output is JSON, returns a JSON string.
        """

        if not self.api_token:
            self.api_token = os.getenv("CreateAI_KEY")
            if not self.api_token:
                raise ValueError("api_token not provided and CreateAI_KEY not set")

        if not (self.system_prompt or self.user_prompt):
            raise ValueError("Provide at least one of system_prompt or user_prompt")

        start_time = datetime.now()

        # construct payload
        query_text = ""
        if self.system_prompt:
            query_text += self.system_prompt + "\n\n"
        if self.user_prompt:
            query_text += self.user_prompt

        payload: Dict[str, Any] = {
            "action": "query",
            "project_id": self.session_id,
            "model_name": self.model,
            "model_provider": self.model_provider,
            "query": query_text,
        }
        if self.response_format:
            payload["response_format"] = self.response_format

        # compute websocket base url (preserve path)
        parsed = urlparse(API_URL)
        if parsed.scheme in ("ws", "wss"):
            scheme = parsed.scheme
        elif parsed.scheme == "http":
            scheme = "ws"
        elif parsed.scheme == "https":
            scheme = "wss"
        else:
            raise ValueError(f"Unsupported API_URL scheme: {parsed.scheme!r}")

        base = f"{scheme}://{parsed.netloc}{parsed.path or ''}"
        wss_base = base.rstrip("/") + "/"
        token = self.api_token

        def _safe_snippet(text: str, max_len: int = 300) -> str:
            if not text:
                return "<empty>"
            return (text[:max_len] + "...") if len(text) > max_len else text

        def _make_headers(include_auth: bool) -> List[Tuple[str, str]]:
            headers: List[Tuple[str, str]] = []
            if include_auth:
                headers.append(("Authorization", f"Bearer {token}"))
            if origin:
                headers.append(("Origin", origin))
            if extra_headers:
                headers.extend(extra_headers)
            return headers

        def _normalize_non_dict(val: Any, out_acc: List[str]) -> None:
            # keep behavior for incremental text extraction (not used for final assembly)
            if isinstance(val, str):
                out_acc.append(val)
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, dict):
                        out_acc.append(json.dumps(item))
                    elif isinstance(item, str):
                        out_acc.append(item)
                    else:
                        out_acc.append(str(item))
            else:
                out_acc.append(str(val))

        async def _try_connect_and_receive(mode: str) -> Optional[str]:
            """
            Connect in the given mode and run the receive loop.
            Collect both:
               - frames: exact raw frames in arrival order (for final join)
               - final_parts: streaming normalized pieces for 'delta' and other cases
            Return assembled response string if completed here, or None if no content and no finalization.
            """
            if mode == "header":
                url = wss_base
                headers_list = _make_headers(include_auth=True)
            else:
                url = wss_base.rstrip("/") + f"/?access_token={quote_plus(token)}"
                headers_list = _make_headers(include_auth=False)

            logger.debug("Attempting connect (mode=%s) url=%s headers=%s", mode, _safe_snippet(url, 200), bool(headers_list))

            frames: List[str] = []         # store raw received frames in order
            final_parts: List[str] = []    # normalized streaming parts for delta/response
            buffer = ""
            decoder = json.JSONDecoder()

            async with websockets.connect(url, extra_headers=headers_list, ping_interval=ping_interval, subprotocols=subprotocols, open_timeout=15) as ws:
                logger.debug("Handshake succeeded (mode=%s)", mode)
                await ws.send(json.dumps(payload))

                while True:
                    try:
                        raw = await ws.recv()
                    except ConnectionClosedError:
                        logger.info("Connection closed by server (mode=%s)", mode)
                        break
                    except asyncio.CancelledError:
                        logger.info("Receive cancelled")
                        raise

                    if raw is None:
                        logger.info("Received None frame")
                        break

                    # normalize bytes -> str
                    if isinstance(raw, bytes):
                        raw = raw.decode("utf-8", errors="replace")

                    # record raw frame *as received* for final assembly
                    frames.append(raw)

                    logger.debug("Frame snippet: %s", _safe_snippet(raw, 200))
                    buffer += raw

                    # Quick EOS detection by looking at the raw frames concatenation (buffer includes all raws)
                    if eos_marker and eos_marker in buffer:
                        logger.debug("Detected EOS marker in buffer (mode=%s). Finalizing.", mode)
                        # Build final string from raw frames to preserve structure and spacing
                        joined_raw = "".join(frames).replace(eos_marker, "")
                        trimmed = joined_raw.strip()
                        # If looks like JSON, attempt to parse and return valid JSON string
                        if trimmed.startswith("{") or trimmed.startswith("["):
                            try:
                                parsed = json.loads(trimmed)
                                result = json.dumps(parsed, ensure_ascii=False)
                                return result
                            except Exception:
                                return joined_raw
                        return joined_raw

                    # NDJSON and incremental parsing attempt
                    chunks: List[str] = []
                    if "\n" in buffer:
                        parts = buffer.split("\n")
                        buffer = parts.pop()
                        chunks = parts
                    else:
                        stripped = buffer.strip()
                        if stripped.startswith("{") and stripped.endswith("}"):
                            chunks = [buffer]
                            buffer = ""

                    for chunk in chunks:
                        if not chunk or chunk.strip() in ("[DONE]", "", "--heartbeat--"):
                            continue

                        try:
                            data = json.loads(chunk)
                        except Exception:
                            try:
                                match = WHITESPACE.match(chunk, 0)
                                pos = match.end()
                                data, end = decoder.raw_decode(chunk, pos)
                            except json.JSONDecodeError:
                                logger.debug("Incomplete chunk; waiting for more data")
                                buffer = chunk + ("\n" if buffer else "") + buffer
                                continue

                        if not isinstance(data, dict):
                            logger.debug("Parsed JSON not dict; normalizing text")
                            _normalize_non_dict(data, final_parts)
                            continue

                        # delta frames
                        if "delta" in data:
                            delta = data.get("delta")
                            if isinstance(delta, dict):
                                final_parts.append(delta.get("content", "") or "")
                            elif isinstance(delta, str):
                                final_parts.append(delta or "")
                            else:
                                final_parts.append(str(delta))
                            continue

                        # full response frame
                        if "response" in data:
                            resp = data.get("response")
                            if isinstance(resp, str):
                                final_parts = [resp]
                            else:
                                try:
                                    final_parts = [json.dumps(resp)]
                                except Exception:
                                    final_parts = [str(resp)]
                            meta = data.get("metadata", {}) or {}
                            usage = meta.get("usage_metric", {}) or {}
                            self.input_tokens = usage.get("input_token_count", self.input_tokens or 0)
                            self.output_tokens = usage.get("output_token_count", self.output_tokens or 0)
                            logger.info("Full response frame received; returning assembled response from raw frames if possible.")
                            # Use raw frames to assemble final result (preferred) 
                            joined_raw = "".join(frames).strip()
                            joined_raw = joined_raw.replace(eos_marker, "")
                            trimmed = joined_raw.strip()
                            if trimmed.startswith("{") or trimmed.startswith("["):
                                try:
                                    parsed = json.loads(trimmed)
                                    return json.dumps(parsed, ensure_ascii=False)
                                except Exception:
                                    return joined_raw
                            return joined_raw

                        # metadata-only frames
                        if "metadata" in data:
                            meta = data.get("metadata", {}) or {}
                            usage = meta.get("usage_metric", {}) or {}
                            self.input_tokens = usage.get("input_token_count", self.input_tokens or 0)
                            self.output_tokens = usage.get("output_token_count", self.output_tokens or 0)
                            continue

                    # attempt incremental raw_decode on leftover buffer
                    if buffer and not chunks:
                        try:
                            match = WHITESPACE.match(buffer, 0)
                            pos = match.end()
                            data, end = decoder.raw_decode(buffer, pos)
                            buffer = buffer[end:]
                            if not isinstance(data, dict):
                                _normalize_non_dict(data, final_parts)
                                continue
                            # handle dict-case as above
                            if "delta" in data:
                                delta = data.get("delta")
                                if isinstance(delta, dict):
                                    final_parts.append(delta.get("content", "") or "")
                                elif isinstance(delta, str):
                                    final_parts.append(delta or "")
                                else:
                                    final_parts.append(str(delta))
                                continue
                            if "response" in data:
                                resp = data.get("response")
                                if isinstance(resp, str):
                                    final_parts = [resp]
                                else:
                                    try:
                                        final_parts = [json.dumps(resp)]
                                    except Exception:
                                        final_parts = [str(resp)]
                                meta = data.get("metadata", {}) or {}
                                usage = meta.get("usage_metric", {}) or {}
                                self.input_tokens = usage.get("input_token_count", self.input_tokens or 0)
                                self.output_tokens = usage.get("output_token_count", self.output_tokens or 0)
                                # prefer raw frames for final assembly
                                joined_raw = "".join(frames).strip().replace(eos_marker, "")
                                trimmed = joined_raw.strip()
                                if trimmed.startswith("{") or trimmed.startswith("["):
                                    try:
                                        parsed = json.loads(trimmed)
                                        return json.dumps(parsed, ensure_ascii=False)
                                    except Exception:
                                        return joined_raw
                                return joined_raw
                            if "metadata" in data:
                                meta = data.get("metadata", {}) or {}
                                usage = meta.get("usage_metric", {}) or {}
                                self.input_tokens = usage.get("input_token_count", self.input_tokens or 0)
                                self.output_tokens = usage.get("output_token_count", self.output_tokens or 0)
                                continue
                        except json.JSONDecodeError:
                            logger.debug("Incomplete JSON in buffer; waiting for more data")
                            pass

                # receive loop ended normally (server closed)
                # Finalize using raw frames (preferred) or normalized parts as fallback
                joined_raw = "".join(frames).strip().replace(eos_marker, "")
                if joined_raw:
                    trimmed = joined_raw.strip()
                    if trimmed.startswith("{") or trimmed.startswith("["):
                        try:
                            parsed = json.loads(trimmed)
                            return json.dumps(parsed, ensure_ascii=False)
                        except Exception:
                            return joined_raw
                    return joined_raw

                if final_parts:
                    joined = "".join(final_parts)
                    trimmed = joined.strip()
                    if trimmed.startswith("{") or trimmed.startswith("["):
                        try:
                            parsed = json.loads(trimmed)
                            return json.dumps(parsed, ensure_ascii=False)
                        except Exception:
                            return joined
                    return joined

                return None  # nothing to return here

        # Build modes according to preference
        pref = (auth_preference or "auto").lower()
        if pref == "header":
            modes = ["header"]
        elif pref == "query":
            modes = ["query"]
        else:
            modes = ["header", "query"]

        last_exc: Optional[Exception] = None
        for mode in modes:
            try:
                result = await _try_connect_and_receive(mode)
                if result is not None:
                    self.most_recent_completion = result
                    self.most_recent_execution_time = datetime.now() - start_time
                    return result
                # else: try next mode
            except InvalidStatusCode as e:
                logger.warning("Handshake failed (mode=%s) status=%s headers=%s", mode, getattr(e, "status_code", None), getattr(e, "headers", None))
                last_exc = e
                continue
            except Exception as e:
                logger.exception("Connection/receive error (mode=%s): %s", mode, e)
                last_exc = e
                continue

        # after trying modes
        if last_exc:
            raise last_exc

        # nothing collected
        self.most_recent_completion = ""
        self.most_recent_execution_time = datetime.now() - start_time
        return ""





# ## REST METHOD (synchronous and asynchronous) - DEPRECATED

# from __future__ import annotations

# import logging
# import os
# from datetime import datetime, timedelta
# from typing import Any, Dict, Optional

# import requests
# import json
# import httpx
# from pydantic import BaseModel, Field
# from dotenv import load_dotenv

# load_dotenv()
# logger = logging.getLogger(__name__)


# api_url = os.getenv("API_URL")
# if not api_url:
#     logger.error("API_URL is not set.")
#     raise ValueError("API_URL is not set.")


# class Agent(BaseModel):
#     model: str = Field(..., description="Model name, e.g., 'gpt-4o'")
#     session_id: str = Field(..., description="Session identifier for the API")
#     api_token: Optional[str] = Field(None, description="API token for authentication")
#     response_format: Dict[str, Any] = Field(..., description="Desired response format")

#     system_prompt: Optional[str] = None
#     user_prompt: Optional[str] = None
#     model_provider: Optional[str] = "openai"
#     temperature: Optional[float] = 0.7
#     max_tokens: Optional[int] = None

#     most_recent_completion: Optional[str] = None
#     most_recent_execution_time: Optional[timedelta] = None
#     input_tokens: Optional[int] = None
#     output_tokens: Optional[int] = None

#     class Config:
#         arbitrary_types_allowed = True

#     def get_metadata(self) -> Dict[str, Any]:
#         return {
#             "session_id": self.session_id,
#             "api_token": self.api_token,
#             "system_prompt": self.system_prompt,
#             "user_prompt": self.user_prompt,
#             "model": self.model,
#             "completion": self.most_recent_completion,
#             "execution_time": (
#                 str(self.most_recent_execution_time)
#                 if self.most_recent_execution_time is not None
#                 else None
#             ),
#             "input_tokens": self.input_tokens,
#             "output_tokens": self.output_tokens,
#         }



#     # ---------------- asynchronous ----------------
#     async def completion_generation(
#         self,
#         *,
#         timeout_seconds: float = 100.0,
#     ) -> str:
#         if not self.api_token:
#             logger.info("api_token is not provided by the user. Defaulting to lcoal environment variable.")
#             self.api_token = os.getenv("CreateAI_KEY")

#             if not self.api_token:
#                 logger.error("CreateAI_KEY is not set.")
#                 raise ValueError("CreateAI_KEY is not set.")

#         if not (self.system_prompt or self.user_prompt):
#             raise ValueError("At least one of 'system_prompt' or 'user_prompt' must be provided.")

#         start_time = datetime.now()

#         messages = []
#         if self.system_prompt:
#             messages.append({"role": "system", "content": self.system_prompt})
#         if self.user_prompt:
#             messages.append({"role": "user", "content": self.user_prompt})

#         headers = {
#             "Authorization": f"Bearer {self.api_token}",
#             "Content-Type": "application/json",
#         }

#         payload = {
#             "session_id": self.session_id,
#             "query": json.dumps(messages),
#             "model_provider": self.model_provider,
#             "model_name": self.model,
#             "response_format": self.response_format,
#         }
#         if self.temperature is not None:
#             payload["temperature"] = self.temperature
#         if self.max_tokens is not None:
#             payload["max_tokens"] = self.max_tokens

#         async with httpx.AsyncClient(timeout=timeout_seconds) as client:
#             try:
#                 resp = await client.post(api_url, json=payload, headers=headers)
#                 self.most_recent_execution_time = datetime.now() - start_time

#                 if resp.status_code != 200:
#                     logger.error("Async API request failed with status code %s: %s", resp.status_code, resp.text)
#                     raise ValueError(f"API request failed with status code {resp.status_code}: {resp.text}")

#                 output_all = resp.json()
#                 self.most_recent_completion = output_all.get("response", "")

#                 usage = output_all.get("metadata", {}).get("usage_metric", {}) or {}
#                 self.input_tokens = usage.get("input_token_count", 0)
#                 self.output_tokens = usage.get("output_token_count", 0)

#                 if not self.most_recent_completion:
#                     logger.warning("Received empty output from API (async).")

#                 return self.most_recent_completion

#             except httpx.RequestError as e:
#                 logger.error("Error during async API request: %s", e)
#                 self.most_recent_execution_time = datetime.now() - start_time
#                 raise



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