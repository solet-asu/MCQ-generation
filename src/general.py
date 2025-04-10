import os
from typing import List

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