from src.prompt_fetch import *
from src.agent import Agent
from src.general import *
import sqlite3
from typing import Dict

# dictionary map to link question types to their respective prompts
question_type_prompt_map = {
    "details": "details_prompts.yaml",
    "inference": "inference_prompts.yaml",
    "main_idea": "main_idea_prompts.yaml",
}


# Define the database file
DATABASE_FILE = '../database/mcq_metadata.db'

def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT name FROM sqlite_master WHERE type='table' AND name=?
        ''', (table_name,))
        return cursor.fetchone() is not None

def create_table():
    """Create the mcq_metadata table if it doesn't exist."""
    if not table_exists('mcq_metadata'):
        with sqlite3.connect(DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE mcq_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_type TEXT,
                    system_prompt TEXT,
                    user_prompt TEXT,
                    model TEXT,
                    completion TEXT,
                    extraction TEXT,
                    execution_time TEXT,
                    input_tokens INTEGER,
                    output_tokens INTEGER
                )
            ''')
            conn.commit()

def insert_metadata(metadata: Dict[str, str]):
    """Insert mcq_metadata into the database."""
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO mcq_metadata (
                question_type, system_prompt, user_prompt, model, 
                completion, extraction, execution_time, input_tokens, output_tokens
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metadata['question_type'],
            metadata['system_prompt'],
            metadata['user_prompt'],
            metadata['model'],
            metadata['completion'],
            metadata['extraction'],
            metadata['execution_time'],
            metadata['input_tokens'],
            metadata['output_tokens']
        ))
        conn.commit()

def generate_mcq(text: str, question_type: str, num_questions=1) -> dict:
    """
    Generates multiple-choice questions based on the provided text and question type.

    Args:
        text (str): The text to generate questions from.
        question_type (str): The type of question to generate. Options are "details", "inference", or "main_idea".
        num_questions (int): The number of questions to generate.

    Returns:
        dict: A dictionary containing the generated questions and their options.
    """
    
    # Ensure the table exists before proceeding
    create_table()
    
    # Determine the prompt file based on the question type
    prompt_file = question_type_prompt_map.get(question_type.lower())
    if prompt_file is None:
        raise ValueError(f"Invalid question type: {question_type}. Valid options are: {', '.join(question_type_prompt_map.keys())}.")
    
    # Fetch the prompt for generating MCQs
    prompts = get_prompts(prompt_file)
    system_prompt = prompts.get("system_prompt", "")
    user_prompt = prompts.get("user_prompt", "").format(text=text)

    # Initialize the agent with the prompt for generating MCQs
    agent = Agent(question_type=question_type, 
                  model="gpt-3.5-turbo",
                  system_prompt=system_prompt,
                  user_prompt=user_prompt)
    
    # First attempt to generate the MCQ
    agent.completion_generation()
    mcq_metadata = agent.get_metadata()

    # Insert the metadata into the database
    insert_metadata(mcq_metadata)

    return mcq_metadata

