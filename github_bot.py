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
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
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

USER_STATE = {}  # {user_id: {"selected_repo": "..."}}

# Initialize Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# GitHub tools for Gemini
GITHUB_TOOLS = [
    {
        "name": "read_file",
        "description": "Read the content of a file from a GitHub repository",
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
        "description": "Create or edit a file and commit the changes to GitHub. Also use this to create new files.",
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
        "name": "delete_file",
        "description": "Delete a file from the repository and commit the deletion",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "repo": {"type": "STRING", "description": "Repository name (owner/repo)"},
                "path": {"type": "STRING", "description": "File path to delete"},
                "commit_message": {"type": "STRING", "description": "Commit message"},
                "branch": {"type": "STRING", "description": "Branch (default: main)"}
            },
            "required": ["repo", "path", "commit_message"]
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
    },
    {
        "name": "list_branches",
        "description": "List all branches in the repository",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "repo": {"type": "STRING", "description": "Repository name (owner/repo)"}
            },
            "required": ["repo"]
        }
    },
    {
        "name": "get_commits",
        "description": "Get the latest commits from a branch",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "repo": {"type": "STRING", "description": "Repository name (owner/repo)"},
                "branch": {"type": "STRING", "description": "Branch name (default: main)"},
                "count": {"type": "INTEGER", "description": "Number of commits to return (default: 5)"}
            },
            "required": ["repo"]
        }
    },
    {
        "name": "create_pull_request",
        "description": "Create a pull request from one branch to another",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "repo": {"type": "STRING", "description": "Repository name (owner/repo)"},
                "title": {"type": "STRING", "description": "Pull request title"},
                "body": {"type": "STRING", "description": "Pull request description"},
                "head": {"type": "STRING", "description": "The branch with changes"},
                "base": {"type": "STRING", "description": "The branch to merge into (default: main)"}
            },
            "required": ["repo", "title", "head"]
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
        
        elif tool_name == "delete_file":
            result = gh.delete_file(
                tool_input["repo"],
                tool_input["path"],
                tool_input["commit_message"],
                tool_input.get("branch", "main")
            )
            return f"File deleted: {result}"
        
        elif tool_name == "list_files":
            files = gh.list_files(
                tool_input["repo"],
                tool_input.get("path", ""),
                tool_input.get("branch", "main")
            )
            return "Files:\n" + "\n".join(files)
        
        elif tool_name == "create_branch":
            result = gh.create_branch(
                tool_input["repo"],
                tool_input["branch_name"],
                tool_input.get("from_branch", "main")
            )
            return f"Branch created: {result}"
        
        elif tool_name == "list_branches":
            branches = gh.list_branches(tool_input["repo"])
            return "Branches:\n" + "\n".join(branches)
        
        elif tool_name == "get_commits":
            commits = gh.get_latest_commits(
                tool_input["repo"],
                tool_input.get("branch", "main"),
                int(tool_input.get("count", 5))
            )
            return f"Recent commits:\n{commits}"
        
        elif tool_name == "create_pull_request":
            result = gh.create_pull_request(
                tool_input["repo"],
                tool_input["title"],
                tool_input.get("body", ""),
                tool_input["head"],
                tool_input.get("base", "main")
            )
            return f"Pull request created: {result}"
        
        else:
            return f"Unknown tool: {tool_name}"
    
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
    system_prompt = (
        "You are an AI assistant that helps users interact with their GitHub repositories. "
        "When the user mentions a task (review code, list files, fix a bug, etc.), "
        "use the available tools to read files, make edits, or create branches as needed. "
        "If an [Active Repository: owner/repo] tag appears at the start of the message, "
        "always use that as the repository for all tool calls unless the user explicitly specifies another."
    )

    messages = [
        {
            "role": "user",
            "parts": [user_message]
        }
    ]

    # Create model with tools and system instruction
    model = genai.GenerativeModel(
        "gemini-flash-latest",
        tools=GITHUB_TOOLS,
        system_instruction=system_prompt
    )

    try:
        # First call to Gemini
        response = model.generate_content(
            messages,
            tool_config={'function_calling_config': 'AUTO'}
        )
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise Exception(f"AI error: {str(e)}")

    # Process tool calls in a loop
    max_iterations = 5
    iteration = 0

    def _get_function_calls(resp):
        """Extract all function_call parts from a response"""
        calls = []
        for part in resp.candidates[0].content.parts:
            if hasattr(part, 'function_call') and part.function_call.name:
                calls.append(part.function_call)
        return calls

    func_calls = _get_function_calls(response)

    while func_calls and iteration < max_iterations:
        iteration += 1
        logger.info(f"Agentic iteration {iteration}, tool calls: {[c.name for c in func_calls]}")

        tool_results = []
        for tool_call in func_calls:
            logger.info(f"Executing tool: {tool_call.name} with args: {dict(tool_call.args)}")
            try:
                result = execute_github_tool(
                    tool_call.name,
                    dict(tool_call.args),
                    github_token
                )
            except Exception as e:
                result = f"Tool error ({tool_call.name}): {str(e)}"
                logger.error(result)

            tool_results.append({
                "function_name": tool_call.name,
                "content": result
            })

        # Add model response and tool results to history
        messages.append(response.candidates[0].content)
        messages.append({
            "role": "user",
            "parts": [
                genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=r["function_name"],
                        response={"result": r["content"]}
                    )
                )
                for r in tool_results
            ]
        })

        try:
            response = model.generate_content(
                messages,
                tool_config={'function_calling_config': 'AUTO'}
            )
        except Exception as e:
            logger.error(f"Gemini API error on iteration {iteration}: {e}")
            raise Exception(f"AI error during tool processing: {str(e)}")

        func_calls = _get_function_calls(response)

    # Extract final text response
    final_response = ""
    for part in response.candidates[0].content.parts:
        if hasattr(part, 'text') and part.text:
            final_response += part.text

    return final_response.strip() if final_response.strip() else "Task completed, but no summary was returned."



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command - welcome message"""
    keyboard = [[InlineKeyboardButton("📂 Browse My Repositories", callback_data="show_repos:0:")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Hey! I'm your AI-powered GitHub assistant 👋\n\n"
        "Just talk to me naturally — no commands needed!\n\n"
        "You can say things like:\n"
        "• *Show me files in my project*\n"
        "• *Add error handling to auth.py*\n"
        "• *Create a hotfix branch*\n"
        "• *Commit my changes with a good message*\n\n"
        "First, pick a repository to work with 👇",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )




async def list_repos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List repositories with pagination and optional search"""
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        await update.message.reply_text("❌ GITHUB_TOKEN not set in environment.")
        return

    search_term = context.args[0].lower() if context.args else ""
    user_id = update.effective_user.id
    page = 0
    
    await _send_repos_page(update.message, github_token, search_term, page, user_id)

