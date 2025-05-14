#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Telegram File Storage Bot
A bot that stores files and provides shareable links for them
"""

import os
import json
import logging
import uuid
import time
import requests
import ai_helper

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Configuration
TOKEN = os.environ.get("BOT_TOKEN", "")
DEVELOPER_ID = os.environ.get("DEVELOPER_ID", "123456789")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB maximum file size

# Data storage
DATA_DIR = "data"
FILES_DATA = os.path.join(DATA_DIR, "files.json")
USERS_DATA = os.path.join(DATA_DIR, "users.json")
BOT_TOKENS_DATA = os.path.join(DATA_DIR, "bot_tokens.json")  # Store custom bot tokens

# In-memory databases
stored_files = {}  # unique_id: file_info
user_data = {}     # user_id: user_info
banned_users = set()  # set of banned user IDs
custom_bot_tokens = {}  # user_id: bot_token

# Utility functions
def is_admin(user_id):
    """Check if user is an admin"""
    return str(user_id) == str(DEVELOPER_ID)

def format_bytes(size_bytes):
    """Format bytes to human-readable size"""
    if size_bytes is None:
        return "Unknown size"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(size_bytes)
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.2f} {units[unit_index]}"

# Data storage functions
def ensure_data_directory():
    """Ensure the data directory exists"""
    os.makedirs(DATA_DIR, exist_ok=True)

def load_files_data():
    """Load stored files data from JSON file"""
    global stored_files
    try:
        if os.path.exists(FILES_DATA):
            with open(FILES_DATA, 'r') as f:
                stored_files = json.load(f)
                logger.info(f"Loaded {len(stored_files)} files from storage")
    except Exception as e:
        logger.error(f"Error loading files data: {e}")

def load_users_data():
    """Load user data and banned users from JSON file"""
    global user_data, banned_users
    try:
        if os.path.exists(USERS_DATA):
            with open(USERS_DATA, 'r') as f:
                data = json.load(f)
                user_data = data.get("users", {})
                banned_users = set(data.get("banned_users", []))
                logger.info(f"Loaded {len(user_data)} users and {len(banned_users)} banned users from storage")
    except Exception as e:
        logger.error(f"Error loading users data: {e}")

def save_files_data():
    """Save stored files data to JSON file"""
    try:
        ensure_data_directory()
        with open(FILES_DATA, 'w') as f:
            json.dump(stored_files, f, indent=2)
        logger.debug(f"Saved {len(stored_files)} files to storage")
    except Exception as e:
        logger.error(f"Error saving files data: {e}")

def save_users_data():
    """Save user data and banned users to JSON file"""
    try:
        ensure_data_directory()
        data = {
            "users": user_data,
            "banned_users": list(banned_users)
        }
        with open(USERS_DATA, 'w') as f:
            json.dump(data, f, indent=2)
        logger.debug(f"Saved {len(user_data)} users and {len(banned_users)} banned users to storage")
    except Exception as e:
        logger.error(f"Error saving users data: {e}")

def load_bot_tokens_data():
    """Load custom bot tokens from JSON file"""
    global custom_bot_tokens
    try:
        if os.path.exists(BOT_TOKENS_DATA):
            with open(BOT_TOKENS_DATA, 'r') as f:
                custom_bot_tokens = json.load(f)
                logger.info(f"Loaded {len(custom_bot_tokens)} custom bot tokens from storage")
    except Exception as e:
        logger.error(f"Error loading bot tokens data: {e}")

def save_bot_tokens_data():
    """Save custom bot tokens to JSON file"""
    try:
        ensure_data_directory()
        with open(BOT_TOKENS_DATA, 'w') as f:
            json.dump(custom_bot_tokens, f, indent=2)
        logger.debug(f"Saved {len(custom_bot_tokens)} custom bot tokens to storage")
    except Exception as e:
        logger.error(f"Error saving bot tokens data: {e}")

def load_data():
    """Load all data from storage"""
    ensure_data_directory()
    load_files_data()
    load_users_data()
    load_bot_tokens_data()
    ai_helper.load_data()  # Load AI-related data

def save_all_data():
    """Save all data to storage"""
    save_files_data()
    save_users_data()
    save_bot_tokens_data()
    ai_helper.save_all_data()  # Save AI-related data

# Telegram API methods
def send_message(chat_id, text, reply_markup=None):
    """Send a message to a specific chat"""
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    
    if reply_markup:
        payload["reply_markup"] = reply_markup
        
    return requests.post(url, json=payload).json()

def send_document(chat_id, file_id, caption=None):
    """Send a document to a specific chat"""
    url = f"{BASE_URL}/sendDocument"
    payload = {
        "chat_id": chat_id,
        "document": file_id
    }
    
    if caption:
        payload["caption"] = caption
        
    return requests.post(url, json=payload).json()

def send_photo(chat_id, file_id, caption=None):
    """Send a photo to a specific chat"""
    url = f"{BASE_URL}/sendPhoto"
    payload = {
        "chat_id": chat_id,
        "photo": file_id
    }
    
    if caption:
        payload["caption"] = caption
        
    return requests.post(url, json=payload).json()

def send_video(chat_id, file_id, caption=None):
    """Send a video to a specific chat"""
    url = f"{BASE_URL}/sendVideo"
    payload = {
        "chat_id": chat_id,
        "video": file_id
    }
    
    if caption:
        payload["caption"] = caption
        
    return requests.post(url, json=payload).json()

def send_audio(chat_id, file_id, caption=None):
    """Send an audio to a specific chat"""
    url = f"{BASE_URL}/sendAudio"
    payload = {
        "chat_id": chat_id,
        "audio": file_id
    }
    
    if caption:
        payload["caption"] = caption
        
    return requests.post(url, json=payload).json()

def get_updates(offset=None):
    """Get updates from Telegram"""
    url = f"{BASE_URL}/getUpdates"
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
        
    return requests.get(url, params=params).json()

def get_file_info(file_id):
    """Get file info from Telegram"""
    url = f"{BASE_URL}/getFile"
    params = {"file_id": file_id}
    
    return requests.get(url, params=params).json()

def get_bot_username():
    """Get the bot's username"""
    url = f"{BASE_URL}/getMe"
    response = requests.get(url).json()
    
    if response.get("ok"):
        return response["result"]["username"]
    return None

