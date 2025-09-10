import re
import logging
from typing import Dict, Optional, Any, List, Mapping, Sequence
from collections import defaultdict
from src.prompt_fetch import get_prompts
from src.agent import Agent
from src.general import *
from src.database_handler import *
from src.evaluator import generate_evaluation
from src.option_shortener_workflow import check_and_shorten_long_option
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
    """Extract content between <ITEM>...</ITEM> tags robustly."""
    pattern = re.compile(rf"<{item}\b[^>]*>(.*?)</{item}\s*>", re.DOTALL | re.IGNORECASE)
    match = pattern.search(input_str)
    if match:
        target_str = match.group(1).strip()
        target_str = target_str.replace("\\n", "\n").replace("\\t", "\t")
        return target_str
    else:
        logger.error(f"No desired tags found in '{input_str}'.")
        return None


def _has_all_four_options(mcq_text: str) -> bool:
    """
    Validate that MCQ contains options A), B), C), and D) at line starts.
    """
    letters = set(re.findall(r'^([A-D])\)\s+', mcq_text, flags=re.MULTILINE | re.IGNORECASE))
    return {'A', 'B', 'C', 'D'}.issubset({l.upper() for l in letters})


def _normalize_answer(ans: str) -> str:
    """Normalize answer strings like 'b', 'B)', 'Choice B' to single letter A-D."""
    if not isinstance(ans, str):
        return "N/A"
    m = re.search(r'([A-D])', ans.upper())
    return m.group(1) if m else ans.strip()


