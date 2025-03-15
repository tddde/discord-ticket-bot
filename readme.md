# Discord Ticket Bot

This is a simple Discord.py Ticket Bot with HTML Transcripts using chat_exporter

## Features
- Create multiple ticket categories.
- Get a HTML transcript of your tickets by closing/deleting the ticket.
- Fully customizable ticket panel.

## Requirements
- Python 3.8+
- `discord.py` and `chat_exporter`

## Installation
1. Clone this repository.
2. Install dependencies:
   ```sh
   pip install discord.py chat_exporter
   ```
3. Set your bot token in the script.
4. Run the bot:
   ```sh
   python bot.py
   ```

## Permissions
- The bot requires `Read Message History` and `Manage Messages` permissions.
- All the commands are restricted to allowed roles from `config.json`
