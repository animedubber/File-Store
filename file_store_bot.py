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
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, CallbackQueryHandler,
    Filters, CallbackContext
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Configuration
TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
DEVELOPER_ID = int(os.environ.get("DEVELOPER_ID", "123456789"))
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB maximum file size

# Data storage
DATA_DIR = "data"
FILES_DATA = os.path.join(DATA_DIR, "files.json")
USERS_DATA = os.path.join(DATA_DIR, "users.json")

# In-memory databases
stored_files = {}  # unique_id: file_info
user_data = {}     # user_id: user_info
banned_users = set()  # set of banned user IDs

# Utility functions
def is_admin(user_id):
    """Check if user is an admin"""
    return user_id == DEVELOPER_ID

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

def make_keyboard():
    """Create a basic keyboard with developer contact"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{DEVELOPER_ID}")]
    ])

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

def load_data():
    """Load all data from storage"""
    ensure_data_directory()
    load_files_data()
    load_users_data()

def save_all_data():
    """Save all data to storage"""
    save_files_data()
    save_users_data()

# Command handlers
def start_command(update: Update, context: CallbackContext):
    """Handler for /start command"""
    # Check if this is a file download command
    text = update.message.text
    if text and " " in text:
        parts = text.split(" ", 1)
        if len(parts) == 2 and parts[0] == "/start" and parts[1].startswith("dl_"):
            # Extract the file ID
            file_id = parts[1][3:]  # Remove the 'dl_' prefix
            return handle_download(update, context, file_id)
    
    user_id = update.effective_user.id
    
    # Check if user is banned
    if user_id in banned_users:
        return update.message.reply_text("🚫 You are banned from using this bot.")
    
    # Save user data if new
    if str(user_id) not in user_data:
        user_data[str(user_id)] = {
            "joined_at": int(time.time()),
            "username": update.effective_user.username,
            "first_name": update.effective_user.first_name,
            "last_name": update.effective_user.last_name,
            "stored_files": 0,
            "settings": {
                "receive_broadcast": True
            }
        }
        save_users_data()
    
    update.message.reply_text(
        "👋 I am a Permanent File Store Bot!\n"
        "Store and share files with unique links.\n\n"
        "📚 Available Commands:\n"
        "➛ /help - Show help information\n"
        "➛ /genlink - Store one file\n"
        "➛ /stats - Show bot stats (admin only)\n"
        "➛ /broadcast - Send message to all users (admin only)\n"
        "➛ /ban /unban - Admin moderation (admin only)",
        reply_markup=make_keyboard()
    )

def handle_download(update: Update, context: CallbackContext, file_id: str):
    """Handle file download requests from shared links"""
    user_id = update.effective_user.id
    
    # Check if user is banned
    if user_id in banned_users:
        return update.message.reply_text("🚫 You are banned from using this bot.")
    
    # Check if the file exists
    if file_id not in stored_files:
        return update.message.reply_text(
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
    
    # Save data
    save_files_data()
    
    try:
        # Send the file based on type
        if file_type == "photo":
            update.message.reply_photo(
                telegram_file_id, 
                caption=f"🖼️ {file_name}"
            )
        elif file_type == "video":
            update.message.reply_video(
                telegram_file_id, 
                caption=f"🎬 {file_name}"
            )
        elif file_type == "audio":
            update.message.reply_audio(
                telegram_file_id, 
                caption=f"🎵 {file_name}"
            )
        else:  # default to document
            update.message.reply_document(
                telegram_file_id, 
                caption=f"📄 {file_name}"
            )
    except Exception as e:
        logger.error(f"Error sending file: {e}")
        update.message.reply_text(
            "⚠️ Failed to send the file. Please try again later or contact the admin."
        )

def help_command(update: Update, context: CallbackContext):
    """Handler for /help command"""
    user_id = update.effective_user.id
    
    if user_id in banned_users:
        return update.message.reply_text("🚫 You are banned from using this bot.")
    
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
        "Admin Commands (for bot developers only):\n"
        "➛ /broadcast - Send message to all users\n"
        "➛ /ban - Ban a user from using the bot\n"
        "➛ /unban - Unban a previously banned user\n"
        "➛ /stats - Show bot statistics"
    )
    
    update.message.reply_text(help_text)

def genlink_command(update: Update, context: CallbackContext):
    """Handler for /genlink command - stores a file and generates a shareable link"""
    user_id = update.effective_user.id
    
    if user_id in banned_users:
        return update.message.reply_text("🚫 You are banned from using this bot.")

    reply = update.message.reply_to_message
    if not reply or not (reply.document or reply.video or reply.audio or reply.photo):
        return update.message.reply_text("⚠️ Reply to a file to store it.")
    
    # Generate a unique ID for the file
    unique_id = str(uuid.uuid4())[:8]
    
    # Get file info based on type
    if reply.document:
        file_id = reply.document.file_id
        file_name = reply.document.file_name
        file_size = reply.document.file_size
        file_type = "document"
    elif reply.video:
        file_id = reply.video.file_id
        file_name = "video.mp4"
        file_size = reply.video.file_size
        file_type = "video"
    elif reply.audio:
        file_id = reply.audio.file_id
        file_name = getattr(reply.audio, "file_name", "audio.mp3")
        file_size = reply.audio.file_size
        file_type = "audio"
    else:  # photo
        file_id = reply.photo[-1].file_id
        file_name = "photo.jpg"
        file_size = reply.photo[-1].file_size
        file_type = "photo"
    
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
    
    share_link = f"https://t.me/{context.bot.username}?start=dl_{unique_id}"
    
    update.message.reply_text(
        f"✅ File Stored Successfully!\n\n"
        f"📄 File: {file_name}\n"
        f"💾 Size: {format_bytes(file_size)}\n"
        f"🔗 Shareable Link: {share_link}\n\n"
        f"This link will work permanently as long as the bot is active."
    )

def stats_command(update: Update, context: CallbackContext):
    """Handler for /stats command - show bot statistics"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return update.message.reply_text("❌ This command is for admins only.")
    
    total_files = len(stored_files)
    total_users = len(user_data)
    total_banned = len(banned_users)
    
    total_size = sum(file.get("size", 0) for file in stored_files.values())
    
    update.message.reply_text(
        f"📊 Bot Statistics\n\n"
        f"👥 Total Users: {total_users}\n"
        f"🚫 Banned Users: {total_banned}\n"
        f"📁 Stored Files: {total_files}\n"
        f"💾 Total Storage: {format_bytes(total_size)}"
    )

