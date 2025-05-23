import sys
import argparse
import shutil
import textwrap
from pathlib import Path
from .code_manager import CodeManager

def main():
    parser = argparse.ArgumentParser(description="Rollama Code - Code Workspace Manager with AI capabilities")
    
    # Model and remote options
    parser.add_argument("--model", "-m", help="Model to use (defaults to config default_model)")
    parser.add_argument("--remote", "-r", help="Remote server name to use")
    
    args = parser.parse_args()
    
    code_manager = CodeManager()
    
    # Set model in config if specified
    if args.model:
        code_manager.config.set_default_model(args.model)
    
    # Set remote in config if specified
    if args.remote:
        if args.remote.lower() in ("none", "local"):
            code_manager.config.config["default_remote"] = None
        elif code_manager.config.get_remote(args.remote):
            code_manager.config.set_default_remote(args.remote)
        else:
            print(f"Error: Remote server '{args.remote}' not found")
            return 1

    def show_help():
        """Show help message with available commands"""
        help_text = """
        Rollama Code - Code Workspace Manager with AI capabilities
        
        Usage: rollama-code [--model MODEL] [--remote REMOTE]
        
        Optional Arguments:
        --model, -m MODEL    Model to use (defaults to config default_model)
        --remote, -r REMOTE  Remote server to use (use "local" for local Ollama)
        
        Available Commands:
        workspace
            create <name>       Create a new workspace
            list               List all workspaces
            switch <name>      Switch to a different workspace
            delete <name>      Delete a workspace
            
        file
            list [path]        List files in current directory or specified path
            create <path>      Create a new file
            edit <path>        Edit an existing file
            read <path>        Display file contents
            delete <path>      Delete a file or directory
            rename <old> <new> Rename a file or directory
            generate <path>    Generate a new file using AI
            
        directory
            create <path>      Create a new directory
            generate <path>    Generate a new project structure using AI

        code
            create <desc>      Create new code based on description
            edit <file> <desc> Edit existing file based on description
            analyze [path]     Analyze code and suggest improvements
            
        Any other input will be treated as a natural language request to the AI assistant.
        The assistant can help you:
        - Generate new code files
        - Edit existing files
        - Create/rename/delete folders
        - Analyze code and suggest improvements
        - Answer questions about your code
            
        help                   Show this help message
        exit                   Exit the program
        """
        print(textwrap.dedent(help_text))

    def handle_workspace_command(args):
        """Handle workspace-related commands"""
        if not args:
            print("Error: No workspace command specified")
            return
            
        cmd = args[0]
        try:
            if cmd == "create" and len(args) > 1:
                print(code_manager.create_workspace(args[1]))
            elif cmd == "list":
                for workspace in code_manager.list_workspaces():
                    print(workspace)
            elif cmd == "switch" and len(args) > 1:
                print(code_manager.switch_workspace(args[1]))
            elif cmd == "delete" and len(args) > 1:
                print(code_manager.delete_workspace(args[1]))
            else:
                print(f"Error: Invalid workspace command: {cmd}")
        except Exception as e:
            print(f"Error: {str(e)}")

    def handle_file_command(args):
        """Handle file-related commands"""
        if not args:
            print("Error: No file command specified")
            return
            
        cmd = args[0]
        try:
            if cmd == "list":
                path = args[1] if len(args) > 1 else "."
                for item in code_manager.list_files(path):
                    print(item)
            elif cmd == "create" and len(args) > 1:
                path = args[1]
                print("Enter file content (press Ctrl+D or Ctrl+Z when done):")
                content = sys.stdin.read()
                print(code_manager.create_file(path, content))
            elif cmd == "edit" and len(args) > 1:
                path = args[1]
                current = code_manager.read_file(path)
                print(f"Current content of {path}:")
                print("---")
                print(current)
                print("---")
                print("Enter new content (press Ctrl+D or Ctrl+Z when done):")
                content = sys.stdin.read()
                print(code_manager.edit_file(path, content))
            elif cmd == "generate" and len(args) > 1:
                path = args[1]
                description = " ".join(args[2:]) if len(args) > 2 else f"Generate content for {path}"
                ai_prompt = f"Generate content for file {path}. {description}"
                handle_ai_command(ai_prompt)
            elif cmd == "read" and len(args) > 1:
                print(code_manager.read_file(args[1]))
            elif cmd == "delete" and len(args) > 1:
                print(code_manager.delete_file(args[1]))
            elif cmd == "rename" and len(args) > 2:
                print(code_manager.rename(args[1], args[2]))
            else:
                print(f"Error: Invalid file command: {cmd}")
        except Exception as e:
            print(f"Error: {str(e)}")

    def handle_directory_command(args):
        """Handle directory-related commands"""
        if not args:
            print("Error: No directory command specified")
            return
            
        cmd = args[0]
        try:
            if cmd == "create" and len(args) > 1:
                print(code_manager.create_directory(args[1]))
            elif cmd == "generate" and len(args) > 1:
                path = args[1]
                description = " ".join(args[2:]) if len(args) > 2 else f"Generate project structure in {path}"
                ai_prompt = f"Generate a project structure in directory {path}. {description}"
                handle_ai_command(ai_prompt)
            else:
                print(f"Error: Invalid directory command: {cmd}")
        except Exception as e:
            print(f"Error: {str(e)}")

    def handle_code_command(args):
        """Handle code-related commands"""
        if not args:
            print("Error: No code command specified")
            return

        cmd = args[0]
        try:
            if cmd == "create" and len(args) > 1:
                description = " ".join(args[1:])
                ai_prompt = f"Create new code based on this description: {description}"
                handle_ai_command(ai_prompt)
            elif cmd == "edit" and len(args) > 2:
                file_path = args[1]
                description = " ".join(args[2:])
                
                # Read current content to provide context
                try:
                    current_content = code_manager.read_file(file_path)
                    ai_prompt = f"Edit the following file ({file_path}) according to this description: {description}\n\nCurrent content:\n{current_content}"
                except:
                    ai_prompt = f"Edit file {file_path} according to this description: {description}"
                
                handle_ai_command(ai_prompt)
            elif cmd == "analyze":
                path = args[1] if len(args) > 1 else "."
                files = code_manager.list_files(path)
                file_contents = []
                
                for file in files:
                    try:
                        content = code_manager.read_file(file)
                        file_contents.append(f"\n=== {file} ===\n{content}")
                    except:
                        continue
                
                if file_contents:
                    ai_prompt = f"Analyze the following code and suggest improvements:\n{''.join(file_contents)}"
                    handle_ai_command(ai_prompt)
                else:
                    print("No files found to analyze")
            else:
                print(f"Error: Invalid code command: {cmd}")
        except Exception as e:
            print(f"Error: {str(e)}")

    def handle_ai_command(command):
        """Handle natural language commands using AI"""
        try:
            print("\nProcessing request with AI assistant...")
            response = code_manager.execute_ai_command(command)
            print("\nAI Assistant Response:")
            print("----------------------")
            print(response)
            print("----------------------")
            
            # Check if any files were modified
            if "CREATE FILE:" in response or "EDIT FILE:" in response or "CREATE DIR:" in response:
                print("\nFiles have been updated. Use 'file list' to see the current workspace contents.")
        except Exception as e:
            print(f"Error: {str(e)}")

    def interactive_mode():
        """Run in interactive mode"""
        show_help()
        while True:
            try:
                if code_manager.current_workspace:
                    workspace_name = code_manager.current_workspace.name
                    prompt = f"\n[{workspace_name}]> "
                else:
                    prompt = "\n[no workspace]> "
                    
                command = input(prompt).strip()
                if not command:
                    continue
                    
                parts = command.split()
                cmd = parts[0].lower()
                args = parts[1:]
                
                if cmd == "exit":
                    break
                elif cmd == "help":
                    show_help()
                elif cmd == "workspace":
                    handle_workspace_command(args)
                elif cmd == "file":
                    handle_file_command(args)
                elif cmd == "directory":
                    handle_directory_command(args)
                elif cmd == "code":
                    handle_code_command(args)
                else:
                    # Any other input is treated as a natural language request
                    handle_ai_command(command)
                    
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except EOFError:
                break
            except Exception as e:
                print(f"Error: {str(e)}")

    # Run in interactive mode
    try:
        interactive_mode()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())