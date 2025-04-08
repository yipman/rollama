import sys
import re
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
        
        try:
            if stream:
                # Try to use the streaming version if available
                if hasattr(client, 'run_stream') or hasattr(client, 'chat_stream'):
                    # Choose the appropriate streaming method
                    stream_method = client.run_stream if hasattr(client, 'run_stream') else client.chat_stream
                    response = stream_method(model_name, prompt)
                    
                    # Improved handling of streaming chunks to prevent overwriting
                    accumulated_text = ""  # Track what we've output so far
                    last_chunk = ""  # Track the last chunk for spacing logic
                    
                    for chunk in response:
                        piece = chunk.get('response', chunk.get('content', ''))
                        if not piece:
                            continue
                            
                        # Remove any potential control characters that could cause overwriting
                        piece = re.sub(r'[\r\b\x1b\[\d*[A-Za-z]]', '', piece)
                        
                        # Better spacing handling
                        if piece and piece[0].isalnum() and accumulated_text and accumulated_text[-1].isalnum():
                            # If this piece starts with a letter/number and the previous ended with one,
                            # we need a space to avoid words running together
                            sys.stdout.write(" ")
                            accumulated_text += " "
                        
                        # Write the cleaned piece
                        sys.stdout.write(piece)
                        sys.stdout.flush()
                        
                        # Update our tracking variables
                        accumulated_text += piece
                        last_chunk = piece
                        
                    # End the output with a newline
                    sys.stdout.write('\n')
                    sys.stdout.flush()
                    return None
                else:
                    # No streaming method available, fallback to non-streaming
                    print("\nWarning: Streaming not supported. Falling back to standard mode.")
                    stream = False
            
            # Non-streaming methods
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
            return f"Error running model: {str(e)}"
    
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
