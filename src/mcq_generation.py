import re
import logging
from typing import Dict, Optional
from src.prompt_fetch import get_prompts
from src.agent import Agent
from src.general import *
from src.database_handler import *
import asyncio

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

QUESTION_TYPE_PROMPT_MAP = {
    "fact": "fact_prompts.yaml",
    "inference": "inference_prompts.yaml",
    "main_idea": "main_idea_prompts.yaml",
}

def extract_output(input_str: str, item: str = "QUESTION") -> Optional[str]:
    """Extract content between specified tags from the input string."""
    pattern = re.compile(rf"<{item}>(.*?)</?{item}>", re.DOTALL)
    match = pattern.search(input_str)
    if match:
        target_str = match.group(1).strip()
        target_str = target_str.replace("\\n", "\n").replace("\\t", "\t")
        return target_str
    else:
        logger.error(f"No desired tags found in '{input_str}'.")
        return None


async def generate_mcq(invocation_id: str, 
                       model: str, 
                       task: Dict, 
                       table_name: str = "mcq_metadata", 
                       database_file: str = '../database/mcq_metadata.db') -> Dict:
    """Generate a multiple-choice question (MCQ) and store metadata."""
    
    create_table(table_name, database_file)

    question_type = task.get("question_type", "").lower()
    prompt_file = QUESTION_TYPE_PROMPT_MAP.get(question_type)
    if prompt_file is None:
        raise ValueError(f"Invalid question type: {question_type}.")

    prompts = get_prompts(prompt_file)
    text = task.get("text", "")
    system_prompt = prompts.get("system_prompt", "")
    user_prompt = prompts.get("user_prompt", "").format(
        content=task.get("content", ""),
        text=text,
        context=task.get("context", "")
    )

    question_generation_agent = Agent(
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt
    )
    
    generated_text = await question_generation_agent.completion_generation()
    mcq_metadata = question_generation_agent.get_metadata()
    mcq_metadata.update({
        "question_type": question_type,
        "invocation_id": invocation_id
    })

    if generated_text:
        mcq_extracted = extract_output(generated_text, item="QUESTION")
        if mcq_extracted:
            logger.info("MCQ extracted successfully.")
            mcq_metadata["mcq"] = mcq_extracted
            answer_extracted = extract_output(generated_text, item="ANSWER")
            if answer_extracted:
                logger.info("Answer extracted successfully.")
                mcq_metadata["mcq_answer"] = answer_extracted
            else:
                logger.warning("Falling back to answer agent.")
                mcq_metadata["mcq_answer"] = await extract_answer_with_agent(generated_text)
        else:
            mcq_metadata["mcq"] = await extract_mcq_with_agent(generated_text)
        insert_metadata(mcq_metadata, table_name, database_file)

    return mcq_metadata


async def extract_answer_with_agent(generated_text: str) -> str:
    """Extract the answer from the generated text using an agent."""
    prompts = get_prompts("mcq_answer_extractor_prompts.yaml")
    agent = Agent(
        model="gpt-3.5-turbo",
        system_prompt=prompts.get("system_prompt", ""),
        user_prompt=prompts.get("user_prompt", "").format(text=generated_text)
    )
    result = await agent.completion_generation()
    return result or "Sorry, the answer for this question was not provided."


async def extract_mcq_with_agent(generated_text: str) -> str:
    """Extract the MCQ from the generated text using an agent."""
    prompts = get_prompts("mcq_extractor_prompts.yaml")
    agent = Agent(
        model="gpt-3.5-turbo",
        system_prompt=prompts.get("system_prompt", ""),
        user_prompt=prompts.get("user_prompt", "").format(text=generated_text)
    )
    result = await agent.completion_generation()
    return result or "Sorry, We couldn't generate a multiple-choice question for you."


async def generate_all_mcqs(task_list, 
                            invocation_id, 
                            model="gpt-4o", 
                            table_name="mcq_metadata", 
                            database_file="../database/mcq_metadata.db"):
    tasks = [
        generate_mcq(
            invocation_id=invocation_id,
            model=model,
            task=task,
            table_name=table_name,
            database_file=database_file
        )
        for task in task_list
    ]
    questions = await asyncio.gather(*tasks)
    return questions