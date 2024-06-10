import os
import json
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from tkinter import messagebox
from tkinter import filedialog
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.ai import generativelanguage as glm

# --- Configuration ---
CONFIG_FILE = "chatbot_config.json"  # Name of the config file
DEFAULT_MODEL = "gemini-1.5-pro"  # Default model to use
DEFAULT_TEMPERATURE = 0.3  # Default temperature for the model
DEFAULT_SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}
DEFAULT_USER_NAME = "User"  # Default user name
DEFAULT_BOT_NAME = "Gemini"  # Default bot name

# --- Load API Key and Config ---
def load_api_key():
    """Loads API key from config file or prompts the user for it."""
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            api_key = config.get("api_key")
            if api_key:
                return api_key
    except FileNotFoundError:
        pass
    return None

def load_config():
    """Loads configuration from config file."""
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_config(config):
    """Saves configuration to config file."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def load_instructions():
    """Loads instructions from instructions.txt, creating it if it doesn't exist."""
    try:
        with open("instructions.txt", "r") as f:
            return f.read()
    except FileNotFoundError:
        # Create the file if it doesn't exist
        with open("instructions.txt", "w") as f:
            f.write("## System Instructions\n\n")  # Add a default header
        return ""  # Return an empty string since the file is newly created

# --- API Key Validation ---
def validate_api_key(api_key):
    """Validates the API key."""
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        print(f"API Key Validation Error: {e}")
        return False

# --- Chatbot Logic ---
def start_chat():
    """Starts the chatbot session."""
    global chat_session, model
    api_key = load_api_key()
    if api_key:
        config = load_config()  # Load config here
        instructions = load_instructions()

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name=config.get("model", DEFAULT_MODEL),
            generation_config=genai.types.GenerationConfig(
                temperature=config.get("temperature", DEFAULT_TEMPERATURE)
            ),
            safety_settings=config.get("safety_settings", DEFAULT_SAFETY_SETTINGS),
            system_instruction=instructions,  # Set system instructions here
        )

        print(f"API key loaded: {'OK' if api_key else 'Failed'}")
        print(f"Config file loaded: {'OK' if config else 'Failed'}")
        print(f"Instructions file loaded: {'OK' if instructions else 'Failed'}")
        print("Chat Started:")

        chat_session = model.start_chat(history=[])
        # No need to send instructions here, they are set in the model

        update_chat_history()
    else:
        show_api_key_popup()

def send_message():
    """Sends the user's message to the chatbot."""
    global chat_session, model
    user_message = input_field.get("1.0", tk.END).strip()
    if user_message:
        input_field.delete("1.0", tk.END)  # Clear input field

        # Send message and let ChatSession handle history
        response = chat_session.send_message(user_message)

        update_chat_history()

def regen_last_message():
    """Regenerates the previous bot response using the entire conversation history."""
    global chat_session, model
    if len(chat_session.history) > 2:  # Need at least 3 messages for regen

        # Get the user's last message (before removing anything)
        last_user_message = chat_session.history[-2].parts[0].text

        # Remove the last two messages (bot's response and user's message)
        chat_session.history.pop()
        chat_session.history.pop()

        # Rebuild the history up to the last user message using glm.Content objects
        regenerated_history = []
        for message in chat_session.history:
            regenerated_history.append(
                glm.Content(parts=[glm.Part(text=message.parts[0].text)], role=message.role)
            )

        # Start a new chat session with the regenerated history 
        # (system instructions are already set in the model)
        chat_session = model.start_chat(history=regenerated_history)

        # Put the last user message back into the input field
        input_field.delete("1.0", tk.END)
        input_field.insert(tk.END, last_user_message)

def update_chat_history():
    """Updates the chat history text widget."""
    global chat_session
    chat_history_text.config(state=tk.NORMAL)  # Enable editing
    chat_history_text.delete("1.0", tk.END)
    config = load_config()  # Load config to get user and bot names
    user_name = config.get("user_name", DEFAULT_USER_NAME)
    bot_name = config.get("bot_name", DEFAULT_BOT_NAME)
    for message in chat_session.history:
        if message.role == "user":
            chat_history_text.insert(
                tk.END, f"{user_name}: {message.parts[0].text}\n\n"
            )
        else:
            chat_history_text.insert(
                tk.END, f"{bot_name}: {message.parts[0].text}\n\n"
            )
    chat_history_text.see(tk.END)  # Scroll to the bottom
    chat_history_text.config(state=tk.DISABLED)  # Disable editing

def save_chat():
    """Saves the chat history to a JSON file."""
    global chat_session
    filename = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON files", "*.json")],
        initialdir=".",  # Save in the same directory as the script
        title="Save Chat History",
    )
    if filename:
        save_chat(chat_session, filename)  # Pass chat_session and filename
        messagebox.showinfo("Chat Saved", f"Chat saved to {filename}")

def load_chat():
    """Loads the chat history from a JSON file."""
    global chat_session
    filename = filedialog.askopenfilename(
        defaultextension=".json",
        filetypes=[("JSON files", "*.json")],
        initialdir=".",  # Start in the same directory as the script
        title="Load Chat History",
    )
    if filename:
        load_chat(filename)  # Pass only filename
        update_chat_history()  # Update the chat history display after loading
        messagebox.showinfo("Chat Loaded", f"Chat loaded from {filename}")

def save_chat(chat_session, filename):
    """Saves the chat history to a JSON file."""
    chat_history = []
    for message in chat_session.history:
        chat_history.append(
            {"role": message.role, "text": message.parts[0].text}
        )
    with open(filename, "w") as f:
        json.dump(chat_history, f, indent=4)