def broadcast_command(update: Update, context: CallbackContext):
    """Handler for /broadcast command - broadcast message to all users"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return update.message.reply_text("❌ This command is for admins only.")
    
    if not context.args:
        return update.message.reply_text("⚠️ Usage: /broadcast <message>")
    
    message = " ".join(context.args)
    
    sent_count = 0
    failed_count = 0
    
    update.message.reply_text("📢 Starting broadcast...")
    
    for user_id_str, user_info in user_data.items():
        if user_info.get("settings", {}).get("receive_broadcast", True):
            try:
                user_id = int(user_id_str)
                context.bot.send_message(
                    chat_id=user_id,
                    text=f"📢 Broadcast Message:\n\n{message}"
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send broadcast to {user_id_str}: {e}")
                failed_count += 1
    
    update.message.reply_text(
        f"📢 Broadcast Completed\n\n"
        f"✅ Successfully sent: {sent_count}\n"
        f"❌ Failed: {failed_count}"
    )

def ban_command(update: Update, context: CallbackContext):
    """Handler for /ban command - ban a user"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return update.message.reply_text("❌ This command is for admins only.")
    
    if not context.args:
        return update.message.reply_text("⚠️ Usage: /ban <user_id>")
    
    try:
        target_id = int(context.args[0])
        banned_users.add(target_id)
        save_users_data()
        update.message.reply_text(f"🚫 User {target_id} has been banned.")
    except ValueError:
        update.message.reply_text("⚠️ Invalid user ID. Please provide a valid numeric ID.")

