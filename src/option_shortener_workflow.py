# option_shortener_workflow.py
from __future__ import annotations

from typing import Dict, Tuple, List, Optional
import json

from src.general import extract_mcq_components, extract_correct_answer_letter
from src.option_shortening_helper import (
    identify_longer_options,
    syntactic_analysis,
    calculate_length_range,
    generate_candidate_short_options,
    select_best_candidate,
    update_mcq_with_new_option,
    format_answer_from_letter,   # builds "X) text" from letter + options
)

import logging

# Configure logging
logger = logging.getLogger(__name__)

async def check_and_shorten_long_option(
    invocation_id: str,
    mcq: str,
    mcq_answer: str,
    model: str = "gpt-4o",
) -> Tuple[str, str, Dict]:
    """Shorten an outlier option if needed and return:
       (updated_mcq, updated_mcq_answer, {"input_tokens": int, "output_tokens": int})

    Notes:
      - Candidate normalization happens **in the helper**.
      - This workflow avoids redundant JSON parsing / re-normalization.
    """
    
    # ---- Step 1: Parse MCQ and current answer ----
    question, options = extract_mcq_components(mcq)
    correct_answer_letter = extract_correct_answer_letter(mcq_answer)
    updated_mcq_answer = format_answer_from_letter(correct_answer_letter, options)
    log_extra = {"invocation_id": invocation_id}

    # ---- Step 2: Detect noticeably longer option ----
    longer_option_index, longer_option_text = identify_longer_options(options)
    if not longer_option_text:
        logging.info("No noticeably longer option in this question", extra=log_extra)
        return mcq, updated_mcq_answer, {}  # nothing to do
        
    logging.info("Noticeably longer option DETECTED in this question")
    input_tokens_accumulated = 0
    output_tokens_accumulated = 0

    # ---- Step 3: Analyze syntactic structure (async) ----
    identified_rule_meta = await syntactic_analysis(
        invocation_id=invocation_id,
        model=model,
        temperature=0.3,
        question_stem=question,
        options=options,
    )
    identified_rule = identified_rule_meta.get("syntactic_rule", "")
    input_tokens_accumulated += int(identified_rule_meta.get("input_tokens") or 0)
    output_tokens_accumulated += int(identified_rule_meta.get("output_tokens") or 0)

    # ---- Step 4: Compute target length range ----
    min_length, max_length = calculate_length_range(options)

    # ---- Step 5: Generate candidates (async) ----
    cand_meta = await generate_candidate_short_options(
        invocation_id=invocation_id,
        model=model,
        options=options,
        option_to_shorten=longer_option_text,
        syntactic_rule=identified_rule,
        min_target=min_length,
        max_target=max_length,
        table_name="candidate_shortening_metadata",
        database_file="../database/mcq_metadata.db",
    )
    # Prefer the pre-normalized list provided by the helper.
    # Fallback: parse the JSON string once if needed.
    candidates: List[str] = cand_meta.get("candidates_list")
    if candidates is None:
        candidates = json.loads(cand_meta.get("candidates", "[]"))

    input_tokens_accumulated += int(cand_meta.get("input_tokens") or 0)
    output_tokens_accumulated += int(cand_meta.get("output_tokens") or 0)

    if not candidates:
        return mcq, updated_mcq_answer, {
            "input_tokens": input_tokens_accumulated,
            "output_tokens": output_tokens_accumulated,
        }

    # ---- Step 6: Select best candidate (async) ----
    selection_meta = await select_best_candidate(
        invocation_id=invocation_id,
        model=model,
        options=options,
        option_to_shorten=longer_option_text,
        syntactic_rule=identified_rule,
        min_target=min_length,
        max_target=max_length,
        candidates=candidates,  # already normalized; no extra checks here
        table_name="candidate_selection_metadata",
        database_file="../database/mcq_metadata.db",
    )
    best_candidate: Optional[str] = selection_meta.get("best_candidate")
    input_tokens_accumulated += int(selection_meta.get("input_tokens") or 0)
    output_tokens_accumulated += int(selection_meta.get("output_tokens") or 0)

    if not best_candidate:
        logging.info("No candidate is chosen, falling back to the original question option", extra=log_extra)
        return mcq, updated_mcq_answer, {
            "input_tokens": input_tokens_accumulated,
            "output_tokens": output_tokens_accumulated,
        }

    # ---- Step 7: Update MCQ and final answer string ----
    updated_mcq = update_mcq_with_new_option(mcq, best_candidate, longer_option_index)

    # Re-parse options from updated text to ensure the answer string matches final rendering.
    _, updated_options = extract_mcq_components(updated_mcq)
    updated_mcq_answer = format_answer_from_letter(correct_answer_letter, updated_options)
    logging.info("Noticeably longer option SHORTENED for this question", extra=log_extra)

    return updated_mcq, updated_mcq_answer, {
        "input_tokens": input_tokens_accumulated,
        "output_tokens": output_tokens_accumulated,
    }
