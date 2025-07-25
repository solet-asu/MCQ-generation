from typing import List, Dict, Union
import ast
import re
import random
import Levenshtein
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def shuffle_mcq(mcq_dict: Dict[str, str]) -> None:
    """
    Shuffles the options of a multiple-choice question and updates the correct answer accordingly.
    If all options contain numbers (e.g., 1920s, 1930s), sorts them in numerical order instead.

    Args:
        mcq_dict (dict): A dictionary containing 'mcq' and 'mcq_answer' fields.
                         'mcq' is a string with the question and options.
                         'mcq_answer' is a string indicating the correct option (e.g., "A) Option text").
    
    Raises:
        ValueError: If the correct answer text does not match any option in the question.
    """
    mcq_str = mcq_dict['mcq']

    # Find the index where the first option (A)-D)) appears
    match = re.search(r'\b[A-D]\)', mcq_str)
    if not match:
        # If no valid option labels (A)-D)) found, log an error and raise an exception and print the mcq_str
        logging.error(f"Invalid MCQ string format: {mcq_str}")
        logging.error(f"No options in the mcq: {mcq_dict}")
        logging.error("No valid option labels (A)-D)) found in MCQ string")
        raise ValueError("No valid option labels (A)-D)) found in MCQ string")

    start_index = match.start()
    question = mcq_str[:start_index].strip()
    options_str = mcq_str[start_index:]

    # Extract options as ["A) Option text", "B) Option text", ...]
    options = re.findall(r'([A-D]\)\s.*?)(?=\n[A-D]\)|\Z)', options_str, flags=re.DOTALL)
    options = [opt.strip() for opt in options]

    # Extract option texts without labels, ensuring no extra spaces
    option_texts = [opt.split(") ", 1)[1].strip() for opt in options]

    # Extract correct answer text
    mcq_answer = mcq_dict['mcq_answer']
    match = re.match(r'^\s*([A-D])\)\s*(.+)', mcq_answer)
    if not match:
        logging.error("Invalid format for 'mcq_answer'. Expected format like 'A) Option text'")
        raise ValueError("Invalid format for 'mcq_answer'. Expected format like 'A) Option text'")

    correct_letter, correct_text = match.groups()
    correct_text = correct_text.strip()

    # if correct_text not in option_texts:
    #     logging.error("Correct answer text does not match any option in the question")
    #     raise ValueError("Correct answer text does not match any option in the question")

    # Check if all options contain numbers
    all_have_digits = all(re.search(r'\d+', text) for text in option_texts)

    if all_have_digits:
        # Sort options based on the first number in each text
        new_texts = sorted(option_texts, key=lambda text: int(re.search(r'\d+', text).group()))
        logging.info("MCQ options sorted numerically.")
    else:
        # Shuffle options randomly
        new_texts = option_texts.copy()
        random.shuffle(new_texts)
        logging.info("MCQ options shuffled randomly.")

   # Assign new letters (A, B, C, D) to the options
    letters = ['A', 'B', 'C', 'D']
    new_options = [f"{letters[i]}) {new_texts[i]}" for i in range(len(new_texts))]

    # Assuming new_texts is a list of options, correct_text is the target string, and letters is a list of corresponding answer letters
    distances = [Levenshtein.distance(correct_text, text) for text in new_texts]
    min_distance = min(distances)
    # Optional: Add a check for large distances to catch potential mismatches
    if min_distance > 10:  
        logging.warning(f"Warning: Closest match has a distance of {min_distance}, which might indicate a mismatch.")
    new_index = distances.index(min_distance)
    new_letter = letters[new_index]
    

    # Rebuild the MCQ string
    new_mcq = question + "\n\n" + "\n\n".join(new_options)

    # Update dictionary
    mcq_dict['mcq'] = new_mcq
    mcq_dict['mcq_answer'] = f"{new_letter}) {correct_text}"

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