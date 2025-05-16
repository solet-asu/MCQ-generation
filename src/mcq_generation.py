from src.prompt_fetch import *
from src.agent import Agent
from src.general import *
from src.database_handler import *
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
database_file = '../database/mcq_metadata.db'


def extract_output(input_str: str, item: str="QUESTION") -> str | None:
        # Use regex to extract content within <MCQ> and </MCQ> tags
        pattern = re.compile(rf"<{item}>(.*?)</?{item}>", re.DOTALL)
        match = pattern.search(input_str)
        if match:
            target_str = match.group(1).strip()

            # Replace escaped newlines and tabs that are within the string
            target_str = target_str.replace("\\n", "\n").replace("\\t", "\t")

            return target_str
        
        else:
            
            logger.error(f"No desired tags found in '{input_str}'.")
            return None

# TODO Revise this function as generic to all types of questions. 
def generate_mcq(text: str, question_type: str, table_name="mcq_metadata") -> dict:
    """
    Generates multiple-choice questions based on the provided text and question type.

    Args:
        text (str): The text to generate questions from.
        question_type (str): The type of question to generate. Options are "details", "inference", or "main_idea".

    Returns:
        dict: A dictionary containing the generated questions and their options.
    """
    
    # Ensure the table exists before proceeding
    create_table(table_name, database_file)
    
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
                  model="gpt-4o",
                  system_prompt=system_prompt,
                  user_prompt=user_prompt)
    
    # First attempt to generate the MCQ
    generated_text = question_generation_agent.completion_generation()
    mcq_metadata = question_generation_agent.get_metadata()


    #### The following code is used for extracting the MCQ from the generated text
    if generated_text:

        # first attempt: extract the mcq from the generated text using the MCQ tags
        mcq_extracted = extract_output(generated_text, item="QUESTION")
        if mcq_extracted:
            logger.info("MCQ extracted successfully using the MCQ tags from the generated text.")
            mcq_metadata["mcq"] = mcq_extracted
            # extract answer from the generated text 
            answer_extracted = extract_output(generated_text, item="ANSWER")
            if answer_extracted:
                logger.info("Answer extracted successfully using the ANSWER tags from the generated text.")
                mcq_metadata["mcq_answer"] = answer_extracted
            else:
                logger.warning("Failed to extract answer using the ANSWER tags.")
                        # Fetch the prompt using an llm-powered agent
                mcq_answer_extractor_prompts = get_prompts("mcq_answer_extractor_prompts.yaml")
                mcq_answer_extractor_system_prompt = mcq_answer_extractor_prompts.get("system_prompt", "")
                mcq_answer_extractor_user_prompt = mcq_answer_extractor_prompts.get("user_prompt", "").format(text=generated_text)
                # Add a mcq_extractor_agent to extract the MCQ from the messy generated text 
                mcq_answer_extractor_agent = Agent(question_type=question_type, 
                                model="gpt-3.5-turbo",
                                system_prompt=mcq_answer_extractor_system_prompt,
                                user_prompt=mcq_answer_extractor_user_prompt)
                
                mcq_answer_extracted_llm = mcq_answer_extractor_agent.completion_generation()
                if mcq_answer_extracted_llm:
                    logger.info("Answer extracted successfully using the mcq_answer_extractor_agent.")
                    mcq_metadata["mcq_answer"] = mcq_answer_extracted_llm
                else:
                    logger.warning("Failed to extract answer using the mcq_answer_extractor_agent.")
                    mcq_metadata["mcq_answer"] = "Sorry, the answer for this question was not provided."
                
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
                insert_metadata(mcq_metadata, table_name, database_file)

                mcq_extractor_metadata = mcq_extractor_agent.get_metadata()
                mcq_extractor_metadata["mcq"] = mcq_extracted_llm

                # Insert the metadata into the database
                insert_metadata(mcq_extractor_metadata, table_name, database_file)

            else:
                logger.warning("Failed to extract MCQ using the mcq_extractor_agent. Return a sorry message")
                sorry_message = "Sorry, We couldn't generate a multiple-choice question for you. Please try again."
                mcq_metadata["mcq"] = sorry_message
                # Insert the metadata into the database
                insert_metadata(mcq_metadata, table_name, database_file)    

                mcq_extractor_metadata["mcq"] = sorry_message
                # Insert the metadata into the database
                insert_metadata(mcq_extractor_metadata, table_name, database_file)           

    return mcq_metadata

