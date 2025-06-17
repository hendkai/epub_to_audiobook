from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class CostCalculator:
    """Utility class for calculating TTS API costs"""
    
    # Pricing per 1000 characters (as of 2024/2025)
    PRICING = {
        'openai': {
            'tts-1': 0.015,     # $0.015 per 1K characters
            'tts-1-hd': 0.030,  # $0.030 per 1K characters
        },
        'azure': {
            'standard': 0.004,   # $4 per 1M characters = $0.004 per 1K
            'neural': 0.016,     # $16 per 1M characters = $0.016 per 1K
        },
        'edge': {
            'free': 0.0,        # Edge TTS is free
        },
        'piper': {
            'local': 0.0,       # Piper is local and free
        }
    }
    
    def __init__(self):
        pass
    
    def estimate_costs(self, text_length: int, tts_provider: str = "azure", 
                      model: str = "neural", voice: str = "") -> Dict[str, float]:
        """
        Estimate costs for TTS conversion
        
        Args:
            text_length: Number of characters in the text
            tts_provider: TTS provider ('openai', 'azure', 'edge', 'piper')
            model: Model name for the provider
            voice: Voice name (for future use)
        
        Returns:
            Dictionary with cost estimates
        """
        try:
            # Convert characters to thousands
            chars_in_thousands = text_length / 1000.0
            
            # Get pricing based on provider and model
            provider_pricing = self.PRICING.get(tts_provider.lower(), {})
            
            if tts_provider.lower() == 'openai':
                rate = provider_pricing.get(model, provider_pricing.get('tts-1', 0.015))
            elif tts_provider.lower() == 'azure':
                # Default to neural if model not specified
                rate = provider_pricing.get('neural', 0.016)
            elif tts_provider.lower() == 'edge':
                rate = 0.0  # Free
            elif tts_provider.lower() == 'piper':
                rate = 0.0  # Free/Local
            else:
                rate = 0.0  # Unknown provider, assume free
            
            estimated_cost = chars_in_thousands * rate
            
            return {
                'provider': tts_provider,
                'model': model,
                'text_length': text_length,
                'chars_in_thousands': chars_in_thousands,
                'rate_per_1k_chars': rate,
                'estimated_cost_usd': round(estimated_cost, 4),
                'estimated_cost_eur': round(estimated_cost * 0.85, 4),  # Rough EUR conversion
                'is_free': rate == 0.0
            }
            
        except Exception as e:
            logger.error(f"Error calculating costs: {e}")
            return {
                'provider': tts_provider,
                'model': model,
                'text_length': text_length,
                'estimated_cost_usd': 0.0,
                'estimated_cost_eur': 0.0,
                'error': str(e)
            }
    
    def get_cost_comparison(self, text_length: int) -> Dict[str, Dict]:
        """Get cost comparison across all providers"""
        providers = [
            ('openai', 'tts-1'),
            ('openai', 'tts-1-hd'),
            ('azure', 'neural'),
            ('azure', 'standard'),
            ('edge', 'free'),
            ('piper', 'local')
        ]
        
        comparison = {}
        for provider, model in providers:
            key = f"{provider}_{model}"
            comparison[key] = self.estimate_costs(text_length, provider, model)
        
        return comparison
    
    def format_cost_info(self, cost_info: Dict) -> str:
        """Format cost information for display"""
        if cost_info.get('is_free', False):
            return f"💰 {cost_info['provider'].title()} ({cost_info['model']}): **KOSTENLOS**"
        
        cost_usd = cost_info.get('estimated_cost_usd', 0)
        cost_eur = cost_info.get('estimated_cost_eur', 0)
        chars = cost_info.get('text_length', 0)
        
        return (f"💰 {cost_info['provider'].title()} ({cost_info['model']}): "
                f"~${cost_usd:.4f} USD / ~€{cost_eur:.4f} EUR "
                f"({chars:,} Zeichen)")
    
    def get_cheapest_option(self, text_length: int) -> Tuple[str, Dict]:
        """Get the cheapest TTS option"""
        comparison = self.get_cost_comparison(text_length)
        
        # Filter out free options first
        paid_options = {k: v for k, v in comparison.items() 
                       if not v.get('is_free', False)}
        
        if not paid_options:
            # All are free, return edge as default
            return 'edge_free', comparison.get('edge_free', {})
        
        # Find cheapest paid option
        cheapest_key = min(paid_options.keys(), 
                          key=lambda k: paid_options[k].get('estimated_cost_usd', float('inf')))
        
        return cheapest_key, paid_options[cheapest_key] 