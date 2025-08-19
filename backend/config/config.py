#!/usr/bin/env python3
"""
Simple Configuration Loader

Easy-to-use configuration system that loads from config.yaml
and provides simple parameter management.

Usage:
    from config.config import config
    print(f"Using {config.ai_provider} with {config.model}")
    
    # Configuration is loaded from YAML file
    # All settings are read-only and managed through config.yaml
"""

import os
import yaml
import logging
import glob
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class SimpleConfig:
    """Simple configuration class with easy access to all settings."""
    
    # AI Settings
    ai_provider: str
    model: str
    temperature: float
    
    # Processing Settings
    parallel_processing: bool
    validate_outputs: bool
    
    # Paths
    inputs_dir: str
    outputs_dir: str
    logs_dir: str
    
    def __post_init__(self):
        """Load configuration from file after initialization."""
        # Ensure central file logging to logs/app.log is configured once
        try:
            root_logger = logging.getLogger()
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            logs_dir = os.path.join(project_root, 'backend', 'logs')
            os.makedirs(logs_dir, exist_ok=True)

            log_path = os.path.join(logs_dir, 'app.log')
            has_our_file = any(
                isinstance(h, logging.FileHandler) and getattr(h, 'baseFilename', None) == log_path
                for h in root_logger.handlers
            )
            if not has_our_file:
                # Remove any existing FileHandlers to avoid multiple files
                for h in list(root_logger.handlers):
                    if isinstance(h, logging.FileHandler):
                        try:
                            root_logger.removeHandler(h)
                        except Exception:
                            pass
                fh = None
                try:
                    # Overwrite the log file instead of appending
                    fh = logging.FileHandler(log_path, mode='w')
                except (OSError, PermissionError) as e:
                    import sys
                    print(f"Warning: could not attach file handler {log_path}: {e}", file=sys.stderr)
                if fh is not None:
                    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
                    root_logger.addHandler(fh)
            if root_logger.level == logging.NOTSET:
                root_logger.setLevel(logging.INFO)
        except Exception as e:
            # Last-resort: don't crash app on logging setup failure
            import sys
            print(f"Warning: logging setup failed: {e}", file=sys.stderr)
        self.load_from_yaml()
    
    def load_from_yaml(self, filename: str = None) -> None:
        """Load configuration from YAML file."""
        try:
            # Resolve YAML path relative to this file's directory by default
            if not filename:
                filename = os.path.join(os.path.dirname(__file__), 'config.yaml')
            if not os.path.exists(filename):
                raise FileNotFoundError(f"Configuration file not found: {filename}")
            
            with open(filename, 'r') as f:
                yaml_config = yaml.safe_load(f)
                
            if not yaml_config:
                raise ValueError(f"Configuration file {filename} is empty or invalid")
            
            # Validate and set required configuration values
            required_fields = [
                'ai_provider', 'model', 'temperature', 'parallel_processing',
                'validate_outputs', 'inputs_dir', 'outputs_dir', 'logs_dir'
            ]
            
            missing_fields = []
            for field in required_fields:
                if field not in yaml_config:
                    missing_fields.append(field)
                elif hasattr(self, field):
                    setattr(self, field, yaml_config[field])
            
            if missing_fields:
                raise ValueError(f"Missing required configuration fields: {', '.join(missing_fields)}")
                
            # Validate specific field values
            self._validate_config_values()
            
        except Exception as e:
            error_msg = f"Failed to load configuration from {filename}: {str(e)}"
            logging.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _validate_config_values(self) -> None:
        """Validate configuration values and log warnings for invalid ones."""
        warnings = []
        
        # Validate AI provider
        if self.ai_provider not in ['claude', 'gemini']:
            warnings.append(f"Invalid ai_provider: {self.ai_provider}. Must be 'claude' or 'gemini'")
        
        # Validate temperature range
        if not (0.0 <= self.temperature <= 1.0):
            warnings.append(f"Invalid temperature: {self.temperature}. Must be between 0.0 and 1.0")
        
        # Validate boolean fields
        if not isinstance(self.parallel_processing, bool):
            warnings.append(f"Invalid parallel_processing: {self.parallel_processing}. Must be boolean")
        
        if not isinstance(self.validate_outputs, bool):
            warnings.append(f"Invalid validate_outputs: {self.validate_outputs}. Must be boolean")
        
        # Validate directory paths
        if not isinstance(self.inputs_dir, str) or not self.inputs_dir:
            warnings.append(f"Invalid inputs_dir: {self.inputs_dir}. Must be non-empty string")
        
        if not isinstance(self.outputs_dir, str) or not self.outputs_dir:
            warnings.append(f"Invalid outputs_dir: {self.outputs_dir}. Must be non-empty string")
        
        if not isinstance(self.logs_dir, str) or not self.logs_dir:
            warnings.append(f"Invalid logs_dir: {self.logs_dir}. Must be non-empty string")
        
        # Log all warnings
        for warning in warnings:
            logging.warning(f"Configuration warning: {warning}")
        
        # If there are critical validation errors, raise exception
        critical_errors = [w for w in warnings if 'ai_provider' in w or 'temperature' in w]
        if critical_errors:
            raise ValueError(f"Critical configuration errors: {'; '.join(critical_errors)}")
    

    
    def get_api_config(self, provider_name: str) -> Dict[str, Any]:
        """Get API configuration for a specific provider."""
        # Ensure environment variables are loaded
        from dotenv import load_dotenv
        load_dotenv()
        
        if provider_name.lower() == 'claude':
            api_key = os.getenv('CLAUDE_API_KEY', '').strip()
            if api_key:
                api_key = api_key.replace('\n', '').replace(' ', '')
            if not api_key:
                logging.error("CLAUDE_API_KEY not found in environment variables for provider 'claude'")
                raise ValueError("CLAUDE_API_KEY not found in environment variables")
            return {
                'api_key': api_key,
                'model': os.getenv('CLAUDE_MODEL', self.model),
                'provider_class': 'ClaudeProvider'
            }
        elif provider_name.lower() == 'gemini':
            api_key = os.getenv('GEMINI_API_KEY', '').strip()
            if not api_key or api_key == 'your_gemini_api_key_here':
                logging.error("GEMINI_API_KEY not found or not configured in environment variables for provider 'gemini'")
                raise ValueError("GEMINI_API_KEY not found or not configured in environment variables")
            return {
                'api_key': api_key,
                'model': os.getenv('GEMINI_MODEL', self.model),
                'provider_class': 'GeminiProvider'
            }
        else:
            logging.error(f"Unsupported provider requested in configuration: {provider_name}")
            raise ValueError(f"Unsupported provider: {provider_name}")

 


def initialize_config() -> SimpleConfig:
    """Initialize configuration with proper error handling."""
    global config
    try:
        # Create config instance with placeholder values (will be overridden by YAML)
        config = SimpleConfig(
            ai_provider="",
            model="",
            temperature=0.0,
            parallel_processing=False,
            validate_outputs=True,
            inputs_dir="",
            outputs_dir="",
            logs_dir=""
        )
        return config
    except Exception as e:
        logging.error(f"Failed to initialize configuration: {str(e)}")
        raise
    
config = initialize_config()
