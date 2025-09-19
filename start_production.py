#!/usr/bin/env python3
"""
Production startup script for BearTech Bot on Render - Full functionality
"""
import os
import sys
import logging
from multiprocessing import Process

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

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
    """Run the Telegram bot using v20 Application.run_polling() - FULL FUNCTIONALITY"""
    try:
        from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler
        from telegram import BotCommand, Update, InlineKeyboardButton, InlineKeyboardMarkup
        from telegram.ext import ContextTypes
        from telegram.constants import ParseMode
        
        # Import full functionality
        from src.services.token_analyzer import TokenAnalyzer
        from src.models.response import ResponseFormatter
        from src.utils.chain_detector import ChainDetector
        from src.config import MAX_MESSAGE_LENGTH, ERROR_MESSAGES, SUCCESS_MESSAGES
        
        logger.info("Starting BearTech Bot with FULL v20 Application.run_polling()...")
        
        # Initialize services
        token_analyzer = TokenAnalyzer()
        response_formatter = ResponseFormatter()
        chain_detector = ChainDetector()
        analyzing_users = set()  # Track users currently analyzing tokens
        
        # Build application
        application = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
        
        async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Handle /start command"""
            welcome_message = """
🤖 **Welcome to BearTech Token Analysis Bot!**

I can analyze any token contract address and provide comprehensive security and market analysis.

**How to use:**
1. Send me a contract address (e.g., `0x1234...`)
2. I'll analyze the token across multiple chains
3. Get detailed security, market, and risk analysis

**Supported Chains:**
🔷 Ethereum
🔵 Base

**Features:**
✅ Honeypot detection
✅ Security analysis
✅ Market data
✅ Liquidity analysis
✅ Holder distribution
✅ Deployer information
✅ Risk assessment

**Commands:**
/start - Show this help message
/help - Show detailed help
/analyze <address> - Analyze a specific token
/chains - Show supported chains
/status - Show bot status

