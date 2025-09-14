from typing import Dict, Any, Tuple, List
import re
from src.general import dict_check_and_convert
import logging

# Configure logger
logger = logging.getLogger(__name__)

def validate_and_parse_plan(plan: Dict[str, Any], fact: int, inference: int) -> Tuple[str, List[str], List[str]]:
    """
    Validates the plan against the user request and parses the summary, facts, and inferences.

    Args:
        plan (Dict[str, Any]): The dictionary object representing the plan.
        fact: A integer suggesting the expected counts of facts as requested by the user.
        inference: A integer suggesting the expected counts of inferences as requested by the user.

    Returns:
        Tuple[str, List[str], List[str]]: A tuple containing the summary, list of facts, and list of inferences.

    """
    logger.info(
        "validate_and_parse_plan called (expected facts=%d, inferences=%d)",
        fact, inference
    )
    try:
        # Extract facts and inferences from the plan
        facts = plan.get("facts", {})
        inferences = plan.get("inferences", {})
        logger.debug(
            "Raw plan keys present: facts=%s, inferences=%s, summary_present=%s",
            isinstance(facts, (dict, list)), isinstance(inferences, (dict, list)), "summary" in plan
        )

        facts_dict = dict_check_and_convert(facts)
        inferences_dict = dict_check_and_convert(inferences)

        # Count validation
        actual_facts_count = len(facts_dict)
        actual_inferences_count = len(inferences_dict)
        expected_facts_count = fact
        expected_inferences_count = inference

        logger.info(
            "Counts — facts: expected=%d actual=%d; inferences: expected=%d actual=%d",
            expected_facts_count, actual_facts_count, expected_inferences_count, actual_inferences_count
        )

        errors = []

        if actual_facts_count != expected_facts_count:
            error_msg = (
                f"Mismatch in facts count: expected {expected_facts_count}, got {actual_facts_count}."
            )
            logger.error(error_msg)
            errors.append(error_msg)

        if actual_inferences_count != expected_inferences_count:
            error_msg = (
                f"Mismatch in inferences count: expected {expected_inferences_count}, got {actual_inferences_count}."
            )
            logger.error(error_msg)
            errors.append(error_msg)

        if errors:
            logger.debug("Validation errors encountered: %s", errors)
            raise ValueError("Validation failed. See logged errors.")

        # Parse summary, facts, and inferences 
        summary = plan.get("summary", "")
        facts = [fact for fact in facts_dict.values()]
        inferences = [inf for inf in inferences_dict.values()]

        logger.info(
            "Validation passed. Parsed summary_len=%d, facts=%d, inferences=%d",
            len(summary), len(facts), len(inferences)
        )

        return summary, facts, inferences

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise RuntimeError("An unexpected error occurred.") from e
    
    

def extract_chunks(text: str, chunks: List[str]) -> str:
    """
    Extract content from text enclosed by specified chunk tags.

    Args:
        text (str): The text containing HTML-like chunk tags.
        chunks (List[str]): A list of chunk labels to extract.

    Returns:
        List[str]: A list of content strings from the specified chunks.
    """
    logger.info("extract_chunks called with %d chunk label(s)", len(chunks))
    extracted_contents = []

    for chunk_label in chunks:
        # Match opening and closing tags like <chunk1>...</chunk1>
        pattern = fr"<{re.escape(chunk_label)}>(.*?)</{re.escape(chunk_label)}>"
        matches = re.findall(pattern, text, flags=re.DOTALL)
        logger.debug("Found %d match(es) for label '%s'", len(matches), chunk_label)

        # Strip whitespace from matches and add to results
        extracted_contents.extend([match.strip() for match in matches])

    #join the extracted contents into a single string, concatenating with a line break
    extracted_contents = "\n".join(extracted_contents)
    logger.info("extract_chunks returning text_len=%d", len(extracted_contents))

    return extracted_contents


