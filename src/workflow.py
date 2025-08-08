from src.text_processing import add_chunk_markers
from src.planner import generate_plan
from src.controller_helper import create_task_list
from src.mcq_generation import generate_all_mcqs
from src.formatter import reformat_mcq_metadata, reformat_mcq_metadata_without_shuffling
from src.database_handler import create_table, insert_metadata
import uuid
from datetime import datetime
import logging
import json

async def question_generation_workflow(text:str, 
                                       fact:int, 
                                       inference:int, 
                                       main_idea:int, 
                                       model:str,  
                                       table_name: str = "workflow_metadata", 
                                       database_file: str ="../database/mcq_metadata.db") -> list[dict[str, str]]:
    """
    Main function to generate questions based on the provided text and parameters.
    
    :param text: The raw text to be processed.
    :param fact: The number of fact-based questions to generate.
    :param inference: The number of inference-based questions to generate.
    :param main_idea: The number of main idea questions to generate.
    :return: A list of dictionaries containing the generated Multiple choice questions and their answers. For example:
       [
        {
            "question_type": "facts",
            "question": "What is author of the book?",
            "answer": "B"
        }
        {
            "question_type": "inferences",
            "question": "What can you infer from the text?",
            "answer": "D"
        }
       ] 


    """
    
    # Record the start time of the workflow
    start_time = datetime.now()
    logging.info(f"Workflow started at: {start_time}")

    # Generate a unique invocation ID for this workflow run
    invocation_id = str(uuid.uuid4())
    logging.info(f"Invocation ID: {invocation_id}")
    
    # Step 1: text preprocessing 
    chunked_text = add_chunk_markers(text)
    logging.info(f"Text is now successfully chunked into smaller parts.")
    
    # Step 2: make a plan
    plan = await generate_plan(
        invocation_id=invocation_id,
        model= model,
        text =chunked_text,
        fact = fact,   
        inference = inference, 
        table_name="plan_metadata", 
        database_file='../database/mcq_metadata.db')
    
    logging.info(f"Plan generated successfully.")

    
    # Step 3: parse the plan and make a task list
    task_list = create_task_list(chunked_text, plan, fact, inference, main_idea)
    logging.info(f"Task list created successfully.")

    # Step 4: generate questions
    questions_list = await generate_all_mcqs(
                    task_list, 
                    invocation_id, 
                    model=model, 
                    table_name="mcq_metadata", 
                    database_file="../database/mcq_metadata.db",
                    max_attempt=3)
    logging.info(f"Questions generated successfully.")
    


    # Step 5: order and reformat the questions
    reformatted_questions = reformat_mcq_metadata_without_shuffling(questions_list)
    logging.info(f"Questions reformatted successfully.")
    
    # Step 6: store the data in a new table "mcq_formatted_metadata"  
    # Record the end time of the workflow
    end_time = datetime.now()
    execution_time = end_time - start_time

    # calculate the total tokens used
    # Calculate total input_tokens and output_tokens
    total_input_tokens = sum(item.get('input_tokens', 0) for item in reformatted_questions)
    total_output_tokens = sum(item.get('output_tokens', 0) for item in reformatted_questions)

    # create a workflow metadata dictionary
    workflow_metadata = {
        "invocation_id": invocation_id,
        "output": json.dumps(reformatted_questions),
        "execution_time": str(execution_time),
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "timestamp": str(datetime.now())
    }
    # Create the table for workflow metadata
    create_table(table_name, database_file)
    # Insert the workflow metadata into the database
    insert_metadata(workflow_metadata, table_name, database_file)
    logging.info(f"Workflow metadata stored successfully.")

    return reformatted_questions
    


