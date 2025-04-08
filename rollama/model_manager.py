import sys
from .api_client import ApiClient

class ModelManager:
    """Manages interactions with Ollama models, both local and remote."""
    
    def __init__(self, config):
        """
        Initialize the model manager
        
        Args:
            config (Config): Configuration object
        """
        self.config = config
    
    def _get_client(self, remote=None):
        """
        Get the API client based on remote configuration
        
        Args:
            remote (str, optional): Remote server name to use
            
        Returns:
            ApiClient: API client instance
        """
        remote_config = None
        if remote:
            remote_config = self.config.get_remote(remote)
            if not remote_config:
                raise ValueError(f"Error: Remote server '{remote}' not found")
        elif self.config.get_remote():
            remote_config = self.config.get_remote()
        
        return ApiClient(remote_config)
    
    def run_model(self, model_name, prompt, remote=None, stream=True):
        """
        Run a model with the given prompt.
        
        Args:
            model_name (str): Name of the model to run
            prompt (str): Prompt to send to the model
            remote (str, optional): Remote server to use
            stream (bool, optional): Whether to stream the response. Defaults to True.
            
        Returns:
            If stream=True: None (prints directly to console)
            If stream=False: str containing full response
        """
        # Get the client for the specified remote or default
        client = self._get_client(remote)
        
        if stream:
            # Stream the response directly to console
            full_response = ""
            for chunk in client.generate(model_name, prompt):
                response_piece = chunk.get('response', '')
                full_response += response_piece
                sys.stdout.write(response_piece)
                sys.stdout.flush()
            sys.stdout.write('\n')
            return None
        else:
            # Return the full response at once
            response = client.generate_sync(model_name, prompt)
            return response.get('response', '')
    
    def list_models(self, remote=None):
        """
        List available models
        
        Args:
            remote (str, optional): Remote server name to list models from
            
        Returns:
            list: Available models
        """
        client = self._get_client(remote)
        
        if client.remote_config:
            models = client.list_remote_models()
            source = f"Remote ({remote or 'default'})"
        else:
            models = client.list_local_models()
            source = "Local"
            
        if not models:
            return [f"No models found on {source}"]
            
        return [f"{model} ({source})" for model in models]
