import os
import json
from pathlib import Path

class Config:
    def __init__(self):
        self.config_dir = Path.home() / ".rollama"
        self.config_file = self.config_dir / "config.json"
        self._ensure_config_exists()
        self.config = self._load_config()
    
    def _ensure_config_exists(self):
        """Create config directory and files if they don't exist"""
        self.config_dir.mkdir(exist_ok=True)
        
        if not self.config_file.exists():
            default_config = {
                "remotes": {},
                "default_remote": None,
                "default_model": "llama2",
                "font_family": "Courier",
                "font_size": 10
            }
            
            with open(self.config_file, "w") as f:
                json.dump(default_config, f, indent=2)
    
    def _load_config(self):
        """Load the configuration from file"""
        with open(self.config_file, "r") as f:
            return json.load(f)
    
    def _save_config(self):
        """Save the configuration to file"""
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=2)
    
    def add_remote(self, name, url, api_key=None):
        """Add a remote server to the configuration"""
        self.config.setdefault("remotes", {})
        self.config["remotes"][name] = {
            "url": url,
            "api_key": api_key
        }
        self._save_config()
    
    def remove_remote(self, name):
        """Remove a remote server from the configuration"""
        if name in self.config.get("remotes", {}):
            del self.config["remotes"][name]
            if self.config.get("default_remote") == name:
                self.config["default_remote"] = None
            self._save_config()
    
    def list_remotes(self):
        """Get a dictionary of remote servers"""
        return {name: remote["url"] for name, remote in self.config.get("remotes", {}).items()}
    
    def get_remote(self, name=None):
        """Get the details for a specific remote server"""
        if name is None:
            name = self.config.get("default_remote")
            if name is None:
                return None
                
        return self.config.get("remotes", {}).get(name)
    
    def set_default_remote(self, name):
        """Set the default remote server"""
        if name in self.config.get("remotes", {}):
            self.config["default_remote"] = name
            self._save_config()
    
    def get_default_model(self):
        """Get the default model to use"""
        return self.config.get("default_model", "llama2")
    
    def set_default_model(self, model):
        """Set the default model to use"""
        self.config["default_model"] = model
        self._save_config()
