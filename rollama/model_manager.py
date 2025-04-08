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
            try:
                # Try different client API patterns
                response = client.completion(
                    model=model_name,
                    prompt=prompt,
                    stream=True,
                )
                
                for chunk in response:
                    if 'response' in chunk:
                        response_piece = chunk['response']
                        full_response += response_piece
                        sys.stdout.write(response_piece)
                        sys.stdout.flush()
                    elif 'content' in chunk:  # Alternative API format
                        response_piece = chunk['content']
                        full_response += response_piece
                        sys.stdout.write(response_piece)
                        sys.stdout.flush()
                
                sys.stdout.write('\n')
                return None
                
            except (AttributeError, TypeError) as e:
                # Fallback to non-streaming if streaming fails
                print(f"\nWarning: Streaming not supported ({str(e)}). Falling back to standard mode.")
                stream = False
                
        if not stream:
            # Return the full response at once
            try:
                response = client.completion(
                    model=model_name,
                    prompt=prompt,
                )
                
                if isinstance(response, dict):
                    return response.get('response', '')
                else:
                    return str(response)
                    
            except AttributeError:
                # Try alternative API pattern
                try:
                    response = client.generate(
                        model_name=model_name,
                        prompt=prompt,
                    )
                    if isinstance(response, dict):
                        return response.get('response', '')
                    else:
                        return str(response)
                except Exception as e:
                    return f"Error: {str(e)}"
    
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
