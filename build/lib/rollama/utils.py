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
    print("Type 'clear history' to reset conversation memory.")
    
    # Initialize conversation history - list of (speaker, message) tuples
    chat_history = []
    
    while True:
        try:
            # Use standard prompt without tags for user display
            user_input = input("\n> ")
            
            # Handle special commands
            if user_input.lower() in ['exit', 'quit']:
                break
            elif user_input.lower() == 'clear history':
                chat_history = []
                print("Conversation history cleared.")
                continue
            
            # Add user input to history with tag
            chat_history.append(("user", user_input))
            
            # Create context with conversation history
            if len(chat_history) > 1:
                # Format conversation history for context
                context = "Chat history:\n"
                for speaker, message in chat_history:
                    # Use clear role tags for the model, but not visible to user
                    role_tag = "[USER]" if speaker == "user" else "[ASSISTANT]"
                    context += f"{role_tag}: {message}\n"
                # Add a prompt for the assistant to continue
                context += "[ASSISTANT]: "
                prompt = context
            else:
                # First interaction
                prompt = f"[USER]: {user_input}\n[ASSISTANT]: "
            
            # Run model with streaming and capture response in a single call
            response = model_manager.run_model(model_name, prompt, remote=remote, stream=True)
            
            # Store response in history if available
            if response:
                chat_history.append(("assistant", response))
            else:
                # Fallback if response is None (e.g., due to error)
                print("\nWarning: Could not capture response for history")
                chat_history.append(("assistant", "(Response not captured)"))
                
        except KeyboardInterrupt:
            print("\nExiting interactive mode.")
            break
        except Exception as e:
            print(f"Error: {str(e)}")
