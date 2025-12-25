import dashscope
from http import HTTPStatus
import os

# Default model, can be overridden
DEFAULT_MODEL = "qwen-flash"

def generate_text(prompt: str, api_key: str = None, model: str = DEFAULT_MODEL) -> str:
    """
    Calls DashScope API to generate text based on the prompt.
    
    Args:
        prompt (str): The input prompt.
        api_key (str): DashScope API Key. If None, checks env var DASHSCOPE_API_KEY.
        model (str): The model name to use.
        
    Returns:
        str: The generated text content.
    """
    
    # Ensure API Key is available
    if not api_key:
        api_key = os.getenv("DASHSCOPE_API_KEY")
    
    if not api_key:
        return "Error: API Key is missing. Please provide it in the sidebar or .env file."

    dashscope.api_key = api_key
    
    try:
        response = dashscope.Generation.call(
            model=model,
            prompt=prompt,
            result_format='message',  # Use message format for chat models
        )
        
        if response.status_code == HTTPStatus.OK:
            return response.output.choices[0].message.content
        else:
            return f"Error {response.code}: {response.message}"
            
    except Exception as e:
        return f"Exception during generation: {str(e)}"
