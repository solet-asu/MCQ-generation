import json
import logging
from typing import Dict, Any, Tuple, List
import re
from src.general import dict_check_and_convert


# Configure logger
logging.basicConfig(level=logging.INFO)
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
    try:

        # Extract facts and inferences from the plan
        facts = plan.get("facts", {})
        facts_dict = dict_check_and_convert(facts)
        inferences = plan.get("inferences", {})
        inferences_dict = dict_check_and_convert(inferences)

        # Count validation
        actual_facts_count = len(facts_dict)
        actual_inferences_count = len(inferences_dict)
        expected_facts_count = fact
        expected_inferences_count = inference

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
            raise ValueError("Validation failed. See logged errors.")

        # Parse summary, facts, and inferences 
        summary = plan.get("summary", "")
        facts = [fact for fact in facts_dict.values()]
        inferences = [inf for inf in inferences_dict.values()]

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
    extracted_contents = []

    for chunk_label in chunks:
        # Match opening and closing tags like <chunk1>...</chunk1>
        pattern = fr"<{re.escape(chunk_label)}>(.*?)</{re.escape(chunk_label)}>"
        matches = re.findall(pattern, text, flags=re.DOTALL)

        # Strip whitespace from matches and add to results
        extracted_contents.extend([match.strip() for match in matches])

    #join the extracted contents into a single string, concatenating with a line break
    extracted_contents = "\n".join(extracted_contents)

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
    # Regex pattern to find all chunked segments in the format <chunkX>...</chunkX>
    chunk_pattern = re.compile(r"<(chunk\d+)>(.*?)</\1>", re.DOTALL)
    
    # Find all chunks in the summary
    all_chunks = chunk_pattern.findall(summary)

    # Filter out chunks listed in the exclusion list
    filtered_texts = [
        text.strip() for label, text in all_chunks if label not in chunks
    ]

    # Join the filtered texts with a space
    return " ".join(filtered_texts)



def extract_summary(text: str) -> str:
    """
    Removes all HTML-style chunk tags from the summarized text.

    Args:
        text (str): The summarized text with tags like <chunk1>...</chunk1>.

    Returns:
        str: The cleaned summarized text without any tags.
    """
    # Remove all tags like <chunkX> and </chunkX>
    cleaned_text = re.sub(r"</?chunk\d+>", "", text)
    return cleaned_text.strip()


def create_task_list(plan: Dict[str, Any], fact: int, inference: int, main_idea: int) -> List[Dict[str, str]]:
    """
    Create a task list from the provided plan.

    Args:
        plan (Dict[str, Any]): The plan containing text summary, facts, and inferences.

    Returns:
        List[Dict[str, str]]: A list of dictionaries representing tasks.
    """
    task_list = []

    summary, facts, inferences = validate_and_parse_plan(plan, fact, inference)
    if facts:
        for a_fact in facts:

            fact_task ={
                "question_type": "fact",
                "content": a_fact.get("content", ""),
                "text": extract_chunks(summary, a_fact.get("chunks", [])),
                "context": extract_unlisted_chunks(summary, a_fact.get("chunks", [])),
            }
            task_list.append(fact_task)
    
    if inferences:
        for a_inference in inferences:
            inference_task = {
                "question_type": "inference",
                "content": a_inference.get("content", ""),
                "text": extract_chunks(summary, a_inference.get("chunks", [])),
                "context": extract_unlisted_chunks(summary, a_inference.get("chunks", [])),
            }
            task_list.append(inference_task)
    
    if main_idea:
        main_idea_task = {
            "question_type": "main_idea",
            "text": extract_summary(summary)
        }
        task_list.append(main_idea_task)
    return task_list



