from typing import List, Dict, Union
import ast
import re
import random
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def shuffle_mcq(mcq_dict: Dict[str, str]) -> None:
    """
    Shuffles the options of a multiple-choice question and updates the correct answer accordingly.

    Args:
        mcq_dict (dict): A dictionary containing 'mcq' and 'mcq_answer' fields.
                         'mcq' is a string with the question and options separated by "\n  \n".
                         'mcq_answer' is a string indicating the correct option (e.g., "A) Option text").
    
    Raises:
        ValueError: If the correct answer text does not match any option in the question.
    """
    # Get the mcq string and split into question and options
    mcq_str = mcq_dict['mcq']
    parts = mcq_str.split("\n  \n")
    question = parts[0]
    options = parts[1:]
    
    # Extract the text of each option, removing the letter prefix (e.g., "A) ")
    option_texts = [opt.split(") ", 1)[1] for opt in options]
    
    # Extract the correct answer text from mcq_answer
    mcq_answer = mcq_dict['mcq_answer']
    correct_letter, correct_text = mcq_answer.split(") ", 1)
    
    # Verify that the correct answer text matches one of the options
    if correct_text not in option_texts:
        logging.error("Correct answer text does not match any option in the question")
        raise ValueError("Correct answer text does not match any option in the question")
    
    # Create a copy of option texts and shuffle them
    shuffled_texts = option_texts.copy()
    random.shuffle(shuffled_texts)
    
    # Find the new position of the correct answer in the shuffled list
    new_index = shuffled_texts.index(correct_text)
    
    # Assign new letters (A, B, C, D) based on the shuffled order
    letters = ['A', 'B', 'C', 'D']
    new_letter = letters[new_index]
    
    # Reconstruct the mcq string with the shuffled options
    new_options = [f"{letters[i]}) {shuffled_texts[i]}" for i in range(len(shuffled_texts))]
    new_mcq = question + "\n  \n" + "\n  \n".join(new_options)
    
    # Update mcq_answer with the new letter
    new_mcq_answer = f"{new_letter}) {correct_text}"
    
    # Update the dictionary in place
    mcq_dict['mcq'] = new_mcq
    mcq_dict['mcq_answer'] = new_mcq_answer

    logging.info("MCQ options shuffled successfully.")


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
    # Shuffle the options in each MCQ
    for d in mcq_metadata:
        shuffle_mcq(d)
        
    reordered = reorder_mcq_metadata(mcq_metadata)
    marked = add_question_markers(reordered)
    return marked