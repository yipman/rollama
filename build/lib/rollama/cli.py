import argparse
import sys
from .config import Config
from .model_manager import ModelManager
from .utils import interactive_mode

def main():
    parser = argparse.ArgumentParser(description="Rollama - Ollama with remote capabilities")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run a model")
    run_parser.add_argument("model", help="Model to run")
    run_parser.add_argument("prompt", nargs="?", help="Prompt to send to the model")
    run_parser.add_argument("--remote", "-r", help="Remote server name to use")
    run_parser.add_argument("--interactive", "-i", action="store_true", help="Start interactive mode")
    run_parser.add_argument("--no-stream", action="store_true", help="Disable response streaming")
    
    # List models command
    list_parser = subparsers.add_parser("list", help="List available models")
    list_parser.add_argument("--remote", "-r", help="Remote server name to show models from")
    
    # Add remote server
    remote_parser = subparsers.add_parser("remote", help="Manage remote servers")
    remote_subparsers = remote_parser.add_subparsers(dest="remote_command")
    
    add_parser = remote_subparsers.add_parser("add", help="Add a remote server")
    add_parser.add_argument("name", help="Name for the remote server")
    add_parser.add_argument("url", help="URL of the remote Ollama server")
    add_parser.add_argument("--api-key", help="API key for the remote server (if needed)")
    add_parser.add_argument("--default", "-d", action="store_true", help="Set as default remote")
    
    remove_parser = remote_subparsers.add_parser("remove", help="Remove a remote server")
    remove_parser.add_argument("name", help="Name of the remote server")
    
    list_remote_parser = remote_subparsers.add_parser("list", help="List remote servers")
    
    default_parser = remote_subparsers.add_parser("default", help="Set default remote server")
    default_parser.add_argument("name", help="Name of the remote server")
    
    args = parser.parse_args()
    
    config = Config()
    model_manager = ModelManager(config)
    
    if not args.command:
        parser.print_help()
        return 1
        
    if args.command == "run":
        if not args.model:
            run_parser.print_help()
            return 1
            
        if args.interactive:
            interactive_mode(model_manager, args.model, args.remote)
        elif args.prompt:
            response = model_manager.run_model(
                args.model, 
                args.prompt, 
                remote=args.remote,
                stream=not args.no_stream
            )
            
            if not args.no_stream:
                # For streaming mode, run_model will handle printing
                pass
            else:
                # For non-streaming mode, print the full response
                print(response)
        else:
            run_parser.print_help()
            return 1
            
    elif args.command == "list":
        models = model_manager.list_models(remote=args.remote)
        for model in models:
            print(model)
            
    elif args.command == "remote":
        if args.remote_command == "add":
            config.add_remote(args.name, args.url, args.api_key)
            print(f"Added remote server '{args.name}'")
            
            if args.default:
                config.set_default_remote(args.name)
                print(f"Set '{args.name}' as default remote server")
                
        elif args.remote_command == "remove":
            config.remove_remote(args.name)
            print(f"Removed remote server '{args.name}'")
            
        elif args.remote_command == "list":
            remotes = config.list_remotes()
            default_remote = config.get_remote()
            
            if remotes:
                print("Available remote servers:")
                for name, url in remotes.items():
                    is_default = " (default)" if default_remote and name == config.config.get("default_remote") else ""
                    print(f"  {name}: {url}{is_default}")
            else:
                print("No remote servers configured")
                
        elif args.remote_command == "default":
            config.set_default_remote(args.name)
            print(f"Set '{args.name}' as default remote server")
            
        else:
            remote_parser.print_help()
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
