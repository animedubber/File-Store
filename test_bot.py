#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test bot to check if python-telegram-bot is working correctly"""

import os
import logging
from telegram.ext import Updater, CommandHandler

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hello! I am a test bot.')

def help_command(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')

def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token
    token = os.environ.get("BOT_TOKEN", "")
    if not token:
        logger.error("No BOT_TOKEN environment variable found. Please set it.")
        return
        
    updater = Updater(token)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # Start the Bot
    logger.info("Starting bot")
    updater.start_polling()
    
    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()