import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from .config import Config
from .model_manager import ModelManager

class CodeManager:
    def __init__(self):
        self.workspace_dir = Path.home() / ".rollama" / "code_workspaces"
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
                with open(state_file, "r") as f:
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
        with open(state_file, "w") as f:
            json.dump(state, f)

    def create_workspace(self, name):
        """Create a new workspace"""
        workspace_path = self.workspace_dir / name
        if workspace_path.exists():
            raise ValueError(f"Workspace '{name}' already exists")
        workspace_path.mkdir()
        self.current_workspace = workspace_path
        self._save_workspace_state()
        return f"Created workspace: {name}"

    def list_workspaces(self):
        """List all workspaces"""
        workspaces = []
        for item in self.workspace_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                is_current = self.current_workspace and item.samefile(self.current_workspace)
                workspaces.append(f"{item.name} {'(current)' if is_current else ''}")
        return workspaces if workspaces else ["No workspaces found"]

    def switch_workspace(self, name):
        """Switch to a different workspace"""
        workspace_path = self.workspace_dir / name
        if not workspace_path.exists():
            raise ValueError(f"Workspace '{name}' does not exist")
        self.current_workspace = workspace_path
        self._save_workspace_state()
        return f"Switched to workspace: {name}"

    def delete_workspace(self, name):
        """Delete a workspace"""
        workspace_path = self.workspace_dir / name
        if not workspace_path.exists():
            raise ValueError(f"Workspace '{name}' does not exist")
        if self.current_workspace and workspace_path.samefile(self.current_workspace):
            self.current_workspace = None
        shutil.rmtree(workspace_path)
        self._save_workspace_state()
        return f"Deleted workspace: {name}"

    def list_files(self, path="."):
        """List files in the current workspace"""
        if not self.current_workspace:
            raise ValueError("No workspace selected")
        
        target_path = self.current_workspace / path
        if not target_path.exists():
            raise ValueError(f"Path '{path}' does not exist")
            
        files = []
        try:
            for item in target_path.iterdir():
                item_type = "📁 " if item.is_dir() else "📄 "
                files.append(f"{item_type}{item.relative_to(self.current_workspace)}")
        except Exception as e:
            raise ValueError(f"Error listing files: {str(e)}")
            
        return sorted(files) if files else ["Directory is empty"]

    def create_file(self, path, content=""):
        """Create a new file in the current workspace"""
        if not self.current_workspace:
            raise ValueError("No workspace selected")
            
        file_path = self.current_workspace / path
        if file_path.exists():
            raise ValueError(f"File '{path}' already exists")
            
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return f"Created file: {path}"

    def edit_file(self, path, content):
        """Edit a file in the current workspace"""
        if not self.current_workspace:
            raise ValueError("No workspace selected")
            
        file_path = self.current_workspace / path
        if not file_path.exists():
            raise ValueError(f"File '{path}' does not exist")
            
        file_path.write_text(content)
        return f"Updated file: {path}"

    def read_file(self, path):
        """Read a file from the current workspace"""
        if not self.current_workspace:
            raise ValueError("No workspace selected")
            
        file_path = self.current_workspace / path
        if not file_path.exists():
            raise ValueError(f"File '{path}' does not exist")
            
        return file_path.read_text()

    def delete_file(self, path):
        """Delete a file from the current workspace"""
        if not self.current_workspace:
            raise ValueError("No workspace selected")
            
        file_path = self.current_workspace / path
        if not file_path.exists():
            raise ValueError(f"File '{path}' does not exist")
            
        if file_path.is_dir():
            shutil.rmtree(file_path)
        else:
            file_path.unlink()
        return f"Deleted: {path}"

    def create_directory(self, path):
        """Create a new directory in the current workspace"""
        if not self.current_workspace:
            raise ValueError("No workspace selected")
            
        dir_path = self.current_workspace / path
        if dir_path.exists():
            raise ValueError(f"Directory '{path}' already exists")
            
        dir_path.mkdir(parents=True)
        return f"Created directory: {path}"

    def rename(self, old_path, new_path):
        """Rename a file or directory in the current workspace"""
        if not self.current_workspace:
            raise ValueError("No workspace selected")
            
        old_path = self.current_workspace / old_path
        new_path = self.current_workspace / new_path
        
        if not old_path.exists():
            raise ValueError(f"Path '{old_path}' does not exist")
        if new_path.exists():
            raise ValueError(f"Path '{new_path}' already exists")
            
        old_path.rename(new_path)
        return f"Renamed: {old_path.name} -> {new_path.name}"

    def execute_ai_command(self, prompt):
        """Execute an AI command using the current model"""
        if not self.current_workspace:
            raise ValueError("No workspace selected")
            
        # Add workspace context to the prompt
        files = self.list_files()
        workspace_context = f"""
Current workspace: {self.current_workspace.name}
Files in workspace:
{chr(10).join(files)}

User request: {prompt}

You are a coding assistant. The user wants you to help with their code. You can:
1. Generate new code files
2. Edit existing files
3. Create/rename/delete folders
4. Analyze code and suggest improvements
5. Answer questions about the code

Current workspace files are shown above. Respond with clear explanations and include any code changes needed.
"""
        
        model = self.config.get_default_model()
        response = self.model_manager.run_model(model, workspace_context)
        
        # If the response mentions file operations, execute them
        self._process_ai_response(response)
        
        return response

    def _process_ai_response(self, response):
        """Process file operations mentioned in the AI response"""
        # Look for special markers that indicate file operations
        lines = response.split('\n')
        current_file = None
        content_buffer = []
        
        for line in lines:
            if line.startswith('CREATE FILE:'):
                # Flush any previous file operation
                if current_file and content_buffer:
                    self.create_file(current_file, '\n'.join(content_buffer))
                    content_buffer = []
                
                current_file = line.split(':', 1)[1].strip()
            elif line.startswith('EDIT FILE:'):
                # Flush any previous file operation
                if current_file and content_buffer:
                    self.create_file(current_file, '\n'.join(content_buffer))
                    content_buffer = []
                    
                current_file = line.split(':', 1)[1].strip()
                if not Path(self.current_workspace / current_file).exists():
                    raise ValueError(f"File not found: {current_file}")
            elif line.startswith('DELETE FILE:'):
                path = line.split(':', 1)[1].strip()
                self.delete_file(path)
                current_file = None
            elif line.startswith('CREATE DIR:'):
                path = line.split(':', 1)[1].strip()
                self.create_directory(path)
                current_file = None
            elif current_file:
                content_buffer.append(line)
        
        # Flush any remaining file operation
        if current_file and content_buffer:
            if current_file.startswith('EDIT FILE:'):
                self.edit_file(current_file, '\n'.join(content_buffer))
            else:
                self.create_file(current_file, '\n'.join(content_buffer))