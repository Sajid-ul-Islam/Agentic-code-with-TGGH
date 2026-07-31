import re

with open("github_bot.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Imports
content = content.replace(
    "from telegram import Update\nfrom telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes",
    "from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup\nfrom telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler"
)

# 2. State
content = content.replace(
    "logger = logging.getLogger(__name__)\n\n# Initialize Gemini",
    "logger = logging.getLogger(__name__)\n\nUSER_STATE = {}  # {user_id: {\"selected_repo\": \"...\"}}\n\n# Initialize Gemini"
)

# 3. /repos command and callback
new_funcs = """
async def list_repos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    \"\"\"List repositories with pagination and optional search\"\"\"
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
            text += f"\\nFiltering by: '{search_term}'"
            
        # If this is an edit (from callback)
        if hasattr(message, 'edit_text'):
            await message.edit_text(text, reply_markup=reply_markup)
        else:
            await message.reply_text(text, reply_markup=reply_markup)
            
    except Exception as e:
        await message.reply_text(f"❌ Error fetching repos: {str(e)}")

async def repo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    \"\"\"Handle repository selection and pagination\"\"\"
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data.startswith("repo:"):
        selected_repo = data.split(":", 1)[1]
        if user_id not in USER_STATE:
            USER_STATE[user_id] = {}
        USER_STATE[user_id]["selected_repo"] = selected_repo
        
        await query.edit_message_text(f"✅ Selected repository: **{selected_repo}**")
        
    elif data.startswith("page:"):
        _, page_str, search_term = data.split(":", 2)
        page = int(page_str)
        github_token = os.getenv("GITHUB_TOKEN")
        await _send_repos_page(query.message, github_token, search_term, page, user_id)

"""

content = content.replace("async def test_command", new_funcs + "async def test_command")

# 4. Handle message context injection
# find: user_message = update.message.text
# insert repo context

content = content.replace(
    "user_message = update.message.text\n    user_id = update.effective_user.id",
    "user_message = update.message.text\n    user_id = update.effective_user.id\n\n    # Inject repo context if selected\n    if user_id in USER_STATE and 'selected_repo' in USER_STATE[user_id]:\n        repo = USER_STATE[user_id]['selected_repo']\n        user_message = f\"[Active Repository: {repo}]\\n\\n\" + user_message"
)

# 5. Add handlers to main
content = content.replace(
    "app.add_handler(CommandHandler(\"test\", test_command))",
    "app.add_handler(CommandHandler(\"repos\", list_repos))\n    app.add_handler(CallbackQueryHandler(repo_callback))\n    app.add_handler(CommandHandler(\"test\", test_command))"
)

with open("github_bot.py", "w", encoding="utf-8") as f:
    f.write(content)
print("github_bot.py patched successfully")
