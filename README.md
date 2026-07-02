# Crimson Bot

A Discord bot written in Python to automatically detect, alert, and solve events created by the Dank Memer Discord bot.

## Features

### Event Alerting
- **Categorization:** Routes events to specific alert channels based on the event title.
- **Invite Links:** Generates a server invite and appends a link to the forwarded embed.
- **Role Pinging:** Pings designated roles when an event starts to notify users.
- **Excluded Servers:** Includes built-in support to prevent forwarding loops or alerts within specific servers.

### Automated Solvers
The bot includes automatic solvers for various Dank Memer mini-games and events. It provides answers in code blocks or posts the solution directly.
- **Item & Fish Guesser:** Parses the event's image URL ID and cross-references it with a database of items, fish, and NPCs to provide the correct name.
- **Dank Scrambled Eggs:** Decrypts anagrams by sorting and matching characters against the items database.
- **Reverse Reverse:** Reads the target phrase and outputs the reversed string.
- **Fortnite Dance Mode:** Extracts sequences of arrows (e.g., `ArrowUp`, `ArrowDown`) and outputs the directions in plain text.
- **"Say" Events:** Detects prompts requiring users to repeat a specific phrase and provides the phrase.

### Design
- Caches Discord invites and guesser images in memory to minimize API calls.
- Pre-compiles regular expressions for text processing.

## Technologies Used
- Python
- discord.py
- asyncio
- python-dotenv
- Regular Expressions (Regex)

## Project Structure
- `cogs/` - Modular bot extensions for features like access control, role management, channels, and utility commands.
- `main.py` - Core bot logic, event listeners, embed parsing, alert routing, and automated solver implementations.
- `dank_data.py` - Knowledge base mapping Dank Memer item names to their respective Discord image IDs. Generates lookup tables on initialization.
- `requirements.txt` - Python dependencies required to run the bot.
- `.env.example` - Template for environment variables.
- `.gitignore` - Git ignore rules to prevent committing sensitive or temporary files.

## Requirements
- Python 3.9+
- A registered Discord Bot Token

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file based on the example and add your bot token:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` to include your token:
   ```env
   BOT_TOKEN=your_discord_bot_token_here
   ```

3. Run the bot:
   ```bash
   python main.py
   ```

## Configuration

Update the hardcoded variables in `main.py` (e.g., `DANK_MEMER_ID`, `EXCLUDED_SERVER_ID`, `POOKIE_MOD_ROLE_ID`) to match your Discord server setup before starting the bot.

