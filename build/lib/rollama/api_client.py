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
            cmd = ["ollama", "run", model, "--format", "json"]
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            process.stdin.write(prompt + "\n")
            process.stdin.flush()
            process.stdin.close()
            
            for line in process.stdout:
                if not line.strip():
                    continue
                    
                try:
                    data = json.loads(line)
                    if 'response' in data:
                        content = data['response']
                        if content:
                            yield {"response": content}
                except json.JSONDecodeError:
                    clean_text = re.sub(r'^\s+', '', line)
                    if clean_text.strip():
                        yield {"response": clean_text.strip()}
            
            process.wait()
            if process.returncode != 0:
                stderr = process.stderr.read()
                if stderr:
                    yield {"response": f"\nError: {stderr.strip()}"}
                    
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
            
            with requests.post(
                f"{self.remote['url']}/v1/chat/completions",
                headers=headers,
                json=payload,
                stream=True,
                timeout=12000
            ) as response:
                if response.status_code != 200:
                    yield {"response": f"\nError: API returned status code {response.status_code}"}
                    return
                
                for line in response.iter_lines():
                    if not line:
                        continue
                        
                    line = line.decode('utf-8')
                    if line.startswith('data:'):
                        line = line[5:].strip()
                    if line == '[DONE]':
                        continue
                        
                    try:
                        data = json.loads(line)
                        if 'choices' in data and len(data['choices']) > 0:
                            choice = data['choices'][0]
                            content = ''
                            if 'delta' in choice:
                                content = choice['delta'].get('content', '')
                            elif 'message' in choice:
                                content = choice['message'].get('content', '')
                            else:
                                content = data.get('response', '')
                                
                            if content:
                                yield {"response": content}
                    except:
                        if line.strip():
                            yield {"response": line.strip()}
                        
        except Exception as e:
            yield {"response": f"Error: {str(e)}"}
    
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
