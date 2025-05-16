import json
import logging
from typing import Dict, Any, Tuple, List
import re



# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_and_parse_plan(plan_json: str, user_request: Dict[str, int]) -> Tuple[str, List[str], List[str]]:
    """
    Validates the plan JSON against the user request and parses the summary, facts, and inferences.

    Args:
        plan_json (str): The JSON string representing the plan.
        user_request (Dict[str, int]): A dictionary containing the expected counts of facts and inferences.

    Returns:
        Tuple[str, List[str], List[str]]: A tuple containing the summary, list of facts, and list of inferences.

    Raises:
        ValueError: If the JSON is invalid or validation fails.
    """
    try:
        # Convert JSON string to Python dictionary
        plan: Dict[str, Any] = json.loads(plan_json)

        # Extract facts and inferences from the plan
        facts_dict = plan.get("selection", {}).get("facts", {})
        inferences_dict = plan.get("selection", {}).get("inferences", {})

        # Count validation
        actual_facts_count = len(facts_dict)
        actual_inferences_count = len(inferences_dict)
        expected_facts_count = user_request.get("facts", 0)
        expected_inferences_count = user_request.get("inferences", 0)

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

        # Parse summary, facts, and inferences content
        summary = plan.get("summary", "")
        facts = [fact["content"] for fact in facts_dict.values()]
        inferences = [inf["content"] for inf in inferences_dict.values()]

        return summary, facts, inferences

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON input: {e}")
        raise ValueError("Invalid JSON input.") from e

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise RuntimeError("An unexpected error occurred.") from e
    
    

def extract_chunks(text: str, chunks: List[str]) -> List[str]:
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

    return extracted_contents


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



