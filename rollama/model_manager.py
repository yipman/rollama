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
        # Get the client for the specified remote or default
        client = self._get_client(remote)
        
        try:
            if stream:
                # Try to use the streaming version if available
                if hasattr(client, 'run_stream'):
                    response = client.run_stream(model_name, prompt)
                    
                    # Extra safety measure: add a small delay and ensure a clean start 
                    # This allows spinner animation to fully clear
                    time.sleep(0.1)  # Short delay to ensure spinner has stopped
                    
                    for chunk in response:
                        piece = chunk.get('response', chunk.get('content', ''))
                        # Ensure no control characters remain
                        piece = re.sub(r'[\r\b\x1b\[\d*[A-Za-z]]', '', piece)
                        sys.stdout.write(piece)
                        sys.stdout.flush()
                    sys.stdout.write('\n')
                    return None
                    
                elif hasattr(client, 'chat_stream'):
                    response = client.chat_stream(model_name, prompt)
                    
                    # Extra safety measure: add a small delay and ensure a clean start 
                    time.sleep(0.1)  # Short delay to ensure spinner has stopped
                    
                    for chunk in response:
                        piece = chunk.get('response', chunk.get('content', ''))
                        # Ensure no control characters remain
                        piece = re.sub(r'[\r\b\x1b\[\d*[A-Za-z]]', '', piece)
                        sys.stdout.write(piece)
                        sys.stdout.flush()
                    sys.stdout.write('\n')
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
    
    def _process_streaming_response(self, response_iterator):
        """
        Process and display streaming response safely with proper formatting
        
        Args:
            response_iterator: Iterator yielding response chunks
        """
        full_text = ""
        last_chunk = ""
        
        for chunk in response_iterator:
            piece = chunk.get('response', chunk.get('content', ''))
            if not piece:
                continue
                
            # Clean any control characters that might cause overwriting
            clean_piece = re.sub(r'\r', '', piece)  # Remove carriage returns
            clean_piece = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', clean_piece)  # Remove ANSI escape codes
            
            # Add space between words if needed
            if (clean_piece and clean_piece[0].isalnum() and 
                full_text and full_text[-1].isalnum()):
                sys.stdout.write(' ')
                sys.stdout.flush()
                full_text += ' '
            
            sys.stdout.write(clean_piece)
            sys.stdout.flush()
            full_text += clean_piece
            last_chunk = clean_piece
            
        # Add final newline for cleaner output
        sys.stdout.write('\n')
        sys.stdout.flush()
        
        return None
    
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
