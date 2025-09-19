#!/usr/bin/env python3
"""
Minimal production startup script for BearTech Bot on Render - v20 only
"""
import os
import logging
from multiprocessing import Process

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('beartech_bot.log')
    ]
)

logger = logging.getLogger(__name__)

def run_health_server():
    """Run the health check server in a separate process"""
    try:
        from health_check import app
        port = int(os.getenv("PORT", 8000))
        logger.info(f"Starting health check server on port {port}")
        app.run(host="0.0.0.0", port=port)
    except Exception as e:
        logger.error(f"Health server error: {str(e)}")

def run_bot():
    """Run the Telegram bot using v20 Application.run_polling() - MINIMAL"""
    try:
        from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler
        from telegram import BotCommand, Update, InlineKeyboardButton, InlineKeyboardMarkup
        from telegram.ext import ContextTypes
        from telegram.constants import ParseMode
        
        logger.info("Starting BearTech Bot with MINIMAL v20 Application.run_polling()...")
        
        # Build application
        application = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
        
        # Add basic handlers directly (no imports from src)
        async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text("🤖 BearTech Token Analysis Bot is running!")
        
        async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text("📊 Send a token contract address to analyze it.")
        
        async def analyze_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text("🔍 Token analysis feature will be available soon!")
        
        # Add handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("analyze", analyze_token))
        
        # Set bot commands
        async def set_commands():
            commands = [
                BotCommand("start", "Start the bot and see welcome message"),
                BotCommand("help", "Show detailed help and usage instructions"),
                BotCommand("analyze", "Analyze a specific token contract address"),
            ]
            await application.bot.set_my_commands(commands)
            logger.info("Bot commands set successfully")
        
        # Run polling (blocking) - NO Updater
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"]
        )
    except Exception as e:
        logger.error(f"Bot error: {str(e)}")
        raise

def main():
    """Main production startup function"""
    logger.info("Starting BearTech Bot in production mode...")
    
    # Check required environment variables
    required_vars = ["TELEGRAM_BOT_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        return
    
    # Start health check server in a separate process
    health_process = Process(target=run_health_server)
    health_process.start()
    
    # Start the bot in the main process
    try:
        run_bot()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
    finally:
        # Clean up health server process
        if health_process.is_alive():
            health_process.terminate()
            health_process.join()

if __name__ == "__main__":
    main()
