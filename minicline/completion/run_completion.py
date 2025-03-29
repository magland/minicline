from typing import Dict, Any, List, Tuple
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

def run_completion(
    messages: List[Dict[str, Any]],
    *,
    model: str
) -> Tuple[str, List[Dict[str, Any]], int, int]:
    """Execute an AI completion request using the OpenRouter API

    This function manages a conversation with an AI model

    Args:
        messages: List of conversation messages, each being a dictionary with role and content.
        model: Name of the OpenRouter model to use for completion.

    Returns:
        tuple: Contains:
            - content (str): The final response content from the model
            - conversation_messages (List): Complete conversation history
            - total_prompt_tokens (int): Total tokens used in prompts
            - total_completion_tokens (int): Total tokens used in completions

    Raises:
        ValueError: If OPENROUTER_API_KEY environment variable is not set
        RuntimeError: If the OpenRouter API request fails

    Notes:

    The OPENROUTER_API_KEY environment variable must be set with a valid API key from OpenRouter.

    The messages is a list of dicts with the following structure:
    [
        {"role": "system", "content": "You are a helpful assistant... etc."},
        {"role": "user", "content": "I need help with... etc."},
        {"role": "assistant", "content": "I can help with that... etc."},
        {"role": "user", "content": "Yes, please... etc."},
        ...
    ]
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable not set")

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://neurosift.app",
        "Content-Type": "application/json"
    }

    conversation_messages = [m for m in messages]

    total_prompt_tokens = 0
    total_completion_tokens = 0

    while True:
        # Make API request
        payload = {
            "model": model,
            "messages": conversation_messages
        }
        print(f"Using model: {payload['model']}")
        print(f"Num. messages in conversation: {len(conversation_messages)}")

        print("Submitting completion request...")
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            raise RuntimeError(f"OpenRouter API request failed: {response.text}")

        print("Processing response...")
        completion = response.json()
        prompt_tokens = completion["usage"]["prompt_tokens"]
        completion_tokens = completion["usage"]["completion_tokens"]

        total_prompt_tokens += prompt_tokens
        total_completion_tokens += completion_tokens
        # print(f'TOKENS: {int(promt_tokens / 100) / 10} prompt, {int(completion_tokens / 100) / 10} completion; total: {int(total_prompt_tokens / 100) / 10} prompt, {int(total_completion_tokens / 100) / 10} completion')

        message = completion["choices"][0]["message"]
        content: str = message.get("content", "")

        # print("\nReceived assistant response...")
        # Track assistant response
        current_response = {
            "role": "assistant",
            "content": content
        }
        conversation_messages.append(current_response)

        return content, conversation_messages, total_prompt_tokens, total_completion_tokens
