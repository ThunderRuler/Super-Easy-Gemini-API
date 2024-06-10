This is intended to be a very quick way to interact witht he Gemini API. Simply download the .py file and run it (so long as python and google-generativeai is installed)

If all you want to do is chat with the API and *that's it*. This should be perfect.

## Gemini v#.#.py

This Python script provides a VERY basic GUI for messaging the Google Gemini API and nothing more.

## Features

- **Basic Chat Interface:**  A basic interface for sending messages to the Gemini model (gemini 1.5 pro default) and viewing responses.
- **Customizable Names:** Set custom names for the user and the bot, which will be displayed in the chat history.
- **Font Settings:** Adjust the font for the chat history and input field.
- **Save/Load Chat History:** Save and load chat history to a JSON file for later reference.
- **System Instructions:**  Uses a `instructions.txt` file to provide system instructions to the Gemini model, guiding its responses and behavior.
- **Regenerate Last Message:**  Use the "Regen" button to remove the last two messages (bot's response and user's message) from the chat history, copy the user's last message into the input field, and start a new chat session with the remaining history. This allows you to edit and resend your last message for regeneration.

## Requirements
### ( in order )

- API key (get at https://aistudio.google.com/app/apikey)
- Python 3.7 or higher (https://www.python.org/downloads/)
- Google AI Python SDK: `pip install -q -U google-generativeai` (https://ai.google.dev/gemini-api/docs/quickstart?lang=python)

## How to run
1. run the .py file 
2. enter system instructions into instructions.txt (required)

## Contributions are welcome
This is a side project and I used Gemini to help make this script so if there's something that can be improved feel free to create a pull request. 

**License
This project is licensed under the MIT License.