# Message handlers
def handle_start_command(message):
    """Handle /start command"""
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    
    # Check if this is a file download command
    text = message.get("text", "")
    if " " in text:
        parts = text.split(" ", 1)
        if len(parts) == 2 and parts[0] == "/start" and parts[1].startswith("dl_"):
            # Extract the file ID
            file_id = parts[1][3:]  # Remove the 'dl_' prefix
            return handle_download(message, file_id)
    
    # Check if user is banned
    if str(user_id) in banned_users:
        return send_message(chat_id, "🚫 You are banned from using this bot.")
    
    # Save user data if new
    if str(user_id) not in user_data:
        user_data[str(user_id)] = {
            "joined_at": int(time.time()),
            "username": message["from"].get("username"),
            "first_name": message["from"].get("first_name"),
            "last_name": message["from"].get("last_name"),
            "stored_files": 0,
            "settings": {
                "receive_broadcast": True,
                "auto_rename_files": False,
                "file_preview": True,
                "link_format": "standard"
            }
        }
        save_users_data()
    
    return send_message(
        chat_id,
        "👋 I am a Permanent File Store Bot!\n"
        "Store and share files with unique links.\n\n"
        "📚 Available Commands:\n"
        "➛ /help - Show help information\n"
        "➛ /genlink - Store one file\n"
        "➛ /files - Browse your files by category\n"
        "➛ /recommend - Get AI-powered file recommendations\n"
        "➛ /settings - Customize your experience\n"
        "➛ /mybot - Set up your own bot token\n\n"
        "Admin Commands:\n"
        "➛ /stats - Show bot stats\n"
        "➛ /broadcast - Send message to all users\n"
        "➛ /ban /unban - User moderation"
    )

def handle_download(message, file_id):
    """Handle file download requests from shared links"""
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    
    # Check if user is banned
    if str(user_id) in banned_users:
        return send_message(chat_id, "🚫 You are banned from using this bot.")
    
    # Check if the file exists
    if file_id not in stored_files:
        return send_message(
            chat_id,
            "⚠️ File not found. It may have been deleted or the link is invalid."
        )
    
    file_info = stored_files[file_id]
    telegram_file_id = file_info["file_id"]
    file_type = file_info.get("type", "document")
    file_name = file_info.get("name", "Unnamed File")
    
    # Update download count if it exists
    if "downloads" in file_info:
        file_info["downloads"] += 1
    else:
        file_info["downloads"] = 1
    
    # Record last access time
    file_info["last_accessed"] = int(time.time())
    
    # Track file access for AI recommendations
    try:
        unique_id = file_info.get("unique_id", file_id)
        ai_helper.track_file_access(unique_id)
        ai_helper.update_user_preferences(user_id, unique_id)
    except Exception as e:
        logger.error(f"Error tracking file access for AI: {e}")
    
    # Save data
    save_files_data()
    
    # Get file metadata info if available
    ai_info = ""
    unique_id = file_info.get("unique_id", file_id)
    if unique_id in ai_helper.file_metadata:
        metadata = ai_helper.file_metadata[unique_id]
        category = metadata.get("category", "")
        tags = metadata.get("tags", [])
        description = metadata.get("description", "")
        
        if category:
            ai_info += f"\n📂 Category: {category}"
        if description:
            ai_info += f"\n📝 {description}"
    
    # Get similar files for recommendation
    try:
        similar_files = ai_helper.get_similar_files(unique_id, stored_files, count=2)
        
        # Add similar files info if available
        if similar_files:
            ai_info += "\n\n<b>You might also like:</b>"
            for sim_id in similar_files:
                sim_file = stored_files.get(sim_id, {})
                sim_name = sim_file.get("name", "Unnamed File")
                sim_bot_username = get_bot_username()
                
                # Check if uploader has a custom bot
                sim_user_id = sim_file.get("from_user_id")
                if sim_user_id and str(sim_user_id) in custom_bot_tokens:
                    sim_bot_username = custom_bot_tokens[str(sim_user_id)]["username"]
                
                sim_link = f"https://t.me/{sim_bot_username}?start=dl_{sim_id}"
                ai_info += f"\n- <a href='{sim_link}'>{sim_name}</a>"
    except Exception as e:
        logger.error(f"Error getting similar files: {e}")
    
    try:
        caption = f"{'🖼️' if file_type == 'photo' else '🎬' if file_type == 'video' else '🎵' if file_type == 'audio' else '📄'} {file_name}{ai_info}"
        
        # Send the file based on type
        if file_type == "photo":
            send_photo(chat_id, telegram_file_id, caption=caption)
        elif file_type == "video":
            send_video(chat_id, telegram_file_id, caption=caption)
        elif file_type == "audio":
            send_audio(chat_id, telegram_file_id, caption=caption)
        else:  # default to document
            send_document(chat_id, telegram_file_id, caption=caption)
    except Exception as e:
        logger.error(f"Error sending file: {e}")
        send_message(
            chat_id,
            "⚠️ Failed to send the file. Please try again later or contact the admin."
        )