def load_chat(filename):
    """Loads the chat history from a JSON file."""
    global chat_session
    try:
        with open(filename, "r") as f:
            chat_history = json.load(f)
        chat_session.history = [] # Clear the current chat history
        for message in chat_history:
            # Directly append the loaded messages to the chat history
            chat_session.history.append(glm.Content(parts=[glm.Part(text=message["text"])], role=message["role"]))
        update_chat_history()  # Update the chat history display after loading
    except FileNotFoundError:
        print(f"File '{filename}' not found.")

# --- API Key Popup ---
def show_api_key_popup():
    """Shows a popup to enter the API key."""
    global api_key_popup
    api_key_popup = tk.Toplevel(root)
    api_key_popup.title("Enter API Key")

    api_key_label = tk.Label(api_key_popup, text="Enter your Gemini API Key:")
    api_key_label.pack(pady=10)

    api_key_entry = tk.Entry(api_key_popup, width=50)
    api_key_entry.pack(pady=10)

    def validate_and_save():
        """Validates the API key and saves it to the config file."""
        global api_key_popup
        api_key = api_key_entry.get()
        if validate_api_key(api_key):
            save_config({"api_key": api_key})
            api_key_popup.destroy()
            start_chat()
        else:
            messagebox.showerror("Invalid API Key", "Please enter a valid API key.")

    save_button = tk.Button(api_key_popup, text="Save", command=validate_and_save)
    save_button.pack(pady=10)

# --- GUI Setup ---
root = tk.Tk()
root.title("Gemini Chatbot")

# --- Chat History ---
chat_history_frame = tk.Frame(root)
chat_history_frame.pack(fill=tk.BOTH, expand=True)

chat_history_text = scrolledtext.ScrolledText(
    chat_history_frame, wrap=tk.WORD, state=tk.DISABLED, font=("Arial", 16)
)
chat_history_text.pack(fill=tk.BOTH, expand=True)

# --- Input Field ---
input_frame = tk.Frame(root)
input_frame.pack(fill=tk.X)

input_field = tk.Text(input_frame, height=1, wrap=tk.WORD, font=("Arial", 16))
input_field.pack(side=tk.LEFT, fill=tk.X, expand=True)

# --- Send Button ---
send_button = tk.Button(input_frame, text="Send", command=send_message)
send_button.pack(side=tk.LEFT)

# --- Regen Button ---
regen_button = tk.Button(input_frame, text="Regen", command=regen_last_message)
regen_button.pack(side=tk.LEFT)

# --- File Dialogs ---
save_file_dialog = tk.StringVar(value="")
load_file_dialog = tk.StringVar(value="")

save_button = tk.Button(root, text="Save", command=lambda: save_chat(chat_session, filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")], initialdir=".",  # Save in the same directory as the script
                                                                                                                                                                         title="Save Chat History")))  # Pass chat_session
save_button.pack(side=tk.LEFT)

load_button = tk.Button(root, text="Load", command=lambda: load_chat(filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")], initialdir=".",  # Start in the same directory as the script
                                                                                                                                                                         title="Load Chat History")))  # Pass chat_session
load_button.pack(side=tk.LEFT)

# --- Font Settings ---
def set_font():
    """Sets the font for the input field and chat history."""
    font_family = font_family_combobox.get()
    font_size = int(font_size_entry.get())
    input_field.config(font=(font_family, font_size))
    chat_history_text.config(font=(font_family, font_size))

font_frame = tk.Frame(root)
font_frame.pack(fill=tk.X)

# Font Settings
font_label = tk.Label(font_frame, text="Font:")
font_label.pack(side=tk.LEFT)

font_family = tk.StringVar(value="Arial")
font_family_combobox = ttk.Combobox(
    font_frame, textvariable=font_family, values=["Arial", "Courier", "Times"]
)
font_family_combobox.pack(side=tk.LEFT)

font_size = tk.StringVar(value="16")  # Default font size 16
font_size_entry = tk.Entry(font_frame, textvariable=font_size, width=5)
font_size_entry.pack(side=tk.LEFT)

font_button = tk.Button(font_frame, text="Set", command=set_font)
font_button.pack(side=tk.LEFT)

# --- Name Settings ---
def set_user_name():
    """Saves the user name to the config file."""
    user_name = user_name_entry.get()
    config = load_config()
    config["user_name"] = user_name
    save_config(config)
    update_chat_history()  # Update chat history after changing user name

def set_bot_name():
    """Saves the bot name to the config file."""
    bot_name = bot_name_entry.get()
    config = load_config()
    config["bot_name"] = bot_name
    save_config(config)
    update_chat_history()  # Update chat history after changing bot name

name_frame = tk.Frame(root)
name_frame.pack(fill=tk.X)

# User Name Settings
user_name_label = tk.Label(name_frame, text="User Name:")
user_name_label.pack(side=tk.LEFT)

user_name_entry = tk.Entry(name_frame, width=10)
user_name_entry.pack(side=tk.LEFT)

user_name_button = tk.Button(name_frame, text="Set", command=set_user_name)
user_name_button.pack(side=tk.LEFT)

# Bot Name Settings
bot_name_label = tk.Label(name_frame, text="Bot Name:")
bot_name_label.pack(side=tk.LEFT)

bot_name_entry = tk.Entry(name_frame, width=10)
bot_name_entry.pack(side=tk.LEFT)

bot_name_button = tk.Button(name_frame, text="Set", command=set_bot_name)
bot_name_button.pack(side=tk.LEFT)

# --- Bind Enter Key ---
input_field.bind("<Return>", lambda event: send_message())

# --- Start Chat ---
start_chat()

root.mainloop()