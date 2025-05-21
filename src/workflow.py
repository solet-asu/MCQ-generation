from src.text_processing import add_chunk_markers
from src.planner import generate_plan
from src.controller_helper import create_task_list
import uuid
import logging

# Step 1: text preprocessing:
def question_generation_workflow(text:str, fact:int, inference:int, main_idea:int) -> list[dict[str, str]]:
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

    # step 1: text preprocessing 
    chunked_text = add_chunk_markers(text)

    # step 2: make a plan
    # Generate a unique invocation ID for this workflow run
    invocation_id = str(uuid.uuid4())
    logging.info(f"Invocation ID: {invocation_id}")

    plan = generate_plan(
        invocation_id=invocation_id,
        model= "gpt-4o",
        text =chunked_text,
        fact = fact,   
        inference = inference, 
        table_name="plan_metadata", 
        database_file='../database/mcq_metadata.db')
    
    # Step 3: parse the plan and make a task list

    task_list = create_task_list(plan, fact, inference, main_idea)



    