def handle_files_command(message):
    """Handle /files command - show user's files organized by category"""
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    
    if str(user_id) in banned_users:
        return send_message(chat_id, "🚫 You are banned from using this bot.")
    
    # Get user's files
    user_files = {}
    for file_id, file_info in stored_files.items():
        if file_info.get("from_user_id") == user_id:
            user_files[file_id] = file_info
    
    if not user_files:
        return send_message(
            chat_id,
            "📂 You haven't stored any files yet.\n"
            "Send me a file to store it and get a shareable link!"
        )
    
    # Organize files by category
    categorized_files = ai_helper.organize_files_by_category(user_files)
    
    # Format the message
    response = "📂 <b>Your Files by Category</b>\n\n"
    
    bot_username = get_bot_username()
    if str(user_id) in custom_bot_tokens:
        bot_data = custom_bot_tokens[str(user_id)]
        bot_username = bot_data["username"]
    
    # Add each category with its files
    for category, files in categorized_files.items():
        response += f"<b>{category}</b> ({len(files)})\n"
        # Show up to 5 files per category
        for i, file_id in enumerate(files[:5]):
            file_info = user_files[file_id]
            file_name = file_info.get("name", "Unnamed File")
            share_link = f"https://t.me/{bot_username}?start=dl_{file_id}"
            response += f"➛ <a href='{share_link}'>{file_name}</a>\n"
        
        # Add "more" indicator if there are more files
        if len(files) > 5:
            response += f"➛ ... and {len(files) - 5} more\n"
        
        response += "\n"
    
    # Add command to browse specific category
    response += "Use /category [name] to browse a specific category"
    
    return send_message(chat_id, response)

def handle_category_command(message):
    """Handle /category command - browse files in a specific category"""
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    
    if str(user_id) in banned_users:
        return send_message(chat_id, "🚫 You are banned from using this bot.")
    
    # Get the category name
    text = message.get("text", "")
    parts = text.split(" ", 1)
    
    if len(parts) < 2:
        # No category specified, show available categories
        return send_message(
            chat_id,
            "📂 Please specify a category name:\n\n"
            "Example: /category Documents\n\n"
            "Available categories:\n" + 
            "\n".join([f"➛ {cat}" for cat in ai_helper.DEFAULT_CATEGORIES])
        )
    
    category_name = parts[1].strip()
    
    # Find matching category (case-insensitive)
    found_category = None
    for cat in ai_helper.DEFAULT_CATEGORIES:
        if cat.lower() == category_name.lower():
            found_category = cat
            break
    
    if not found_category:
        return send_message(
            chat_id,
            f"⚠️ Category '{category_name}' not found.\n\n"
            "Available categories:\n" + 
            "\n".join([f"➛ {cat}" for cat in ai_helper.DEFAULT_CATEGORIES])
        )
    
    # Get user's files
    user_files = {}
    for file_id, file_info in stored_files.items():
        if file_info.get("from_user_id") == user_id:
            user_files[file_id] = file_info
    
    # Get files in the category
    category_files = []
    for file_id, file_info in user_files.items():
        meta_id = file_info.get("unique_id", file_id)
        if meta_id in ai_helper.file_metadata:
            metadata = ai_helper.file_metadata[meta_id]
            if metadata.get("category") == found_category:
                category_files.append((file_id, file_info))
    
    if not category_files:
        return send_message(
            chat_id,
            f"📂 You don't have any files in the '{found_category}' category."
        )
    
    # Format the message
    response = f"📂 <b>Your {found_category}</b> ({len(category_files)})\n\n"
    
    bot_username = get_bot_username()
    if str(user_id) in custom_bot_tokens:
        bot_data = custom_bot_tokens[str(user_id)]
        bot_username = bot_data["username"]
    
    # Add each file
    for file_id, file_info in category_files:
        file_name = file_info.get("name", "Unnamed File")
        share_link = f"https://t.me/{bot_username}?start=dl_{file_id}"
        file_size = format_bytes(file_info.get("size", 0))
        
        # Get tags if available
        tags = ""
        meta_id = file_info.get("unique_id", file_id)
        if meta_id in ai_helper.file_metadata:
            metadata = ai_helper.file_metadata[meta_id]
            if metadata.get("tags"):
                tags = " #" + " #".join(metadata.get("tags", []))
        
        response += f"➛ <a href='{share_link}'>{file_name}</a> ({file_size}){tags}\n"
    
    return send_message(chat_id, response)

def handle_recommend_command(message):
    """Handle /recommend command - show recommended files"""
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    
    if str(user_id) in banned_users:
        return send_message(chat_id, "🚫 You are banned from using this bot.")
    
    # Get recommendations
    recommended_file_ids = ai_helper.get_recommendations(user_id, stored_files, count=8)
    
    if not recommended_file_ids:
        return send_message(
            chat_id,
            "🔍 No recommendations available yet.\n"
            "Try browsing more files to get personalized recommendations!"
        )
    
    # Format the message
    response = "🔍 <b>Recommended Files For You</b>\n\n"
    
    bot_username = get_bot_username()
    
    # Add each recommended file
    for file_id in recommended_file_ids:
        if file_id not in stored_files:
            continue
            
        file_info = stored_files[file_id]
        file_name = file_info.get("name", "Unnamed File")
        file_type = file_info.get("type", "document")
        
        # Check if the file uploader has a custom bot
        uploader_id = file_info.get("from_user_id")
        if uploader_id and str(uploader_id) in custom_bot_tokens:
            file_bot_username = custom_bot_tokens[str(uploader_id)]["username"]
        else:
            file_bot_username = bot_username
            
        share_link = f"https://t.me/{file_bot_username}?start=dl_{file_id}"
        
        # Get file info
        type_emoji = "📄"
        if file_type == "photo":
            type_emoji = "🖼️"
        elif file_type == "video":
            type_emoji = "🎬"
        elif file_type == "audio":
            type_emoji = "🎵"
        
        # Get category if available
        category = ""
        meta_id = file_info.get("unique_id", file_id)
        if meta_id in ai_helper.file_metadata:
            metadata = ai_helper.file_metadata[meta_id]
            if metadata.get("category"):
                category = f" ({metadata.get('category')})"
        
        response += f"{type_emoji} <a href='{share_link}'>{file_name}</a>{category}\n"
    
    return send_message(chat_id, response)

