import json
import requests
import subprocess

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
