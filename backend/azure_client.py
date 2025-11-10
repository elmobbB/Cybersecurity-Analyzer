"""
Azure OpenAI client configuration and utilities.
"""
import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

def get_azure_openai_client():
    """
    Initialize and return an Azure OpenAI client.
    
    Returns:
        AzureOpenAI: Configured Azure OpenAI client
    """
    api_key = os.getenv("AZURE_OPENAI_KEY_GPT_5_NANO")
    endpoint = os.getenv("AI_FOUNDRY_ENDPOINT_GPT_5_NANO")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
    
    if not api_key or not endpoint:
        raise ValueError(
            "Azure OpenAI configuration missing. "
            "Please set AZURE_OPENAI_KEY_GPT_5_NANO and AI_FOUNDRY_ENDPOINT_GPT_5_NANO environment variables."
        )
    
    return AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=endpoint,
    )

def get_azure_deployment_id(model_name: str) -> str:
    """
    Get the Azure deployment ID for a given model name.
    
    Args:
        model_name: The name of the model (e.g., 'gpt-4.1-mini')
        
    Returns:
        str: The deployment ID for the model
    """
    # Map model names to deployment IDs
    deployment_map = {
        'gpt-4.1-mini': os.getenv('AZURE_DEPLOYMENT_GPT4_MINI', 'gpt-4.1-mini'),
        # Add more model mappings as needed
    }
    
    return deployment_map.get(model_name, model_name)
