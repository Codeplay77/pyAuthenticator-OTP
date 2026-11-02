"""
Configuration Management Module for Python Authenticator

Handles all application settings including:
- Global hotkey configurations
- UI preferences (position, theme, etc.)
- System tray behavior
- Auto-update settings

Configuration is stored in JSON format for easy editing and portability.

Author: Codeplay
Date: June 2025
"""

import os
import sys
import json
from typing import Any, Dict, Optional


class ConfigManager:
    """Manage application configuration settings.
    
    Provides a centralized interface for reading and writing application
    configuration. Settings are persisted in a JSON file located in the
    application directory.
    
    Configuration Categories:
        - hotkeys: Global keyboard shortcuts
        - ui: Window position, theme, and behavior
        - tray: System tray icon settings
        - update: Token refresh and update settings
    
    Attributes:
        config_file (str): Full path to config.json
        config (Dict): Loaded configuration dictionary
        
    File Location:
        - Frozen app: Same directory as executable
        - Script: Same directory as Python script
    """
    
    def __init__(self) -> None:
        """Initialize configuration manager and load settings."""
        self.config_file = self.get_config_path()
        self.config = self.load_config()
    
    def get_config_path(self) -> str:
        """Determine configuration file path.
        
        Returns path based on execution context:
        - PyInstaller frozen: Directory containing executable
        - Python script: Directory containing script file
        
        Returns:
            str: Absolute path to config.json
        """
        if getattr(sys, 'frozen', False):
            config_dir = os.path.dirname(sys.executable)
        else:
            config_dir = os.path.dirname(os.path.abspath(__file__))
        
        return os.path.join(config_dir, 'config.json')
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values.
        
        Returns:
            Dict containing default settings for all categories.
            
        Default Settings:
            hotkeys:
                - toggle_window: Ctrl+Shift+A (show/hide app)
                - add_account: Ctrl+Shift+N (add new account)
            ui:
                - theme: "system" (follows Windows; "light" or "dark" to force)
                - window_position: "right" (screen edge)
                - margin: 20 (pixels from screen edge)
                - always_on_top: False
            tray:
                - enabled: True (show system tray icon)
                - hide_on_close: True (minimize to tray on close)
            update:
                - auto_refresh: True (update tokens automatically)
                - refresh_interval: 1 (second)
        """
        return {
            "hotkeys": {
                "toggle_window": "ctrl+shift+a",
                "add_account": "ctrl+shift+n"
            },
            "ui": {
                "theme": "system",
                "window_position": "right",
                "margin": 20,
                "always_on_top": False,
                "custom_x": 100,
                "custom_y": 100
            },
            "tray": {
                "enabled": True,
                "hide_on_close": True,
                "tooltip": "Python Authenticator"
            },
            "update": {
                "auto_refresh": True,
                "refresh_interval": 1,
                "show_progress_bar": True
            }
        }
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file.
        
        Attempts to load existing config.json. If file doesn't exist or
        is invalid, creates a new file with default values.
        
        User settings are merged with defaults to ensure all required
        keys exist (handles config file from older versions).
        
        Returns:
            Dict: Complete configuration with all required keys
            
        Error Handling:
            - Missing file: Creates default config
            - Invalid JSON: Uses default config and logs error
            - Permission error: Uses default config and logs warning
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                default = self.get_default_config()
                self.merge_config(default, config)
                return default
            else:
                config = self.get_default_config()
                self.save_config(config)
                return config
        except Exception as e:
            print(f"Erro ao carregar config: {e}")
            return self.get_default_config()
    
    def merge_config(self, default, user):
        """Merge configuração do usuário com padrões"""
        for key, value in user.items():
            if key in default:
                if isinstance(value, dict) and isinstance(default[key], dict):
                    self.merge_config(default[key], value)
                else:
                    default[key] = value
    
    def save_config(self, config: Optional[Dict] = None) -> bool:
        """Save configuration to JSON file.
        
        Args:
            config: Configuration dict to save (uses self.config if None)
            
        Returns:
            bool: True if save successful, False otherwise
            
        File Format:
            JSON with 2-space indentation, UTF-8 encoding
            
        Error Handling:
            Returns False and logs error if save fails due to:
            - Permission issues
            - Disk full
            - Invalid JSON (shouldn't happen with dict input)
        """
        try:
            config_to_save = config or self.config
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar config: {e}")
            return False
    
    def get(self, path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation path.
        
        Args:
            path: Dot-separated path (e.g., 'ui.window_position')
            default: Value to return if path doesn't exist
            
        Returns:
            Configuration value or default if path not found
            
        Examples:
            >>> config.get('hotkeys.toggle_window')
            'ctrl+shift+a'
            >>> config.get('ui.margin')
            20
            >>> config.get('nonexistent.key', 'fallback')
            'fallback'
        """
        keys = path.split('.')
        value = self.config
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, path: str, value: Any) -> None:
        """Set configuration value using dot notation path.
        
        Creates intermediate dictionaries if they don't exist.
        Automatically saves configuration after update.
        
        Args:
            path: Dot-separated path (e.g., 'ui.window_position')
            value: Value to set (any JSON-serializable type)
            
        Examples:
            >>> config.set('ui.margin', 30)
            >>> config.set('hotkeys.toggle_window', 'ctrl+alt+a')
        """
        keys = path.split('.')
        config = self.config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
        self.save_config()
    
    def get_hotkeys(self):
        """Retorna configuração de atalhos"""
        return self.config.get('hotkeys', {})
    
    def get_ui_config(self):
        """Retorna configuração de UI"""
        return self.config.get('ui', {})
    
    def get_tray_config(self):
        """Retorna configuração do system tray"""
        return self.config.get('tray', {})
    
    def get_update_config(self):
        """Retorna configuração de atualização"""
        return self.config.get('update', {})