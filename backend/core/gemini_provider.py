#!/usr/bin/env python3
"""
Gemini AI Provider Implementation

Implementation of the Google Gemini AI provider for maintenance
voice note parsing using the SIMPLIFIED v3.0 prompt.

Author: AI Assistant
Version: 2.0
"""

import json
import time
from typing import Dict, Any, Optional
import google.generativeai as genai

from .base import AIProvider


class GeminiProvider(AIProvider):
    """
    Gemini AI provider implementation for maintenance voice note parsing.
    
    Uses Google's Gemini models with the optimized SIMPLIFIED v3.0 prompt
    for consistent and accurate work item classification.
    """
    
    def __init__(self, api_key: str, model: str, temperature: float = None):
        """
        Initialize Gemini provider.
        
        Args:
            api_key: Google API key
            model: Gemini model name from config.yaml
            temperature: Temperature setting for generation
        """
        super().__init__(model, temperature)
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Store the primary model from config.yaml
        self.primary_model = model
        
        # Available models for fallback (only used if primary model fails)
        self.available_models = [
            'gemini-1.5-pro',
            'gemini-1.5-flash',
            'gemini-1.0-pro'
        ]
        
        # Start with the primary model from config.yaml
        if model in self.available_models:
            self.current_model_index = self.available_models.index(model)
            self.log('info', f"Using primary model from config: {model}")
        else:
            # Fallback to first available model if config model not in list
            self.current_model_index = 0
            self.log('warning', f"Model '{model}' not in available models, using fallback: {self.available_models[0]}")
        
        # Initialize model
        self.model_instance = None
        self._initialize_model()
    
    def _initialize_model(self) -> None:
        """Initialize the Gemini model instance."""
        try:
            current_model = self.available_models[self.current_model_index]
            self.model_instance = genai.GenerativeModel(
                model_name=current_model,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=2000
                )
            )
            self.log('info', f"Gemini model initialized: {current_model}")
        except Exception as e:
            self.log('error', f"Failed to initialize Gemini model: {e}")
            raise
    
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
        """Make API call to Gemini with centralized retry logic."""
        
        def make_gemini_call():
            response = self.model_instance.generate_content(prompt)
            if response.text:
                return response.text
            else:
                self.log('error', "Empty response from Gemini API")
                raise ValueError("Empty response from Gemini API")
        
        # Use centralized retry logic from base class
        return self._execute_with_retry(operation, make_gemini_call, provider_name="Gemini")
    
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
                self.log('info', f"Switching Gemini from {old_model} to fallback model: {new_model}")
                
                # Try to initialize the model instance with the new model
                try:
                    self._initialize_model()
                    return True  # Successfully switched to new model
                except Exception as e:
                    self.log('error', f"Failed to initialize fallback model {new_model}: {e}")
                    # Continue to next model instead of giving up
                    continue
        
        self.log('warning', "No more Gemini models available for fallback")
        return False
    

