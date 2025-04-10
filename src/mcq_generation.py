from src.prompt_fetch import *
from src.agent import Agent
from src.general import *
import sqlite3
from typing import Dict
from datetime import datetime 
import re

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

def create_table(table_name: str = "mcq_metadata"):
    """Create the table if it doesn't exist."""
    if not table_exists(table_name):
        with sqlite3.connect(DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                CREATE TABLE {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_type TEXT,
                    system_prompt TEXT,
                    user_prompt TEXT,
                    model TEXT,
                    completion TEXT,
                    mcq TEXT,
                    execution_time TEXT,
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    timestamp TEXT
                )
            ''')
            conn.commit()

def insert_metadata(metadata: Dict[str, str], table_name: str = "mcq_metadata"):
    """Insert table into the database."""
    timestamp = datetime.now().isoformat()
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            INSERT INTO {table_name} (
                question_type, system_prompt, user_prompt, model, 
                completion, mcq, execution_time, input_tokens, output_tokens, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metadata['question_type'],
            metadata['system_prompt'],
            metadata['user_prompt'],
            metadata['model'],
            metadata['completion'],
            metadata['mcq'],
            metadata['execution_time'],
            metadata['input_tokens'],
            metadata['output_tokens'],
            timestamp
        ))
        conn.commit()


def extract_output(input_str: str) -> str | None:
        # Use regex to extract content within <MCQ> and </MCQ> tags
        pattern = re.compile(r"<MCQ>(.*?)</?MCQ>", re.DOTALL)
        match = pattern.search(input_str)
        if match:
            target_str = match.group(1).strip()

            # Replace escaped newlines and tabs that are within the string
            target_str = target_str.replace("\\n", "\n").replace("\\t", "\t")

            return target_str
        
        else:
            
            logger.error(f"No <MCQ> tags found in '{input_str}'.")
            return None


def generate_mcq(text: str, question_type: str, num_questions=1, table_name="mcq_metadata") -> dict:
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
    create_table(table_name)
    
    # Determine the prompt file based on the question type
    prompt_file = question_type_prompt_map.get(question_type.lower())
    if prompt_file is None:
        raise ValueError(f"Invalid question type: {question_type}. Valid options are: {', '.join(question_type_prompt_map.keys())}.")
    
    # Fetch the prompt for generating MCQs
    prompts = get_prompts(prompt_file)
    system_prompt = prompts.get("system_prompt", "")
    user_prompt = prompts.get("user_prompt", "").format(text=text)

    # Initialize the agent with the prompt for generating MCQs
    question_generation_agent = Agent(question_type=question_type, 
                  model="gpt-3.5-turbo",
                  system_prompt=system_prompt,
                  user_prompt=user_prompt)
    
    # First attempt to generate the MCQ
    generated_text = question_generation_agent.completion_generation()
    mcq_metadata = question_generation_agent.get_metadata()


    #### The following code is used for extracting the MCQ from the generated text
    if generated_text:

        # first attempt: extract the mcq from the generated text using the MCQ tags
        mcq_extracted = extract_output(generated_text)
        if mcq_extracted:
            logger.info("MCQ extracted successfully using the MCQ tags from the generated text.")
            mcq_metadata["mcq"] = mcq_extracted
            # Insert the metadata into the database
            insert_metadata(mcq_metadata, table_name)

        else:

            # Fetch the prompt using an llm-powered agent
            mcq_extractor_prompts = get_prompts("mcq_extractor_prompts.yaml")
            mcq_extractor_system_prompt = mcq_extractor_prompts.get("system_prompt", "")
            mcq_extractor_user_prompt = mcq_extractor_prompts.get("user_prompt", "").format(text=generated_text)
            # Add a mcq_extractor_agent to extract the MCQ from the messy generated text 
            mcq_extractor_agent = Agent(question_type=question_type, 
                            model="gpt-3.5-turbo",
                            system_prompt=mcq_extractor_system_prompt,
                            user_prompt=mcq_extractor_user_prompt)
            
            mcq_extracted_llm = mcq_extractor_agent.completion_generation()

            if mcq_extracted_llm:
                logger.info("MCQ extracted successfully using the mcq_extractor_agent.")
                mcq_metadata["mcq"] = mcq_extracted_llm
                # Insert the metadata into the database
                insert_metadata(mcq_metadata, table_name)

                mcq_extractor_metadata = mcq_extractor_agent.get_metadata()
                mcq_extractor_metadata["mcq"] = mcq_extracted_llm

                # Insert the metadata into the database
                insert_metadata(mcq_extractor_metadata, table_name)

            else:
                logger.warning("Failed to extract MCQ using the mcq_extractor_agent. Return a sorry message")
                sorry_message = "Sorry, We couldn't generate a multiple-choice question for you. Please try again."
                mcq_metadata["mcq"] = sorry_message
                # Insert the metadata into the database
                insert_metadata(mcq_metadata, table_name)    

                mcq_extractor_metadata["mcq"] = sorry_message
                # Insert the metadata into the database
                insert_metadata(mcq_extractor_metadata, table_name)           

    return mcq_metadata