def handle_help_command(message):
    """Handle /help command"""
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    
    if str(user_id) in banned_users:
        return send_message(chat_id, "🚫 You are banned from using this bot.")
    
    help_text = (
        "📖 Help Information\n\n"
        "This bot allows you to store files permanently and share them using unique links.\n\n"
        "How to store a file:\n"
        "1. Send the file to the bot\n"
        "2. OR use /genlink command while replying to a file\n"
        "3. The bot will generate a shareable link\n\n"
        "How to access a stored file:\n"
        "1. Click on the generated link\n"
        "2. The bot will send you the file directly\n\n"
        "User Commands:\n"
        "➛ /files - Browse your files by category\n"
        "➛ /category [name] - Browse specific category\n"
        "➛ /recommend - Get personalized file recommendations\n"
        "➛ /settings - Customize your experience\n"
        "➛ /mybot - Set up your own bot token\n\n"
        "Admin Commands (for bot developers only):\n"
        "➛ /broadcast - Send message to all users\n"
        "➛ /ban - Ban a user from using the bot\n"
        "➛ /unban - Unban a previously banned user\n"
        "➛ /stats - Show bot statistics"
    )
    
    return send_message(chat_id, help_text)

def handle_genlink_command(message):
    """Handle /genlink command - stores a file and generates a shareable link"""
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    
    if str(user_id) in banned_users:
        return send_message(chat_id, "🚫 You are banned from using this bot.")

    # We need a reply to a file message
    if not message.get("reply_to_message"):
        return send_message(chat_id, "⚠️ Reply to a file to store it.")
    
    reply = message["reply_to_message"]
    
    # Check if the reply contains a file
    file_id = None
    file_name = "Unnamed File"
    file_size = 0
    file_type = "document"
    
    if "document" in reply:
        file_id = reply["document"]["file_id"]
        file_name = reply["document"].get("file_name", "document.file")
        file_size = reply["document"].get("file_size", 0)
        file_type = "document"
    elif "video" in reply:
        file_id = reply["video"]["file_id"]
        file_name = "video.mp4"
        file_size = reply["video"].get("file_size", 0)
        file_type = "video"
    elif "audio" in reply:
        file_id = reply["audio"]["file_id"]
        file_name = reply["audio"].get("file_name", "audio.mp3")
        file_size = reply["audio"].get("file_size", 0)
        file_type = "audio"
    elif "photo" in reply:
        # Get the largest photo
        photos = reply["photo"]
        photo = max(photos, key=lambda p: p.get("file_size", 0))
        file_id = photo["file_id"]
        file_name = "photo.jpg"
        file_size = photo.get("file_size", 0)
        file_type = "photo"
    
    if not file_id:
        return send_message(chat_id, "⚠️ No file found in the replied message.")
    
    # Generate a unique ID for the file
    unique_id = str(uuid.uuid4())[:8]
    
    # Store the file
    stored_files[unique_id] = {
        "file_id": file_id,
        "from_user_id": user_id,
        "name": file_name,
        "size": file_size,
        "type": file_type,
        "timestamp": int(time.time())
    }
    
    # Update user's stored files count
    if str(user_id) in user_data:
        user_data[str(user_id)]["stored_files"] += 1
    
    # Save data
    save_files_data()
    save_users_data()
    
    # Get bot username for creating the link
    bot_username = get_bot_username()
    if not bot_username:
        # Fallback in case we can't get the username
        bot_username = "YourBot"
    
    share_link = f"https://t.me/{bot_username}?start=dl_{unique_id}"
    
    return send_message(
        chat_id,
        f"✅ File Stored Successfully!\n\n"
        f"📄 File: {file_name}\n"
        f"💾 Size: {format_bytes(file_size)}\n"
        f"🔗 Shareable Link: {share_link}\n\n"
        f"This link will work permanently as long as the bot is active."
    )

def handle_stats_command(message):
    """Handle /stats command - show bot statistics"""
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    
    if not is_admin(user_id):
        return send_message(chat_id, "❌ This command is for admins only.")
    
    total_files = len(stored_files)
    total_users = len(user_data)
    total_banned = len(banned_users)
    
    total_size = sum(file.get("size", 0) for file in stored_files.values())
    
    return send_message(
        chat_id,
        f"📊 Bot Statistics\n\n"
        f"👥 Total Users: {total_users}\n"
        f"🚫 Banned Users: {total_banned}\n"
        f"📁 Stored Files: {total_files}\n"
        f"💾 Total Storage: {format_bytes(total_size)}"
    )

