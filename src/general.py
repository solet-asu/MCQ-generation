import os
from typing import List, Union, Dict, Optional, Tuple
import json
import logging
import csv
import pandas as pd
import math
import re
from __future__ import annotations


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
    
    
def read_csv_file(file_path: str) -> List[Dict[str, str]]:
    """
    Reads a CSV file and returns its content as a list of dictionaries.
    
    Each dictionary represents a row in the CSV, with keys as column headers.
    
    Args:
        file_path (str): The path to the CSV file.
        
    Returns:
        List[Dict[str, str]]: A list of dictionaries representing the CSV rows.
    """
    
    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            return [row for row in reader]
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        return []
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")
        return []
    

def count_words(text: str | None) -> int:
    """Simple whitespace token count; treats None/empty as 0."""
    if not text:
        return 0
    # Collapse internal whitespace and split
    return len([t for t in str(text).strip().split() if t])


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


def combine_csv_files(directory_path: str, output_file: str) -> None:
    """
    Combine all CSV files in the specified directory into a single CSV file.

    :param directory_path: The path to the directory containing CSV files.
    :param output_file: The path to the output CSV file.
    """
    # Get all CSV files in the directory
    csv_files = get_files_in_directory(directory_path)

    # Initialize a list to store DataFrames
    dataframes = []

    # Iterate over each file and read it into a DataFrame
    for file in csv_files:
        if file.endswith('.csv'):
            df = pd.read_csv(file)
            dataframes.append(df)

    # Concatenate all DataFrames
    combined_df = pd.concat(dataframes, ignore_index=True)

    # Save the combined DataFrame to a CSV file
    combined_df.to_csv(output_file, index=False)


def remove_duplicates_by_column(input_file: str, column_name: str, output_file: str) -> None:
    """
    Remove duplicated rows based on the specified column from a CSV file.

    Parameters:
    - input_file (str): Path to the input CSV file.
    - column_name (str): Name of the column to check for duplicates (e.g., "Question").
    - output_file (str): Path to the output CSV file without duplicates.
    """
    try:
        # Load the CSV file into a DataFrame
        df = pd.read_csv(input_file)
        
        # Remove duplicates based on the specified column
        df_deduplicated = df.drop_duplicates(subset=column_name, keep='first')
        
        # Save the deduplicated DataFrame to a new CSV file
        df_deduplicated.to_csv(output_file, index=False)
        
        print(f"Successfully removed duplicates. Output saved to '{output_file}'.")
        
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")



_OPTION_START = re.compile(
    r"""(?imx)            # i:ignorecase, m:multiline, x:verbose
    ^\s*                  # start of line, optional leading space
    (?:\(|\[)?            # optional opening paren/bracket
    (?P<label>[A-H])      # capture A..H (allows up to 8 options; we’ll return A-D)
    (?:\)|\])?            # optional closing paren/bracket
    \s*                   # optional space
    (?:[.:)\-])?          # common delimiters after label: '.', ':', ')', '-'
    \s+                   # at least one space before the text
    """
)

_ANSWER_LETTER_RE = re.compile(
    r"""(?ix)            # i: ignore case, x: verbose
    ^\s*
    (?: (?:correct\s*)?answer \s*[:\-]\s* )?  # optional "Answer:" or "correct answer -"
    (?:\(|\[)?                               # optional opening paren/bracket
    (?P<letter>[A-D])                        # capture A–D only
    (?:\)|\])?                               # optional closing paren/bracket
    \s*
    (?:[.:)\-])?                             # optional delimiter after label
    """,
)

_CODE_FENCE_LINE = re.compile(r"^\s*```.*$")

def _is_missing(value: object) -> bool:
    # Robust "missing" check without pandas
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):  # e.g., came from a DataFrame
        return True
    s = str(value).strip()
    return s == "" or s.lower() in {"nan", "none", "null"}

def _normalize(text: str) -> str:
    """
    Normalize common MCQ text artifacts:
    - Strip code fences (``` or ```question format)
    - Convert escaped '\\n' sequences to real newlines
    - Normalize CRLF/CR to LF
    - Collapse excessive blank lines
    """
    # Remove single-line code fences if present
    lines = [ln for ln in text.splitlines() if not _CODE_FENCE_LINE.match(ln)]
    s = "\n".join(lines).strip()

    # Turn literal backslash-n into real newlines (handles CSVs with '\\nA)')
    s = s.replace("\\n", "\n")

    # Normalize newlines
    s = s.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse 3+ blank lines to one
    s = re.sub(r"\n{3,}", "\n\n", s)

    return s.strip()

