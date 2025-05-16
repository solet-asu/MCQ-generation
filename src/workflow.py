from src.text_processing import add_chunk_markers


# Step 1: text preprocessing:
def question_generation_workflow(text:str, facts:int, inferences:int, main_idea:int) -> list[dict[str, str]]:
    """
    Main function to generate questions based on the provided text and parameters.
    
    :param text: The raw text to be processed.
    :param facts: The number of fact-based questions to generate.
    :param inferences: The number of inference-based questions to generate.
    :param main_idea: The number of main idea questions to generate.
    :return: A list of dictionaries containing the generated questions and their answers. For example:
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
    


