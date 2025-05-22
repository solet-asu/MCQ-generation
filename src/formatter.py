from typing import List, Dict, Union
import ast
import re
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_chunk_number(chunk_str: str) -> Union[int, float]:
    """Extracts the last chunk number from a stringified list.
    
    Args:
        chunk_str (str): A string representation of a list of chunks.
        
    Returns:
        int: The extracted chunk number.
        float: Returns infinity if no valid chunk number is found.
    """
    try:
        chunks = ast.literal_eval(chunk_str)
        if not chunks:
            return float('inf')  # Treat empty chunks as coming last before main_idea
        last_chunk = chunks[-1]
        match = re.search(r'\d+', last_chunk)
        return int(match.group()) if match else float('inf')
    except (ValueError, SyntaxError) as e:
        logging.error(f"Error parsing chunk string: {chunk_str} - {e}")
        return float('inf')


def reorder_mcq_metadata(mcq_metadata: List[Dict]) -> List[Dict]:
    """Reorders mcq_metadata based on chunk order and question type.
    
    Args:
        mcq_metadata (List[Dict]): List of metadata dictionaries.
        
    Returns:
        List[Dict]: Reordered list of metadata dictionaries.
    """
    main_ideas = [item for item in mcq_metadata if item.get("question_type") == "main_idea"]
    others = [item for item in mcq_metadata if item.get("question_type") != "main_idea"]

    # Sort 'others' based on the extracted chunk number, maintaining original order within groups
    others.sort(key=lambda x: extract_chunk_number(x.get("chunk", "[]")))

    return others + main_ideas


def add_question_markers(mcq_metadata: List[Dict]) -> List[Dict]:
    """Adds Q1:, Q2:, ... to mcq and mcq_answer fields.
    
    Args:
        mcq_metadata (List[Dict]): List of metadata dictionaries.
        
    Returns:
        List[Dict]: List of metadata dictionaries with question markers added.
    """
    for idx, item in enumerate(mcq_metadata, 1):
        prefix = f"Q{idx}: "
        item["mcq"] = prefix + item["mcq"].lstrip()
        item["mcq_answer"] = prefix + item["mcq_answer"].lstrip()
    return mcq_metadata


def reformat_mcq_metadata(mcq_metadata: List[Dict]) -> List[Dict]:
    """Full processing pipeline for MCQ metadata.
    
    Args:
        mcq_metadata (List[Dict]): List of metadata dictionaries.
        
    Returns:
        List[Dict]: Fully processed list of metadata dictionaries.
    """
    reordered = reorder_mcq_metadata(mcq_metadata)
    marked = add_question_markers(reordered)
    return marked