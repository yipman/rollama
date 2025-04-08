import tkinter as tk
from tkinter import scrolledtext, filedialog, ttk, messagebox
from tkinter.font import Font, families
import os
import sys
import threading
import queue
import io
from PIL import Image, ImageTk
import base64

from .config import Config
from .model_manager import ModelManager
from .utils import setup_history

class RollamaTerminal(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        
        self.config = Config()
        self.model_manager = ModelManager(self.config)
        
        self.current_model = self.config.get_default_model()
        self.current_remote = None
        if self.config.get_remote():
            self.current_remote = self.config.config.get("default_remote")
        
        # Load font settings or use defaults
        self.font_family = self.config.config.get("font_family", "Courier")
        self.font_size = self.config.config.get("font_size", 10)
        
        self.create_widgets()
        self.create_menu()
        
        self.command_history = []
        self.history_index = 0
        
        # For file and image attachments
        self.attachments = []
        
        # Output queue for background processing
        self.output_queue = queue.Queue()
        self.check_output_queue()
        
        # Initial greeting
        self.terminal.insert(tk.END, f"Rollama Terminal - Connected to model: {self.current_model}\n")
        self.terminal.insert(tk.END, f"Remote server: {self.current_remote if self.current_remote else 'None (using local)'}\n")
        self.terminal.insert(tk.END, "Type 'help' for available commands.\n\n")
        self.show_prompt()
        
    def create_widgets(self):
        # Terminal output
        terminal_font = Font(family=self.font_family, size=self.font_size)
        self.terminal = scrolledtext.ScrolledText(self, wrap=tk.WORD, bg="black", fg="light green", 
                                                insertbackground="white", font=terminal_font)
        self.terminal.pack(fill=tk.BOTH, expand=True)
        self.terminal.bind("<Key>", self.handle_key)
        self.terminal.bind("<Return>", self.process_command)
        self.terminal.bind("<Up>", self.handle_up_key)
        self.terminal.bind("<Down>", self.handle_down_key)
        self.terminal.bind("<Tab>", self.handle_tab)
        
        # Bottom frame for input enhancements
        bottom_frame = tk.Frame(self)
        bottom_frame.pack(fill=tk.X, pady=5)
        
        # File attachment button
        self.attach_btn = tk.Button(bottom_frame, text="Attach File", command=self.attach_file)
        self.attach_btn.pack(side=tk.LEFT, padx=5)
        
        # Image attachment button
        self.image_btn = tk.Button(bottom_frame, text="Attach Image", command=self.attach_image)
        self.image_btn.pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set(f"Model: {self.current_model} | Server: {self.current_remote or 'Local'}")
        self.status_bar = tk.Label(self, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def create_menu(self):
        menu_bar = tk.Menu(self.parent)
        
        # File menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Clear Terminal", command=self.clear_terminal)
        file_menu.add_command(label="Save Conversation", command=self.save_conversation)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.parent.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)
        
        # Settings menu
        settings_menu = tk.Menu(menu_bar, tearoff=0)
        settings_menu.add_command(label="Configure", command=self.open_settings)
        settings_menu.add_command(label="Manage Remotes", command=self.open_remote_manager)
        menu_bar.add_cascade(label="Settings", menu=settings_menu)
        
        # Models menu
        models_menu = tk.Menu(menu_bar, tearoff=0)
        models_menu.add_command(label="List Models", command=self.list_models)
        models_menu.add_command(label="Switch Model", command=self.switch_model)
        menu_bar.add_cascade(label="Models", menu=models_menu)
        
        # Help menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="Commands", command=self.show_help)
        help_menu.add_command(label="About", command=self.show_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        
        self.parent.config(menu=menu_bar)
        
    def show_prompt(self):
        prompt_text = "> "
        self.terminal.insert(tk.END, prompt_text)
        self.prompt_start = self.terminal.index(tk.INSERT)
        
    def handle_key(self, event):
        # Prevent editing text before the prompt
        cursor_pos = self.terminal.index(tk.INSERT)
        if self.terminal.compare(cursor_pos, '<', self.prompt_start):
            self.terminal.mark_set(tk.INSERT, tk.END)
            return "break"
        return None
        
    def handle_up_key(self, event):
        if self.command_history and self.history_index > 0:
            self.history_index -= 1
            self.replace_current_input(self.command_history[self.history_index])
        return "break"
        
    def handle_down_key(self, event):
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.replace_current_input(self.command_history[self.history_index])
        elif self.history_index == len(self.command_history) - 1:
            self.history_index += 1
            self.replace_current_input("")
        return "break"
    
    def handle_tab(self, event):
        # Auto-completion could be implemented here
        return "break"
        
    def replace_current_input(self, new_text):
        self.terminal.delete(self.prompt_start, tk.END)
        self.terminal.insert(tk.END, new_text)
        
    def get_current_input(self):
        return self.terminal.get(self.prompt_start, tk.END).strip()
        
    def process_command(self, event=None):
        command = self.get_current_input()
        
        if not command:
            self.terminal.insert(tk.END, "\n")
            self.show_prompt()
            return "break"
            
        # Add to history
        if not self.command_history or command != self.command_history[-1]:
            self.command_history.append(command)
        self.history_index = len(self.command_history)
        
        self.terminal.insert(tk.END, "\n")
        
        # Special commands
        if command.lower() == "help":
            self.show_help_in_terminal()
        elif command.lower() == "clear":
            self.clear_terminal()
        elif command.lower() in ("exit", "quit"):
            self.parent.quit()
        elif command.lower() == "list models":
            self.list_models_in_terminal()
        elif command.lower().startswith("switch model "):
            model_name = command[13:].strip()
            self.current_model = model_name
            self.status_var.set(f"Model: {self.current_model} | Server: {self.current_remote or 'Local'}")
            self.terminal.insert(tk.END, f"Switched to model: {model_name}\n")
        elif command.lower().startswith("switch remote "):
            remote_name = command[14:].strip()
            if remote_name.lower() == "local" or remote_name.lower() == "none":
                self.current_remote = None
                self.terminal.insert(tk.END, "Switched to local Ollama\n")
            elif self.config.get_remote(remote_name):
                self.current_remote = remote_name
                self.terminal.insert(tk.END, f"Switched to remote: {remote_name}\n")
            else:
                self.terminal.insert(tk.END, f"Error: Remote '{remote_name}' not found\n")
            self.status_var.set(f"Model: {self.current_model} | Server: {self.current_remote or 'Local'}")
        elif command.lower() == "show attachments":
            self.show_attachments()
        elif command.lower() == "clear attachments":
            self.attachments = []
            self.terminal.insert(tk.END, "Attachments cleared\n")
        else:
            # Process as a model prompt
            self.terminal.insert(tk.END, f"Processing request with {self.current_model}...\n")
            
            # Prepare context with attachments
            context = command
            if self.attachments:
                attachment_info = "\n\nAttached files:\n"
                for i, (attachment_type, attachment_data, filename) in enumerate(self.attachments, 1):
                    attachment_info += f"{i}. {filename} ({attachment_type})\n"
                    
                    # For text files, include content
                    if attachment_type == "text":
                        attachment_info += f"\nContent of {filename}:\n{attachment_data}\n"
                
                context = attachment_info + "\n\n" + context
            
            # Run in a separate thread to avoid UI freezing
            threading.Thread(target=self.run_model_query, 
                             args=(self.current_model, context, self.current_remote)).start()
            
        if command.lower() not in ("clear", "exit", "quit"):
            # Don't show prompt for these commands
            self.show_prompt()
            
        return "break"
        
    def run_model_query(self, model, prompt, remote=None):
        try:
            response = self.model_manager.run_model(model, prompt, remote=remote)
            self.output_queue.put(("\n" + response + "\n\n", "response"))
        except Exception as e:
            self.output_queue.put(("\nError: " + str(e) + "\n\n", "error"))
            
    def check_output_queue(self):
        try:
            while True:
                message, msg_type = self.output_queue.get_nowait()
                if msg_type == "error":
                    self.terminal.insert(tk.END, message, "error")
                    # Configure tag for error text
                    self.terminal.tag_config("error", foreground="red")
                else:
                    self.terminal.insert(tk.END, message)
                self.terminal.see(tk.END)
                self.output_queue.task_done()
        except queue.Empty:
            pass
        finally:
            # Check again after 100ms
            self.after(100, self.check_output_queue)
            
    def show_help_in_terminal(self):
        help_text = """
Available Commands:
------------------
help                   - Show this help message
clear                  - Clear the terminal
exit, quit             - Exit the application
list models            - List available models
switch model <name>    - Switch to a different model
switch remote <name>   - Switch to a different remote server (use "local" for local Ollama)
show attachments       - Show current attachments
clear attachments      - Remove all attachments

Any other text will be sent as a prompt to the current model.
        """
        self.terminal.insert(tk.END, help_text)
        
    def list_models_in_terminal(self):
        self.terminal.insert(tk.END, "Fetching models, please wait...\n")
        
        # Run in separate thread to avoid UI freezing
        threading.Thread(target=self.fetch_models_thread).start()
        
    def fetch_models_thread(self):
        try:
            models = self.model_manager.list_models(remote=self.current_remote)
            model_text = "Available models:\n" + "\n".join(models) + "\n"
            self.output_queue.put((model_text, "normal"))
        except Exception as e:
            self.output_queue.put(("\nError fetching models: " + str(e) + "\n", "error"))
            
    def attach_file(self):
        file_path = filedialog.askopenfilename(
            title="Select File to Attach",
            filetypes=[("Text files", "*.txt"), ("Python files", "*.py"), 
                       ("Markdown files", "*.md"), ("JSON files", "*.json"),
                       ("All files", "*.*")]
        )
        
        if file_path:
            try:
                file_size = os.path.getsize(file_path)
                if file_size > 1024 * 1024:  # Limit to 1MB
                    messagebox.showerror("Error", "File too large (max 1MB)")
                    return
                    
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                filename = os.path.basename(file_path)
                self.attachments.append(("text", content, filename))
                
                self.terminal.insert(tk.END, f"\nAttached file: {filename}\n")
                self.show_prompt()
            except Exception as e:
                messagebox.showerror("Error", f"Could not read file: {str(e)}")
                
    def attach_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Image to Attach",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        
        if file_path:
            try:
                # Check file size
                file_size = os.path.getsize(file_path)
                if file_size > 5 * 1024 * 1024:  # Limit to 5MB
                    messagebox.showerror("Error", "Image too large (max 5MB)")
                    return
                    
                # Load and encode the image
                with open(file_path, 'rb') as f:
                    image_data = f.read()
                
                # Base64 encode for text representation
                encoded = base64.b64encode(image_data).decode('utf-8')
                
                filename = os.path.basename(file_path)
                self.attachments.append(("image", encoded, filename))
                
                # Display a thumbnail
                try:
                    img = Image.open(file_path)
                    img.thumbnail((200, 200))  # Resize for display
                    photo = ImageTk.PhotoImage(img)
                    
                    # Insert a mark and create a window at that mark
                    self.terminal.insert(tk.END, f"\nAttached image: {filename}\n")
                    img_label = tk.Label(self.terminal, image=photo)
                    img_label.image = photo  # Keep a reference
                    self.terminal.window_create(tk.END, window=img_label)
                    self.terminal.insert(tk.END, "\n")
                    self.show_prompt()
                except Exception as e:
                    self.terminal.insert(tk.END, f"\nAttached image: {filename} (thumbnail not available)\n")
                    self.show_prompt()
                    
            except Exception as e:
                messagebox.showerror("Error", f"Could not process image: {str(e)}")
                
    def show_attachments(self):
        if not self.attachments:
            self.terminal.insert(tk.END, "No attachments\n")
            return
            
        self.terminal.insert(tk.END, f"Attachments ({len(self.attachments)}):\n")
        for i, (attachment_type, _, filename) in enumerate(self.attachments, 1):
            self.terminal.insert(tk.END, f"{i}. {filename} ({attachment_type})\n")
            
    def clear_terminal(self):
        self.terminal.delete(1.0, tk.END)
        self.show_prompt()
        
    def save_conversation(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.terminal.get(1.0, tk.END))
                messagebox.showinfo("Success", "Conversation saved successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file: {str(e)}")
                
    def open_settings(self):
        settings_window = tk.Toplevel(self.parent)
        settings_window.title("Rollama Settings")
        settings_window.geometry("400x400")  # Increased height to accommodate new options
        settings_window.resizable(False, False)
        
        # Create a notebook for tabbed settings
        notebook = ttk.Notebook(settings_window)
        notebook.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        # General settings tab
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="General")
        
        # Default model setting
        tk.Label(general_frame, text="Default Model:").grid(row=0, column=0, sticky=tk.W, pady=5)
        default_model_entry = tk.Entry(general_frame, width=20)
        default_model_entry.grid(row=0, column=1, padx=5, pady=5)
        default_model_entry.insert(0, self.config.get_default_model())
        
        # Theme setting
        tk.Label(general_frame, text="Terminal Theme:").grid(row=1, column=0, sticky=tk.W, pady=5)
        theme_var = tk.StringVar(value="dark")
        theme_menu = ttk.Combobox(general_frame, textvariable=theme_var, state="readonly")
        theme_menu['values'] = ['Dark', 'Light', 'Matrix']
        theme_menu.grid(row=1, column=1, padx=5, pady=5)
        
        # Font settings
        tk.Label(general_frame, text="Font Family:").grid(row=2, column=0, sticky=tk.W, pady=5)
        font_family_var = tk.StringVar(value=self.font_family)
        font_family_menu = ttk.Combobox(general_frame, textvariable=font_family_var, state="readonly", width=18)
        # Get available monospace fonts
        available_fonts = sorted([f for f in families() if f.lower() in 
                                 ['courier', 'consolas', 'monaco', 'menlo', 'monospace', 
                                  'fixedsys', 'terminal', 'dejavu sans mono', 'liberation mono']])
        if not available_fonts:  # Fallback if no monospace fonts found
            available_fonts = sorted(families())
        font_family_menu['values'] = available_fonts
        font_family_menu.grid(row=2, column=1, padx=5, pady=5)
        
        tk.Label(general_frame, text="Font Size:").grid(row=3, column=0, sticky=tk.W, pady=5)
        font_size_var = tk.IntVar(value=self.font_size)
        font_size_spinbox = tk.Spinbox(general_frame, from_=8, to=24, width=5, textvariable=font_size_var)
        font_size_spinbox.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Preview label
        tk.Label(general_frame, text="Preview:").grid(row=4, column=0, sticky=tk.W, pady=5)
        preview_frame = tk.Frame(general_frame, bg="black", width=200, height=50)
        preview_frame.grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)
        preview_label = tk.Label(preview_frame, text="Aa Bb Cc 123", bg="black", fg="light green")
        preview_label.pack(expand=True, fill=tk.BOTH)
        
        # Update preview when font settings change
        def update_preview(*args):
            try:
                preview_font = Font(family=font_family_var.get(), size=font_size_var.get())
                preview_label.config(font=preview_font)
            except:
                pass  # Ignore font errors in preview
        
        font_family_menu.bind("<<ComboboxSelected>>", update_preview)
        font_size_spinbox.bind("<KeyRelease>", update_preview)
        
        # Save button
        save_btn = tk.Button(general_frame, text="Save Settings", 
                             command=lambda: self.save_settings(
                                 default_model_entry.get(), 
                                 theme_var.get(),
                                 font_family_var.get(),
                                 font_size_var.get()))
        save_btn.grid(row=5, column=0, columnspan=2, pady=20)
        
    def save_settings(self, default_model, theme, font_family, font_size):
        # Save default model
        if default_model:
            self.config.set_default_model(default_model)
        
        # Apply theme (could be expanded)
        if theme.lower() == "dark":
            self.terminal.config(bg="black", fg="light green")
        elif theme.lower() == "light":
            self.terminal.config(bg="white", fg="black")
        elif theme.lower() == "matrix":
            self.terminal.config(bg="black", fg="green")
            
        # Save and apply font settings
        try:
            # Update config values
            self.config.config["font_family"] = font_family
            self.config.config["font_size"] = int(font_size)
            self.config._save_config()
            
            # Store current values
            self.font_family = font_family
            self.font_size = int(font_size)
            
            # Apply new font
            new_font = Font(family=font_family, size=int(font_size))
            self.terminal.config(font=new_font)
            
            messagebox.showinfo("Settings", "Settings saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving font settings: {str(e)}")
        
    def open_remote_manager(self):
        remote_window = tk.Toplevel(self.parent)
        remote_window.title("Remote Server Manager")
        remote_window.geometry("500x400")
        
        # Create list of remotes
        frame = tk.Frame(remote_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Remotes list with scrollbar
        tk.Label(frame, text="Available Remote Servers:").pack(anchor=tk.W)
        list_frame = tk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        remote_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        remote_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=remote_listbox.yview)
        
        # Populate listbox
        remotes = self.config.list_remotes()
        default_remote = self.config.config.get("default_remote")
        
        for name, url in remotes.items():
            display_name = f"{name} - {url}"
            if name == default_remote:
                display_name += " (default)"
            remote_listbox.insert(tk.END, display_name)
        
        # Buttons frame
        button_frame = tk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        add_btn = tk.Button(button_frame, text="Add Remote", 
                           command=lambda: self.add_remote_dialog(remote_window, remote_listbox))
        add_btn.pack(side=tk.LEFT, padx=5)
        
        remove_btn = tk.Button(button_frame, text="Remove Selected", 
                              command=lambda: self.remove_remote(remote_listbox))
        remove_btn.pack(side=tk.LEFT, padx=5)
        
        set_default_btn = tk.Button(button_frame, text="Set as Default", 
                                   command=lambda: self.set_default_remote(remote_listbox))
        set_default_btn.pack(side=tk.LEFT, padx=5)
        
    def add_remote_dialog(self, parent_window, listbox):
        dialog = tk.Toplevel(parent_window)
        dialog.title("Add Remote Server")
        dialog.geometry("350x200")
        dialog.transient(parent_window)
        dialog.resizable(False, False)
        
        tk.Label(dialog, text="Remote Name:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        name_entry = tk.Entry(dialog, width=25)
        name_entry.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(dialog, text="Server URL:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        url_entry = tk.Entry(dialog, width=25)
        url_entry.grid(row=1, column=1, padx=10, pady=5)
        
        tk.Label(dialog, text="API Key (optional):").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        api_key_entry = tk.Entry(dialog, width=25)
        api_key_entry.grid(row=2, column=1, padx=10, pady=5)
        
        default_var = tk.BooleanVar()
        default_check = tk.Checkbutton(dialog, text="Set as default", variable=default_var)
        default_check.grid(row=3, column=0, columnspan=2, pady=5)
        
        def save_remote():
            name = name_entry.get().strip()
            url = url_entry.get().strip()
            api_key = api_key_entry.get().strip() or None
            
            if not name or not url:
                messagebox.showerror("Error", "Name and URL are required")
                return
                
            self.config.add_remote(name, url, api_key)
            
            if default_var.get():
                self.config.set_default_remote(name)
                
            # Refresh listbox
            listbox.delete(0, tk.END)
            remotes = self.config.list_remotes()
            default_remote = self.config.config.get("default_remote")
            
            for n, u in remotes.items():
                display_name = f"{n} - {u}"
                if n == default_remote:
                    display_name += " (default)"
                listbox.insert(tk.END, display_name)
                
            dialog.destroy()
            
        save_btn = tk.Button(dialog, text="Save", command=save_remote)
        save_btn.grid(row=4, column=0, columnspan=2, pady=15)
        
    def remove_remote(self, listbox):
        selection = listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "No remote server selected")
            return
            
        # Extract remote name from the list item
        remote_item = listbox.get(selection[0])
        remote_name = remote_item.split(" - ")[0]
        
        # Confirm deletion
        if messagebox.askyesno("Confirm", f"Are you sure you want to remove '{remote_name}'?"):
            self.config.remove_remote(remote_name)
            
            # Refresh listbox
            listbox.delete(0, tk.END)
            remotes = self.config.list_remotes()
            default_remote = self.config.config.get("default_remote")
            
            for name, url in remotes.items():
                display_name = f"{name} - {url}"
                if name == default_remote:
                    display_name += " (default)"
                listbox.insert(tk.END, display_name)
                
    def set_default_remote(self, listbox):
        selection = listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "No remote server selected")
            return
            
        # Extract remote name from the list item
        remote_item = listbox.get(selection[0])
        remote_name = remote_item.split(" - ")[0]
        
        self.config.set_default_remote(remote_name)
        
        # Refresh listbox to show the updated default
        listbox.delete(0, tk.END)
        remotes = self.config.list_remotes()
        default_remote = self.config.config.get("default_remote")
        
        for name, url in remotes.items():
            display_name = f"{name} - {url}"
            if name == default_remote:
                display_name += " (default)"
            listbox.insert(tk.END, display_name)
            
        # Update current remote
        self.current_remote = remote_name
        self.status_var.set(f"Model: {self.current_model} | Server: {self.current_remote or 'Local'}")
        
    def list_models(self):
        self.list_models_in_terminal()
        
    def switch_model(self):
        model_window = tk.Toplevel(self.parent)
        model_window.title("Switch Model")
        model_window.geometry("300x400")
        
        tk.Label(model_window, text="Available Models:").pack(anchor=tk.W, padx=10, pady=5)
        
        # Listbox with scrollbar
        list_frame = tk.Frame(model_window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        model_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        model_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=model_listbox.yview)
        
        # Status label
        status_label = tk.Label(model_window, text="Loading models...")
        status_label.pack(pady=5)
        
        def fetch_models_for_listbox():
            try:
                models = self.model_manager.list_models(remote=self.current_remote)
                
                # Update UI from main thread
                model_window.after(0, lambda: update_model_list(models))
                
            except Exception as e:
                model_window.after(0, lambda: status_label.config(
                    text=f"Error: {str(e)}", fg="red"))
                
        def update_model_list(models):
            model_listbox.delete(0, tk.END)
            for model in models:
                model_listbox.insert(tk.END, model)
            status_label.config(text=f"Found {len(models)} models")
            
        def select_model():
            selection = model_listbox.curselection()
            if not selection:
                messagebox.showerror("Error", "No model selected")
                return
                
            # Extract model name
            model_item = model_listbox.get(selection[0])
            model_name = model_item.split(" ")[0]  # Get just the model name part
            
            self.current_model = model_name
            self.status_var.set(f"Model: {self.current_model} | Server: {self.current_remote or 'Local'}")
            
            self.terminal.insert(tk.END, f"\nSwitched to model: {model_name}\n")
            model_window.destroy()
            
        # Start fetching models in background
        threading.Thread(target=fetch_models_for_listbox).start()
        
        # Select button
        select_btn = tk.Button(model_window, text="Select Model", command=select_model)
        select_btn.pack(pady=10)
        
    def show_about(self):
        about_text = """
Rollama GUI v0.1.0

A graphical interface for Rollama that provides:
- Terminal-like interaction with models
- File and image attachments
- Configuration management
- Remote server connections

Created with Python and Tkinter
        """
        messagebox.showinfo("About Rollama GUI", about_text)
        
    def show_help(self):
        self.show_help_in_terminal()

class RollamaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Rollama GUI")
        self.root.geometry("800x600")
        
        # Set icon if available
        try:
            # This is just a placeholder - you would need to create an icon
            self.root.iconbitmap("rollama.ico")
        except:
            pass
            
        # Terminal frame takes up the entire window
        self.terminal = RollamaTerminal(root)
        self.terminal.pack(fill=tk.BOTH, expand=True)

def main():
    root = tk.Tk()
    app = RollamaGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
