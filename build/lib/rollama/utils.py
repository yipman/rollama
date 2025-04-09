import os
import readline
import atexit
import sys

def setup_history():
    """Set up command history for interactive mode"""
    histfile = os.path.join(os.path.expanduser("~"), ".rollama_history")
    try:
        readline.read_history_file(histfile)
        readline.set_history_length(1000)
    except FileNotFoundError:
        pass
    
    atexit.register(readline.write_history_file, histfile)

def interactive_mode(model_manager, model_name, remote=None):
    """Run the model in interactive mode with streaming support."""
    setup_history()
    
    print(f"Starting interactive session with {model_name}. Type 'exit' or 'quit' to end the session.")
    
    while True:
        try:
            user_input = input("\n> ")
            if user_input.lower() in ['exit', 'quit']:
                break
                
            model_manager.run_model(model_name, user_input, remote=remote, stream=True)
                
        except KeyboardInterrupt:
            print("\nExiting interactive mode.")
            break
        except Exception as e:
            print(f"Error: {str(e)}")
