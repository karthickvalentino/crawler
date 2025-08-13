import logging
import json
import httpx
from typing import Dict, Any

from src.config import settings

logger = logging.getLogger(__name__)

# --- Predefined Schemas ---

PREDEFINED_SCHEMAS = {
    "ecommerce": {
        "product_name": "string",
        "price": "number",
        "currency": "string (e.g., USD, EUR)",
        "sku": "string",
        "description": "string",
        "category": "string",
    },
    "blog": {
        "post_title": "string",
        "author": "string",
        "publication_date": "string (ISO 8601 format)",
        "tags": "array of strings",
        "summary": "string",
    },
}

# --- Core Extraction Logic ---

def generate_extraction_prompt(content: str, schema: Dict[str, str]) -> str:
    """
    Generates a detailed prompt for the LLM to extract structured data.
    """
    schema_str = json.dumps(schema, indent=2)
    return f"""
    You are an expert data extraction agent. Your task is to analyze the following text content and extract structured data based on the provided JSON schema.

    Only extract information that is explicitly present in the text. If a field is not mentioned, do not include it in the output. Your response MUST be a valid JSON object that adheres to the schema.

    **JSON Schema:**
    ```json
    {schema_str}
    ```

    **Text Content:**
    ---
    {content}
    ---

    **Your JSON Output:**
    """

def extract_structured_data_with_ollama(content: str, schema_name: str = "ecommerce") -> Dict[str, Any]:
    """
    Uses Ollama to extract structured data from text based on a predefined schema.
    """
    if schema_name not in PREDEFINED_SCHEMAS:
        logger.warning(f"Unknown schema '{schema_name}' requested. No data will be extracted.")
        return {}

    schema = PREDEFINED_SCHEMAS[schema_name]
    prompt = generate_extraction_prompt(content, schema)

    try:
        response = httpx.post(
            settings.ollama_chat_url,
            json={
                "model": settings.ollama_llama_model,
                "messages": [{"role": "user", "content": prompt}],
                "format": "json",  # Request JSON output from Ollama
                "stream": False,
            },
            timeout=120.0, # Increased timeout for potentially long extractions
        )
        response.raise_for_status()

        # The response from Ollama with format=json should be a JSON object string
        response_data = response.json()
        message_content = response_data.get("message", {}).get("content", "{}")
        
        # Parse the JSON string from the message content
        extracted_data = json.loads(message_content)
        
        logger.info(f"Successfully extracted structured data using schema '{schema_name}'.")
        return extracted_data

    except httpx.RequestError as e:
        logger.error(f"Error making request to Ollama for structured data extraction: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON response from Ollama: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during structured data extraction: {e}", exc_info=True)

    return {}
