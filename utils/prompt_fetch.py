import functools
import importlib.resources
import logging
import yaml
import utils

# Set up logging for the module
logger = logging.getLogger(__name__)

@functools.cache
def get_prompts(filename: str = "prompts.yaml") -> dict[str, str]:
    """
    Retrieve prompts from a YAML file.

    This function caches the result to avoid re-reading the file multiple times.
    
    Args:
        filename (str): The name of the YAML file containing prompts. Defaults to 'prompts.yaml'.
    
    Returns:
        dict[str, str]: A dictionary with prompt keys and their corresponding text.
    """
    try:
        # Locate the resources directory within the utils package
        resources_dir = importlib.resources.files(utils)
        prompt_path = resources_dir / filename
        
        # Open and read the YAML file
        with open(prompt_path, encoding="utf-8") as f:
            prompts = yaml.safe_load(f)
        
        return prompts
    
    except FileNotFoundError as e:
        logger.error(f"File not found: {prompt_path}")
        raise e
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file: {prompt_path}")
        raise e