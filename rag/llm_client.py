"""
OpenAI-compatible local LLM HTTP client.

This module provides a client for interacting with local LLMs that expose
an OpenAI-compatible API (e.g., vLLM, FastChat, LocalAI, text-generation-webui).
"""

import os
import requests
from typing import List, Dict, Any, Optional, Iterator
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMClient:
    """
    Client for OpenAI-compatible local LLM endpoints.
    
    Supports chat completion with configurable parameters and
    optional streaming responses.
    
    Attributes:
        base_url (str): Base URL of the LLM API endpoint
        api_key (str): API key for authentication (if required)
        timeout (int): Request timeout in seconds
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 60,
        verify_ssl: bool = True
    ):
        """
        Initialize LLM client.
        
        Args:
            base_url: Base URL of the API (default: from OPENAI_BASE_URL env var)
            api_key: API key (default: from OPENAI_API_KEY env var)
            timeout: Request timeout in seconds (default: 60)
            verify_ssl: Whether to verify SSL certificates (default: True)
        """
        # Get base_url from environment if not provided
        self.base_url = base_url or os.getenv(
            'OPENAI_BASE_URL',
            'http://localhost:8000/v1'
        )
        
        # Get api_key from environment if not provided
        self.api_key = api_key or os.getenv('OPENAI_API_KEY', 'EMPTY')
        
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        
        # Ensure base_url doesn't end with slash
        self.base_url = self.base_url.rstrip('/')
        
        logger.info(f"Initialized LLM client with base_url: {self.base_url}")
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get request headers with authentication.
        
        Returns:
            Dictionary of HTTP headers
        """
        headers = {
            'Content-Type': 'application/json'
        }
        
        if self.api_key and self.api_key != 'EMPTY':
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        return headers
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "default",
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate chat completion.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model name (default: "default")
            temperature: Sampling temperature (default: 0.7)
            top_p: Nucleus sampling parameter (default: 0.9)
            max_tokens: Maximum tokens to generate (default: None)
            stream: Whether to stream the response (default: False)
            **kwargs: Additional parameters passed to the API
            
        Returns:
            Response dictionary containing the generated text and metadata
            
        Example:
            >>> client = LLMClient()
            >>> messages = [
            ...     {"role": "system", "content": "You are a helpful assistant."},
            ...     {"role": "user", "content": "What is the capital of France?"}
            ... ]
            >>> response = client.chat_completion(messages)
            >>> print(response['choices'][0]['message']['content'])
        """
        endpoint = f"{self.base_url}/chat/completions"
        
        # Prepare request payload
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "stream": stream,
            **kwargs
        }
        
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        
        logger.info(f"Sending chat completion request to {endpoint}")
        logger.debug(f"Payload: {json.dumps(payload, ensure_ascii=False)}")
        
        try:
            if stream:
                return self._stream_completion(endpoint, payload)
            else:
                response = requests.post(
                    endpoint,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=self.timeout,
                    verify=self.verify_ssl
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info("Chat completion successful")
                return result
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error during chat completion: {e}")
            raise
    
    def _stream_completion(
        self,
        endpoint: str,
        payload: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        """
        Stream chat completion response.
        
        Args:
            endpoint: API endpoint URL
            payload: Request payload
            
        Yields:
            Chunks of the streaming response
        """
        response = requests.post(
            endpoint,
            headers=self._get_headers(),
            json=payload,
            timeout=self.timeout,
            verify=self.verify_ssl,
            stream=True
        )
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]  # Remove 'data: ' prefix
                    if data.strip() == '[DONE]':
                        break
                    try:
                        chunk = json.loads(data)
                        yield chunk
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to decode JSON: {data}")
    
    def simple_generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Simple text generation interface.
        
        Args:
            prompt: User prompt/query
            system_message: Optional system message (default: None)
            **kwargs: Additional parameters for chat_completion
            
        Returns:
            Generated text as string
        """
        messages = []
        
        if system_message:
            messages.append({
                "role": "system",
                "content": system_message
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        response = self.chat_completion(messages, **kwargs)
        
        return response['choices'][0]['message']['content']
    
    def test_connection(self) -> bool:
        """
        Test connection to the LLM endpoint.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            logger.info("Connection test successful")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


def create_llm_client(
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs
) -> LLMClient:
    """
    Factory function to create an LLM client instance.
    
    Args:
        base_url: Base URL of the API
        api_key: API key for authentication
        **kwargs: Additional parameters for LLMClient
        
    Returns:
        LLMClient instance
    """
    return LLMClient(base_url=base_url, api_key=api_key, **kwargs)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Test LLM client with OpenAI-compatible endpoint'
    )
    parser.add_argument(
        '--base-url',
        type=str,
        help='Base URL of the LLM API (default: from OPENAI_BASE_URL env)'
    )
    parser.add_argument(
        '--api-key',
        type=str,
        help='API key (default: from OPENAI_API_KEY env)'
    )
    parser.add_argument(
        '--prompt',
        type=str,
        default='你好，请介绍一下你自己',
        help='Test prompt (default: "你好，请介绍一下你自己")'
    )
    parser.add_argument(
        '--system',
        type=str,
        default='你是一个专业的AI助手',
        help='System message (default: "你是一个专业的AI助手")'
    )
    parser.add_argument(
        '--stream',
        action='store_true',
        help='Enable streaming output'
    )
    
    args = parser.parse_args()
    
    print("=== LLM Client Test ===\n")
    
    # Create client
    client = create_llm_client(
        base_url=args.base_url,
        api_key=args.api_key
    )
    
    print(f"Base URL: {client.base_url}")
    print(f"Testing connection...\n")
    
    # Test connection
    if not client.test_connection():
        print("ERROR: Connection test failed!")
        print("\nPlease ensure:")
        print("1. The LLM server is running")
        print("2. The base URL is correct")
        print("3. The API key is valid (if required)")
        print("\nExample setup:")
        print("  export OPENAI_BASE_URL='http://localhost:8000/v1'")
        print("  export OPENAI_API_KEY='your-api-key'")
        exit(1)
    
    print("Connection successful!\n")
    
    # Prepare messages
    messages = [
        {"role": "system", "content": args.system},
        {"role": "user", "content": args.prompt}
    ]
    
    print(f"System: {args.system}")
    print(f"User: {args.prompt}\n")
    print("Assistant: ", end='', flush=True)
    
    # Generate response
    if args.stream:
        # Streaming response
        for chunk in client.chat_completion(messages, stream=True):
            if 'choices' in chunk and len(chunk['choices']) > 0:
                delta = chunk['choices'][0].get('delta', {})
                if 'content' in delta:
                    print(delta['content'], end='', flush=True)
        print()
    else:
        # Non-streaming response
        response = client.chat_completion(messages)
        content = response['choices'][0]['message']['content']
        print(content)
    
    print("\n=== Test completed ===")
