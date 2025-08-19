# Core AI processing modules

from .base import AIProvider
from .claude_provider import ClaudeProvider  
from .gemini_provider import GeminiProvider

# Factory function
def create_ai_provider(provider_name: str, model: str, temperature: float = None) -> AIProvider:
    """
    Create an AI provider instance using centralized configuration.
    
    Args:
        provider_name: Name of the AI provider ('claude' or 'gemini')
        model: Specific model to use
        temperature: Temperature setting for generation
        
    Returns:
        Configured AI provider instance
        
    Raises:
        ValueError: If provider_name is not supported or API key is missing
        Exception: If provider initialization fails
    """
    from ..config.config import config as global_config
    
    # Get full configuration from centralized method (includes API key validation)
    cfg = global_config.get_api_config(provider_name)
    
    # Use temperature from config if not provided
    if temperature is None:
        temperature = global_config.temperature
    
    # Create provider based on provider class from config
    if cfg['provider_class'] == 'ClaudeProvider':
        return ClaudeProvider(api_key=cfg['api_key'], model=model, temperature=temperature)
    elif cfg['provider_class'] == 'GeminiProvider':
        return GeminiProvider(api_key=cfg['api_key'], model=model, temperature=temperature)
    else:
        raise ValueError(f"Unknown provider class: {cfg['provider_class']}")


__all__ = [
    'create_ai_provider',
    'AIProvider',
    'ClaudeProvider', 
    'GeminiProvider',
]