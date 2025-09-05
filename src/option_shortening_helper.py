
from __future__ import annotations
import math
from typing import List, Optional, Sequence, Tuple, Dict
from src.agent import Agent
from src.general import count_words, extract_json_string
from src.prompt_fetch import get_prompts
from src.database_handler import *
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

_MIN_WORDS = 10
_THRESH_10_TO_15 = 0.30  # 30% longer than 2nd-longest when 10..15 words
_THRESH_GT_15 = 0.20     # 20% longer than 2nd-longest when >15 words


def identify_longer_options(
    options: Sequence[Optional[str]],
    *,
    min_words: int = 10,
    thresh_10_to_15: float = 0.30,  # 30% longer than 2nd-longest when 10..15 words
    thresh_gt_15: float = 0.20,     # 20% longer when >15 words
) -> str:
    """Return the option text that is noticeably longer, or '' if none.

    Rules (across ALL A–D options):
      1) Longest option must be >= min_words.
      2) If longest has 10..15 words, it must be ≥30% longer than 2nd-longest.
      3) If longest has >15 words, it must be ≥20% longer than 2nd-longest.

    Args:
        options: Sequence of up to 4 option texts [A, B, C, D]. Missing/None allowed.

    Returns:
        str: The longest option that violates the balance rules, or '' if none.
    """
    # Normalize to exactly 4 options
    opts = [(o or "").strip() for o in (options or [])[:4]]
    while len(opts) < 4:
        opts.append("")

    # Word counts (whitespace tokenization is sufficient here)
    counts = [len(o.split()) for o in opts]

    # Require at least two non-empty options to compare fairly
    if sum(1 for c in counts if c > 0) < 2:
        return ""

    max_len = max(counts)
    # Tied longest means no single outlier
    if counts.count(max_len) > 1:
        return ""

    longest_idx = counts.index(max_len)
    second_len = max(c for i, c in enumerate(counts) if i != longest_idx)

    # Must clear the minimum length gate
    if max_len < min_words:
        return ""

    # Compare against the appropriate threshold
    if 10 <= max_len <= 15:
        needs_shortening = (max_len - second_len) >= thresh_10_to_15 * second_len
    else:  # max_len > 15
        needs_shortening = (max_len - second_len) >= thresh_gt_15 * second_len

    return opts[longest_idx] if needs_shortening else ""

# syntactic analyzer 

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def _normalize_options(opts: Sequence[Optional[str]]) -> List[str]:
    """Return exactly 4 option strings (A..D), trimmed, with None->''."""
    safe = [(o or "").strip() for o in (opts or [])]
    safe = (safe + ["", "", "", ""])[:4]  # pad/truncate
    return safe


def syntactic_analysis(model: str = "gpt-4o", 
                       temperature: float =0.3,
                       question_stem: str = "",
                       options: List[str] = []) -> str:

    """Generate syntatic rules."""

    if not isinstance(model, str) or not model.strip():
        raise ValueError("Parameter 'model' must be a non-empty string.")
    
    stem = (question_stem or "").strip()
    if not stem:
        logger.warning("Empty question_stem provided.")

    optA, optB, optC, optD = _normalize_options(options)
    
    prompt_file = "syntactic_analyzer_prompts.yaml"
    prompts = get_prompts(prompt_file)

    system_prompt = prompts.get("system_prompt", "")
    user_prompt = prompts.get("user_prompt", "").format(
        question =question_stem,
            option_a=optA,
            option_b=optB,
            option_c=optC,
            option_d=optD
    )

    syntactic_analyzer = Agent(
        model=model,
        temperature=temperature,
        system_prompt=system_prompt,
        user_prompt=user_prompt
    )
    
    generated_text = syntactic_analyzer.completion_generation()

    if generated_text:
        generated_text_dict = extract_json_string(generated_text)

        identified_rule = str(generated_text_dict.get("syntactic_rule", "") or "").strip()
        confidence = generated_text_dict.get("confidence", "")
        logger.info(f"Syntactic analysis result: rule='{identified_rule}', confidence='{confidence}'")
    else:
        logger.warning("Failed to generate an evaluation.")
        identified_rule = "No common structure identified."

 
    return identified_rule


def calculate_length_range(options: Sequence[Optional[str]]) -> Tuple[int, int]:
    """
    Calculate acceptable word-count range for option shortening.

    Uses a simplified, integer-safe variant of the user's formula:
      min_target = floor(0.8 * min_length)
      max_target = ceil(1.1 * max_length)

    Returns (0, 0) if no non-empty options are provided.
    """
    # Consider only the first four options; treat None/empty as 0 words
    counts = [count_words(o) for o in (options or [])[:4]]

    # Use only positive counts to avoid skew; if none, return a neutral range
    positive = [c for c in counts if c > 0]
    if not positive:
        return (0, 0)

    min_len = min(positive)
    max_len = max(positive)

    min_target = max(1, math.floor(0.8 * min_len))
    max_target = math.ceil(1.1 * max_len)

    # Ensure coherent range in edge cases
    if min_target > max_target:
        min_target = max_target

    return (min_target, max_target)


def generate_candidate_short_options(
        invocation_id: str,
        model: str, 
        options: List[str],
        option_to_shorten: str,
        syntactic_rule: str,
        min_target:int,
        max_target:int,
        table_name: str="candidate_shortening_metadata",
         database_file: str= '../database/mcq_metadata.db') -> Dict:

    """Generate candidate short options and store metadata."""
    create_table(table_name, database_file)

    if not isinstance(model, str) or not model.strip():
        raise ValueError("Parameter 'model' must be a non-empty string.")
    
    optA, optB, optC, optD = _normalize_options(options)
    other_options = [o for o in [optA, optB, optC, optD] if o != option_to_shorten]
    if len(other_options) != 3:
        logger.warning("Expected exactly one option to shorten among four options.")
    other_options_str="\n ".join(other_options)

    prompt_file = "candidate_generation_prompts.yaml"
    prompts = get_prompts(prompt_file)

    system_prompt = prompts.get("system_prompt", "")
    user_prompt = prompts.get("user_prompt", "").format(
        original_option =option_to_shorten,
        syntactic_rule=syntactic_rule,
        min_target=min_target,
        max_target=max_target,
        other_options_text=other_options_str
    )

    candidate_generator = Agent(
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt
    )
    
    generated_text = candidate_generator.completion_generation()

    candidate_shortening_metadata = candidate_generator.get_metadata()
    candidate_shortening_metadata.update({
        "invocation_id": invocation_id,
        "option_to_shorten": option_to_shorten,
        "syntactic_rule": syntactic_rule,
        "min_target": min_target,
        "max_target": max_target
    })


    if generated_text:
        try:
            generated_text_dict = extract_json_string(generated_text)
        except Exception:
            logger.exception("Failed to parse model output as JSON.")
            generated_text_dict = {}

        if isinstance(generated_text_dict, dict):
            candidates = generated_text_dict.get("candidates", {})
            candidate_shortening_metadata["candidates"] = str(candidates)
            reasoning = generated_text_dict.get("reasoning", "")
            candidate_shortening_metadata["reasoning"] = reasoning
            logger.info(f"Generated {len(candidates)} candidate options.")
        else:
            candidates = {}
            logger.warning("Extracted candidates is not a dictionary.")

    else:
        logger.warning("Failed to generate candidates.")
    
        # Insert the metadata into the database
        insert_metadata(candidate_shortening_metadata, table_name, database_file) 
    return candidates


