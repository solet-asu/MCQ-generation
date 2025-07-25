import functools
import importlib.resources
import logging
import yaml
import prompts

# Set up logging for the module
logger = logging.getLogger(__name__)

@functools.cache
def get_prompts(filename: str = "fact_prompts.yaml") -> dict[str, str]:
    """
    Retrieve prompts from a YAML file.

    This function caches the result to avoid re-reading the file multiple times.
    
    Args:
        filename (str): The name of the YAML file containing prompts. Defaults to 'prompts.yaml'.
    
    Returns:
        dict[str, str]: A dictionary with prompt keys and their corresponding text.
    """
    try:
        # Locate the resources directory within the prompts package
        resources_dir = importlib.resources.files(prompts)
        prompt_path = resources_dir / filename
        
        # Open and read the YAML file
        with open(prompt_path, encoding="utf-8") as f:
            prompts_data = yaml.safe_load(f)
        
        return prompts_data
    
    except FileNotFoundError as e:
        logger.error(f"File not found: {prompt_path}")
        raise e
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file: {prompt_path}")
        raise e