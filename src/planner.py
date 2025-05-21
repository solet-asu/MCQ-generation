from src.prompt_fetch import *
from src.agent import Agent
from src.general import *
from src.database_handler import *
import sqlite3
from typing import Dict
from datetime import datetime 
import re
import json

def generate_plan(invocation_id: str,
                  model: str,
                  text: str, 
                  fact: int, 
                  inference: int, 
                  table_name:str="plan_metadata", 
                  database_file:str='../database/mcq_metadata.db') -> dict:
    """
    Create a plan for multiple-choice question generation based on the provided text and the number of different questions requested by the user.

    Args:
        text (str): The text to generate questions from.
        fact(int): The number of fact questions to generate. 
        inference(int): The number of inference questions to generate.

    Returns:
        dict: A dictionary containing the a summary of the text and essential facts and/or inferences for question generation.
    """
    
    # Ensure the table exists before proceeding
    create_table(table_name, database_file)
    
    prompt_file = "planner_prompts.yaml"

    # Fetch the prompt for generating plans
    prompts = get_prompts(prompt_file)
    system_prompt = prompts.get("system_prompt", "")
    user_prompt = prompts.get("user_prompt", "").format(text=text, n_facts=fact, n_inferences=inference)

    # Initialize the agent with the prompt for generating MCQs
    planner_agent = Agent(
                  model=model,
                  system_prompt=system_prompt,
                  user_prompt=user_prompt)
    
    # First attempt to generate the plan
    generated_text = planner_agent.completion_generation().strip()
    plan_metadata = planner_agent.get_metadata()
    plan_metadata["invocation_id"] = invocation_id


    #### The following code is used for extracting the plan from the generated text
    if generated_text:
        generated_text_dict = extract_json_string(generated_text)
        
        # extract summary, facts, and inferences from the generated text
        summary = generated_text_dict.get("summary", "")
        facts = generated_text_dict.get("selection", {}).get("facts", {})
        inferences = generated_text_dict.get("selection", {}).get("inferences", {})
        # add the summary, facts, and inferences to the plan metadata
        plan_metadata["summary"] = summary
        # Add the facts and inferences to the plan metadata as JSON strings
        plan_metadata["facts"] = json.dumps(facts)  
        plan_metadata["inferences"] = json.dumps(inferences) 

        # Insert the metadata into the database
        insert_metadata(plan_metadata, table_name, database_file) 
    else:
        logger.warning("Failed to extract MCQ using the mcq_extractor_agent. Return a sorry message")

        # extract summary, facts, and inferences from the generated text
        summary = ""
        facts = {}
        inferences = {}
        # add the summary, facts, and inferences to the plan metadata
        plan_metadata["summary"] = summary
        # Add the facts and inferences to the plan metadata as JSON strings
        plan_metadata["facts"] = json.dumps(facts)  
        plan_metadata["inferences"] = json.dumps(inferences) 

    return plan_metadata

