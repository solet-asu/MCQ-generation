from src.prompt_fetch import *
from src.agent_createAI import Agent
from src.general import *
from src.database_handler import *
import json

import logging

# Configure logging
logger = logging.getLogger(__name__)


async def generate_plan(
        session_id:str,
        api_token: Optional[str],
        invocation_id: str,
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
    logger.info(
        "generate_plan invoked: invocation_id=%s model=%s fact=%d inference=%d text_len=%d",
        invocation_id, model, fact, inference, len(text or "")
    )
    
    # Ensure the table exists before proceeding
    create_table(table_name, database_file)
     
    prompt_file = "planner_prompts.yaml"

    # Fetch the prompt for generating plans
    prompts = get_prompts(prompt_file)
    system_prompt = prompts.get("system_prompt", "")
    user_prompt = prompts.get("user_prompt", "").format(text=text, n_facts=fact, n_inferences=inference)

    # Initialize the agent with the prompt for generating MCQs
    planner_agent = Agent(
        session_id=session_id,
        api_token=api_token,
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_format={"type": "json_object"}
    )
    logger.info("Planner agent initialized with model: %s", model)
    
    # First attempt to generate the plan
    try:
        generated_text = await planner_agent.completion_generation()
    except Exception as e:
        logger.error("Planner_agent completion generation failed: %s", e)
        raise

    plan_metadata = planner_agent.get_metadata()
    plan_metadata["invocation_id"] = invocation_id

    #### The following code is used for extracting the plan from the generated text
    if generated_text:
        try:
            generated_text_dict = extract_json_string(generated_text)
            # extract summary, facts, and inferences from the generated text
            summary = generated_text_dict.get("summary", "")
            facts = generated_text_dict.get("selection", {}).get("facts", {}) or {}
            inferences = generated_text_dict.get("selection", {}).get("inferences", {}) or {}
            logger.info(
                "Parsed plan JSON successfully (facts=%d, inferences=%d)",
                len(facts), len(inferences)
            )
        except ValueError as e:
            logger.warning("Failed to parse JSON from generated text: %s", e)
            summary, facts, inferences = "", {}, {}
    else:
        logger.warning("Failed to generate a plan (empty completion).")
        summary, facts, inferences = "", {}, {}

    # add the summary, facts, and inferences to the plan metadata
    plan_metadata["summary"] = json.dumps(summary)
    # Add the facts and inferences to the plan metadata as JSON strings
    plan_metadata["facts"] = json.dumps(facts)  
    plan_metadata["inferences"] = json.dumps(inferences) 

    # Insert the metadata into the database
    insert_metadata(plan_metadata, table_name, database_file)
    logger.info("Plan metadata inserted into DB: table=%s invocation_id=%s", table_name, invocation_id)

    return plan_metadata
