async def generate_mcq(
    invocation_id: str,
    model: str,
    task: Dict,
    mcq_metadata_table_name: str = "mcq_metadata",
    evaluation_metadata_table_name: str = "evaluation_metadata",
    database_file: str = '../database/mcq_metadata.db',
    max_attempt: int = 3,
    attempt: int = 1
) -> Dict:
    """Generate a multiple-choice question (MCQ) and store metadata."""

    create_table(mcq_metadata_table_name, database_file)

    question_type = task.get("question_type", "").lower()
    # Safe JSON dump in case chunk has non-serializable objects
    try:
        chunk = json.dumps(task.get("chunk", []), default=str)
    except Exception as e:
        logger.warning("Failed to JSON-serialize 'chunk': %s. Falling back to str(...).", e)
        chunk = str(task.get("chunk", []))

    prompt_file = QUESTION_TYPE_PROMPT_MAP.get(question_type)
    if prompt_file is None:
        raise ValueError(f"Invalid question type: {question_type}.")

    # Load prompts defensively
    try:
        prompts = get_prompts(prompt_file)
    except Exception as e:
        logger.error("Prompt load failed for %s: %s", prompt_file, e)
        prompts = {"system_prompt": "", "user_prompt": ""}

    text = task.get("text", "")
    system_prompt = prompts.get("system_prompt", "")
    # Safe templating (avoid KeyError on missing keys)
    user_prompt = prompts.get("user_prompt", "").format_map(defaultdict(str, {
        "content": task.get("content", ""),
        "text": text,
        "context": task.get("context", ""),
    }))

    # Add revision information if this isn't the first attempt
    if attempt > 1:
        previous_mcq = task.get("previous_mcq", "No previous MCQ")
        previous_answer = task.get("previous_answer", "No previous answer")
        evaluation_reasoning = task.get("evaluation_reasoning", "No reasoning")
        user_prompt += (
            f"\n\nRevise your generated multiple-choice question.\n\n"
            f"Previous MCQ:\n{previous_mcq}\n\n"
            f"Previous Answer:\n{previous_answer}\n\n"
            f"Evaluation Reasoning:\n{evaluation_reasoning}"
        )

    question_generation_agent = Agent(
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt
    )

    # Retry logic for generating a question with valid options (max 3 attempts)
    max_generation_tries = 3
    used_mcq_extractor = False
    mcq_metadata: Dict[str, Any] = {}
    generated_text: Optional[str] = None

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
                mcq_metadata["mcq"] = mcq_extracted #TODO need to move this somewhere done the line
                # Check for valid options (A-D)
                if _has_all_four_options(mcq_extracted):
                    logger.info(f"Valid MCQ generated on try {generation_try}.")
                    break  # Exit the retry loop if valid options are found
                else:
                    logger.error(
                        f"Generated question lacks valid options (try {generation_try}): {mcq_extracted}"
                    )
            else:
                logger.warning(f"Falling back to MCQ agent (try {generation_try}).")
                mcq_metadata["mcq"] = await extract_mcq_with_agent(generated_text, model=model) #TODO need to move this somewhere done the line
                used_mcq_extractor = True
                # Validate again after extractor
                if not _has_all_four_options(mcq_metadata["mcq"]):
                    logger.error("MCQ extractor did not produce all four options A-D; continuing retries.")
                    continue
                break
        else:
            logger.error(f"Failed to generate text on try {generation_try}.")

        if generation_try == max_generation_tries:
            logger.warning("Max generation tries (3) reached. Setting default failure values.")
            mcq_metadata["mcq"] = "No MCQ generated due to missing options."
            mcq_metadata["mcq_answer"] = "No answer generated due to missing options."
            insert_metadata(mcq_metadata, mcq_metadata_table_name, database_file)
            return mcq_metadata

    # If a valid question is generated, proceed to extract answer
    if "mcq" in mcq_metadata:
        # If we used the extractor path, try extracting the answer from the cleaned MCQ text.
        answer_extracted = None
        if used_mcq_extractor:
            answer_extracted = extract_output(mcq_metadata["mcq"], item="ANSWER")
        if not answer_extracted and generated_text:
            answer_extracted = extract_output(generated_text, item="ANSWER")
        if answer_extracted:
            logger.info("Answer extracted successfully.")
            mcq_metadata["mcq_answer"] = _normalize_answer(answer_extracted)
        else:
            logger.warning("Falling back to answer agent.")
            # Use generated_text if available; otherwise use mcq text
            source_text = generated_text if generated_text else mcq_metadata["mcq"]
            mcq_metadata["mcq_answer"] = _normalize_answer(
                await extract_answer_with_agent(source_text, model=model)
            )
        
        # Use the shorten workflow to check and shorten long options if needed
        updated_mcq, updated_mcq_answer, token_usage = await check_and_shorten_long_option(
            invocation_id=invocation_id,
            mcq=mcq_metadata.get("mcq", ""),
            model=model,
        )
        mcq_metadata["mcq"] = updated_mcq
        # update the answer if needed. 
        if token_usage:
            mcq_metadata["mcq_answer"] = updated_mcq_answer

        # Evaluate the generated question
        evaluation_meta = await generate_evaluation(
            invocation_id=invocation_id,
            model=model,
            mcq_metadata=mcq_metadata,
            task=task,
            table_name=evaluation_metadata_table_name,
            database_file=database_file
        )
        if evaluation_meta:
            logger.info("Evaluation metadata generated successfully.")
            # Normalize evaluation to dict
            if isinstance(evaluation_meta, dict):
                evaluation_meta_dict = evaluation_meta
            elif isinstance(evaluation_meta, str):
                try:
                    evaluation_meta_dict = extract_json_string(evaluation_meta)  # may return dict/str
                    if not isinstance(evaluation_meta_dict, dict):
                        logger.error("Parsed evaluation_meta is not a dict; using empty dict.")
                        evaluation_meta_dict = {}
                except Exception as e:
                    logger.error(f"Failed to parse evaluation_meta as JSON: {e}")
                    evaluation_meta_dict = {}
            else:
                logger.error(f"Unexpected type for evaluation_meta: {type(evaluation_meta)}")
                evaluation_meta_dict = {}
            if evaluation_meta_dict:
                status = evaluation_meta_dict.get("evaluation")
                if status == "YES":
                    logger.info("Evaluation passed successfully.")
                elif status == "REVISED":
                    logger.info("Evaluation revised successfully.")
                    revised_mcq = evaluation_meta_dict.get("revised_mcq", "")
                    revised_answer = evaluation_meta_dict.get("revised_answer", "")
                    if revised_mcq:
                        mcq_metadata["mcq"] = revised_mcq
                    if revised_answer:
                        mcq_metadata["mcq_answer"] = _normalize_answer(revised_answer)
                elif status == "NO":
                    logger.info(f"Evaluation failed on attempt {attempt}/{max_attempt}")
                    if attempt < max_attempt:
                        # Prepare for next attempt
                        task["previous_mcq"] = mcq_metadata.get("mcq", "No MCQ")
                        task["previous_answer"] = mcq_metadata.get("mcq_answer", "No answer")
                        task["evaluation_reasoning"] = evaluation_meta_dict.get("reasoning", "No reasoning")
                        return await generate_mcq(
                            invocation_id=invocation_id,
                            model=model,
                            task=task,
                            mcq_metadata_table_name=mcq_metadata_table_name,
                            evaluation_metadata_table_name=evaluation_metadata_table_name,
                            database_file=database_file,
                            max_attempt=max_attempt,
                            attempt=attempt + 1
                        )
                    else:
                        logger.warning("Max attempts reached. Setting default failure values.")
                        mcq_metadata["mcq"] = "No MCQ generated due to evaluation failure."
                        mcq_metadata["mcq_answer"] = "No answer generated due to evaluation failure."
                else:
                    logger.warning("Unknown evaluation status: %r", status)

        insert_metadata(mcq_metadata, mcq_metadata_table_name, database_file)

    return mcq_metadata


