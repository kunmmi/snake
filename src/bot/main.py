"""
Main entry point for BearTech Token Analysis Bot
"""
import asyncio
import logging
import signal
import sys
from typing import Optional

from telegram.ext import Application, ApplicationBuilder
from telegram import Bot

from ..config import TELEGRAM_BOT_TOKEN, REQUEST_TIMEOUT
from ..utils.cache import cache_manager
from .handlers import get_handlers

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('beartech_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class BotManager:
    """Bot manager for webhook mode (Render deployment)"""
    
    def __init__(self):
        self.application: Optional[Application] = None
    
    async def initialize(self) -> None:
        """Initialize the bot for webhook mode"""
        try:
            logger.info("Initializing BearTech Token Analysis Bot for webhook mode...")
            
            # Create application
            self.application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
            
            # Add handlers
            handlers = get_handlers()
            for handler in handlers:
                self.application.add_handler(handler)
            
            # Initialize cache manager
            await cache_manager.start_cleanup_task()
            
            # Initialize the application
            await self.application.initialize()
            await self.application.start()
            
            # Set bot commands
            await self._set_bot_commands()
            
            logger.info("Bot initialized successfully for webhook mode")
        
        except Exception as e:
            logger.error(f"Error initializing bot: {str(e)}")
            raise
    
    async def process_webhook_update(self, update_data: dict) -> None:
        """Process webhook update"""
        try:
            if self.application:
                from telegram import Update
                update = Update.de_json(update_data, self.application.bot)
                await self.application.process_update(update)
        except Exception as e:
            logger.error(f"Error processing webhook update: {str(e)}")
            raise
    
    async def _set_bot_commands(self) -> None:
        """Set bot commands for Telegram"""
        try:
            from telegram import BotCommand
            
            commands = [
                BotCommand("start", "Start the bot and see welcome message"),
                BotCommand("help", "Show detailed help and usage instructions"),
                BotCommand("analyze", "Analyze a specific token contract address"),
                BotCommand("chains", "Show supported blockchain networks"),
                BotCommand("status", "Show bot status and statistics")
            ]
            
            await self.application.bot.set_my_commands(commands)
            logger.info("Bot commands set successfully")
        
        except Exception as e:
            logger.error(f"Error setting bot commands: {str(e)}")


class BearTechBot:
    """Main bot class for polling mode"""
    
    def __init__(self, token: str):
        self.token = token
        self.application: Optional[Application] = None
        self.bot: Optional[Bot] = None
        self._shutdown_event = asyncio.Event()
    
    async def initialize(self) -> None:
        """Initialize the bot"""
        try:
            logger.info("Initializing BearTech Token Analysis Bot...")
            
            # Create application
            self.application = ApplicationBuilder().token(self.token).build()
            
            # Get bot instance
            self.bot = self.application.bot
            
            # Add handlers
            handlers = get_handlers()
            for handler in handlers:
                self.application.add_handler(handler)
            
            # Initialize cache manager
            await cache_manager.start_cleanup_task()
            
            logger.info("Bot initialized successfully")
        
        except Exception as e:
            logger.error(f"Error initializing bot: {str(e)}")
            raise
    
    async def start(self) -> None:
        """Start the bot (v20 initialize/start only; no Updater)."""
        try:
            if not self.application:
                raise RuntimeError("Bot not initialized. Call initialize() first.")

            logger.info("Starting BearTech Token Analysis Bot...")

            await self.application.initialize()
            await self.application.start()

            await self._set_bot_commands()

            logger.info("Application started (handlers active). Use run_bot() for polling mode.")

            await self._shutdown_event.wait()

        except Exception as e:
            logger.error(f"Error starting bot: {str(e)}")
            raise
    
    async def stop(self) -> None:
        """Stop the bot"""
        try:
            logger.info("Stopping BearTech Token Analysis Bot...")
            
            if self.application:
                # No updater in v20; just stop application
                await self.application.stop()
                await self.application.shutdown()
            
            # Stop cache cleanup
            await cache_manager.stop_cleanup_task()
            
            logger.info("Bot stopped successfully")
        
        except Exception as e:
            logger.error(f"Error stopping bot: {str(e)}")
    
    async def _set_bot_commands(self) -> None:
        """Set bot commands for Telegram"""
        try:
            from telegram import BotCommand
            
            commands = [
                BotCommand("start", "Start the bot and see welcome message"),
                BotCommand("help", "Show detailed help and usage instructions"),
                BotCommand("analyze", "Analyze a specific token contract address"),
                BotCommand("chains", "Show supported blockchain networks"),
                BotCommand("status", "Show bot status and statistics")
            ]
            
            await self.bot.set_my_commands(commands)
            logger.info("Bot commands set successfully")
        
        except Exception as e:
            logger.error(f"Error setting bot commands: {str(e)}")
    
    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            self._shutdown_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def get_bot_info(self) -> dict:
        """Get bot information"""
        try:
            if not self.bot:
                return {}
            
            bot_info = await self.bot.get_me()
            return {
                "id": bot_info.id,
                "username": bot_info.username,
                "first_name": bot_info.first_name,
                "can_join_groups": bot_info.can_join_groups,
                "can_read_all_group_messages": bot_info.can_read_all_group_messages,
                "supports_inline_queries": bot_info.supports_inline_queries
            }
        
        except Exception as e:
            logger.error(f"Error getting bot info: {str(e)}")
            return {}


async def main():
    """Main function"""
    try:
        # Create bot instance
        bot = BearTechBot(TELEGRAM_BOT_TOKEN)
        
        # Setup signal handlers
        bot.setup_signal_handlers()
        
        # Initialize bot
        await bot.initialize()
        
        # Get and log bot info
        bot_info = await bot.get_bot_info()
        if bot_info:
            logger.info(f"Bot info: {bot_info}")
        
        # Start bot
        await bot.start()
    
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)
    finally:
        # Ensure bot is stopped
        try:
            await bot.stop()
        except:
            pass


def run_bot():
    """Run the bot using python-telegram-bot v20 Application.run_polling()"""
    try:
        # Build application
        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

        # Add handlers
        handlers = get_handlers()
        for handler in handlers:
            application.add_handler(handler)

        # Set bot commands
        async def set_commands():
            from telegram import BotCommand
            commands = [
                BotCommand("start", "Start the bot and see welcome message"),
                BotCommand("help", "Show detailed help and usage instructions"),
                BotCommand("analyze", "Analyze a specific token contract address"),
                BotCommand("chains", "Show supported blockchain networks"),
                BotCommand("status", "Show bot status and statistics")
            ]
            await application.bot.set_my_commands(commands)
            logger.info("Bot commands set successfully")

        # Run polling (blocking)
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"]
        )
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    run_bot()