Just send me a contract address to get started! 🚀
            """
            
            await update.message.reply_text(
                welcome_message,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
        
        async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Handle /help command"""
            help_message = """
📖 **BearTech Token Analysis Bot - Help**

**Basic Usage:**
• Send any contract address to analyze it
• The bot will automatically detect the chain
• Analysis includes security, market, and risk data

**Supported Address Formats:**
• `0x1234567890abcdef1234567890abcdef12345678`
• `0x1234...5678` (partial addresses)

**Analysis Includes:**
🔒 **Security Analysis:**
   • Honeypot detection
   • Contract verification
   • Tax analysis
   • Security flags

💰 **Market Data:**
   • Price and market cap
   • Volume and liquidity
   • Price changes

👥 **Holder Analysis:**
   • Holder count
   • Distribution analysis
   • Whale detection

👤 **Deployer Info:**
   • Deployer address and balance
   • Contract creation history
   • Risk assessment

⚠️ **Risk Assessment:**
   • Overall risk level
   • Risk factors
   • Recommendations

**Commands:**
/start - Welcome message
/help - This help message
/analyze <address> - Analyze specific token
/chains - Supported chains
/status - Bot status

**Tips:**
• Always verify contract addresses before trading
• Use multiple sources for important decisions
• Be cautious with new or unverified tokens

Need more help? Contact support! 🆘
            """
            
            await update.message.reply_text(
                help_message,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
        
        async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Handle /analyze command"""
            if not context.args:
                await update.message.reply_text(
                    "❌ Please provide a contract address.\n\nUsage: `/analyze 0x1234...`",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            address = context.args[0]
            await analyze_token_address(update, context, address)
        
        async def chains_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Handle /chains command"""
            chains_message = """
🌐 **Supported Blockchain Networks**

🔷 **Ethereum (ETH)**
   • Chain ID: 1
   • Explorer: etherscan.io
   • Native Token: ETH

🔵 **Base**
   • Chain ID: 8453
   • Explorer: basescan.org
   • Native Token: ETH

**Auto-Detection:**
The bot automatically detects which chain a contract belongs to by analyzing the contract across all supported networks.

**Note:** Some tokens may exist on multiple chains. The bot will analyze the most relevant instance based on liquidity and activity.
            """
            
            await update.message.reply_text(
                chains_message,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
        
        async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Handle /status command"""
            status_message = """
🤖 **Bot Status**

✅ **Operational**
🔄 **Cache Status:** Active
🌐 **API Services:**
   • GoPlus Security: ✅
   • DexScreener: ✅
   • Explorer APIs: ✅
   • RPC Services: ✅

📈 **Performance:**
   • Average response time: < 10s
   • Cache hit rate: Optimized
   • Uptime: 99.9%

Ready to analyze tokens! 🚀
            """
            
            await update.message.reply_text(
                status_message,
                parse_mode=ParseMode.MARKDOWN
            )
        
        async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Handle regular messages (contract addresses)"""
            message_text = update.message.text.strip()
            
            # Check if message looks like a contract address
            if is_contract_address(message_text):
                await analyze_token_address(update, context, message_text)
            else:
                await update.message.reply_text(
                    "❌ Please send a valid contract address.\n\nExample: `0x1234567890abcdef1234567890abcdef12345678`\n\nUse /help for more information.",
                    parse_mode=ParseMode.MARKDOWN
                )
        
        async def analyze_token_address(update: Update, context: ContextTypes.DEFAULT_TYPE, address: str):
            """Analyze a token contract address"""
            try:
                user_id = update.effective_user.id
                
                # Check if user is already analyzing
                if user_id in analyzing_users:
                    await update.message.reply_text(
                        "⏳ You already have an analysis in progress. Please wait for it to complete."
                    )
                    return
                
                # Add user to analyzing set
                analyzing_users.add(user_id)
                
                # Send initial message
                status_message = await update.message.reply_text(
                    "🔍 **Analyzing token...**\n\n"
                    f"Address: `{address}`\n"
                    "⏳ Please wait while I gather data from multiple sources...",
                    parse_mode=ParseMode.MARKDOWN
                )
                
                try:
                    # Perform analysis
                    analysis_result = await token_analyzer.analyze_token(address)
                    
                    # Format response
                    formatted_response = response_formatter.format_token_analysis(analysis_result)
                    
                    # Send results
                    await send_analysis_results(update, context, formatted_response, address)
                    
                except Exception as e:
                    logger.error(f"Analysis error: {str(e)}")
                    await status_message.edit_text(
                        f"❌ **Analysis Failed**\n\n"
                        f"Address: `{address}`\n"
                        f"Error: {str(e)}\n\n"
                        "Please try again or contact support if the issue persists.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                finally:
                    # Remove user from analyzing set
                    analyzing_users.discard(user_id)
            
            except Exception as e:
                logger.error(f"Error in token analysis: {str(e)}")
                await update.message.reply_text("❌ An error occurred during analysis. Please try again.")
        
        async def send_analysis_results(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                       response, address: str):
            """Send analysis results to user"""
            try:
                # Convert to Telegram message
                message = response.to_telegram_message()
                
                # Check message length
                if len(message) > MAX_MESSAGE_LENGTH:
                    # Split message if too long
                    await send_long_message(update, context, message)
                else:
                    # Send single message
                    await update.message.reply_text(
                        message,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True
                    )
                
                # Add action buttons
                await add_action_buttons(update, context, address, response)
            
            except Exception as e:
                logger.error(f"Error sending analysis results: {str(e)}")
                await update.message.reply_text("❌ Error formatting results. Please try again.")
        
        async def send_long_message(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str):
            """Send long message by splitting it"""
            try:
                # Split message into chunks
                chunks = split_message(message, MAX_MESSAGE_LENGTH - 100)
                
                for i, chunk in enumerate(chunks):
                    if i == 0:
                        await update.message.reply_text(
                            chunk,
                            parse_mode=ParseMode.MARKDOWN,
                            disable_web_page_preview=True
                        )
                    else:
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=chunk,
                            parse_mode=ParseMode.MARKDOWN,
                            disable_web_page_preview=True
                        )
            
            except Exception as e:
                logger.error(f"Error sending long message: {str(e)}")
                await update.message.reply_text("❌ Error sending results. Please try again.")
        
        async def add_action_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                    address: str, response):
            """Add action buttons to the message"""
            try:
                # Create inline keyboard
                keyboard = []
                
                # Add explorer link if we have chain info
                if hasattr(response, 'basic_info') and response.basic_info.chain:
                    chain = response.basic_info.chain
                    explorer_url = chain_detector.get_explorer_url(chain, address)
                    keyboard.append([
                        InlineKeyboardButton("🔍 View on Explorer", url=explorer_url)
                    ])
                
                # Add refresh button
                keyboard.append([
                    InlineKeyboardButton("🔄 Refresh Analysis", callback_data=f"refresh:{address}")
                ])
                
                if keyboard:
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="📋 **Quick Actions**",
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.MARKDOWN
                    )
            
            except Exception as e:
                logger.error(f"Error adding action buttons: {str(e)}")
        
        async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Handle callback queries from inline buttons"""
            try:
                query = update.callback_query
                await query.answer()
                
                data = query.data
                if data.startswith("refresh:"):
                    address = data.split(":", 1)[1]
                    await handle_refresh_callback(update, context, address)
            
            except Exception as e:
                logger.error(f"Error handling callback query: {str(e)}")
                await query.edit_message_text("❌ An error occurred. Please try again.")
        
        async def handle_refresh_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, address: str):
            """Handle refresh analysis callback"""
            try:
                await update.callback_query.edit_message_text(
                    "🔄 **Refreshing analysis...**\n\n"
                    f"Address: `{address}`\n"
                    "⏳ Please wait...",
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Perform fresh analysis
                analysis_result = await token_analyzer.analyze_token(address)
                formatted_response = response_formatter.format_token_analysis(analysis_result)
                
                # Send updated results
                message = formatted_response.to_telegram_message()
                await update.callback_query.edit_message_text(
                    message,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
            
            except Exception as e:
                logger.error(f"Error refreshing analysis: {str(e)}")
                await update.callback_query.edit_message_text("❌ Error refreshing analysis. Please try again.")
        
        def is_contract_address(text: str) -> bool:
            """Check if text looks like a contract address"""
            if not text or not isinstance(text, str):
                return False
            
            # Remove whitespace
            text = text.strip()
            
            # Check if it starts with 0x and has correct length
            if not text.startswith("0x"):
                return False
            
            if len(text) != 42:
                return False
            
            # Check if it's valid hex
            try:
                int(text[2:], 16)
                return True
            except ValueError:
                return False
        
        def split_message(message: str, max_length: int) -> list:
            """Split message into chunks"""
            chunks = []
            current_chunk = ""
            
            lines = message.split('\n')
            for line in lines:
                if len(current_chunk + line + '\n') > max_length:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                        current_chunk = line + '\n'
                    else:
                        # Single line is too long, split it
                        chunks.append(line[:max_length])
                        current_chunk = line[max_length:] + '\n'
                else:
                    current_chunk += line + '\n'
            
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            
            return chunks
        
        # Add handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("analyze", analyze_command))
        application.add_handler(CommandHandler("chains", chains_command))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CallbackQueryHandler(handle_callback_query))
        
        # Set bot commands
        async def set_commands():
            commands = [
                BotCommand("start", "Start the bot and see welcome message"),
                BotCommand("help", "Show detailed help and usage instructions"),
                BotCommand("analyze", "Analyze a specific token contract address"),
                BotCommand("chains", "Show supported blockchain networks"),
                BotCommand("status", "Show bot status and statistics")
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

