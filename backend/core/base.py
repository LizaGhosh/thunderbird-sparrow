#!/usr/bin/env python3
"""
Base AI Provider Class

Abstract base class for all AI providers with common functionality
for maintenance voice note parsing.

Author: AI Assistant
Version: 3.0
"""

import logging
import os
import time
import yaml
import json
import re
from abc import ABC, abstractmethod
from typing import Dict, Any

# Logging setup is handled by config.py when the application starts
# No need for module-level setup here


class AIProvider(ABC):
    """Abstract base class for AI providers with common functionality."""
    
    TEMPERATURE = 0.0
    
    def __init__(self, model: str, temperature: float = None):
        self.model = model
        self.temperature = temperature if temperature is not None else self.TEMPERATURE
        
        # Setup logging
        self.logger = logging.getLogger(self.__class__.__name__)
        if self.logger.level == logging.NOTSET:
            self.logger.setLevel(logging.INFO)
        

        
        # Load prompts
        self._prompts = self._load_prompts()
    
    def log(self, level: str, message: str) -> None:
        """Unified logging method."""
        getattr(self.logger, level.lower())(message)
    
    def _log_api_success(self, operation: str, duration: float) -> None:
        """Log successful API call."""
        self.log('info', f"{operation} | Duration: {duration:.1f}s")
    
    @abstractmethod
    def analyze_work_intent(self, text: str, test_id: str = None) -> Dict[str, Any]:
        """Analyze text and determine work intent."""
        pass
    
    @abstractmethod
    def generate_closing_comment(self, text: str, test_id: str = None) -> str:
        """Generate closing comment for completed work."""
        pass
    

    
    def _extract_json_from_response(self, response: str) -> str:
        """Extract valid JSON from API response using regex."""
        # Find JSON object using regex - much simpler than brace counting
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response)
        if not json_match:
            self.log('error', "No JSON object found in response")
            raise ValueError("No JSON object found in response")
        return json_match.group()
    
    def _validate_json_structure(self, data: Dict[str, Any]) -> bool:
        """Validate JSON response structure."""
        from .validation import validate_output
        
        output_type = 'closing_comment' if 'closing_comment' in data else 'work_triaging'
        return validate_output(data, output_type, "validation_check")
    

    
    def _load_prompts(self) -> Dict[str, Any]:
        """Load prompts from YAML file."""
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            prompts_file = os.path.join(project_root, 'backend', 'config', 'prompts.yaml')
            
            with open(prompts_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError as e:
            self.log('error', f"Prompts file not found: {e}")
            return {}
        except yaml.YAMLError as e:
            self.log('error', f"Invalid YAML format in prompts file: {e}")
            return {}
        except Exception as e:
            self.log('error', f"Failed to load prompts: {e}")
            return {}
    
    def get_prompt(self, prompt_type: str, **kwargs) -> str:
        """Get prompt with template variables replaced."""
        if prompt_type not in self._prompts:
            self.log('error', f"Prompt type '{prompt_type}' not found")
            raise KeyError(f"Prompt type '{prompt_type}' not found")
        
        try:
            return self._prompts[prompt_type]['prompt'].format(**kwargs)
        except KeyError as e:
            self.log('error', f"Missing template variable in prompt '{prompt_type}': {e}")
            raise ValueError(f"Prompt template error: {e}")
        except Exception as e:
            self.log('error', f"Failed to format prompt '{prompt_type}': {e}")
            raise ValueError(f"Prompt formatting error: {e}")
    
    def _save_raw_llm_output(self, test_id: str, prompt_type: str, raw_response: str) -> None:
        """Save raw LLM output to file."""
        try:
            from ..config.config import config
            llm_raw_dir = os.path.join(config.outputs_dir, 'llm_raw')
            os.makedirs(llm_raw_dir, exist_ok=True)
            
            filename = os.path.join(llm_raw_dir, f"{test_id}_{prompt_type}.txt")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Test ID: {test_id}\nPrompt Type: {prompt_type}\n")
                f.write(f"AI Provider: {self.__class__.__name__}\n{'='*50}\n")
                f.write(f"RAW LLM RESPONSE:\n{'='*50}\n{raw_response}\n{'='*50}\n")
        except Exception as e:
            self.log('error', f"Failed to save raw LLM output: {e}")
    
    def _process_ai_response(self, response: str, operation: str, test_id: str = None, 
                           start_time: float = None, validate_structure: bool = True) -> Dict[str, Any]:
        """Common method to process AI responses and handle validation."""
        # Save raw output
        self._save_raw_llm_output(test_id, operation, response)
        
        # Extract and parse JSON
        json_text = self._extract_json_from_response(response)
        result = json.loads(json_text)
        
        # Validate structure if requested
        if validate_structure and not self._validate_json_structure(result):
            self.log('error', "Invalid JSON structure in response")
            raise ValueError("Invalid JSON structure in response")
        
        # Log success
        if start_time:
            duration = time.time() - start_time
            self._log_api_success(operation, duration)
        
        return result
    
    def _handle_api_error(self, error: Exception, attempt: int, max_retries: int, 
                         operation: str, provider_name: str) -> tuple[bool, str]:
        """Centralized API error handling for all providers."""
        error_msg = str(error).lower()
        
        # Define error patterns and their handling
        error_patterns = {
            'rate_limit': (['rate_limit', 'quota', 'billing', 'payment'], True, 'warning'),
            'authentication': (['authentication', 'api_key', 'unauthorized', 'forbidden'], False, 'error'),
            'content_policy': (['content_policy', 'harmful', 'safety', 'violation'], False, 'error'),
            'token_limit': (['token'], False, 'error'),  # Combined with 'limit'/'exceeded' check
            'model_unavailable': (['model'], True, 'info'),  # Combined with availability check
            'timeout': (['timeout', 'deadline', 'timed out'], attempt < max_retries, 'warning')
        }
        
        # Check each error pattern
        for error_type, (terms, should_retry, log_level) in error_patterns.items():
            if any(term in error_msg for term in terms):
                # Special handling for token limits and model availability
                if error_type == 'token_limit' and not any(term in error_msg for term in ['limit', 'exceeded']):
                    continue
                if error_type == 'model_unavailable' and not any(term in error_msg for term in ['not found', 'unavailable', 'not available']):
                    continue
                
                # Log the error
                if error_type == 'rate_limit':
                    self.log(log_level, f"{provider_name} rate limit/quota hit on attempt {attempt}/{max_retries}")
                elif error_type == 'authentication':
                    self.log(log_level, f"{provider_name} authentication failed: {error}")
                elif error_type == 'content_policy':
                    self.log(log_level, f"{provider_name} content policy violation: {error}")
                elif error_type == 'token_limit':
                    self.log(log_level, f"{provider_name} token limit exceeded: {error}")
                elif error_type == 'model_unavailable':
                    self.log(log_level, f"{provider_name} model unavailable, will try fallback")
                elif error_type == 'timeout':
                    self.log(log_level, f"{provider_name} request timeout on attempt {attempt}/{max_retries}")
                
                return should_retry, error_type
        
        # Default: retry if attempts remain
        self.log('error', f"{provider_name} API error on attempt {attempt}: {error}")
        return attempt < max_retries, "api_error"
    
    def _get_retry_delay(self, attempt: int, base_wait_time: float = 1.0) -> float:
        """Calculate exponential backoff delay for retries."""
        return base_wait_time * (2 ** (attempt - 1))
    
    def _switch_to_next_model(self) -> bool:
        """
        Switch to next available model for fallback.
        This method should be overridden by providers that support model switching.
        
        Returns:
            bool: True if model was switched, False if no more models available
        """
        # Default implementation - providers should override this
        return False
    
    def _execute_with_retry(self, operation: str, api_call_func, max_retries: int = 3, 
                           base_wait_time: float = 1.0, provider_name: str = "AI Provider") -> str:
        """Execute API call with centralized retry logic and error handling."""
        for attempt in range(1, max_retries + 1):
            try:
                return api_call_func()
                
            except Exception as e:
                should_retry, error_type = self._handle_api_error(e, attempt, max_retries, operation, provider_name)
                
                # Handle non-retryable errors immediately
                if error_type in ["authentication", "content_policy", "token_limit"]:
                    error_messages = {
                        "authentication": f"Invalid or expired {provider_name} API key",
                        "content_policy": f"Prompt violates {provider_name}'s content policy",
                        "token_limit": "Prompt too long - reduce input text length"
                    }
                    raise ValueError(error_messages[error_type])
                
                # Handle retryable errors
                if should_retry and attempt < max_retries:
                    # Try to switch models if this is a model-related error
                    if error_type == "model_unavailable":
                        if self._switch_to_next_model():
                            self.log('info', f"Switched to fallback model, retrying {operation}")
                        else:
                            self.log('warning', f"No more fallback models available for {operation}")
                    
                    delay = self._get_retry_delay(attempt, base_wait_time)
                    self.log('info', f"Retrying {operation} in {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue
                
                # All retries exhausted
                if attempt >= max_retries:
                    self.log('error', f"Failed to complete {operation} after {max_retries} attempts")
                    raise Exception(f"Failed to complete {operation} after {max_retries} attempts")
        
        # This should never be reached
        raise Exception(f"Unexpected error in {operation}")
