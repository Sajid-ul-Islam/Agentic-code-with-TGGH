#!/usr/bin/env python3
"""
GitHub Telegram Bot - Agentic POC
Uses Gemini API with tool_use to decide GitHub actions
"""

import os
import json
import logging
import asyncio
from typing import Optional
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from github_helper import GitHubHelper

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# GitHub tools for Gemini
GITHUB_TOOLS = [
    {
        "name": "read_file",
        "description": "Read a file from GitHub repository",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "repo": {"type": "STRING", "description": "Repository name (owner/repo)"},
                "path": {"type": "STRING", "description": "File path in repo"},
                "branch": {"type": "STRING", "description": "Branch name (default: main)"}
            },
            "required": ["repo", "path"]
        }
    },
    {
        "name": "edit_and_commit",
        "description": "Edit a file and commit changes to GitHub",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "repo": {"type": "STRING", "description": "Repository name (owner/repo)"},
                "path": {"type": "STRING", "description": "File path"},
                "new_content": {"type": "STRING", "description": "New file content"},
                "commit_message": {"type": "STRING", "description": "Commit message"},
                "branch": {"type": "STRING", "description": "Branch to commit to (default: main)"}
            },
            "required": ["repo", "path", "new_content", "commit_message"]
        }
    },
    {
        "name": "list_files",
        "description": "List files in a directory of the repository",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "repo": {"type": "STRING", "description": "Repository name (owner/repo)"},
                "path": {"type": "STRING", "description": "Directory path (empty for root)"},
                "branch": {"type": "STRING", "description": "Branch name (default: main)"}
            },
            "required": ["repo"]
        }
    },
    {
        "name": "create_branch",
        "description": "Create a new branch in the repository",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "repo": {"type": "STRING", "description": "Repository name (owner/repo)"},
                "branch_name": {"type": "STRING", "description": "Name of new branch"},
                "from_branch": {"type": "STRING", "description": "Branch to create from (default: main)"}
            },
            "required": ["repo", "branch_name"]
        }
    }
]


def execute_github_tool(tool_name: str, tool_input: dict, github_token: str) -> str:
    """Execute a GitHub tool using GitHubHelper"""
    gh = GitHubHelper(github_token)
    
    try:
        if tool_name == "read_file":
            content = gh.read_file(
                tool_input["repo"],
                tool_input["path"],
                tool_input.get("branch", "main")
            )
            return f"File content:\n{content}"
        
        elif tool_name == "edit_and_commit":
            result = gh.edit_and_commit(
                tool_input["repo"],
                tool_input["path"],
                tool_input["new_content"],
                tool_input["commit_message"],
                tool_input.get("branch", "main")
            )
            return f"Committed successfully: {result}"
        
        elif tool_name == "list_files":
            files = gh.list_files(
                tool_input["repo"],
                tool_input.get("path", ""),
                tool_input.get("branch", "main")
            )
            return f"Files:\n" + "\n".join(files)
        
        elif tool_name == "create_branch":
            result = gh.create_branch(
                tool_input["repo"],
                tool_input["branch_name"],
                tool_input.get("from_branch", "main")
            )
            return f"Branch created: {result}"
    
    except Exception as e:
        return f"Error: {str(e)}"


async def agentic_workflow(user_message: str, github_token: str, user_id: int) -> str:
    """
    Run Gemini agentic workflow:
    1. Send user request to Gemini with GitHub tools
    2. Gemini decides which tools to use
    3. Execute tools and get results
    4. Gemini synthesizes final response
    """
    
    messages = [
        {
            "role": "user",
            "content": user_message
        }
    ]
    
    # Create model with tools
    model = genai.GenerativeModel(
        "gemini-2.0-flash",
        tools=GITHUB_TOOLS
    )
    
    # First call to Gemini
    response = model.generate_content(
        messages,
        tool_config={'function_calling_config': 'AUTO'}
    )
    
    # Process tool calls in a loop
    max_iterations = 5
    iteration = 0
    
    while response.candidates[0].content.parts[-1].function_calls and iteration < max_iterations:
        iteration += 1
        
        tool_calls = response.candidates[0].content.parts[-1].function_calls
        tool_results = []
        
        for tool_call in tool_calls:
            logger.info(f"Executing tool: {tool_call.name}")
            
            # Execute the tool
            result = execute_github_tool(
                tool_call.name,
                dict(tool_call.args),
                github_token
            )
            
            tool_results.append({
                "function_name": tool_call.name,
                "content": result
            })
        
        # Add assistant response and tool results to messages
        messages.append({
            "role": "model",
            "content": response.candidates[0].content
        })
        
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "function_result",
                    "id": i,
                    "function_name": result["function_name"],
                    "result": result["content"]
                }
                for i, result in enumerate(tool_results)
            ]
        })
        
        # Second call with results
        response = model.generate_content(
            messages,
            tool_config={'function_calling_config': 'AUTO'}
        )
    
    # Extract final text response
    final_response = ""
    for part in response.candidates[0].content.parts:
        if hasattr(part, 'text'):
            final_response += part.text
    
    return final_response if final_response else "Task completed. No additional notes."


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command - show setup instructions"""
    await update.message.reply_text(
        "🤖 GitHub Telegram Bot\n\n"
        "Just ask me things like:\n"
        "- Fix the null pointer in auth.js\n"
        "- Add error handling to this function\n"
        "- Show me the latest commit in main branch\n\n"
        "I'll read your GitHub repo, make changes, and push them! 🚀"
    )



async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Quick test"""
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        await update.message.reply_text("❌ GITHUB_TOKEN not set in environment.")
        return
    
    await update.message.reply_text("🔄 Testing... (this may take 10-15 seconds)")
    
    user_id = update.effective_user.id
    
    try:
        # Test message
        test_message = (
            "List all Python files in the root of my main branch. "
            "My repo is: <repo_owner>/<repo_name>"
        )
        
        result = await agentic_workflow(test_message, github_token, user_id)
        await update.message.reply_text(f"✅ Result:\n{result[:1000]}")
    
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user messages - send to Gemini agentic workflow"""
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        await update.message.reply_text("❌ GITHUB_TOKEN not set in environment.")
        return
    
    user_message = update.message.text
    user_id = update.effective_user.id
    
    # Show typing indicator
    await update.message.chat.send_action("typing")
    
    try:
        
        # Run agentic workflow
        response = await agentic_workflow(user_message, github_token, user_id)
        
        # Send response (Telegram has 4096 char limit)
        if len(response) > 4000:
            await update.message.reply_text(response[:4000] + "\n...[truncated]")
        else:
            await update.message.reply_text(response)
    
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


def main() -> None:
    """Start the bot"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set")
    
    # Create app
    app = Application.builder().token(token).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Bot started. Press Ctrl+C to stop.")
    
    # Ensure event loop exists for Python 3.14+
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
