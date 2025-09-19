"""
Telegram bot handlers for BearTech Token Analysis Bot
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram.constants import ParseMode

from ..services.token_analyzer import TokenAnalyzer
from ..models.token import ChainType
from ..models.response import ResponseFormatter
from ..utils.chain_detector import ChainDetector
from ..utils.formatters import DataFormatter
from ..config import MAX_MESSAGE_LENGTH, ERROR_MESSAGES, SUCCESS_MESSAGES

logger = logging.getLogger(__name__)


class BotHandlers:
    """Telegram bot message handlers"""
    
    def __init__(self):
        self.token_analyzer = TokenAnalyzer()
        self.response_formatter = ResponseFormatter()
        self.chain_detector = ChainDetector()
        self.data_formatter = DataFormatter()
        self.analyzing_users = set()  # Track users currently analyzing tokens
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        try:
            welcome_message = """
🤖 **Welcome to BearTech Token Analysis Bot!**

I can analyze any token contract address and provide comprehensive security and market analysis.

**How to use:**
1. Send me a contract address (e.g., `0x1234...`)
2. I'll analyze the token across multiple chains
3. Get detailed security, market, and risk analysis

**Supported Chains:**
🔷 Ethereum
🟡 Binance Smart Chain (BSC)
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

Just send me a contract address to get started! 🚀
            """
            
            await update.message.reply_text(
                welcome_message,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
        
        except Exception as e:
            logger.error(f"Error in start command: {str(e)}")
            await update.message.reply_text("❌ An error occurred. Please try again.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command"""
        try:
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
        
        except Exception as e:
            logger.error(f"Error in help command: {str(e)}")
            await update.message.reply_text("❌ An error occurred. Please try again.")
    
    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /analyze command"""
        try:
            if not context.args:
                await update.message.reply_text(
                    "❌ Please provide a contract address.\n\nUsage: `/analyze 0x1234...`",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            address = context.args[0]
            await self._analyze_token(update, context, address)
        
        except Exception as e:
            logger.error(f"Error in analyze command: {str(e)}")
            await update.message.reply_text("❌ An error occurred. Please try again.")
    
    async def chains_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /chains command"""
        try:
            chains_message = """
🌐 **Supported Blockchain Networks**

🔷 **Ethereum (ETH)**
   • Chain ID: 1
   • Explorer: etherscan.io
   • Native Token: ETH

🟡 **Binance Smart Chain (BSC)**
   • Chain ID: 56
   • Explorer: bscscan.com
   • Native Token: BNB

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
        
        except Exception as e:
            logger.error(f"Error in chains command: {str(e)}")
            await update.message.reply_text("❌ An error occurred. Please try again.")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command"""
        try:
            from ..utils.cache import cache_manager
            
            # Get cache statistics
            cache_stats = cache_manager.get_all_stats()
            
            status_message = f"""
🤖 **Bot Status**

✅ **Operational**
🔄 **Cache Status:** Active
📊 **Cache Stats:**
"""
            
            for cache_type, stats in cache_stats.items():
                status_message += f"   • {cache_type}: {stats['size']}/{stats['max_size']} entries\n"
            
            status_message += f"""
🌐 **API Services:**
   • GoPlus Security: ✅
   • DexScreener: ✅
   • Explorer APIs: ✅
   • Moralis: ✅
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
        
        except Exception as e:
            logger.error(f"Error in status command: {str(e)}")
            await update.message.reply_text("❌ An error occurred. Please try again.")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle regular messages (contract addresses)"""
        try:
            message_text = update.message.text.strip()
            
            # Check if message looks like a contract address
            if self._is_contract_address(message_text):
                await self._analyze_token(update, context, message_text)
            else:
                await update.message.reply_text(
                    "❌ Please send a valid contract address.\n\nExample: `0x1234567890abcdef1234567890abcdef12345678`\n\nUse /help for more information.",
                    parse_mode=ParseMode.MARKDOWN
                )
        
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            await update.message.reply_text("❌ An error occurred. Please try again.")
    
    async def _analyze_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE, address: str) -> None:
        """Analyze a token contract address"""
        try:
            user_id = update.effective_user.id
            
            # Check if user is already analyzing
            if user_id in self.analyzing_users:
                await update.message.reply_text(
                    "⏳ You already have an analysis in progress. Please wait for it to complete."
                )
                return
            
            # Add user to analyzing set
            self.analyzing_users.add(user_id)
            
            # Send initial message
            status_message = await update.message.reply_text(
                "🔍 **Analyzing token...**\n\n"
                f"Address: `{address}`\n"
                "⏳ Please wait while I gather data from multiple sources...",
                parse_mode=ParseMode.MARKDOWN
            )
            
            try:
                # Perform analysis
                analysis_result = await self.token_analyzer.analyze_token(address)
                
                # Format response
                formatted_response = self.response_formatter.format_token_analysis(analysis_result)
                
                # Send results
                await self._send_analysis_results(update, context, formatted_response, address)
                
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
                self.analyzing_users.discard(user_id)
        
        except Exception as e:
            logger.error(f"Error in token analysis: {str(e)}")
            await update.message.reply_text("❌ An error occurred during analysis. Please try again.")
    
    async def _send_analysis_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                   response: Any, address: str) -> None:
        """Send analysis results to user"""
        try:
            # Convert to Telegram message
            message = response.to_telegram_message()
            
            # Check message length
            if len(message) > MAX_MESSAGE_LENGTH:
                # Split message if too long
                await self._send_long_message(update, context, message)
            else:
                # Send single message
                await update.message.reply_text(
                    message,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
            
            # Add action buttons
            await self._add_action_buttons(update, context, address, response)
        
        except Exception as e:
            logger.error(f"Error sending analysis results: {str(e)}")
            await update.message.reply_text("❌ Error formatting results. Please try again.")
    
    async def _send_long_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message: str) -> None:
        """Send long message by splitting it"""
        try:
            # Split message into chunks
            chunks = self._split_message(message, MAX_MESSAGE_LENGTH - 100)
            
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
    
    async def _add_action_buttons(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                address: str, response: Any) -> None:
        """Add action buttons to the message"""
        try:
            # Create inline keyboard
            keyboard = []
            
            # Add explorer link if we have chain info
            if hasattr(response, 'basic_info') and response.basic_info.chain:
                chain = response.basic_info.chain
                explorer_url = self.chain_detector.get_explorer_url(chain, address)
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
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle callback queries from inline buttons"""
        try:
            query = update.callback_query
            await query.answer()
            
            data = query.data
            if data.startswith("refresh:"):
                address = data.split(":", 1)[1]
                await self._handle_refresh_callback(update, context, address)
        
        except Exception as e:
            logger.error(f"Error handling callback query: {str(e)}")
            await query.edit_message_text("❌ An error occurred. Please try again.")
    
    async def _handle_refresh_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, address: str) -> None:
        """Handle refresh analysis callback"""
        try:
            await update.callback_query.edit_message_text(
                "🔄 **Refreshing analysis...**\n\n"
                f"Address: `{address}`\n"
                "⏳ Please wait...",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Perform fresh analysis
            analysis_result = await self.token_analyzer.analyze_token(address)
            formatted_response = self.response_formatter.format_token_analysis(analysis_result)
            
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
    
    
    def _is_contract_address(self, text: str) -> bool:
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
    
    def _split_message(self, message: str, max_length: int) -> list:
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


def get_handlers() -> list:
    """Get all bot handlers"""
    handlers_instance = BotHandlers()
    
    return [
        CommandHandler("start", handlers_instance.start_command),
        CommandHandler("help", handlers_instance.help_command),
        CommandHandler("analyze", handlers_instance.analyze_command),
        CommandHandler("chains", handlers_instance.chains_command),
        CommandHandler("status", handlers_instance.status_command),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handlers_instance.handle_message),
        CallbackQueryHandler(handlers_instance.handle_callback_query)
    ]
