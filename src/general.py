import os
from typing import List, Union, Dict
import json
import logging


# Configure logging
logging.basicConfig(level=logging.DEBUG)

def get_files_in_directory(directory_path: str) -> List[str]:
    """
    Get all file paths in the specified directory and return them as a list of strings.

    :param directory_path: The path to the directory to search for files.
    :return: A list of file paths as strings.
    """
    file_list = []

    # Walk through the directory
    for root, _, files in os.walk(directory_path):
        for file in files:
            # Construct the full file path
            file_path = os.path.join(root, file)
            file_list.append(file_path)

    return file_list


def read_text_file(file_path: str) -> str:
    """Reads the content of a text file and returns it as a string."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return "Error: File not found."
    except Exception as e:
        return f"Error: {e}"
    

def count_words(input_string: str) -> int:
    """
    Count the number of words in a given string.

    Args:
        input_string (str): The string to count words in.

    Returns:
        int: The number of words in the string.
    """
    # Split the string into words using whitespace as the delimiter
    words = input_string.split()
    
    # Return the number of words
    return len(words)

def count_paragraphs(input_string: str) -> int:
    """
    Count the number of paragraphs in a given string.

    Args:
        input_string (str): The string to count paragraphs in.

    Returns:
        int: The number of paragraphs in the string.
    """
    # Split the string into paragraphs using newline characters as the delimiter
    paragraphs = input_string.split('\n')
    
    # Filter out empty strings and return the count
    return len([p for p in paragraphs if p.strip()])



def dict_check_and_convert(obj: Union[str, dict]) -> dict:
    """
    Ensures that the input object is a dictionary.
    If the object is a JSON-formatted string, it parses it into a dictionary.
    
    Args:
        obj (str | dict): Input that may be a dictionary or a JSON string.

    Returns:
        dict: A dictionary parsed from the input or the input itself if already a dict.
              Returns an empty dictionary if parsing fails.
    """
    if isinstance(obj, str):
        try:
            return json.loads(obj)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return {}
    elif isinstance(obj, dict):
        return obj
    else:
        print(f"Unsupported input type: {type(obj)}. Expected str or dict.")
        return {}
    



def extract_json_string(text: str) -> Dict:
    """
    Extract a valid JSON object from a string that may contain extra content
    before or after the actual JSON. Returns the parsed JSON object as a dict.
    
    Raises ValueError if no valid JSON object can be found.
    """
    start = text.find('{')
    if start == -1:
        logging.error("No JSON object found in input string")
        raise ValueError("No JSON object found in input string")

    # Try to find the matching closing brace
    brace_count = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            brace_count += 1
        elif text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                json_str = text[start:i+1]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    logging.error(f"Invalid JSON content: {e}")
                    raise ValueError(f"Invalid JSON content: {e}")

    logging.error("Could not find a complete JSON object in the input string")
    raise ValueError("Could not find a complete JSON object in the input string")