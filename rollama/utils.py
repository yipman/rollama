import os
import readline
import atexit
import sys
import time
import threading
import itertools

def setup_history():
    """Set up command history for interactive mode"""
    histfile = os.path.join(os.path.expanduser("~"), ".rollama_history")
    try:
        readline.read_history_file(histfile)
        readline.set_history_length(1000)
    except FileNotFoundError:
        pass
    
    atexit.register(readline.write_history_file, histfile)

class SpinnerAnimation:
    """Displays a spinning animation in the terminal while a process is running."""
    
    def __init__(self, message=None):
        self.message = message
        self.spinner_chars = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
        self.running = False
        self.spinner_thread = None
    
    def _animate(self):
        while self.running:
            if self.message:
                sys.stdout.write(f"\r{next(self.spinner_chars)} {self.message}")
            else:
                sys.stdout.write(f"\r{next(self.spinner_chars)}")
            sys.stdout.flush()
            time.sleep(0.1)
            
    def __enter__(self):
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        # The spinner is now stopped, but the model_manager will handle 
        # printing the newline and starting the response on a clean line
    
    def start(self):
        self.running = True
        if self.message:
            sys.stdout.write(f"\r{next(self.spinner_chars)} {self.message}")
        else:
            sys.stdout.write(f"\r{next(self.spinner_chars)}")
        sys.stdout.flush()
        self.spinner_thread = threading.Thread(target=self._animate)
        self.spinner_thread.daemon = True
        self.spinner_thread.start()
    
    def stop(self):
        self.running = False
        if self.spinner_thread:
            self.spinner_thread.join(0.2)
        
        # Clear the spinner completely
        msg_length = len(self.message) + 2 if self.message else 2
        sys.stdout.write("\r" + " " * msg_length + "\r")
        sys.stdout.flush()
        # Note: We're NOT adding a newline here, as model_manager will handle the transition

def interactive_mode(model_manager, model_name, remote=None):
    """Run the model in interactive mode with streaming support."""
    setup_history()
    
    print(f"Starting interactive session with {model_name}. Type 'exit' or 'quit' to end the session.")
    
    while True:
        try:
            user_input = input("\n> ")
            if user_input.lower() in ['exit', 'quit']:
                break
                
            # Use spinner without text
            with SpinnerAnimation():
                # The model_manager will now handle transitioning from spinner to response
                model_manager.run_model(model_name, user_input, remote=remote, stream=True)
                
        except KeyboardInterrupt:
            print("\nExiting interactive mode.")
            break
        except Exception as e:
            print(f"Error: {str(e)}")
