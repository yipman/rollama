import sys
import re
import time
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
        client = self._get_client(remote)
        
        try:
            if stream:
                stream_method = getattr(client, 'run_stream', None) or getattr(client, 'chat_stream')
                if stream_method:
                    sys.stdout.write('\n')  # Start on new line
                    sys.stdout.flush()
                    
                    response_stream = stream_method(model_name, prompt)
                    last_chunk = ""
                    
                    for chunk in response_stream:
                        piece = chunk.get('response', chunk.get('content', ''))
                        if piece:
                            # Add space between words if needed
                            if piece[0].isalnum() and last_chunk and last_chunk[-1].isalnum():
                                sys.stdout.write(' ')
                            sys.stdout.write(piece)
                            sys.stdout.flush()
                            last_chunk = piece
                            
                    sys.stdout.write('\n')
                    sys.stdout.flush()
                    return None
                else:
                    print("\nWarning: Streaming not supported. Falling back to standard mode.")
                    stream = False
            
            # Non-streaming mode
            if not stream:
                # Try common method names for the Ollama API
                if hasattr(client, 'run'):
                    response = client.run(model_name, prompt)
                elif hasattr(client, 'chat'):
                    response = client.chat(model_name, prompt)
                elif hasattr(client, 'generate_text'):
                    response = client.generate_text(model_name, prompt)
                else:
                    # Last resort: Try calling the client directly if it's callable
                    response = client(model_name, prompt)
                
                # Handle different response formats
                if isinstance(response, dict):
                    return response.get('response', response.get('content', str(response)))
                elif isinstance(response, str):
                    return response
                else:
                    return str(response)
                    
        except Exception as e:
            error_msg = f"Error running model: {str(e)}"
            if stream:
                print(f"\n{error_msg}")
                return None
            return error_msg
    
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