def handle_document(message):
    """Handle document messages"""
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    
    if str(user_id) in banned_users:
        return send_message(chat_id, "🚫 You are banned from using this bot.")
    
    # Get file info
    document = message["document"]
    file_id = document["file_id"]
    file_name = document.get("file_name", "document.file")
    file_size = document.get("file_size", 0)
    file_type = "document"
    
    # Check if auto-rename is enabled for this user
    if str(user_id) in user_data:
        settings = user_data[str(user_id)].get("settings", {})
        if settings.get("auto_rename_files", False):
            # Generate a timestamp-based name
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            ext = file_name.split(".")[-1] if "." in file_name else "file"
            file_name = f"doc_{timestamp}.{ext}"
    
    # Generate a unique ID for the file
    unique_id = str(uuid.uuid4())[:8]
    
    # Store the file
    file_info = {
        "file_id": file_id,
        "from_user_id": user_id,
        "name": file_name,
        "size": file_size,
        "type": file_type,
        "timestamp": int(time.time()),
        "unique_id": unique_id
    }
    
    stored_files[unique_id] = file_info
    
    # Update user's stored files count
    if str(user_id) in user_data:
        user_data[str(user_id)]["stored_files"] += 1
    else:
        # Create new user entry if it doesn't exist
        user_data[str(user_id)] = {
            "joined_at": int(time.time()),
            "username": message["from"].get("username"),
            "first_name": message["from"].get("first_name"),
            "last_name": message["from"].get("last_name"),
            "stored_files": 1,
            "settings": {
                "receive_broadcast": True,
                "auto_rename_files": False,
                "file_preview": True,
                "link_format": "standard"
            }
        }
    
    # AI analysis of the file
    try:
        # Analyze the file with AI (name-based analysis)
        metadata = ai_helper.analyze_file_with_ai(file_info)
        
        # Store the metadata
        ai_helper.file_metadata[unique_id] = metadata
        
        # Update user preferences based on this file
        ai_helper.update_user_preferences(user_id, unique_id)
    except Exception as e:
        logger.error(f"Error during AI analysis: {e}")
    
    # Save all data
    save_files_data()
    save_users_data()
    ai_helper.save_file_metadata()
    
    # Get bot username for creating the link
    bot_username = get_bot_username()
    if not bot_username:
        # Fallback in case we can't get the username
        bot_username = "YourBot"
    
    # Check if user has a custom bot
    if str(user_id) in custom_bot_tokens:
        bot_data = custom_bot_tokens[str(user_id)]
        bot_username = bot_data["username"]
    
    # Generate link based on user preferences
    link_format = user_data[str(user_id)].get("settings", {}).get("link_format", "standard")
    share_link = f"https://t.me/{bot_username}?start=dl_{unique_id}"
    
    # Get file category and tags if available
    ai_info = ""
    if unique_id in ai_helper.file_metadata:
        metadata = ai_helper.file_metadata[unique_id]
        category = metadata.get("category", "")
        tags = metadata.get("tags", [])
        
        if category:
            ai_info += f"📂 Category: {category}\n"
        if tags:
            ai_info += f"🏷️ Tags: {', '.join(tags)}\n"
    
    return send_message(
        chat_id,
        f"✅ File Stored Successfully!\n\n"
        f"📄 File: {file_name}\n"
        f"💾 Size: {format_bytes(file_size)}\n"
        f"{ai_info}"
        f"🔗 Shareable Link: {share_link}\n\n"
        f"This link will work permanently as long as the bot is active."
    )

def handle_broadcast_command(message):
    """Handle /broadcast command - broadcast message to all users"""
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    
    if not is_admin(user_id):
        return send_message(chat_id, "❌ This command is for admins only.")
    
    # Check if there's a reply message to broadcast
    if not message.get("reply_to_message"):
        return send_message(
            chat_id,
            "⚠️ Please reply to a message you want to broadcast to all users."
        )
    
    # Get the message to broadcast
    reply = message["reply_to_message"]
    if "text" not in reply:
        return send_message(
            chat_id,
            "⚠️ Can only broadcast text messages at this time."
        )
    
    broadcast_text = reply["text"]
    
    # Add a header to indicate it's a broadcast
    formatted_message = f"📢 <b>Broadcast from Admin</b>\n\n{broadcast_text}"
    
    # Count users who will receive the broadcast
    count = 0
    
    # Send to all users who have opted to receive broadcasts
    for user_id, data in user_data.items():
        if user_id in banned_users:
            continue
        
        # Check if user has opted to receive broadcasts
        settings = data.get("settings", {})
        if settings.get("receive_broadcast", True):
            try:
                send_message(user_id, formatted_message)
                count += 1
            except Exception as e:
                logger.error(f"Error sending broadcast to user {user_id}: {e}")
    
    return send_message(
        chat_id,
        f"✅ Broadcast sent to {count} users."
    )

def handle_ban_command(message):
    """Handle /ban command - ban a user"""
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    
    if not is_admin(user_id):
        return send_message(chat_id, "❌ This command is for admins only.")
    
    # Get the user ID to ban
    text = message.get("text", "")
    parts = text.split(" ", 1)
    
    if len(parts) != 2:
        return send_message(
            chat_id,
            "⚠️ Please provide a user ID to ban. Example: /ban 123456789"
        )
    
    try:
        target_user_id = parts[1].strip()
        banned_users.add(str(target_user_id))
        save_users_data()
        
        return send_message(
            chat_id,
            f"✅ User {target_user_id} has been banned."
        )
    except Exception as e:
        logger.error(f"Error banning user: {e}")
        return send_message(
            chat_id,
            "⚠️ Failed to ban user. Please check the user ID."
        )

def handle_unban_command(message):
    """Handle /unban command - unban a user"""
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    
    if not is_admin(user_id):
        return send_message(chat_id, "❌ This command is for admins only.")
    
    # Get the user ID to unban
    text = message.get("text", "")
    parts = text.split(" ", 1)
    
    if len(parts) != 2:
        return send_message(
            chat_id,
            "⚠️ Please provide a user ID to unban. Example: /unban 123456789"
        )
    
    try:
        target_user_id = parts[1].strip()
        if str(target_user_id) in banned_users:
            banned_users.remove(str(target_user_id))
            save_users_data()
            
            return send_message(
                chat_id,
                f"✅ User {target_user_id} has been unbanned."
            )
        else:
            return send_message(
                chat_id,
                f"ℹ️ User {target_user_id} is not banned."
            )
    except Exception as e:
        logger.error(f"Error unbanning user: {e}")
        return send_message(
            chat_id,
            "⚠️ Failed to unban user. Please check the user ID."
        )