async def _send_repos_page(message, github_token, search_term, page, user_id):
    try:
        gh = GitHubHelper(github_token)
        all_repos = gh.get_user_repos()
        
        if search_term:
            repos = [r for r in all_repos if search_term in r.lower()]
        else:
            repos = all_repos
            
        if not repos:
            await message.reply_text("No repositories found matching your search.")
            return

        per_page = 10
        total_pages = (len(repos) + per_page - 1) // per_page
        
        # Ensure page is within bounds
        page = max(0, min(page, total_pages - 1))
        
        start_idx = page * per_page
        end_idx = start_idx + per_page
        current_repos = repos[start_idx:end_idx]
        
        keyboard = []
        for repo in current_repos:
            keyboard.append([InlineKeyboardButton(repo, callback_data=f"repo:{repo}")])
            
        # Pagination buttons
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"page:{page-1}:{search_term}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"page:{page+1}:{search_term}"))
            
        if nav_buttons:
            keyboard.append(nav_buttons)
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = f"Select a repository (Page {page+1}/{total_pages}):"
        if search_term:
            text += f"\nFiltering by: '{search_term}'"
            
        # If this is an edit (from callback)
        if hasattr(message, 'edit_text'):
            await message.edit_text(text, reply_markup=reply_markup)
        else:
            await message.reply_text(text, reply_markup=reply_markup)
            
    except Exception as e:
        await message.reply_text(f"❌ Error fetching repos: {str(e)}")

