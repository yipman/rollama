import json
import requests
import subprocess
import re
import time
import shlex

class ApiClient:
    def __init__(self, remote=None):
        """
        Initialize the API client
        
        Args:
            remote (dict): Remote server details (url, api_key)
        """
        self.remote = remote

    def run_local_model(self, model, prompt):
        """
        Run a query against a local Ollama model
        
        Args:
            model (str): Model name
            prompt (str): Prompt to send to the model
            
        Returns:
            str: Model response
        """
        try:
            # Use subprocess to call local Ollama
            result = subprocess.run(
                ["ollama", "run", model, prompt],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error running local model: {e.stderr}"
        except FileNotFoundError:
            return "Error: Ollama not found. Make sure it's installed and in your PATH."

    def run_remote_model(self, model, prompt):
        """
        Run a query against a remote Ollama server
        
        Args:
            model (str): Model name
            prompt (str): Prompt to send to the model
            
        Returns:
            str: Model response
        """
        if not self.remote:
            return "Error: No remote server configured"
            
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            if self.remote.get("api_key"):
                headers["Authorization"] = f"Bearer {self.remote['api_key']}"
                
            # Using OpenAI API compatible format
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False
            }
            
            response = requests.post(
                f"{self.remote['url']}/v1/chat/completions", 
                headers=headers,
                json=payload,
                timeout=12000
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"Error: API returned status code {response.status_code}: {response.text}"
                
        except requests.exceptions.RequestException as e:
            return f"Error connecting to remote server: {str(e)}"
    
    def run_stream(self, model, prompt):
        """
        Run a query against an Ollama model with streaming output
        
        Args:
            model (str): Model name
            prompt (str): Prompt to send to the model
            
        Yields:
            dict: Response chunks with 'response' key containing text
        """
        if self.remote:
            yield from self._run_remote_stream(model, prompt)
        else:
            yield from self._run_local_stream(model, prompt)
    
    def _run_local_stream(self, model, prompt):
        """Stream responses from local Ollama model"""
        try:
            # Use a more reliable approach with the JSON format and different flags
            cmd = ["ollama", "run", model, "--format", "json"]
            
            # Start the process with pipes
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )
            
            # Send the prompt and close stdin
            process.stdin.write(prompt + "\n")
            process.stdin.flush()
            process.stdin.close()
            
            # Accumulated response for handling potentially problematic streaming
            last_chunk = ""
            
            # Read output line by line as it becomes available
            for line in process.stdout:
                if not line.strip():
                    continue
                    
                # Try to parse as JSON first (newer Ollama versions)
                try:
                    data = json.loads(line)
                    if 'response' in data:
                        content = data['response']
                        if content:  # Only yield non-empty responses
                            yield {"response": content}
                    elif 'done' in data and data['done']:
                        # End of generation, don't output anything for this marker
                        continue
                except json.JSONDecodeError:
                    # If not JSON, clean the text thoroughly
                    
                    # Replace any common control sequences
                    clean_text = re.sub(r'\x1b\[[0-9;]*[mKHJ]', '', line)  # ANSI escape sequences
                    clean_text = re.sub(r'\[DONE\]|\[END\]|\r', '', clean_text)  # Status markers and carriage returns
                    clean_text = re.sub(r'^\s+', '', clean_text)  # Leading whitespace
                    
                    # Only output if we have actual content
                    if clean_text.strip():
                        # If the text might be a continuation (no space at start and last chunk didn't end with space)
                        if not clean_text[0].isspace() and last_chunk and not last_chunk[-1].isspace():
                            # Ensure we're not accidentally joining words
                            yield {"response": " " + clean_text.strip()}
                        else:
                            yield {"response": clean_text.strip()}
                        
                    # Remember this chunk for context
                    last_chunk = clean_text
            
            # Check if there was an error
            process.wait()
            if process.returncode != 0:
                stderr_output = process.stderr.read()
                if stderr_output:
                    yield {"response": f"\nError: {stderr_output.strip()}"}
                
        except FileNotFoundError:
            yield {"response": "Error: Ollama not found. Make sure it's installed and in your PATH."}
        except Exception as e:
            yield {"response": f"Error streaming from local model: {str(e)}"}
    
    def _run_remote_stream(self, model, prompt):
        """Stream responses from remote Ollama server"""
        if not self.remote:
            yield {"response": "Error: No remote server configured"}
            return
            
        try:
            # Send a newline first to ensure clean transition after spinner
            yield {"response": "\n"}
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"  
            }
            
            if self.remote.get("api_key"):
                headers["Authorization"] = f"Bearer {self.remote['api_key']}"
            
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": True
            }
            
            # Initialize response tracking
            last_chunk = ""
            buffer = ""
            
            # Remove position tracking since we're handling newlines differently
            with requests.post(
                f"{self.remote['url']}/v1/chat/completions",
                headers=headers,
                json=payload,
                stream=True,
                timeout=12000
            ) as response:
                
                if response.status_code != 200:
                    error_text = response.text
                    try:
                        # Try to parse JSON error response
                        error_data = response.json()
                        if "error" in error_data:
                            error_text = error_data["error"].get("message", error_text)
                    except:
                        pass
                    yield {"response": f"\nError: API returned status code {response.status_code}: {error_text}"}
                    return
                
                # Process the streamed response
                for line in response.iter_lines():
                    if not line:
                        continue
                        
                    line = line.decode('utf-8')
                    
                    # Handle different SSE formats
                    if line.startswith('data:'):
                        line = line[5:].strip()  # Remove 'data:' prefix and whitespace
                        
                    # Skip keep-alive messages and empty lines
                    if line.strip() == '' or line == '[DONE]':
                        continue
                        
                    try:
                        # Parse JSON data
                        data = json.loads(line)
                        
                        # Handle completion - OpenAI compatible format
                        if 'choices' in data and len(data['choices']) > 0:
                            choice = data['choices'][0]
                            
                            # Check if this is a completion message
                            if choice.get('finish_reason') or choice.get('finish_details'):
                                continue
                                
                            # Extract the content
                            if 'delta' in choice:  # Streaming format
                                delta = choice['delta']
                                content = delta.get('content', '')
                            elif 'message' in choice:  # Full message format
                                content = choice['message'].get('content', '')
                            else:
                                # Try direct response format
                                content = data.get('response', '')
                                
                            if content:  # Only yield non-empty responses
                                # More aggressive cleaning of control characters
                                # Remove all ANSI escape sequences, backspaces, carriage returns, etc.
                                clean_content = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', content)  # ANSI escape sequences
                                clean_content = re.sub(r'[\r\b]', '', clean_content)  # Carriage returns and backspaces
                                
                                # Debug check for special characters that might cause overwriting
                                has_control_chars = bool(re.search(r'[\x00-\x1F\x7F]', clean_content))
                                
                                if has_control_chars:
                                    # If there are still control chars, convert to hex for inspection
                                    clean_content = ''.join(c if ord(c) >= 32 else '' for c in clean_content)
                                
                                # Handle spacing between chunks intelligently
                                if (not clean_content[0].isspace() and last_chunk and 
                                    not last_chunk[-1].isspace() and not last_chunk[-1] in '.!?,:;'):
                                    # Need a space between chunks
                                    yield {"response": " " + clean_content}
                                else:
                                    yield {"response": clean_content}
                                
                                last_chunk = clean_content
                                
                    except json.JSONDecodeError:
                        # Not valid JSON, might be raw text response
                        # Clean up any control characters
                        clean_text = line.strip()
                        clean_text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', clean_text)  # ANSI escape sequences
                        clean_text = re.sub(r'[\r\b]', '', clean_text)  # Carriage returns and backspaces
                        clean_text = re.sub(r'\[DONE\]|\[END\]', '', clean_text)  # Remove status markers
                        
                        if clean_text:
                            # Check if this is a continuation of a word
                            if (not clean_text[0].isspace() and buffer and
                                not buffer[-1].isspace() and not buffer[-1] in '.!?,:;'):
                                # Add a space to separate
                                yield {"response": " " + clean_text}
                            else:
                                yield {"response": clean_text}
                            
                            buffer += clean_text
                            
                    except Exception as e:
                        # Log the error but continue processing
                        yield {"response": f"\nWarning: Error parsing response chunk: {str(e)}"}
                
                # If we have content in the buffer after processing all chunks, ensure we end cleanly
                if buffer:
                    yield {"response": "\n"}
                        
        except requests.exceptions.RequestException as e:
            # More detailed error information
            error_msg = f"Error connecting to remote server: {str(e)}"
            if "Connection refused" in str(e):
                error_msg += "\nThe server may be down or the URL might be incorrect."
            elif "Timeout" in str(e):
                error_msg += "\nThe server took too long to respond."
            yield {"response": f"\n{error_msg}"}
        except Exception as e:
            yield {"response": f"\nError in streaming: {str(e)}"}
    
    def chat_stream(self, model, prompt):
        """Alias for run_stream to maintain API compatibility"""
        return self.run_stream(model, prompt)
    
    def list_local_models(self):
        """
        List models available locally
        
        Returns:
            list: List of available models
        """
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse the output to get model names
            lines = result.stdout.strip().split("\n")[1:]  # Skip header line
            models = []
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if parts:
                        models.append(parts[0])
            
            return models
            
        except subprocess.CalledProcessError as e:
            print(f"Error listing local models: {e.stderr}")
            return []
        except FileNotFoundError:
            print("Error: Ollama not found. Make sure it's installed and in your PATH.")
            return []
    
    def list_remote_models(self):
        """
        List models available on the remote server
        
        Returns:
            list: List of available models
        """
        if not self.remote:
            return []
            
        try:
            headers = {}
            if self.remote.get("api_key"):
                headers["Authorization"] = f"Bearer {self.remote['api_key']}"
                
            response = requests.get(
                f"{self.remote['url']}/v1/models", 
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return [model["id"] for model in result.get("data", [])]
            else:
                print(f"Error: API returned status code {response.status_code}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to remote server: {str(e)}")
            return []