def handle_mybot_command(message):
    """Handle /mybot command - set up user's own bot token"""
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    
    if str(user_id) in banned_users:
        return send_message(chat_id, "🚫 You are banned from using this bot.")
    
    # Check if there's a token provided
    text = message.get("text", "")
    parts = text.split(" ", 1)
    
    if len(parts) == 1:
        # No token provided, show instructions
        if str(user_id) in custom_bot_tokens:
            # User already has a token
            return send_message(
                chat_id,
                "🤖 You already have a bot token set up.\n\n"
                "To update your bot token, use:\n"
                "/mybot YOUR_NEW_BOT_TOKEN\n\n"
                "To remove your bot token, use:\n"
                "/mybot remove"
            )
        else:
            # No token set up yet
            return send_message(
                chat_id,
                "🤖 Set up your own Telegram bot to use this file storage system.\n\n"
                "Steps to get your bot token:\n"
                "1. Talk to @BotFather on Telegram\n"
                "2. Create a new bot with /newbot command\n"
                "3. Copy the API token BotFather gives you\n"
                "4. Submit it here with /mybot YOUR_BOT_TOKEN\n\n"
                "Your files will be available through your own bot!"
            )
    
    # Token provided or removal requested
    token_input = parts[1].strip()
    
    if token_input.lower() == "remove":
        # Remove the token
        if str(user_id) in custom_bot_tokens:
            del custom_bot_tokens[str(user_id)]
            save_bot_tokens_data()
            return send_message(
                chat_id,
                "✅ Your bot token has been removed. You will now use the default bot."
            )
        else:
            return send_message(
                chat_id,
                "ℹ️ You don't have a custom bot set up."
            )
    
    # Validate the token format (simple check)
    if not token_input or ":" not in token_input:
        return send_message(
            chat_id,
            "⚠️ Invalid bot token format. Please get a valid token from @BotFather."
        )
    
    # Test the token
    try:
        test_url = f"https://api.telegram.org/bot{token_input}/getMe"
        response = requests.get(test_url).json()
        
        if response.get("ok"):
            # Token is valid, save it
            bot_username = response["result"]["username"]
            custom_bot_tokens[str(user_id)] = {
                "token": token_input,
                "username": bot_username,
                "created_at": int(time.time())
            }
            save_bot_tokens_data()
            
            return send_message(
                chat_id,
                f"✅ Bot token for @{bot_username} set up successfully!\n\n"
                f"Your shared files will now be accessible through your bot."
            )
        else:
            return send_message(
                chat_id,
                "⚠️ Invalid bot token. Please verify your token and try again."
            )
    except Exception as e:
        logger.error(f"Error testing bot token: {e}")
        return send_message(
            chat_id,
            "⚠️ Failed to verify bot token. Please check your internet connection and try again."
        )

def handle_video_message(message):
    """Handle video messages"""
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    
    if str(user_id) in banned_users:
        return send_message(chat_id, "🚫 You are banned from using this bot.")
    
    # Get video info
    video = message["video"]
    file_id = video["file_id"]
    file_name = "video.mp4"
    file_size = video.get("file_size", 0)
    file_type = "video"
    
    # Check if auto-rename is enabled for this user
    if str(user_id) in user_data:
        settings = user_data[str(user_id)].get("settings", {})
        if settings.get("auto_rename_files", False):
            # Generate a timestamp-based name
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            file_name = f"video_{timestamp}.mp4"
    
    # Generate a unique ID for the file
    unique_id = str(uuid.uuid4())[:8]
    
    # Store the file
    stored_files[unique_id] = {
        "file_id": file_id,
        "from_user_id": user_id,
        "name": file_name,
        "size": file_size,
        "type": file_type,
        "timestamp": int(time.time())
    }
    
    # Update user's stored files count
    if str(user_id) in user_data:
        user_data[str(user_id)]["stored_files"] += 1
    else:
        user_data[str(user_id)] = {
            "joined_at": int(time.time()),
            "username": message["from"].get("username"),
            "first_name": message["from"].get("first_name"),
            "last_name": message["from"].get("last_name"),
            "stored_files": 1,
            "settings": {
                "receive_broadcast": True,
                "auto_rename_files": False,
                "file_preview": True,
                "link_format": "standard"
            }
        }
    
    # Save data
    save_files_data()
    save_users_data()
    
    # Get bot username for creating the link
    bot_username = get_bot_username()
    if not bot_username:
        # Fallback in case we can't get the username
        bot_username = "YourBot"
    
    # Check if user has a custom bot
    if str(user_id) in custom_bot_tokens:
        bot_data = custom_bot_tokens[str(user_id)]
        bot_username = bot_data["username"]
    
    # Generate link based on user preferences
    link_format = user_data[str(user_id)].get("settings", {}).get("link_format", "standard")
    
    if link_format == "short":
        # Short link format (simplified)
        share_link = f"https://t.me/{bot_username}?start=dl_{unique_id}"
    else:
        # Standard link format with more details
        share_link = f"https://t.me/{bot_username}?start=dl_{unique_id}"
    
    return send_message(
        chat_id,
        f"✅ Video Stored Successfully!\n\n"
        f"💾 Size: {format_bytes(file_size)}\n"
        f"🔗 Shareable Link: {share_link}\n\n"
        f"This link will work permanently as long as the bot is active."
    )