async def generate_candidate_mcqs_async(
    invocation_id: str,
    model: str,
    task: Dict,
    mcq_table_name: str = "mcq_metadata",
    evaluation_table_name: str = "evaluation_metadata",
    database_file: str = '../database/mcq_metadata.db',
    max_attempt: int = 3,
    attempt: int = 1
) -> Dict:
    """
    Asynchronously generate a single MCQ.
    """
    try:
        mcq_metadata = await generate_mcq(
            invocation_id, model, task,
            mcq_table_name, evaluation_table_name, database_file,
            max_attempt, attempt
        )
        return mcq_metadata
    except Exception as e:
        logger.error(f"Error generating MCQ: {e}")
        # Stable shape on error
        return {"mcq": None, "mcq_answer": None, "error": str(e)}


async def generate_mcq_quality_first(
    invocation_id: str,
    model: str,
    task: Dict,
    mcq_metadata_table_name: str = "mcq_metadata",
    evaluation_metadata_table_name: str = "evaluation_metadata",
    ranking_metadata_table_name: str = "ranking_metadata",
    database_file: str = '../database/mcq_metadata.db',
    max_attempt: int = 3,
    attempt: int = 1,
    candidate_num: int = 5
) -> Dict:
    """
    Generate and evaluate multiple-choice questions (MCQs) and rank them.

    Args:
        invocation_id (str): Unique identifier for the invocation.
        model (str): Model to be used for generation.
        task (Dict): Task details including question type, text, and context.
        mcq_metadata_table_name (str): Name of the table for MCQ metadata.
        evaluation_metadata_table_name (str): Name of the table for evaluation metadata.
        ranking_metadata_table_name (str): Name of the table for ranking metadata.
        database_file (str): Path to the database file.
        max_attempt (int): Maximum number of attempts for generation.
        attempt (int): Current attempt number.
        candidate_num (int): Number of candidate questions to generate.

    Returns:
        Dict: Metadata of the ranking process.
    """
    # Create tables for storing metadata
    create_table(ranking_metadata_table_name, database_file)

    # Generate multiple candidate questions concurrently
    tasks = [
        generate_candidate_mcqs_async(
            invocation_id, model, task,
            mcq_metadata_table_name, evaluation_metadata_table_name,
            database_file, max_attempt, attempt
        )
        for _ in range(candidate_num)
    ]
    candidate_questions_metadata = await asyncio.gather(*tasks)

    # Filter out any None or invalid results, and keep only those with both question and answer
    candidate_questions: List[Dict[str, Any]] = []
    for i, mcq in enumerate(candidate_questions_metadata):
        if isinstance(mcq, dict) and mcq.get("mcq") and mcq.get("mcq_answer"):
            candidate_questions.append({
                "question_number": i,
                "question": mcq["mcq"],
                "answer": mcq["mcq_answer"]
            })

    # Set up prompts for the ranking model
    ranking_prompt_file = "ranking_model.yaml"
    try:
        ranking_prompts = get_prompts(ranking_prompt_file)
    except Exception as e:
        logger.error("Ranking prompt load failed: %s", e)
        ranking_prompts = {"system_prompt": "", "user_prompt": ""}

    system_prompt = ranking_prompts.get("system_prompt", "")
    user_prompt = ranking_prompts.get("user_prompt", "").format_map(defaultdict(str, {
        "question_type": task.get("question_type", "").lower(),
        "text": task.get("text", ""),
        "context": task.get("context", ""),
        "candidate_questions": candidate_questions
    }))

    # Initialize the agent with the prompt
    ranking_agent = Agent(
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt
    )

    # Attempt to generate the plan
    try:
        generated_text = await ranking_agent.completion_generation()
    except Exception as e:
        logger.error(f"Error during completion generation: {e}")
        generated_text = None

    ranking_metadata = ranking_agent.get_metadata()
    ranking_metadata.update({
        "invocation_id": invocation_id,
        "question_type": task.get("question_type", ""),
        "content": task.get("content", ""),
        "text": task.get("text", ""),
        "context": task.get("context", ""),
        "candidate_questions": json.dumps(candidate_questions),
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "model": model
    })

    selected_mcq = "No candidates available."
    selected_mcq_answer = "N/A"
    selected_mcq_num_int = 0  # default fallback

    if generated_text:
        try:
            generated_text_dict = extract_json_string(generated_text)
        except Exception as e:
            logger.warning("Ranking JSON parse failed: %s; defaulting to first candidate.", e)
            generated_text_dict = {}
        if isinstance(generated_text_dict, dict):
            selected_mcq_num = (generated_text_dict.get("best_question") or {}).get("question_number")
            try:
                selected_mcq_num_int = int(selected_mcq_num)
            except (TypeError, ValueError):
                logger.warning("The selected MCQ number is not valid. Defaulting to 0.")
        else:
            logger.warning("Ranking output is not a dict. Defaulting to first candidate (0).")

        if not (0 <= selected_mcq_num_int < len(candidate_questions)):
            logger.warning("The selected MCQ number is out of the allowed range. Defaulting to 0.")
            selected_mcq_num_int = 0

        if candidate_questions:
            selected_mcq = candidate_questions[selected_mcq_num_int]["question"]
            selected_mcq_answer = candidate_questions[selected_mcq_num_int]["answer"]

        ranking_metadata.update({
            "completion": generated_text,
            "mcq": selected_mcq,
            "mcq_answer": selected_mcq_answer
        })
    else:
        logger.warning("Failed to generate a ranking; defaulting to first candidate if available.")
        if candidate_questions:
            selected_mcq = candidate_questions[0]["question"]
            selected_mcq_answer = candidate_questions[0]["answer"]
        ranking_metadata.update({
            "completion": "No ranking generated; chose first candidate if available.",
            "mcq": selected_mcq,
            "mcq_answer": selected_mcq_answer
        })

    # Insert the metadata into the database
    insert_metadata(ranking_metadata, ranking_metadata_table_name, database_file)

    return ranking_metadata