def unban_command(update: Update, context: CallbackContext):
    """Handler for /unban command - unban a user"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return update.message.reply_text("❌ This command is for admins only.")
    
    if not context.args:
        return update.message.reply_text("⚠️ Usage: /unban <user_id>")
    
    try:
        target_id = int(context.args[0])
        if target_id in banned_users:
            banned_users.remove(target_id)
            save_users_data()
            update.message.reply_text(f"✅ User {target_id} has been unbanned.")
        else:
            update.message.reply_text(f"ℹ️ User {target_id} is not banned.")
    except ValueError:
        update.message.reply_text("⚠️ Invalid user ID. Please provide a valid numeric ID.")

def file_handler(update: Update, context: CallbackContext):
    """Handler for directly sent files (document, video, audio)"""
    user_id = update.effective_user.id
    
    if user_id in banned_users:
        return update.message.reply_text("🚫 You are banned from using this bot.")
    
    # Process the file
    message = update.message
    
    # Get file info based on type
    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name
        file_size = message.document.file_size
        file_type = "document"
    elif message.video:
        file_id = message.video.file_id
        file_name = "video.mp4"
        file_size = message.video.file_size
        file_type = "video"
    elif message.audio:
        file_id = message.audio.file_id
        file_name = getattr(message.audio, "file_name", "audio.mp3")
        file_size = message.audio.file_size
        file_type = "audio"
    else:
        return
    
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
        # Create new user entry if it doesn't exist
        user_data[str(user_id)] = {
            "joined_at": int(time.time()),
            "username": update.effective_user.username,
            "first_name": update.effective_user.first_name,
            "last_name": update.effective_user.last_name,
            "stored_files": 1,
            "settings": {
                "receive_broadcast": True
            }
        }
    
    # Save data
    save_files_data()
    save_users_data()
    
    share_link = f"https://t.me/{context.bot.username}?start=dl_{unique_id}"
    
    update.message.reply_text(
        f"✅ File Stored Successfully!\n\n"
        f"📄 File: {file_name}\n"
        f"💾 Size: {format_bytes(file_size)}\n"
        f"🔗 Shareable Link: {share_link}\n\n"
        f"This link will work permanently as long as the bot is active."
    )

def photo_handler(update: Update, context: CallbackContext):
    """Handler for directly sent photos"""
    user_id = update.effective_user.id
    
    if user_id in banned_users:
        return update.message.reply_text("🚫 You are banned from using this bot.")
    
    # Get the highest quality photo
    photo = update.message.photo[-1]
    file_id = photo.file_id
    file_name = "photo.jpg"
    file_size = photo.file_size
    file_type = "photo"
    
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
            "username": update.effective_user.username,
            "first_name": update.effective_user.first_name,
            "last_name": update.effective_user.last_name,
            "stored_files": 1,
            "settings": {
                "receive_broadcast": True
            }
        }
    
    # Save data
    save_files_data()
    save_users_data()
    
    share_link = f"https://t.me/{context.bot.username}?start=dl_{unique_id}"
    
    update.message.reply_text(
        f"✅ Photo Stored Successfully!\n\n"
        f"💾 Size: {format_bytes(file_size)}\n"
        f"🔗 Shareable Link: {share_link}\n\n"
        f"This link will work permanently as long as the bot is active."
    )

def error_handler(update, context):
    """Log errors caused by Updates."""
    logger.warning(f'Update "{update}" caused error "{context.error}"')

def scheduled_data_save(context: CallbackContext):
    """Function to save data periodically"""
    save_all_data()
    logger.info("Performed scheduled data save")

def main() -> None:
    """Start the bot"""
    # Load data from storage
    load_data()
    
    # Create updater
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    # Add command handlers
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("genlink", genlink_command))
    dispatcher.add_handler(CommandHandler("stats", stats_command))
    dispatcher.add_handler(CommandHandler("broadcast", broadcast_command))
    dispatcher.add_handler(CommandHandler("ban", ban_command))
    dispatcher.add_handler(CommandHandler("unban", unban_command))
    
    # Add message handlers for files
    dispatcher.add_handler(MessageHandler(
        Filters.photo, photo_handler
    ))
    dispatcher.add_handler(MessageHandler(
        Filters.audio | Filters.document | Filters.video,
        file_handler
    ))
    
    # Register error handler
    dispatcher.add_error_handler(error_handler)
    
    # Schedule periodic data saving
    job_queue = updater.job_queue
    job_queue.run_repeating(scheduled_data_save, interval=300, first=300)
    
    # Start the Bot
    logger.info("📦 File Store Bot is Starting...")
    
    # Run the bot until the user presses Ctrl-C
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()