def handle_audio_message(message):
    """Handle audio messages"""
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    
    if str(user_id) in banned_users:
        return send_message(chat_id, "🚫 You are banned from using this bot.")
    
    # Get audio info
    audio = message["audio"]
    file_id = audio["file_id"]
    file_name = audio.get("file_name", "audio.mp3")
    file_size = audio.get("file_size", 0)
    file_type = "audio"
    
    # Check if auto-rename is enabled for this user
    if str(user_id) in user_data:
        settings = user_data[str(user_id)].get("settings", {})
        if settings.get("auto_rename_files", False):
            # Generate a timestamp-based name
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            ext = file_name.split(".")[-1] if "." in file_name else "mp3"
            file_name = f"audio_{timestamp}.{ext}"
    
    # Generate a unique ID for the file
    unique_id = str(uuid.uuid4())[:8]
    
    # Store the file
    stored_files[unique_id] = {
        "file_id": file_id,
        "from_user_id": user_id,
        "name": file_name,
        "size": file_size,
        "type": file_type,
        "timestamp": int(time.time())
    }
    
    # Update user's stored files count
    if str(user_id) in user_data:
        user_data[str(user_id)]["stored_files"] += 1
    else:
        user_data[str(user_id)] = {
            "joined_at": int(time.time()),
            "username": message["from"].get("username"),
            "first_name": message["from"].get("first_name"),
            "last_name": message["from"].get("last_name"),
            "stored_files": 1,
            "settings": {
                "receive_broadcast": True,
                "auto_rename_files": False,
                "file_preview": True,
                "link_format": "standard"
            }
        }
    
    # Save data
    save_files_data()
    save_users_data()
    
    # Get bot username for creating the link
    bot_username = get_bot_username()
    if not bot_username:
        # Fallback in case we can't get the username
        bot_username = "YourBot"
    
    # Check if user has a custom bot
    if str(user_id) in custom_bot_tokens:
        bot_data = custom_bot_tokens[str(user_id)]
        bot_username = bot_data["username"]
    
    # Generate link based on user preferences
    link_format = user_data[str(user_id)].get("settings", {}).get("link_format", "standard")
    
    if link_format == "short":
        # Short link format (simplified)
        share_link = f"https://t.me/{bot_username}?start=dl_{unique_id}"
    else:
        # Standard link format with more details
        share_link = f"https://t.me/{bot_username}?start=dl_{unique_id}"
    
    return send_message(
        chat_id,
        f"✅ Audio Stored Successfully!\n\n"
        f"💾 Size: {format_bytes(file_size)}\n"
        f"🔗 Shareable Link: {share_link}\n\n"
        f"This link will work permanently as long as the bot is active."
    )

def handle_photo(message):
    """Handle photo messages"""
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    
    if str(user_id) in banned_users:
        return send_message(chat_id, "🚫 You are banned from using this bot.")
    
    # Get the largest photo
    photos = message["photo"]
    photo = max(photos, key=lambda p: p.get("file_size", 0))
    file_id = photo["file_id"]
    file_name = "photo.jpg"
    file_size = photo.get("file_size", 0)
    file_type = "photo"
    
    # Check if auto-rename is enabled for this user
    if str(user_id) in user_data:
        settings = user_data[str(user_id)].get("settings", {})
        if settings.get("auto_rename_files", False):
            # Generate a timestamp-based name
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            file_name = f"photo_{timestamp}.jpg"
    
    # Generate a unique ID for the file
    unique_id = str(uuid.uuid4())[:8]
    
    # Store the file
    stored_files[unique_id] = {
        "file_id": file_id,
        "from_user_id": user_id,
        "name": file_name,
        "size": file_size,
        "type": file_type,
        "timestamp": int(time.time())
    }
    
    # Update user's stored files count
    if str(user_id) in user_data:
        user_data[str(user_id)]["stored_files"] += 1
    else:
        user_data[str(user_id)] = {
            "joined_at": int(time.time()),
            "username": message["from"].get("username"),
            "first_name": message["from"].get("first_name"),
            "last_name": message["from"].get("last_name"),
            "stored_files": 1,
            "settings": {
                "receive_broadcast": True,
                "auto_rename_files": False,
                "file_preview": True,
                "link_format": "standard"
            }
        }
    
    # Save data
    save_files_data()
    save_users_data()
    
    # Get bot username for creating the link
    bot_username = get_bot_username()
    if not bot_username:
        # Fallback in case we can't get the username
        bot_username = "YourBot"
    
    # Check if user has a custom bot
    if str(user_id) in custom_bot_tokens:
        bot_data = custom_bot_tokens[str(user_id)]
        bot_username = bot_data["username"]
    
    # Generate link based on user preferences
    link_format = user_data[str(user_id)].get("settings", {}).get("link_format", "standard")
    
    if link_format == "short":
        # Short link format (simplified)
        share_link = f"https://t.me/{bot_username}?start=dl_{unique_id}"
    else:
        # Standard link format with more details
        share_link = f"https://t.me/{bot_username}?start=dl_{unique_id}"
    
    return send_message(
        chat_id,
        f"✅ Photo Stored Successfully!\n\n"
        f"💾 Size: {format_bytes(file_size)}\n"
        f"🔗 Shareable Link: {share_link}\n\n"
        f"This link will work permanently as long as the bot is active."
    )

