from src.prompt_fetch import *
from src.agent import Agent
from src.general import *


# dictionary map to link question types to their respective prompts
question_type_prompt_map = {
    "details": "details_prompts.yaml",
    "inference": "inference_prompts.yaml",
    "main_idea": "main_idea_prompts.yaml",
}

def generate_mcq(text: str, question_type, num_questions=1) -> dict:
    """
    Generates multiple-choice questions based on the provided text and learning goal.

    Args:
        text (str): The text to generate questions from.
        question_type (str): The type of question to generate. Options are "details", "inference", or "main_idea".
        num_questions (int): The number of questions to generate.

    Returns:
        list: A list of dictionaries containing the generated questions and their options.
    """
    # determine the prompt file based on the question type
    prompt_file = question_type_prompt_map.get(question_type.lower())
    if prompt_file is None:
        raise ValueError(f"Invalid question type: {question_type}. Valid options are: {', '.join(question_type_prompt_map.keys())}.")
    
    # Fetch the prompt for generating MCQs
    prompts = get_prompts(prompt_file)
    system_prompt = prompts.get("system_prompt", "")
    user_prompt = prompts.get("user_prompt", "").format(text=text)

    # Initialize the agent with the prompt for generating MCQs
    agent = Agent(question_type=question_type, 
                  model="gpt-3.5-turbo",
                  system_prompt=system_prompt,
                  user_prompt=user_prompt,)
    # first attempt to generate the MCQ
    agent.completion_generation()
    mcq_metadata = agent.get_metadata()

    return mcq_metadata