async def repo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle repository selection and pagination"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data.startswith("repo:"):
        selected_repo = data.split(":", 1)[1]
        if user_id not in USER_STATE:
            USER_STATE[user_id] = {}
        USER_STATE[user_id]["selected_repo"] = selected_repo
        
        await query.edit_message_text(
            f"✅ Active repo set to: `{selected_repo}`\n\n"
            f"What would you like to do?",
            parse_mode="Markdown"
        )
        
        # Send suggestions as a follow-up message
        suggestions_keyboard = [
            [InlineKeyboardButton("📋 List files", callback_data=f"quick:list_files"),
             InlineKeyboardButton("📜 Recent commits", callback_data=f"quick:get_commits")],
            [InlineKeyboardButton("🌿 List branches", callback_data=f"quick:list_branches"),
             InlineKeyboardButton("🔍 Review code", callback_data=f"quick:review_code")],
            [InlineKeyboardButton("🐛 Find bugs", callback_data=f"quick:find_bugs"),
             InlineKeyboardButton("📝 Add README", callback_data=f"quick:add_readme")],
            [InlineKeyboardButton("🌿 Create branch", callback_data=f"quick:create_branch"),
             InlineKeyboardButton("🔀 Open a PR", callback_data=f"quick:create_pr")],
        ]
        await query.message.reply_text(
            "Or pick a quick action:",
            reply_markup=InlineKeyboardMarkup(suggestions_keyboard)
        )
        
    elif data.startswith("page:"):
        _, page_str, search_term = data.split(":", 2)
        page = int(page_str)
        github_token = os.getenv("GITHUB_TOKEN")
        await _send_repos_page(query.message, github_token, search_term, page, user_id)

    elif data.startswith("show_repos:"):
        _, page_str, search_term = data.split(":", 2)
        page = int(page_str)
        github_token = os.getenv("GITHUB_TOKEN")
        await _send_repos_page(query.message, github_token, search_term, page, user_id)

    elif data.startswith("quick:"):
        action = data.split(":", 1)[1]
        repo = USER_STATE.get(user_id, {}).get("selected_repo", "")
        if not repo:
            await query.message.reply_text("⚠️ Please select a repository first with /repos")
            return
        
        quick_prompts = {
            "list_files":    f"List all files in the root of {repo}",
            "get_commits":   f"Show me the last 5 commits in {repo}",
            "list_branches": f"List all branches in {repo}",
            "review_code":   f"Review the main source files in {repo} and give me a summary of what the code does",
            "find_bugs":     f"Read the main files in {repo} and identify potential bugs or issues",
            "add_readme":    f"Read the existing README.md or files in {repo} and create/update a comprehensive README.md",
            "create_branch": f"Ask me what to name the new branch, then create it in {repo}",
            "create_pr":     f"List the branches in {repo} and help me create a pull request",
        }
        
        prompt = quick_prompts.get(action, f"Help me with {repo}")
        await query.message.reply_text(f"⏳ Working on it...")
        
        github_token = os.getenv("GITHUB_TOKEN")
        try:
            full_prompt = f"[Active Repository: {repo}]\n\n{prompt}"
            result = await agentic_workflow(full_prompt, github_token, user_id)
            if len(result) > 4000:
                await query.message.reply_text(result[:4000] + "\n...[truncated]")
            else:
                await query.message.reply_text(result)
        except Exception as e:
            await query.message.reply_text(f"❌ Error: {str(e)}")

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

    # Inject repo context if selected
    if user_id in USER_STATE and 'selected_repo' in USER_STATE[user_id]:
        repo = USER_STATE[user_id]['selected_repo']
        user_message = f"[Active Repository: {repo}]\n\n" + user_message
    
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


async def post_init(application: Application) -> None:
    """Register bot commands so they show in Telegram's / menu"""
    await application.bot.set_my_commands([
        BotCommand("start", "Start the bot & pick a repo"),
        BotCommand("repos", "Browse or search your GitHub repos"),
        BotCommand("test", "Run a quick connection test"),
    ])


def main() -> None:
    """Start the bot"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set")
    
    # Create app
    app = Application.builder().token(token).post_init(post_init).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("repos", list_repos))
    app.add_handler(CallbackQueryHandler(repo_callback))
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