def extract_unlisted_chunks(summary: str, chunks: List[str]) -> str:
    """
    Extract text from all chunks in the summary that are NOT listed in `chunks`.

    Args:
        summary (str): The full summary with chunk tags.
        chunks (List[str]): List of chunk labels to exclude (e.g., ["chunk2"]).

    Returns:
        str: Concatenated text from chunks not in the `chunks` list.
    """
    logger.info("extract_unlisted_chunks called; excluding %d chunk label(s)", len(chunks))
    # Regex pattern to find all chunked segments in the format <chunkX>...</chunkX>
    chunk_pattern = re.compile(r"<(chunk\d+)>(.*?)</\1>", re.DOTALL)
    
    # Find all chunks in the summary
    all_chunks = chunk_pattern.findall(summary)
    logger.debug("Total chunk segments found in summary: %d", len(all_chunks))

    # Filter out chunks listed in the exclusion list
    filtered_texts = [
        text.strip() for label, text in all_chunks if label not in chunks
    ]
    logger.info("extract_unlisted_chunks kept %d segment(s)", len(filtered_texts))

    # Join the filtered texts with a space
    result = " ".join(filtered_texts)
    logger.debug("extract_unlisted_chunks result_len=%d", len(result))
    return result



def extract_summary(text: str) -> str:
    """
    Removes all HTML-style chunk tags from the summarized text.

    Args:
        text (str): The summarized text with tags like <chunk1>...</chunk1>.

    Returns:
        str: The cleaned summarized text without any tags.
    """
    logger.info("extract_summary called with text_len=%d", len(text))
    # Remove all tags like <chunkX> and </chunkX>
    cleaned_text = re.sub(r"</?chunk\d+>", "", text)
    cleaned = cleaned_text.strip()
    logger.info("extract_summary returning text_len=%d", len(cleaned))
    return cleaned


def create_task_list(chunked_text: str, plan: Dict[str, Any], fact: int, inference: int, main_idea: int) -> List[Dict[str, str|list]]:
    """
    Create a task list from the provided plan.

    Args:
        plan (Dict[str, Any]): The plan containing text summary, facts, and inferences.

    Returns:
        List[Dict[str, str]]: A list of dictionaries representing tasks.
    """
    logger.info(
        "create_task_list called (requested: facts=%d, inferences=%d, main_idea=%d)",
        fact, inference, main_idea
    )
    task_list = []

    summary, facts, inferences = validate_and_parse_plan(plan, fact, inference)
    logger.info("Validated plan: facts=%d, inferences=%d", len(facts), len(inferences))

    if facts:
        for idx, a_fact in enumerate(facts, start=1):
            logger.debug("Building fact task #%d (chunks=%s)", idx, a_fact.get("chunk", []))
            fact_task ={
                "question_type": "fact",
                "content": a_fact.get("content", ""),
                "text": extract_chunks(chunked_text, a_fact.get("chunk", [])),
                "context": extract_unlisted_chunks(summary, a_fact.get("chunk", [])),
                "chunk": a_fact.get("chunk", [])
            }
            task_list.append(fact_task)
    
    if inferences:
        for idx, a_inference in enumerate(inferences, start=1):
            logger.debug("Building inference task #%d (chunks=%s)", idx, a_inference.get("chunk", []))
            inference_task = {
                "question_type": "inference",
                "content": a_inference.get("content", ""),
                "text": extract_chunks(chunked_text, a_inference.get("chunk", [])),
                "context": extract_unlisted_chunks(summary, a_inference.get("chunk", [])),
                "chunk": a_inference.get("chunk", [])
            }
            task_list.append(inference_task)
    
    if main_idea:
        logger.debug("Adding main_idea task")
        main_idea_task = {
            "question_type": "main_idea",
            "text": extract_summary(summary)
        }
        task_list.append(main_idea_task)

    logger.info("create_task_list built %d task(s) total", len(task_list))
    return task_list

