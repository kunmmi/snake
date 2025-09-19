#!/usr/bin/env python3
"""
BearTech Token Analysis Bot - Web Server Entry Point for Render
"""
import sys
import os
import asyncio
import logging
from aiohttp import web
from aiohttp.web import Request, Response

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.bot.main import BotManager

# Global bot manager instance
bot_manager = None

async def health_check(request: Request) -> Response:
    """Health check endpoint for Render"""
    return Response(text="BearTech Token Analysis Bot is running! 🤖", status=200)

async def webhook_handler(request: Request) -> Response:
    """Handle Telegram webhook updates"""
    try:
        if bot_manager:
            await bot_manager.process_webhook_update(await request.json())
        return Response(text="OK", status=200)
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return Response(text="Error", status=500)

async def init_bot():
    """Initialize the bot manager"""
    global bot_manager
    try:
        bot_manager = BotManager()
        await bot_manager.initialize()
        logging.info("Bot initialized successfully for web server")
    except Exception as e:
        logging.error(f"Failed to initialize bot: {e}")
        raise

def create_app():
    """Create the web application"""
    app = web.Application()
    
    # Add routes
    app.router.add_get('/health', health_check)
    app.router.add_post('/webhook', webhook_handler)
    
    # Initialize bot on startup
    app.on_startup.append(lambda app: asyncio.create_task(init_bot()))
    
    return app

if __name__ == "__main__":
    # For local testing
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))



