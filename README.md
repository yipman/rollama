# Rollama

Rollama is a Python application similar to Ollama but with the ability to connect to remote Ollama servers using OpenAI API compatible interfaces.

## Features

- Run local Ollama models
- Connect to remote Ollama servers
- Manage multiple remote server connections
- Compatible with OpenAI API format
- Interactive chat mode
- GUI interface with terminal emulation and file/image attachments

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/rollama.git
cd rollama

# Install the package
pip install -e .
```

## Usage

### CLI Version

```bash
# Run a local model with a prompt
rollama run llama2 "What is machine learning?"

# Run a model on a remote server
rollama run llama2 "What is machine learning?" --remote my-server

# Start an interactive chat session
rollama run llama2 --interactive
```

### GUI Version

Launch the GUI version with:

```bash
rollama-gui
```

The GUI provides a terminal-like interface with additional features:

- File and image attachments
- Settings configuration window
- Remote server management
- Model switching
- Conversation saving

#### GUI Commands

Within the GUI terminal, you can use these commands:

- `help` - Display available commands
- `clear` - Clear the terminal
- `list models` - Show available models
- `switch model <name>` - Change the active model
- `switch remote <name>` - Change remote server
- `show attachments` - List currently attached files/images
- `clear attachments` - Remove all attachments
- `exit` or `quit` - Close the application

You can also access most features through the menu bar at the top of the window.

### Managing remote servers

```bash
# Add a new remote server
rollama remote add my-server http://example.com:11434 --api-key your-api-key

# Add a new remote server and set as default
rollama remote add my-server http://example.com:11434 --default

# List remote servers
rollama remote list

# Remove a remote server
rollama remote remove my-server

# Set a server as default
rollama remote default my-server
```

### Listing models

```bash
# List local models
rollama list

# List models on a remote server
rollama list --remote my-server
```

## Architecture

Rollama consists of:
1. A configuration manager for storing remote server information
2. An API client for managing connections to local and remote Ollama instances
3. A model manager to handle operations on models
4. A CLI interface for user interaction
5. An interactive mode for chat sessions
6. A GUI interface built with Tkinter

## License

MIT
