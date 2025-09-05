
from __future__ import annotations
import math
from typing import List, Optional, Sequence, Tuple, Dict
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np

from src.agent import Agent
from src.general import count_words, extract_json_string, extract_mcq_components
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
) -> Tuple[int, str]:
    """Return (index, option_text) if a noticeably longer option exists, else (-1, '').

    Rules (across ALL A–D options):
      1) Longest option must be >= min_words.
      2) If longest has 10..15 words, it must be ≥30% longer than 2nd-longest.
      3) If longest has >15 words, it must be ≥20% longer than 2nd-longest.

    Args:
        options: Sequence of up to 4 option texts [A, B, C, D]. Missing/None allowed.

    Returns:
        (longest_index, text): e.g., (1, '...') if needs shortening; (-1, '') otherwise.
    """
    # Normalize to exactly 4 options
    opts = [(o or "").strip() for o in (options or [])[:4]]
    while len(opts) < 4:
        opts.append("")

    counts = [len(o.split()) for o in opts]

    # Need at least two non-empty options to compare fairly
    if sum(1 for c in counts if c > 0) < 2:
        return (-1, "")

    max_len = max(counts)
    # Tied longest means no single outlier
    if counts.count(max_len) > 1:
        return (-1, "")

    longest_idx = counts.index(max_len)
    second_len = max(c for i, c in enumerate(counts) if i != longest_idx)

    # Must clear the minimum length gate
    if max_len < min_words:
        return (-1, "")

    # Compare against the appropriate threshold
    if 10 <= max_len <= 15:
        needs_shortening = (max_len - second_len) >= thresh_10_to_15 * second_len
    else:  # max_len > 15
        needs_shortening = (max_len - second_len) >= thresh_gt_15 * second_len

    if needs_shortening:
        return (longest_idx, opts[longest_idx])
    return (-1, "")

# syntactic analyzer 


def _normalize_options(opts: Sequence[Optional[str]]) -> List[str]:
    """Return exactly 4 option strings (A..D), trimmed, with None->''."""
    safe = [(o or "").strip() for o in (opts or [])]
    safe = (safe + ["", "", "", ""])[:4]  # pad/truncate
    return safe


def syntactic_analysis(
        invocation_id:str,
        model: str = "gpt-4o", 
        temperature: float =0.3,
        question_stem: str = "",
        options: List[str] = [],
        table_name: str= "syntactic_analysis_metadata",
        database_file: str= '../database/mcq_metadata.db') -> Dict:

    """Generate syntatic rules."""
    create_table(table_name, database_file)

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
    syntactic_analysis_metadata = syntactic_analyzer.get_metadata()
    syntactic_analysis_metadata.update({
        "invocation_id": invocation_id,
        "question_stem": question_stem,
        "options": str(options),
   })


    if generated_text:
        generated_text_dict = extract_json_string(generated_text)

        identified_rule = str(generated_text_dict.get("syntactic_rule", "") or "").strip()
        syntactic_analysis_metadata["syntactic_rule"] = identified_rule
        confidence = generated_text_dict.get("confidence", "")
        syntactic_analysis_metadata["confidence"] = confidence
        reasoning = generated_text_dict.get("reasoning", "")
        syntactic_analysis_metadata["reasoning"] = reasoning
        logger.info(f"Syntactic analysis result: rule='{identified_rule}', confidence='{confidence}'")
    else:
        logger.warning("Failed to generate an evaluation.")
        identified_rule = "No common structure identified."

    # Insert the metadata into the database
    insert_metadata(syntactic_analysis_metadata, table_name, database_file)
    return syntactic_analysis_metadata


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
        candidates = {}
    
    # Insert the metadata into the database
    insert_metadata(candidate_shortening_metadata, table_name, database_file) 
    return candidate_shortening_metadata


