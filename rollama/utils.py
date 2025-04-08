import os
import readline
import atexit

def setup_history():
    """Set up command history for interactive mode"""
    histfile = os.path.join(os.path.expanduser("~"), ".rollama_history")
    try:
        readline.read_history_file(histfile)
        readline.set_history_length(1000)
    except FileNotFoundError:
        pass
    
    atexit.register(readline.write_history_file, histfile)

def interactive_mode(model_manager, model, remote=None):
    """
    Start an interactive chat session with the model
    
    Args:
        model_manager (ModelManager): Model manager instance
        model (str): Model to use
        remote (str, optional): Remote server to use
    """
    setup_history()
    
    print(f"Starting chat with model: {model}")
    print("Type 'exit', 'quit', or press Ctrl+D to exit")
    
    history = []
    
    while True:
        try:
            prompt = input("\n> ")
            if prompt.lower() in ("exit", "quit"):
                break
                
            response = model_manager.run_model(model, prompt, remote)
            print("\n" + response)
            
            # Save history for context
            history.append((prompt, response))
            
        except EOFError:
            print("\nExiting...")
            break
        except KeyboardInterrupt:
            print("\nOperation cancelled")
            continue