async def extract_answer_with_agent(generated_text: str, model: str = "gpt-3.5-turbo") -> str:
    """Extract the answer from the generated text using an agent."""
    try:
        prompts = get_prompts("mcq_answer_extractor_prompts.yaml")
    except Exception as e:
        logger.error("Answer extractor prompt load failed: %s", e)
        prompts = {"system_prompt": "", "user_prompt": "Extract the answer from:\n{text}"}
    agent = Agent(
        model=model,
        system_prompt=prompts.get("system_prompt", ""),
        user_prompt=prompts.get("user_prompt", "").format_map(defaultdict(str, {"text": generated_text}))
    )
    result = await agent.completion_generation()
    return result or "Sorry, the answer for this question was not provided."


async def extract_mcq_with_agent(generated_text: str, model: str = "gpt-3.5-turbo") -> str:
    """Extract the MCQ from the generated text using an agent."""
    try:
        prompts = get_prompts("mcq_extractor_prompts.yaml")
    except Exception as e:
        logger.error("MCQ extractor prompt load failed: %s", e)
        prompts = {"system_prompt": "", "user_prompt": "Extract the MCQ from:\n{text}"}
    agent = Agent(
        model=model,
        system_prompt=prompts.get("system_prompt", ""),
        user_prompt=prompts.get("user_prompt", "").format_map(defaultdict(str, {"text": generated_text}))
    )
    result = await agent.completion_generation()
    return result or "Sorry, We couldn't generate a multiple-choice question for you."


