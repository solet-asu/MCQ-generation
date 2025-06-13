import re
import logging
from typing import Dict, Optional
from src.prompt_fetch import get_prompts
from src.agent import Agent
from src.general import *
from src.database_handler import *
import asyncio
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def generate_evaluation(invocation_id: str, 
                       model: str, 
                       mcq_metadata: Dict, # extract the mcq and answer from the metadata
                       task: Dict, # get the source text and context
                       table_name: str = "evaluation_metadata", 
                       database_file: str = '../database/mcq_metadata.db') -> Dict:
    """Generate evaluation for a question and store metadata."""
    
    create_table(table_name, database_file)

    prompt_file = "evaluator_prompts.yaml"
    prompts = get_prompts(prompt_file)

    system_prompt = prompts.get("system_prompt", "")
    user_prompt = prompts.get("user_prompt", "").format(
        question =mcq_metadata.get("mcq", ""),
        answer = mcq_metadata.get("mcq_answer", ""),
        source=task.get("text", ""),
        context=task.get("context", "")
    )

    evaluation_generation_agent = Agent(
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt
    )
    
    generated_text = await evaluation_generation_agent.completion_generation()
    evaluation_metadata = evaluation_generation_agent.get_metadata()
    evaluation_metadata.update({
        "invocation_id": invocation_id,
        "question_type": mcq_metadata.get("question_type", ""),
        "mcq": mcq_metadata.get("mcq", ""),
        "mcq_answer": mcq_metadata.get("mcq_answer", ""),
        "source": task.get("text", ""),
    })

    #### The following code is used for extracting the evaluation from the generated text
    if generated_text:
        generated_text_dict = extract_json_string(generated_text)
        
        # extract evaluation, revised_mcq, and reasoning from the generated text
        evaluation = generated_text_dict.get("evaluation", "")
        revised_mcq = generated_text_dict.get("revised_mcq", "")
        revised_answer = generated_text_dict.get("revised_answer", "")
        reasoning = generated_text_dict.get("reasoning", "")
        # add the evaluation, revised_mcq, and reasoning to the evaluation metadata
        evaluation_metadata["evaluation"] = evaluation
        evaluation_metadata["revised_mcq"] = revised_mcq 
        evaluation_metadata["revised_answer"] = revised_answer  
        evaluation_metadata["reasoning"] = reasoning 

        # Insert the metadata into the database
        insert_metadata(evaluation_metadata, table_name, database_file) 
    else:
        logger.warning("Failed to generate an evaluation.")

        # set evaluation, revised_mcq, and reasoning as empty strings
        evaluation = ""
        revised_mcq = ""
        revised_answer = ""
        reasoning = ""

        # add the evaluation, revised_mcq, and reasoning to the evaluation metadata
        evaluation_metadata["evaluation"] = evaluation
        evaluation_metadata["revised_mcq"] = revised_mcq
        evaluation_metadata["revised_answer"] = revised_answer
        evaluation_metadata["reasoning"] = reasoning
        
        # Insert the metadata into the database
        insert_metadata(evaluation_metadata, table_name, database_file) 
    return evaluation_metadata