# calculate cosine similarity 
def cosine_similarity_analysis(
    original_text: str,
    shortened_text: str,
    model: Optional[SentenceTransformer] = None,
) -> Optional[float]:
    """Return cosine similarity in [-1, 1] or None on failure.

    If `model` is None, tries a global `semantic_model`.
    """
    # Basic input sanity
    if not original_text or not shortened_text:
        return None

    # Resolve model
    if model is None:
        try:
            model = SentenceTransformer('all-MiniLM-L6-v2')  
        except NameError:
            return None

    try:
        # One-shot encoding; normalized so cosine == dot product
        embs = model.encode(
            [original_text, shortened_text],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        sim = float(np.dot(embs[0], embs[1]))
        if not np.isfinite(sim):
            return None
        # Numerical safety
        return float(np.clip(sim, -1.0, 1.0))
    except Exception:
        return None

# select the best candidate or reject all
def select_best_candidate(
        invocation_id: str,
        model: str,
        options: List[str],
        option_to_shorten: str,
        syntactic_rule: str,
        min_target:int,
        max_target:int,
        candidates: List[str],
        table_name: str="candidate_selection_metadata",
        database_file: str= '../database/mcq_metadata.db') -> Dict:

    """Select the best candidate option or reject all."""
    create_table(table_name, database_file)

    if not isinstance(model, str) or not model.strip():
        raise ValueError("Parameter 'model' must be a non-empty string.")
    
    optA, optB, optC, optD = _normalize_options(options)
    other_options = [o for o in [optA, optB, optC, optD] if o != option_to_shorten]
    if len(other_options) != 3:
        logger.warning("Expected exactly one option to shorten among four options.")
    other_options_str="\n ".join(other_options)

    if len(candidates) != 5:
        logger.warning("Expected exactly 5 candidate options.")

    # Calculate cosine similarities
    # put candidate and its similarity score in pairs 
    candidate_and_similarity = []
    for candidate in candidates:
        sim = cosine_similarity_analysis(option_to_shorten, candidate)
        candidate_and_similarity.append((candidate, sim))

    candidate_1, sim1 = candidate_and_similarity[0]
    candidate_2, sim2 = candidate_and_similarity[1]
    candidate_3, sim3 = candidate_and_similarity[2]
    candidate_4, sim4 = candidate_and_similarity[3]
    candidate_5, sim5 = candidate_and_similarity[4]
    
    original_word_count = count_words(option_to_shorten)
    candidate_1_word_count = count_words(candidate_1)
    candidate_2_word_count = count_words(candidate_2)
    candidate_3_word_count = count_words(candidate_3)
    candidate_4_word_count = count_words(candidate_4)

    prompt_file = "candidate_selection_prompts.yaml"
    prompts = get_prompts(prompt_file)

    system_prompt = prompts.get("system_prompt", "")
    user_prompt = prompts.get("user_prompt", "").format(
        original_option =option_to_shorten,
        original_word_count=original_word_count,
        min_target=min_target,
        max_target=max_target,
        syntactic_rule=syntactic_rule,
        other_options_text=other_options_str,
        candidate_1=candidate_1,
        similarity_1=sim1 if sim1 is not None else "N/A",
        candidate_1_word_count=candidate_1_word_count,
        candidate_2=candidate_2,
        similarity_2=sim2 if sim2 is not None else "N/A",
        candidate_2_word_count=candidate_2_word_count,
        candidate_3=candidate_3,
        similarity_3=sim3 if sim3 is not None else "N/A",   
        candidate_3_word_count=candidate_3_word_count,
        candidate_4=candidate_4,
        similarity_4=sim4 if sim4 is not None else "N/A",
        candidate_4_word_count=candidate_4_word_count,
        candidate_5=candidate_5,
        similarity_5=sim5 if sim5 is not None else "N/A",
        candidate_5_word_count=count_words(candidate_5),
   )

    candidate_selector = Agent(
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt
    )
    
    generated_text = candidate_selector.completion_generation()
    candidate_selection_metadata = candidate_selector.get_metadata()
    candidate_selection_metadata.update({
        "invocation_id": invocation_id,
        "option_to_shorten": option_to_shorten,
        "syntactic_rule": syntactic_rule,
        "min_target": min_target,
        "max_target": max_target,
        "candidates": str(candidates),
    })

    if generated_text:
        try:
            generated_text_dict = extract_json_string(generated_text)
        except Exception:
            logger.exception("Failed to parse model output as JSON.")
            generated_text_dict = {}

        if isinstance(generated_text_dict, dict):
            best_candidate = generated_text_dict.get("best_candidate", "")
            candidate_selection_metadata["best_candidate"] = best_candidate
            reasoning = generated_text_dict.get("evaluation_summary", "")
            candidate_selection_metadata["reasoning"] = reasoning
            logger.info(f"Selected candidate: '{best_candidate}'")
        else:
            best_candidate = None
            logger.warning("Extracted best_candidate is not a dictionary.")
    else:
        logger.warning("Failed to generate a selection.")
        best_candidate = None
    # Insert the metadata into the database
    insert_metadata(candidate_selection_metadata, table_name, database_file)
    return candidate_selection_metadata


def update_mcq_with_new_option(mcq: str, shortened_option: str, option_index: int) -> str:
    """Update the MCQ string with the shortened option."""
    if option_index not in [0, 1, 2, 3]:
        raise ValueError("option_index must be 0 (A), 1 (B), 2 (C), or 3 (D).")

    question, options = extract_mcq_components(mcq)
    if len(options) != 4:
        raise ValueError("MCQ must have exactly 4 options.")

    # Replace the specified option with the shortened version
    options[option_index] = shortened_option.strip()

    # Rebuild the MCQ string
    letters = ['A', 'B', 'C', 'D']
    new_options = [f"{letters[i]}) {options[i]}" for i in range(4)]
    new_mcq = question + "\n\n" + "\n\n".join(new_options)

    return new_mcq

