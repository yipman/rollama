import os
import shutil
import json
import sys

try:
    from pathlib import Path
except ImportError:
    # Python 2 fallback
    class Path(object):
        def __init__(self, *args):
            self.path = os.path.join(*args)
        
        def __truediv__(self, other):
            return Path(self.path, str(other))
        
        def mkdir(self, parents=False, exist_ok=False):
            try:
                if parents:
                    os.makedirs(self.path)
                else:
                    os.mkdir(self.path)
            except OSError:
                if not exist_ok:
                    raise
        
        def exists(self):
            return os.path.exists(self.path)
        
        def is_dir(self):
            return os.path.isdir(self.path)
        
        def iterdir(self):
            for item in os.listdir(self.path):
                yield Path(self.path, item)
        
        def relative_to(self, other):
            return os.path.relpath(self.path, str(other))
        
        def samefile(self, other):
            return os.path.samefile(self.path, str(other))
        
        def write_text(self, content):
            with open(self.path, 'w') as f:
                f.write(content)
        
        def read_text(self):
            with open(self.path, 'r') as f:
                return f.read()
        
        def unlink(self):
            os.unlink(self.path)
        
        def rename(self, target):
            os.rename(self.path, str(target))
        
        @property
        def name(self):
            return os.path.basename(self.path)
        
        def __str__(self):
            return self.path

from .config import Config
from .model_manager import ModelManager

class CodeManager:
    def __init__(self):
        self.workspace_dir = Path(os.path.expanduser("~")) / ".rollama" / "code_workspaces"
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.current_workspace = None
        self.config = Config()
        self.model_manager = ModelManager(self.config)
        self._load_workspace_state()

    def _load_workspace_state(self):
        """Load the last active workspace if it exists"""
        state_file = self.workspace_dir / "state.json"
        if state_file.exists():
            try:
                with open(str(state_file), "r") as f:
                    state = json.load(f)
                    last_workspace = state.get("last_workspace")
                    if last_workspace and (self.workspace_dir / last_workspace).exists():
                        self.current_workspace = self.workspace_dir / last_workspace
            except:
                pass

    def _save_workspace_state(self):
        """Save the current workspace state"""
        state_file = self.workspace_dir / "state.json"
        state = {
            "last_workspace": str(self.current_workspace.relative_to(self.workspace_dir))
            if self.current_workspace else None
        }
        with open(str(state_file), "w") as f:
            json.dump(state, f)

    def create_workspace(self, name):
        """Create a new workspace"""
        workspace_path = self.workspace_dir / name
        if workspace_path.exists():
            raise ValueError("Workspace '{}' already exists".format(name))
        workspace_path.mkdir()
        self.current_workspace = workspace_path
        self._save_workspace_state()
        return "Created workspace: {}".format(name)

    def list_workspaces(self):
        """List all workspaces"""
        workspaces = []
        for item in self.workspace_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                is_current = self.current_workspace and item.samefile(self.current_workspace)
                workspaces.append("{} {}".format(item.name, "(current)" if is_current else ""))
        return workspaces if workspaces else ["No workspaces found"]

    def switch_workspace(self, name):
        """Switch to a different workspace"""
        workspace_path = self.workspace_dir / name
        if not workspace_path.exists():
            raise ValueError("Workspace '{}' does not exist".format(name))
        self.current_workspace = workspace_path
        self._save_workspace_state()
        return "Switched to workspace: {}".format(name)

    def delete_workspace(self, name):
        """Delete a workspace"""
        workspace_path = self.workspace_dir / name
        if not workspace_path.exists():
            raise ValueError("Workspace '{}' does not exist".format(name))
        if self.current_workspace and workspace_path.samefile(self.current_workspace):
            self.current_workspace = None
        shutil.rmtree(str(workspace_path))
        self._save_workspace_state()
        return "Deleted workspace: {}".format(name)

    def list_files(self, path="."):
        """List files in the current workspace"""
        if not self.current_workspace:
            raise ValueError("No workspace selected")
        
        target_path = self.current_workspace / path
        if not target_path.exists():
            raise ValueError("Path '{}' does not exist".format(path))
            
        files = []
        try:
            for item in target_path.iterdir():
                item_type = "📁 " if item.is_dir() else "📄 "
                files.append("{}{}".format(item_type, item.relative_to(self.current_workspace)))
        except Exception as e:
            raise ValueError("Error listing files: {}".format(str(e)))
            
        return sorted(files) if files else ["Directory is empty"]

    def create_file(self, path, content=""):
        """Create a new file in the current workspace"""
        if not self.current_workspace:
            raise ValueError("No workspace selected")
            
        file_path = self.current_workspace / path
        if file_path.exists():
            raise ValueError("File '{}' already exists".format(path))
            
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return "Created file: {}".format(path)

    def edit_file(self, path, content):
        """Edit a file in the current workspace"""
        if not self.current_workspace:
            raise ValueError("No workspace selected")
            
        file_path = self.current_workspace / path
        if not file_path.exists():
            raise ValueError("File '{}' does not exist".format(path))
            
        file_path.write_text(content)
        return "Updated file: {}".format(path)

    def read_file(self, path):
        """Read a file from the current workspace"""
        if not self.current_workspace:
            raise ValueError("No workspace selected")
            
        file_path = self.current_workspace / path
        if not file_path.exists():
            raise ValueError("File '{}' does not exist".format(path))
            
        return file_path.read_text()

    def delete_file(self, path):
        """Delete a file from the current workspace"""
        if not self.current_workspace:
            raise ValueError("No workspace selected")
            
        file_path = self.current_workspace / path
        if not file_path.exists():
            raise ValueError("File '{}' does not exist".format(path))
            
        if file_path.is_dir():
            shutil.rmtree(str(file_path))
        else:
            file_path.unlink()
        return "Deleted: {}".format(path)

    def create_directory(self, path):
        """Create a new directory in the current workspace"""
        if not self.current_workspace:
            raise ValueError("No workspace selected")
            
        dir_path = self.current_workspace / path
        if dir_path.exists():
            raise ValueError("Directory '{}' already exists".format(path))
            
        dir_path.mkdir(parents=True)
        return "Created directory: {}".format(path)

    def rename(self, old_path, new_path):
        """Rename a file or directory in the current workspace"""
        if not self.current_workspace:
            raise ValueError("No workspace selected")
            
        old_path = self.current_workspace / old_path
        new_path = self.current_workspace / new_path
        
        if not old_path.exists():
            raise ValueError("Path '{}' does not exist".format(old_path))
        if new_path.exists():
            raise ValueError("Path '{}' already exists".format(new_path))
            
        old_path.rename(new_path)
        return "Renamed: {} -> {}".format(old_path.name, new_path.name)

    def execute_ai_command(self, command):
        """Execute a natural language command using AI"""
        # Create system prompt that encourages direct responses
        system_prompt = "You are a helpful assistant. Provide direct responses to questions without analyzing message history or making observations about the conversation. Focus solely on answering the current question."
        
        try:
            # Get response from AI model
            response = self.model_manager.get_completion(
                system_prompt,
                command
            )
            return response
        except Exception as e:
            raise Exception(f"Failed to execute AI command: {str(e)}")