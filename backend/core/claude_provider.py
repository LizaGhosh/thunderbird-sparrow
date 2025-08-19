#!/usr/bin/env python3
"""
Claude AI Provider Implementation

Implementation of the Anthropic Claude AI provider for maintenance
voice note parsing using the SIMPLIFIED v3.0 prompt.

Author: AI Assistant
Version: 2.0
"""

import json
import time
from typing import Dict, Any, Optional
import anthropic

from .base import AIProvider


class ClaudeProvider(AIProvider):
    """
    Claude AI provider implementation for maintenance voice note parsing.
    
    Uses Anthropic's Claude models with the optimized SIMPLIFIED v3.0 prompt
    for consistent and accurate work item classification.
    """
    
    def __init__(self, api_key: str, model: str, temperature: float = None):
        """
        Initialize Claude provider.
        
        Args:
            api_key: Anthropic API key
            model: Claude model name from config.yaml
            temperature: Temperature setting for generation
        """
        super().__init__(model, temperature)
        
        # Initialize Claude client
        try:
            self.client = anthropic.Anthropic(api_key=api_key)
        except Exception as e:
            self.log('error', f"Failed to initialize Claude client: {e}")
            raise RuntimeError(f"Failed to initialize Claude client: {e}")
        
        # Store the primary model from config.yaml
        self.primary_model = model
        
        # Available models for fallback (only used if primary model fails)
        self.available_models = [
            'claude-3-5-sonnet-20241022',
            'claude-3-5-haiku-20241022', 
            'claude-3-opus-20240229'
        ]
        
        # Start with the primary model from config.yaml
        if model in self.available_models:
            self.current_model_index = self.available_models.index(model)
            self.log('info', f"Using primary model from config: {model}")
        else:
            # Fallback to first available model if config model not in list
            self.current_model_index = 0
            self.log('warning', f"Model '{model}' not in available models, using fallback: {self.available_models[0]}")
    
    def analyze_work_intent(self, text: str, test_id: str = None) -> Dict[str, Any]:
        """Analyze text using SIMPLIFIED v3.0 prompt."""
        prompt = self.get_prompt('work_triaging', text=text)
        
        try:
            start_time = time.time()
            response = self._make_api_call(prompt, "ANALYZE_WORK_INTENT", test_id)
            return self._process_ai_response(response, "ANALYZE_WORK_INTENT", test_id, start_time)
        except Exception as e:
            self.log('error', f"Failed to analyze work intent: {e}")
            raise
    
    def generate_closing_comment(self, text: str, test_id: str = None) -> Dict[str, Any]:
        """Generate closing comment for completed work."""
        prompt = self.get_prompt('closing_comment', text=text)
        
        try:
            start_time = time.time()
            response = self._make_api_call(prompt, "GENERATE_CLOSING_COMMENT", test_id)
            return self._process_ai_response(response, "GENERATE_CLOSING_COMMENT", test_id, start_time, False)
        except Exception as e:
            self.log('error', f"Failed to generate closing comment: {e}")
            return {
                'closing_comment': "Error generating closing comment",
                'actual_downtime_hours': None
            }
    

    
    def _make_api_call(self, prompt: str, operation: str, test_id: str = None) -> str:
        """Make API call to Claude with centralized retry logic."""
        
        def make_claude_call():
            current_model = self.available_models[self.current_model_index]
            response = self.client.messages.create(
                model=current_model,
                max_tokens=2000,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        
        # Use centralized retry logic from base class
        return self._execute_with_retry(operation, make_claude_call, provider_name="Claude")
    
    def _switch_to_next_model(self) -> bool:
        """
        Switch to next available model for fallback.
        
        Returns:
            bool: True if model was switched, False if no more models available
        """
        # Find the next available model (skip the current one)
        for i in range(len(self.available_models)):
            if i > self.current_model_index:
                old_model = self.available_models[self.current_model_index]
                self.current_model_index = i
                new_model = self.available_models[self.current_model_index]
                self.log('info', f"Switching Claude from {old_model} to fallback model: {new_model}")
                return True
        
        self.log('warning', "No more Claude models available for fallback")
        return False
    

