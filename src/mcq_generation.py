import re
import logging
from typing import Dict, Optional
from src.prompt_fetch import get_prompts
from src.agent import Agent
from src.general import *
from src.database_handler import *
from src.evaluator import generate_evaluation
import asyncio
import json

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
                      database_file: str = '../database/mcq_metadata.db',
                      max_attempt: int = 3,
                      attempt: int = 1) -> Dict:
    """Generate a multiple-choice question (MCQ) and store metadata."""
    
    create_table(table_name, database_file)

    question_type = task.get("question_type", "").lower()
    chunk = json.dumps(task.get("chunk", []))
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

    # Add revision information if this isn't the first attempt
    if attempt > 1:
        previous_mcq = task.get("previous_mcq", "No previous MCQ")
        previous_answer = task.get("previous_answer", "No previous answer")
        evaluation_reasoning = task.get("evaluation_reasoning", "No reasoning")
        user_prompt += f"\n\nRevise your generated multiple-choice question.\n\nPrevious MCQ:\n{previous_mcq}\n\nPrevious Answer:\n{previous_answer}\n\nEvaluation Reasoning:\n{evaluation_reasoning}"

    question_generation_agent = Agent(
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt
    )

    # Retry logic for generating a question with valid options (max 3 attempts)
    max_generation_tries = 3
    for generation_try in range(1, max_generation_tries + 1):
        generated_text = await question_generation_agent.completion_generation()
        mcq_metadata = question_generation_agent.get_metadata()
        mcq_metadata.update({
            "question_type": question_type,
            "invocation_id": invocation_id,
            "chunk": chunk,
            "attempt": attempt,
        })

        if generated_text:
            mcq_extracted = extract_output(generated_text, item="QUESTION")
            if mcq_extracted:
                logger.info(f"MCQ extracted on try {generation_try}.")
                mcq_metadata["mcq"] = mcq_extracted
                # Check for valid options (A-D)
                if re.search(r'\b[A-D]\)', mcq_extracted):
                    logger.info(f"Valid MCQ generated on try {generation_try}.")
                    break  # Exit the retry loop if valid options are found
                else:
                    logger.error(f"Generated question lacks valid options (try {generation_try}): {mcq_extracted}")
            else:
                logger.warning(f"Falling back to MCQ agent (try {generation_try}).")
                mcq_metadata["mcq"] = await extract_mcq_with_agent(generated_text)
                # Assume agent produces a valid question
                break
        else:
            logger.error(f"Failed to generate text on try {generation_try}.")

        if generation_try == max_generation_tries:
            logger.warning("Max generation tries (3) reached. Setting default failure values.")
            mcq_metadata["mcq"] = "No MCQ generated due to missing options."
            mcq_metadata["mcq_answer"] = "No answer generated due to missing options."
            insert_metadata(mcq_metadata, table_name, database_file)
            return mcq_metadata

    # If a valid question is generated, proceed to extract answer
    if "mcq" in mcq_metadata:
        answer_extracted = extract_output(generated_text, item="ANSWER")
        if answer_extracted:
            logger.info("Answer extracted successfully.")
            mcq_metadata["mcq_answer"] = answer_extracted
        else:
            logger.warning("Falling back to answer agent.")
            mcq_metadata["mcq_answer"] = await extract_answer_with_agent(generated_text)

    
        # Evaluate the generated question
        evaluation_meta = await generate_evaluation(
            invocation_id=invocation_id,
            model=model,
            mcq_metadata=mcq_metadata,
            task=task,
            table_name="evaluation_metadata",
            database_file=database_file
        )
        if evaluation_meta:
            logger.info("Evaluation metadata generated successfully.")
            if isinstance(evaluation_meta, dict):
                evaluation_meta_dict = evaluation_meta
            elif isinstance(evaluation_meta, str):
                try:
                    evaluation_meta_dict = extract_json_string(evaluation_meta)
                except ValueError as e:
                    logger.error(f"Failed to parse evaluation_meta as JSON: {e}")
                    evaluation_meta_dict = {}  # Fallback to empty dict or handle differently
            else:
                logger.error(f"Unexpected type for evaluation_meta: {type(evaluation_meta)}")
                evaluation_meta_dict = {}  # Fallback to empty dict or raise an error
            if evaluation_meta_dict:
                if evaluation_meta_dict["evaluation"] == "YES":
                    logger.info("Evaluation passed successfully.")
                elif evaluation_meta_dict["evaluation"] == "REVISED":
                    logger.info("Evaluation revised successfully.")
                    revised_mcq = evaluation_meta_dict.get("revised_mcq", "")
                    revised_answer = evaluation_meta_dict.get("revised_answer", "")
                    if revised_mcq:
                        mcq_metadata["mcq"] = revised_mcq
                    if revised_answer:
                        mcq_metadata["mcq_answer"] = revised_answer
                elif evaluation_meta_dict["evaluation"] == "NO":
                    logger.info(f"Evaluation failed on attempt {attempt}/{max_attempt}")
                    if attempt < max_attempt:
                        # Prepare for next attempt
                        task["previous_mcq"] = mcq_metadata.get("mcq", "No MCQ")
                        task["previous_answer"] = mcq_metadata.get("mcq_answer", "No answer")
                        task["evaluation_reasoning"] = evaluation_meta.get("reasoning", "No reasoning")
                        return await generate_mcq(
                            invocation_id=invocation_id,
                            model=model,
                            task=task,
                            table_name=table_name,
                            database_file=database_file,
                            max_attempt=max_attempt,
                            attempt=attempt + 1
                        )
                    else:
                        logger.warning("Max attempts reached. Setting default failure values.")
                        mcq_metadata["mcq"] = "No MCQ generated due to evaluation failure."
                        mcq_metadata["mcq_answer"] = "No answer generated due to evaluation failure."

        insert_metadata(mcq_metadata, table_name, database_file)
        
    return mcq_metadata

async def generate_mcq_quality_first(invocation_id: str, 
                      model: str, 
                      task: Dict, 
                      table_name: str = "mcq_metadata", 
                      database_file: str = '../database/mcq_metadata.db',
                      max_attempt: int = 3,
                      attempt: int = 1,
                      candidate_num: int = 5) -> Dict:
    # set up ranking model medata data template
    ranking_metadata = []
    candidate_questions = []
    for i in range(candidate_num):
        # get the mcq_metadata
        mcq_metadata = generate_mcq(invocation_id, model, task, table_name, database_file, max_attempt, attempt)
        
        if mcq_metadata:
            mcq = mcq_metadata["mcq"]
            mcq_answer = mcq_metadata["mcq_answer"]
            candidate_questions.append({"question_number": i+1, 
                                        "question": mcq,
                                        "answer": mcq_answer})


    pass

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


async def generate_all_mcqs(task_list: list, 
                            invocation_id: str, 
                            model: str, 
                            table_name: str="mcq_metadata", 
                            database_file: str ="../database/mcq_metadata.db",
                            max_attempt: int=3):
    tasks = [
        generate_mcq(
            invocation_id=invocation_id,
            model=model,
            task=task,
            table_name=table_name,
            database_file=database_file,
            max_attempt=max_attempt,
        )
        for task in task_list
    ]
    questions = await asyncio.gather(*tasks)
    return questions