def handle_settings_command(message):
    """Handle /settings command - user settings"""
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    
    if str(user_id) in banned_users:
        return send_message(chat_id, "🚫 You are banned from using this bot.")
    
    # Create user data if it doesn't exist
    if str(user_id) not in user_data:
        user_data[str(user_id)] = {
            "joined_at": int(time.time()),
            "username": message["from"].get("username"),
            "first_name": message["from"].get("first_name"),
            "last_name": message["from"].get("last_name"),
            "stored_files": 0,
            "settings": {
                "receive_broadcast": True,
                "auto_rename_files": False,
                "file_preview": True,
                "link_format": "standard"  # standard or short
            }
        }
    
    # Get current settings
    user_settings = user_data[str(user_id)].get("settings", {})
    
    # Create settings message
    settings_text = (
        "⚙️ <b>User Settings</b>\n\n"
        f"📢 Receive broadcast messages: {'✅ On' if user_settings.get('receive_broadcast', True) else '❌ Off'}\n"
        f"🔄 Auto-rename files: {'✅ On' if user_settings.get('auto_rename_files', False) else '❌ Off'}\n"
        f"👁️ File preview: {'✅ On' if user_settings.get('file_preview', True) else '❌ Off'}\n"
        f"🔗 Link format: {'Standard' if user_settings.get('link_format', 'standard') == 'standard' else 'Short'}\n\n"
        "Use the following commands to change settings:\n"
        "/settings_broadcast - Toggle broadcast messages\n"
        "/settings_rename - Toggle auto-rename files\n"
        "/settings_preview - Toggle file preview\n"
        "/settings_link - Toggle link format\n"
    )
    
    return send_message(chat_id, settings_text)

def handle_settings_toggle(message, setting_key):
    """Handle settings toggle commands"""
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    
    if str(user_id) in banned_users:
        return send_message(chat_id, "🚫 You are banned from using this bot.")
    
    # Create user data if it doesn't exist
    if str(user_id) not in user_data:
        user_data[str(user_id)] = {
            "joined_at": int(time.time()),
            "username": message["from"].get("username"),
            "first_name": message["from"].get("first_name"),
            "last_name": message["from"].get("last_name"),
            "stored_files": 0,
            "settings": {
                "receive_broadcast": True,
                "auto_rename_files": False,
                "file_preview": True,
                "link_format": "standard"
            }
        }
    
    # Get current settings
    user_settings = user_data[str(user_id)].get("settings", {})
    
    setting_details = {
        "broadcast": {
            "name": "Receive broadcast messages",
            "key": "receive_broadcast",
            "default": True
        },
        "rename": {
            "name": "Auto-rename files",
            "key": "auto_rename_files",
            "default": False
        },
        "preview": {
            "name": "File preview",
            "key": "file_preview",
            "default": True
        },
        "link": {
            "name": "Link format",
            "key": "link_format",
            "default": "standard",
            "is_enum": True,
            "values": ["standard", "short"]
        }
    }
    
    if setting_key not in setting_details:
        return send_message(chat_id, "⚠️ Invalid setting key.")
    
    setting = setting_details[setting_key]
    current_key = setting["key"]
    
    # Toggle or cycle through values
    if setting.get("is_enum"):
        values = setting["values"]
        current_value = user_settings.get(current_key, setting["default"])
        current_index = values.index(current_value) if current_value in values else 0
        new_value = values[(current_index + 1) % len(values)]
        user_settings[current_key] = new_value
        value_text = new_value.capitalize()
    else:
        current_value = user_settings.get(current_key, setting["default"])
        user_settings[current_key] = not current_value
        value_text = "On" if user_settings[current_key] else "Off"
    
    # Save updated settings
    user_data[str(user_id)]["settings"] = user_settings
    save_users_data()
    
    return send_message(
        chat_id,
        f"✅ Setting updated: {setting['name']} is now {value_text}"
    )

def handle_update(update):
    """Handle updates from Telegram"""
    # Check if the update contains a message
    if "message" not in update:
        return
    
    message = update["message"]
    
    # Check if the message contains text
    if "text" in message:
        text = message["text"]
        
        # Handle commands
        if text.startswith("/start"):
            return handle_start_command(message)
        elif text == "/help":
            return handle_help_command(message)
        elif text == "/genlink":
            return handle_genlink_command(message)
        elif text == "/stats":
            return handle_stats_command(message)
        elif text == "/settings":
            return handle_settings_command(message)
        elif text == "/settings_broadcast":
            return handle_settings_toggle(message, "broadcast")
        elif text == "/settings_rename":
            return handle_settings_toggle(message, "rename") 
        elif text == "/settings_preview":
            return handle_settings_toggle(message, "preview")
        elif text == "/settings_link":
            return handle_settings_toggle(message, "link")
        elif text.startswith("/mybot"):
            return handle_mybot_command(message)
        elif text.startswith("/broadcast"):
            return handle_broadcast_command(message)
        elif text.startswith("/ban"):
            return handle_ban_command(message)
        elif text.startswith("/unban"):
            return handle_unban_command(message)
        # AI-powered file organization commands
        elif text == "/files":
            return handle_files_command(message)
        elif text.startswith("/category"):
            return handle_category_command(message)
        elif text == "/recommend":
            return handle_recommend_command(message)
    
    # Handle documents
    if "document" in message:
        return handle_document(message)
    
    # Handle photos
    if "photo" in message:
        return handle_photo(message)
    
    # Handle videos
    if "video" in message:
        return handle_video_message(message)
    
    # Handle audio
    if "audio" in message:
        return handle_audio_message(message)

def main():
    """Main function to run the bot"""
    # Ensure TOKEN is available
    if not TOKEN:
        logger.error("No BOT_TOKEN environment variable found.")
        return
    
    # Load data
    load_data()
    
    # Get bot info
    bot_info = requests.get(f"{BASE_URL}/getMe").json()
    if not bot_info.get("ok"):
        logger.error(f"Failed to get bot info: {bot_info}")
        return
    
    bot_username = bot_info["result"]["username"]
    logger.info(f"Bot @{bot_username} is starting...")
    
    # Main loop to get updates
    offset = None
    
    while True:
        try:
            # Get updates
            updates = get_updates(offset)
            
            if not updates.get("ok"):
                logger.error(f"Failed to get updates: {updates}")
                time.sleep(5)
                continue
            
            # Process updates
            for update in updates["result"]:
                handle_update(update)
                offset = update["update_id"] + 1
            
            # Periodically save data
            save_all_data()
            
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()