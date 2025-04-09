<div align="center">

# 🦙 Rollama

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![GitHub stars](https://img.shields.io/github/stars/yipman/rollama?style=social)](https://github.com/yipman/rollama/stargazers)

**Run Ollama models locally or connect to remote servers with ease**

[Features](#features) • 
[Installation](#installation) • 
[Usage](#usage) • 
[Configuration](#configuration) • 
[Contributing](#contributing)

</div>

---

## 🌟 Features

- **Local Model Support**: Run Ollama models on your local machine
- **Remote Connectivity**: Connect seamlessly to remote Ollama servers
- **Server Management**: Easily manage multiple remote server connections
- **API Compatibility**: Works with OpenAI API compatible interfaces
- **Interactive Experience**: Enjoy a responsive chat mode with history
- **Modern GUI**: Use the graphical interface with terminal emulation
- **Code Management**: Smart code generation and workspace management
- **Real-time Code Creation**: Watch your code being written in real-time
- **File Support**: Attach and process files and images in conversations
- **Customization**: Personalize settings to your workflow
- **Cross-Platform**: Works on macOS, Linux, and Windows

## 📦 Installation

### From PyPI (Recommended)

```bash
pip install rollama
```

### From Source

```bash
# Clone the repository
git clone https://github.com/yipman/rollama.git
cd rollama

# Install the package
pip install -e .
```

## 🚀 Usage

### CLI Version

```bash
# Run a local model with a prompt
rollama run llama2 "What is machine learning?"

# Run a model on a remote server
rollama run llama2 "What is machine learning?" --remote my-server

# Start an interactive chat session
rollama run llama2 --interactive

# Run with specific parameters
rollama run llama2 --temperature 0.7 --top-p 0.9 "Generate creative ideas"
```

### Code Management

Rollama includes a powerful code management system that helps you create and manage code projects:

```bash
# Start the code management interface
rollama-code

# Create a new workspace
rollama-code workspace create my-project

# List workspaces
rollama-code workspace list

# Switch to a workspace
rollama-code workspace switch my-project
```

#### Code Generation Features

The code management system includes:

- **Real-time Code Generation**: Watch as code is generated word by word
- **Smart File Operations**: Automatically creates, edits, and manages files
- **Project Understanding**: AI assistant understands your project context
- **Multi-file Support**: Handle complex projects across multiple files
- **Code Analysis**: Get intelligent suggestions and improvements
- **Language Support**: Works with multiple programming languages
- **Interactive Development**: Ask questions and get instant code solutions

Example commands in the code interface:

Command | Description
------- | -----------
`create <project>` | Create a new coding project
`edit <file>` | Edit an existing file
`analyze` | Get code analysis and suggestions
`help` | Show available commands
`exit` | Exit the code interface

### GUI Version

Launch the intuitive graphical interface with:

```bash
rollama-gui
```

<div align="center">
<i>GUI screenshot coming soon</i>
</div>

#### GUI Features

- **Terminal-Like Interface**: Familiar command experience
- **File Attachments**: Drag & drop files and images
- **Visual Settings**: Configure parameters through intuitive controls
- **Server Management**: Connect to different servers without command line
- **Model Switching**: Change models with a single click
- **Conversation History**: Save and load previous chats
- **Export Options**: Save conversations in multiple formats

#### GUI Commands

Within the GUI terminal, you can use these commands:

Command | Description
------- | -----------
`help` | Display available commands
`clear` | Clear the terminal
`list models` | Show available models
`switch model <name>` | Change the active model
`switch remote <name>` | Change remote server
`show attachments` | List currently attached files/images
`clear attachments` | Remove all attachments
`settings` | Open settings window
`save` | Save current conversation
`exit` or `quit` | Close the application

You can also access most features through the menu bar at the top of the window.

## ⚙️ Configuration

### Managing Remote Servers

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

### Working with Models

```bash
# List local models
rollama list

# List models on a remote server
rollama list --remote my-server

# Pull a model from Ollama repository
rollama pull llama2

# Get model information
rollama info llama2
```

### Advanced Configuration

Edit the configuration file located at `~/.config/rollama/config.yaml` to:
- Set global default parameters
- Configure API keys
- Customize model behavior
- Set networking options

## 🔧 Architecture

Rollama is built with a modular architecture:

1. **Configuration Manager**: Securely stores remote server information
2. **API Client**: Manages connections to local and remote Ollama instances
3. **Model Manager**: Handles operations on models for consistent performance
4. **Code Manager**: Provides intelligent code generation and management
5. **Command Interface**: Provides intuitive CLI interaction
6. **Interactive Mode**: Enables responsive chat sessions
7. **GUI Layer**: Delivers a modern user interface with Tkinter

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

<div align="center">
Made with ❤️ by <a href="https://github.com/yipman">yipman</a>
</div>
