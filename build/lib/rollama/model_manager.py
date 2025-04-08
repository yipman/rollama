from .api_client import ApiClient

class ModelManager:
    def __init__(self, config):
        """
        Initialize the model manager
        
        Args:
            config (Config): Configuration object
        """
        self.config = config
    
    def run_model(self, model, prompt, remote=None):
        """
        Run a prompt against a model
        
        Args:
            model (str): Model name to use
            prompt (str): Prompt to send to the model
            remote (str, optional): Remote server name to use
            
        Returns:
            str: Model response
        """
        # Get remote configuration if specified
        remote_config = None
        if remote:
            remote_config = self.config.get_remote(remote)
            if not remote_config:
                return f"Error: Remote server '{remote}' not found"
        elif self.config.get_remote():
            # Use default remote if configured
            remote_config = self.config.get_remote()
            
        # Create API client based on whether we're using remote or local
        client = ApiClient(remote_config)
        
        if remote_config:
            return client.run_remote_model(model, prompt)
        else:
            return client.run_local_model(model, prompt)
    
    def list_models(self, remote=None):
        """
        List available models
        
        Args:
            remote (str, optional): Remote server name to list models from
            
        Returns:
            list: Available models
        """
        # Get remote configuration if specified
        remote_config = None
        if remote:
            remote_config = self.config.get_remote(remote)
            if not remote_config:
                return [f"Error: Remote server '{remote}' not found"]
        elif self.config.get_remote():
            # Use default remote if configured
            remote_config = self.config.get_remote()
            
        # Create API client based on whether we're using remote or local
        client = ApiClient(remote_config)
        
        if remote_config:
            models = client.list_remote_models()
            source = f"Remote ({remote or 'default'})"
        else:
            models = client.list_local_models()
            source = "Local"
            
        if not models:
            return [f"No models found on {source}"]
            
        return [f"{model} ({source})" for model in models]
