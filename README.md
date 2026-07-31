# GitHub Telegram Bot

A Telegram bot that acts as an intelligent agent for interacting with GitHub repositories. It leverages the Gemini API to understand natural language requests, read codebase files, suggest edits, and directly commit changes to your GitHub repos.

## Features
- **Natural Language Interaction:** Tell the bot what you want to do (e.g., "Fix the null pointer in auth.js", "List Python files").
- **Agentic Workflow:** The Gemini agent decides which GitHub tools to use (read files, create branches, edit and commit) to fulfill your request.
- **Direct GitHub Integration:** Reads and writes directly to your GitHub repository.
- **Docker Support:** Easily deploy the bot using Docker Compose.

## Quick Start
Please see [SETUP.md](SETUP.md) for detailed instructions on how to set up your Telegram bot token, Gemini API key, and GitHub token.

### Running with Docker

1. Create a `.env` file based on `.env.example` and add your tokens (including `GITHUB_TOKEN`).
2. Build and start the container:

```bash
docker compose up -d --build
```

3. Check the logs:

```bash
docker compose logs -f
```

## Setup without Docker

1. Create a virtual environment and install dependencies:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

2. Run the bot:
```bash
python github_bot.py
```
