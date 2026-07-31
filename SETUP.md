# GitHub Telegram Bot - POC Setup Guide

## What This Does

A Telegram bot that uses **Gemini API** as an agentic brain to:
- Read your GitHub files
- Edit code based on your instructions
- Commit and push changes automatically
- All from your phone via Telegram

**Flow**: Telegram Message → Gemini (decides actions) → GitHub API (executes) → Response back to you

---

## Step 1: Prerequisites

### Get Your Tokens/Keys

**1.1 Telegram Bot Token**
- Open Telegram, search for `@BotFather`
- Run `/newbot` and follow prompts
- You'll get a token like: `123456789:ABCdefGHIjklmnoPQRstuvWXYZ`
- Save it as `TELEGRAM_BOT_TOKEN`

**1.2 GitHub Personal Access Token**
- Go to: https://github.com/settings/tokens
- Click "Generate new token (classic)"
- Select scopes:
  - ✅ `repo` (full control of private repos)
  - ✅ `workflow` (update workflows)
- Save it securely (you'll use this when authenticating with `/auth_github`)

**1.3 Gemini API Key**
- Go to: https://aistudio.google.com/app/apikeys
- Click "Create API Key"
- Copy the key

**1.4 Python Environment**
```bash
# Clone or save these files
mkdir github-telegram-bot
cd github-telegram-bot

# Copy the files:
# - github_bot.py
# - github_helper.py
# - requirements.txt
# - SETUP.md (this file)

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Step 2: Set Environment Variables

Create a `.env` file in your project directory:

```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
```

**Important:** Never commit `.env` to GitHub!

---

## Step 3: Run the Bot

```bash
source venv/bin/activate  # Activate virtual env
python github_bot.py
```

You should see:
```
INFO:root:Bot started. Press Ctrl+C to stop.
```

---

## Step 4: Authenticate from Telegram

Open Telegram and search for your bot (by the name you gave BotFather).

**Send this command:**
```
/auth_github YOUR_GITHUB_TOKEN
```

Replace `YOUR_GITHUB_TOKEN` with the token you created in Step 1.2.

**Expected response:**
```
✅ GitHub token saved securely!
Ready to work. Try: /test
```

---

## Step 5: Test It

Send this message to the bot:
```
/test
```

The bot will:
1. Contact Gemini
2. Ask Gemini to list Python files in your repo
3. Call GitHub API
4. Return results

---

## Step 6: Use It!

Now just send natural language requests:

### Examples:

**Read a file:**
```
Show me the content of app.py
```

**Fix code:**
```
Add error handling to the login function in auth.py
My repo is: username/myrepo
```

**Create a branch:**
```
Create a hotfix branch called "fix-null-pointer" in username/myrepo
```

**Commit changes:**
```
In username/myrepo, add input validation to the password field in auth.js
Then commit with message: "Add password validation"
```

---

## How It Works Behind The Scenes

1. **You send a message** via Telegram
2. **Bot receives it** and sends to Gemini API
3. **Gemini analyzes** your request and decides which GitHub tools to use
4. **Gemini calls tools** (read_file, edit_and_commit, list_files, create_branch)
5. **Bot executes** each tool using GitHub API
6. **Results go back to Gemini** which synthesizes a final response
7. **Bot sends response** back to Telegram

This is "agentic" because Gemini decides the workflow, not you—it figures out what needs to happen.

---

## Available Tools (Gemini Can Use)

1. **read_file** - Read a file from your repo
2. **edit_and_commit** - Edit and commit a file
3. **list_files** - List files in a directory
4. **create_branch** - Create a new branch

You don't call these directly—just tell the bot what you want and Gemini decides which tools to use.

---

## Troubleshooting

### "TELEGRAM_BOT_TOKEN not set"
- Check your `.env` file exists
- Make sure variable names match exactly

### "Token validation failed"
- Your GitHub token might be invalid
- Regenerate it at: https://github.com/settings/tokens
- Make sure it has `repo` scope

### "GitHub error: 401"
- Token is invalid or expired
- Re-authenticate: `/auth_github NEW_TOKEN`

### "Command 'python3' not found"
- Install Python 3.9+
- On Mac: `brew install python3`
- On Linux: `sudo apt-get install python3`

### Bot doesn't respond to messages
- Is it still running? (Check terminal)
- Did you send `/start` first?
- Did you run `/auth_github` with a valid token?

---

## Production Notes

This is a **POC (proof of concept)**. For production:

1. **Credential Storage** - Currently stores tokens in memory. Use a database:
   - Firebase Realtime DB
   - MongoDB
   - PostgreSQL with encryption

2. **Rate Limiting** - Add cooldowns to prevent API spam

3. **Error Handling** - More granular exception handling

4. **Logging** - Log all actions for audit trail

5. **Security**:
   - Encrypt tokens at rest
   - Use environment variables (not `.env` in production)
   - Rate limit GitHub API calls
   - Validate user inputs

---

## Next Steps

Once this works, you can add:

- ✅ Support for multiple API providers (Claude, OpenAI)
- ✅ Branch/PR management
- ✅ Code review suggestions
- ✅ Automated testing before commit
- ✅ Webhook-based notifications
- ✅ Multi-repo support
- ✅ Schedule-based tasks (daily deployments, etc.)
- ✅ Slash commands for common tasks

---

## Questions?

If something breaks:
1. Check the error message in terminal
2. Verify your tokens/keys in `.env`
3. Make sure bot is running (`python github_bot.py`)
4. Check Telegram bot @BotFather to confirm bot is active

Good luck! 🚀
