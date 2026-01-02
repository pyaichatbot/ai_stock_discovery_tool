"""
Configuration Manager - Smart runtime configuration
Supports: CLI overrides, environment variables, preset profiles
"""

import os
from typing import Optional, Dict, Any
from dataclasses import fields
from config import Config


class ConfigManager:
    """Smart configuration manager with runtime overrides"""
    
    # Preset profiles for different trading modes
    PRESET_PROFILES = {
        'normal': {
            'SYMBOL_SOURCE': 'nifty50',
            'MIN_CONVICTION_SCORE': 60.0,
            'PENNY_STOCK_MODE_ENABLED': False,
            'HVB_ENABLED': False,
        },
        'penny_stock': {
            'SYMBOL_SOURCE': 'nifty_smallcap250',
            'MIN_CONVICTION_SCORE': 50.0,
            'PENNY_STOCK_MODE_ENABLED': True,
            'HVB_ENABLED': False,
            'MIN_AVG_VOLUME': 10000,  # Lower for penny stocks
        },
        'hvb': {
            'SYMBOL_SOURCE': 'nifty50',
            'MIN_CONVICTION_SCORE': 70.0,
            'PENNY_STOCK_MODE_ENABLED': False,
            'HVB_ENABLED': True,
        },
        'aggressive': {
            'SYMBOL_SOURCE': 'nifty200',
            'MIN_CONVICTION_SCORE': 55.0,
            'PENNY_STOCK_MODE_ENABLED': False,
            'HVB_ENABLED': True,
        },
        'conservative': {
            'SYMBOL_SOURCE': 'nifty50',
            'MIN_CONVICTION_SCORE': 75.0,
            'PENNY_STOCK_MODE_ENABLED': False,
            'HVB_ENABLED': False,
        }
    }
    
    @staticmethod
    def create_config(
        profile: Optional[str] = None,
        overrides: Optional[Dict[str, Any]] = None,
        enable_penny_stock: bool = False,
        enable_hvb: bool = False
    ) -> Config:
        """
        Create a Config instance with smart defaults and overrides
        
        Args:
            profile: Preset profile name ('normal', 'penny_stock', 'hvb', etc.)
            overrides: Dict of config values to override
            enable_penny_stock: Auto-configure for penny stocks
            enable_hvb: Auto-configure for HVB mode
        
        Returns:
            Configured Config instance
        """
        # Start with base config
        config = Config()
        
        # Apply profile if specified
        if profile and profile in ConfigManager.PRESET_PROFILES:
            profile_config = ConfigManager.PRESET_PROFILES[profile]
            for key, value in profile_config.items():
                if hasattr(config, key):
                    setattr(config, key, value)
        
        # Auto-configure based on flags (highest priority)
        if enable_penny_stock:
            # Auto-configure for penny stock mode
            penny_config = ConfigManager.PRESET_PROFILES['penny_stock']
            for key, value in penny_config.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            print("🔧 Auto-configured for PENNY STOCK mode")
            print(f"   • Symbol source: {config.SYMBOL_SOURCE}")
            print(f"   • Conviction threshold: {config.MIN_CONVICTION_SCORE}")
            print()
        
        if enable_hvb:
            # Auto-configure for HVB mode
            if not config.HVB_ENABLED:
                config.HVB_ENABLED = True
            if config.MIN_CONVICTION_SCORE < 70.0:
                config.MIN_CONVICTION_SCORE = 70.0
            print("🔧 Auto-configured for HVB mode")
            print(f"   • HVB enabled: {config.HVB_ENABLED}")
            print(f"   • Conviction threshold: {config.MIN_CONVICTION_SCORE}")
            print()
        
        # Apply environment variable overrides
        ConfigManager._apply_env_overrides(config)
        
        # Apply explicit overrides (highest priority)
        if overrides:
            for key, value in overrides.items():
                if hasattr(config, key):
                    setattr(config, key, value)
        
        # Reload symbols if symbol source changed
        if config.SYMBOL_SOURCE:
            config.NIFTY_SYMBOLS = config._load_symbols()
        
        return config
    
    @staticmethod
    def _apply_env_overrides(config: Config):
        """Apply environment variable overrides"""
        # Get all config fields
        config_fields = {f.name for f in fields(config)}
        
        for key, value in os.environ.items():
            # Check if it's a config override (STOCK_* prefix)
            if key.startswith('STOCK_'):
                config_key = key[6:]  # Remove 'STOCK_' prefix
                if config_key in config_fields:
                    # Convert value to appropriate type
                    original_value = getattr(config, config_key)
                    if isinstance(original_value, bool):
                        setattr(config, config_key, value.lower() in ('true', '1', 'yes'))
                    elif isinstance(original_value, int):
                        setattr(config, config_key, int(value))
                    elif isinstance(original_value, float):
                        setattr(config, config_key, float(value))
                    else:
                        setattr(config, config_key, value)
    
    @staticmethod
    def get_profile_names() -> list:
        """Get list of available preset profiles"""
        return list(ConfigManager.PRESET_PROFILES.keys())
    
    @staticmethod
    def show_profiles():
        """Display available profiles"""
        print("📋 Available Configuration Profiles:")
        print("=" * 70)
        for name, settings in ConfigManager.PRESET_PROFILES.items():
            print(f"\n{name.upper()}:")
            for key, value in settings.items():
                print(f"  • {key}: {value}")
        print()