def extract_mcq_components(question_text: object) -> Tuple[str, List[Optional[str]]]:
    """Extract MCQ stem and up to four options (A–D) from raw text.

    The parser is robust to:
      - Escaped newlines (\\n) embedded in a single line.
      - Option markers like `A)`, `A.`, `(A)`, `A:` (case-insensitive).
      - Multi-line option texts.
      - Code-fence wrappers (e.g., ```question format).

    Args:
        question_text: Full question text.

    Returns:
        Tuple[str, List[Optional[str]]]:
            stem, [optA, optB, optC, optD]
            Missing options are returned as None.
    """
    if _is_missing(question_text):
        return "", [None, None, None, None]

    raw = _normalize(str(question_text))
    if not raw:
        return "", [None, None, None, None]

    # Identify the first option start; everything before is stem.
    # We scan line-by-line to avoid false positives mid-line.
    lines = raw.split("\n")

    # Find indices where options start
    matches = []
    for idx, line in enumerate(lines):
        m = _OPTION_START.match(line)
        if m:
            label = m.group("label").upper()
            if "A" <= label <= "H":  # accept up to 8 choices; we’ll return A–D
                matches.append((idx, label))

    if not matches:
        # No explicit options found → entire text is stem
        stem = " ".join(ln.strip() for ln in lines if ln.strip())
        return stem, [None, None, None, None]

    # Stem = lines before the first option block
    first_opt_idx = matches[0][0]
    stem = " ".join(ln.strip() for ln in lines[:first_opt_idx] if ln.strip()).strip()

    # Build segments per option by consuming until next option start
    # Map label -> concatenated text
    option_texts: dict[str, str] = {}

    # Add sentinel end index to simplify slicing
    option_spans = [(idx, label) for idx, label in matches]
    option_spans.append((len(lines), None))  # end sentinel

    for (start_idx, label), (end_idx, _) in zip(option_spans[:-1], option_spans[1:]):
        # Remove the marker from the starting line
        line0 = _OPTION_START.sub("", lines[start_idx], count=1).strip()
        chunk_lines = [line0] if line0 else []
        # Include the lines until (but not including) the next option
        for ln in lines[start_idx + 1 : end_idx]:
            chunk_lines.append(ln.strip())
        # Join and normalize internal whitespace
        text = " ".join(x for x in chunk_lines if x).strip()
        if text:
            option_texts[label] = text
        else:
            option_texts[label] = ""

    # Prepare A–D only; if fewer present, fill with None
    ordered = []
    for lbl in ("A", "B", "C", "D"):
        val = option_texts.get(lbl)
        if val is None:
            ordered.append(None)
        else:
            ordered.append(val if val != "" else None)

    return stem, ordered



def extract_correct_answer_letter(answer_text: object) -> Optional[str]:
    """
    Extract the correct answer letter (A, B, C, or D) from answer text.

    Accepts common variants such as: "A) Text", "A. Text", "(B) Text",
    "Answer: C", "correct answer - d) Text". Returns None if not found.

    Args:
        answer_text: Raw answer text, e.g., "A) Some answer text".

    Returns:
        The uppercase letter "A" | "B" | "C" | "D", or None if not detected.
    """
    # Robust missing checks without requiring pandas
    if answer_text is None:
        return None
    if isinstance(answer_text, float) and math.isnan(answer_text):
        return None

    s = str(answer_text).strip()
    if not s or s.lower() in {"nan", "none", "null"}:
        return None

    # Handle escaped newlines from CSVs (e.g., "A) foo\\nbar")
    s = s.replace("\\n", "\n").splitlines()[0].strip()

    # Primary: label at the start (optionally with "Answer:" prefix)
    m = _ANSWER_LETTER_RE.match(s)
    if m:
        return m.group("letter").upper()

    # Fallback: search anywhere for "...Answer: X..." pattern
    m2 = re.search(r"(?i)\b(?:correct\s*)?answer\s*[:\-]\s*\(?\s*([A-D])\s*\)?", s)
    return m2.group(1).upper() if m2 else None


