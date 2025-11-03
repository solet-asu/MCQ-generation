from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.text_processing import add_chunk_markers
from src.planner import generate_plan
from src.controller_helper import create_task_list
from src.mcq_generation import generate_all_mcqs, generate_all_mcqs_quality_first
from src.formatter import reformat_mcq_metadata_without_shuffling
from src.database_handler import create_table, insert_metadata

logger = logging.getLogger(__name__)


async def question_generation_workflow(
    session_id:str,
    api_token: Optional[str]=None,
    text: str="",
    *,
    fact: int,
    inference: int,
    main_idea: int,
    model: str,
    quality_first: bool = False,
    candidate_num: int = 5,  # used only when quality_first=True
    max_attempt_for_single_mcq: int = 3,
    plan_metadata_table_name: str = "plan_metadata",
    mcq_metadata_table_name: str = "mcq_metadata",
    evaluation_metadata_table_name: str = "evaluation_metadata",
    ranking_metadata_table_name: str = "ranking_metadata",
    workflow_metadata_table_name: str = "workflow_metadata",
    database_file: str = "../database/mcq_metadata.db",
    concurrency: int = 4, # Max concurrent tasks for question generation
) -> list[dict[str, Any]]:
    """
    Generate MCQs from `text` given desired counts per question type.

    Returns:
        A list of MCQ dicts (question, answer, type, and token metrics).
    Raises:
        ValueError: on invalid counts or candidate_num.
    """
    # ---- validation ----
    if not text or not text.strip():
        logger.warning("Empty text provided to question_generation_workflow")
        return []
    if any(n < 0 for n in (fact, inference, main_idea)):
        raise ValueError("Counts for fact, inference, and main_idea must be non-negative.")
    if quality_first and candidate_num <= 0:
        raise ValueError("candidate_num must be > 0 when quality_first=True.")

    invocation_id = str(uuid.uuid4())
    log_extra = {"invocation_id": invocation_id}

    # timing & timestamps
    t0 = time.perf_counter()

    logger.info("Workflow started", extra=log_extra)

    # Normalize DB path early (some libs dislike Path objects)
    db_path = str(Path(database_file))

    # ---- Step 1: text preprocessing ----
    chunked_text = add_chunk_markers(text)
    logger.info("Text successfully chunked", extra=log_extra)

    # ---- Step 2: plan generation ----
    plan = await generate_plan(
        session_id=session_id,
        api_token=api_token,
        invocation_id=invocation_id,
        model=model,
        text=chunked_text,
        fact=fact,
        inference=inference,
        table_name=plan_metadata_table_name,
        database_file=db_path,
    )
    logger.info("Plan generated", extra=log_extra)

    # ---- Step 3: tasks ----
    task_list = create_task_list(chunked_text, plan, fact, inference, main_idea)
    logger.info("Task list created (n=%d)", len(task_list), extra=log_extra)
    if not task_list:
        logger.warning("Empty task list; nothing to generate", extra=log_extra)
        return []

    # ---- Step 4: question generation ----
    if quality_first:
        questions_list = await generate_all_mcqs_quality_first(
            session_id=session_id,
            api_token=api_token,
            task_list=task_list,
            invocation_id=invocation_id,
            model=model,
            mcq_metadata_table_name=mcq_metadata_table_name,
            evaluation_metadata_table_name=evaluation_metadata_table_name,
            ranking_metadata_table_name=ranking_metadata_table_name,
            database_file=db_path,
            max_attempt=max_attempt_for_single_mcq,
            candidate_num=candidate_num,
            concurrency=concurrency, 
        )
    else:
        questions_list = await generate_all_mcqs(
            session_id=session_id,
            api_token=api_token,
            task_list=task_list,
            invocation_id=invocation_id,
            model=model,
            mcq_metadata_table_name=mcq_metadata_table_name,
            evaluation_metadata_table_name=evaluation_metadata_table_name,
            database_file=db_path,
            max_attempt=max_attempt_for_single_mcq,
            concurrency=concurrency,
        )
    logger.info("Questions generated (n=%d)", len(questions_list), extra=log_extra)

    # ---- Step 5: order & reformat ----
    reformatted_questions: List[Dict[str, Any]] = reformat_mcq_metadata_without_shuffling(questions_list)
    logger.info("Questions reformatted", extra=log_extra)

    # ---- Step 6: persist workflow metadata ----
    elapsed = time.perf_counter() - t0

    workflow_metadata = {
        "session_id": session_id,
        "api_token": api_token,
        "invocation_id": invocation_id,
        "output": json.dumps(reformatted_questions, ensure_ascii=False),
        "execution_time": f"{elapsed:.6f}",

    }

    # Run blocking DB operations off the event loop
    await asyncio.to_thread(create_table, workflow_metadata_table_name, db_path)
    await asyncio.to_thread(insert_metadata, workflow_metadata, workflow_metadata_table_name, db_path)
    logger.info("Workflow metadata stored", extra=log_extra)

    return reformatted_questions