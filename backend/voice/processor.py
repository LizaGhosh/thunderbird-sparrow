#!/usr/bin/env python3
"""
Voice Processing Module for Industrial Maintenance Voice Note Parser

This module handles voice recording, transcription, and LLM processing
using the existing infrastructure from the src folder.

Author: AI Assistant
Version: 2.0
"""

import os
import tempfile
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceProcessor:
    """Main class for processing voice inputs using existing LLM infrastructure."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize voice processor.
        
        Args:
            config (dict): Configuration dictionary with LLM settings
        """
        self.config = config
        self.llm_provider = None
        self.voice_recorder = None
        
        # Initialize components
        self._initialize_llm_provider()
        self._initialize_voice_recorder()
    
    def _initialize_llm_provider(self) -> None:
        """Initialize LLM provider using existing factory function."""
        try:
            from ..core import create_ai_provider
            
            # Get configuration
            provider = self.config.get('llm_provider', 'gemini')
            model = self.config.get('model', 'gemini-1.5-pro' if provider == 'gemini' else 'claude-3-opus-20240229')
            temperature = self.config.get('temperature', 0.7)
            
            # Create provider using existing factory
            self.llm_provider = create_ai_provider(
                provider_name=provider,
                model=model,
                temperature=temperature
            )
            
            logger.info(f"Initialized {provider} provider with model {model} and temperature {temperature}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM provider: {e}")
            raise
    
    def _initialize_voice_recorder(self) -> None:
        """Initialize voice recorder component."""
        try:
            from .voice_recorder import create_voice_recorder
            
            whisper_model = self.config.get('whisper_model', 'base')
            self.voice_recorder = create_voice_recorder(whisper_model)
            
        except ImportError:
            logger.warning("Voice recorder dependencies not installed. Run: pip install -r ../requirements.txt")
            self.voice_recorder = None
        except Exception as e:
            logger.error(f"Failed to initialize voice recorder: {e}")
            self.voice_recorder = None
    
    def process_voice_input(self, duration: int = 10, work_type: str = "work_triaging", whisper_model: str = "base") -> Dict[str, Any]:
        """
        Process voice input using existing LLM infrastructure.
        
        Args:
            duration (int): Recording duration in seconds
            work_type (str): Type of work to process ('work_triaging' or 'closing_comments')
            whisper_model (str): Whisper model to use
            
        Returns:
            dict: Processing results
        """
        if not self.voice_recorder:
            return {
                'success': False,
                'error': 'Voice recording dependencies not installed'
            }
        
        try:
            # Step 1: Record audio
            logger.info("Recording audio...")
            audio_path = self.voice_recorder.record_audio(duration=duration)
            
            # Step 2: Transcribe audio
            logger.info("Transcribing audio...")
            transcription = self.voice_recorder.transcribe_audio(audio_path)
            
            # Step 3: Process with LLM
            logger.info("Processing with LLM...")
            llm_output = self._process_with_llm(transcription['text'], work_type)
            
            # Step 4: Compile results
            result = {
                'success': True,
                'transcription': transcription,
                'llm_output': llm_output,
                'audio_path': audio_path,
                'work_type': work_type,
                'timestamp': transcription['timestamp']
            }
            
            logger.info(f"Voice processing completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Voice processing failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_audio_file(self, audio_file, work_type: str, whisper_model: str = 'base') -> Dict[str, Any]:
        """
        Process uploaded audio file using existing LLM infrastructure.
        
        Args:
            audio_file: Uploaded audio file
            work_type (str): Type of work to process
            whisper_model (str): Whisper model to use
            
        Returns:
            dict: Processing results
        """
        if not self.voice_recorder:
            return {
                'success': False,
                'error': 'Voice recording dependencies not installed'
            }
        
        try:
            # Save uploaded file to temporary location
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_filename = f"uploaded_audio_{timestamp}.wav"
            audio_path = os.path.join(tempfile.gettempdir(), temp_filename)
            
            audio_file.save(audio_path)
            logger.info(f"Saved uploaded audio to: {audio_path}")
            
            # Transcribe audio
            logger.info("Transcribing uploaded audio...")
            transcription = self.voice_recorder.transcribe_audio(audio_path)
            
            # Process with LLM
            logger.info("Processing with LLM...")
            llm_output = self._process_with_llm(transcription['text'], work_type)
            
            # Compile results
            result = {
                'success': True,
                'transcription': transcription,
                'llm_output': llm_output,
                'audio_path': audio_path,
                'work_type': work_type,
                'timestamp': transcription['timestamp']
            }
            
            logger.info("Audio file processing completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Audio file processing failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            # Clean up temporary file
            if 'audio_path' in locals() and os.path.exists(audio_path):
                os.remove(audio_path)
                logger.info("Cleaned up temporary audio file")
    
    def _process_with_llm(self, text: str, work_type: str) -> Dict[str, Any]:
        """
        Process transcribed text with existing LLM functions
        
        Args:
            text (str): Transcribed text
            work_type (str): Type of work to process
            
        Returns:
            dict: LLM processing output validated against Pydantic schemas
        """
        try:
            if work_type == "work_triaging":
                return self._process_work_triaging(text)
            elif work_type == "closing_comments":
                return self._process_closing_comments(text)
            else:
                raise ValueError(f"Unsupported work type: {work_type}")
                
        except Exception as e:
            logger.error(f"LLM processing failed: {e}")
            raise
    
    def _process_work_triaging(self, text: str) -> Dict[str, Any]:
        """Process text for work triaging using EXACT same method as main.py"""
        try:
            # Use the EXACT same method that main.py uses
            result = self.llm_provider.analyze_work_intent(text, test_id="voice_input")
            
            # Validate using existing validation method from src
            import sys
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
            from ..core.validation import validate_work_triaging_output
            is_valid = validate_work_triaging_output(result, "voice_input")
            
            if not is_valid:
                logger.warning("Work triaging output validation failed, using fallback")
                result = {
                    'work_requests': [],
                    'work_orders': [],
                    'inspection_tasks': [],
                    'general_tasks': []
                }
            
            # Add metadata
            result['original_text'] = text
            result['voice_input'] = True
            
            return result
            
        except Exception as e:
            logger.error(f"Work triaging failed: {e}")
            # Return fallback response matching the expected structure
            return {
                'work_requests': [],
                'work_orders': [],
                'inspection_tasks': [],
                'general_tasks': [],
                'original_text': text,
                'voice_input': True,
                'error': str(e)
            }
    
    def _process_closing_comments(self, text: str) -> Dict[str, Any]:
        """Process text for closing comments using EXACT same method as main.py"""
        try:
            # Use the EXACT same method that main.py uses
            result = self.llm_provider.generate_closing_comment(text, test_id="voice_input")
            
            # Validate using existing validation method from src
            import sys
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
            from ..core.validation import validate_closing_comment_output
            is_valid = validate_closing_comment_output(result, "voice_input")
            
            if not is_valid:
                logger.warning("Closing comment output validation failed, using fallback")
                result = {
                    'closing_comment': 'Error in output validation',
                    'actual_downtime_hours': None
                }
            
            # Add metadata
            result['original_text'] = text
            result['voice_input'] = True
            
            return result
            
        except Exception as e:
            logger.error(f"Closing comment generation failed: {e}")
            # Return fallback response matching the expected structure
            return {
                'closing_comment': f"Error generating closing comment: {str(e)}",
                'actual_downtime_hours': None,
                'original_text': text,
                'voice_input': True,
                'error': str(e)
            }
    
    def get_available_whisper_models(self) -> list:
        """Get list of available Whisper models"""
        return ['tiny', 'base', 'small', 'medium', 'large']
    
    def cleanup(self):
        """Clean up resources"""
        if self.voice_recorder:
            self.voice_recorder.cleanup()

def create_voice_processor(config: Dict[str, Any]) -> VoiceProcessor:
    """
    Factory function to create a voice processor instance
    
    Args:
        config (dict): Configuration dictionary
        
    Returns:
        VoiceProcessor: Configured voice processor instance
    """
    return VoiceProcessor(config)