async def generate_all_mcqs(
    task_list: Sequence[Mapping[str, Any]],
    invocation_id: str,
    *,
    model: str,
    mcq_metadata_table_name: str = "mcq_metadata",
    evaluation_metadata_table_name: str = "evaluation_metadata",
    database_file: str = "../database/mcq_metadata.db",
    max_attempt: int = 3,
    concurrency: int = 30,  # NEW
) -> List[Dict[str, Any]]:
    sem = asyncio.Semaphore(max(1, concurrency))

    async def _run(task: Mapping[str, Any]) -> Dict[str, Any]:
        async with sem:
            return await generate_mcq(
                invocation_id=invocation_id,
                model=model,
                task=task,
                mcq_metadata_table_name=mcq_metadata_table_name,
                evaluation_metadata_table_name=evaluation_metadata_table_name,
                database_file=database_file,
                max_attempt=max_attempt,
            )

    # Let failures be isolated
    results = await asyncio.gather(*(_run(t) for t in task_list), return_exceptions=True)
    safe: List[Dict[str, Any]] = [r for r in results if isinstance(r, dict)]
    return list(safe)


async def generate_all_mcqs_quality_first(
    task_list: Sequence[Mapping[str, Any]],
    invocation_id: str,
    *,
    model: str,
    mcq_metadata_table_name: str = "mcq_metadata",
    evaluation_metadata_table_name: str = "evaluation_metadata",
    ranking_metadata_table_name: str = "ranking_metadata",
    database_file: str = "../database/mcq_metadata.db",
    max_attempt: int = 3,
    attempt: int = 1,
    candidate_num: int = 5,
    concurrency: int = 30,  # NEW
) -> List[Dict[str, Any]]:
    sem = asyncio.Semaphore(max(1, concurrency))

    async def _run(task: Mapping[str, Any]) -> Dict[str, Any]:
        async with sem:
            return await generate_mcq_quality_first(
                invocation_id=invocation_id,
                model=model,
                task=task,
                mcq_metadata_table_name=mcq_metadata_table_name,
                evaluation_metadata_table_name=evaluation_metadata_table_name,
                ranking_metadata_table_name=ranking_metadata_table_name,
                database_file=database_file,
                max_attempt=max_attempt,
                attempt=attempt,
                candidate_num=candidate_num,
            )

    results = await asyncio.gather(*(_run(t) for t in task_list), return_exceptions=True)
    safe: List[Dict[str, Any]] = [r for r in results if isinstance(r, dict)]
    return list(safe)
