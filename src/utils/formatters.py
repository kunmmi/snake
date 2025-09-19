"""
Data formatting utilities for BearTech Token Analysis Bot
"""
from typing import Any, Optional, Dict, List
from decimal import Decimal
import re
from datetime import datetime, timezone


class DataFormatter:
    """Utility class for formatting various data types"""
    
    @staticmethod
    def format_number(value: Any, decimals: int = 2) -> str:
        """Format large numbers with K, M, B suffixes"""
        if value is None:
            return "Unknown"
        
        try:
            if isinstance(value, str):
                # Remove commas and convert to float
                value = value.replace(',', '')
                num = float(value)
            else:
                num = float(value)
            
            if num == 0:
                return "0"
            
            if num >= 1e12:
                return f"{num/1e12:.{decimals}f}T"
            elif num >= 1e9:
                return f"{num/1e9:.{decimals}f}B"
            elif num >= 1e6:
                return f"{num/1e6:.{decimals}f}M"
            elif num >= 1e3:
                return f"{num/1e3:.{decimals}f}K"
            else:
                return f"{num:.{decimals}f}"
        except (ValueError, TypeError, AttributeError):
            return "Unknown"
    
    @staticmethod
    def format_price(value: Any) -> str:
        """Format price values with appropriate decimal places"""
        if value is None:
            return "Unknown"
        
        try:
            if isinstance(value, str):
                value = value.replace(',', '')
                num = float(value)
            else:
                num = float(value)
            
            if num == 0:
                return "$0.00"
            
            if num >= 1:
                return f"${num:.4f}"
            elif num >= 0.01:
                return f"${num:.6f}"
            elif num >= 0.0001:
                return f"${num:.8f}"
            else:
                return f"${num:.10f}"
        except (ValueError, TypeError, AttributeError):
            return "Unknown"
    
    @staticmethod
    def format_percentage(value: Any, decimals: int = 2) -> str:
        """Format percentage values"""
        if value is None:
            return "Unknown"
        
        try:
            if isinstance(value, str):
                value = value.replace('%', '').replace(',', '')
                num = float(value)
            else:
                num = float(value)
            
            return f"{num:.{decimals}f}%"
        except (ValueError, TypeError, AttributeError):
            return "Unknown"
    
    @staticmethod
    def format_address(address: str, start_chars: int = 6, end_chars: int = 4) -> str:
        """Format address for display"""
        if not address or not isinstance(address, str):
            return "Unknown"
        
        if len(address) <= start_chars + end_chars:
            return address
        
        return f"{address[:start_chars]}...{address[-end_chars:]}"
    
    @staticmethod
    def format_timestamp(timestamp: Any) -> str:
        """Format timestamp to readable date"""
        if timestamp is None:
            return "Unknown"
        
        try:
            if isinstance(timestamp, str):
                # Try to parse various timestamp formats
                if timestamp.isdigit():
                    # Unix timestamp
                    ts = int(timestamp)
                    if ts > 1e10:  # Milliseconds
                        ts = ts / 1000
                    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                else:
                    # ISO format or other
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            elif isinstance(timestamp, (int, float)):
                ts = int(timestamp)
                if ts > 1e10:  # Milliseconds
                    ts = ts / 1000
                dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            else:
                return "Unknown"
            
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except (ValueError, TypeError, OSError):
            return "Unknown"
    
    @staticmethod
    def format_duration(seconds: Any) -> str:
        """Format duration in seconds to human readable format"""
        if seconds is None:
            return "Unknown"
        
        try:
            if isinstance(seconds, str):
                seconds = float(seconds)
            else:
                seconds = float(seconds)
            
            if seconds < 60:
                return f"{int(seconds)}s"
            elif seconds < 3600:
                return f"{int(seconds/60)}m {int(seconds%60)}s"
            elif seconds < 86400:
                hours = int(seconds/3600)
                minutes = int((seconds%3600)/60)
                return f"{hours}h {minutes}m"
            else:
                days = int(seconds/86400)
                hours = int((seconds%86400)/3600)
                return f"{days}d {hours}h"
        except (ValueError, TypeError):
            return "Unknown"
    
    @staticmethod
    def format_boolean(value: Any, true_text: str = "Yes", false_text: str = "No") -> str:
        """Format boolean values"""
        if value is None:
            return "Unknown"
        
        if isinstance(value, bool):
            return true_text if value else false_text
        elif isinstance(value, str):
            return true_text if value.lower() in ['true', 'yes', '1', 'on'] else false_text
        elif isinstance(value, (int, float)):
            return true_text if value != 0 else false_text
        else:
            return "Unknown"
    
    @staticmethod
    def format_risk_level(risk_score: Any) -> str:
        """Format risk score to risk level"""
        if risk_score is None:
            return "Unknown"
        
        try:
            score = float(risk_score)
            if score >= 80:
                return "🚨 High Risk"
            elif score >= 60:
                return "⚠️ Medium-High Risk"
            elif score >= 40:
                return "🟡 Medium Risk"
            elif score >= 20:
                return "🟢 Low-Medium Risk"
            else:
                return "✅ Low Risk"
        except (ValueError, TypeError):
            return "Unknown"
    
    @staticmethod
    def format_liquidity_status(liquidity: Any, locked: bool = False) -> str:
        """Format liquidity status"""
        if liquidity is None:
            return "Unknown"
        
        try:
            liq = float(liquidity)
            if liq == 0:
                return "🚨 No Liquidity (Honeypot)"
            elif liq < 1000:
                return "⚠️ Very Low Liquidity"
            elif liq < 10000:
                return "🟡 Low Liquidity"
            elif liq < 100000:
                return "🟢 Medium Liquidity"
            else:
                status = "✅ High Liquidity"
                if locked:
                    status += " (Locked)"
                return status
        except (ValueError, TypeError):
            return "Unknown"
    
    @staticmethod
    def format_holder_distribution(holders: Any) -> str:
        """Format holder distribution"""
        if holders is None:
            return "Unknown"
        
        try:
            holder_count = int(holders)
            if holder_count == 0:
                return "🚨 No Holders"
            elif holder_count < 10:
                return "⚠️ Very Few Holders"
            elif holder_count < 100:
                return "🟡 Few Holders"
            elif holder_count < 1000:
                return "🟢 Moderate Holders"
            else:
                return "✅ Many Holders"
        except (ValueError, TypeError):
            return "Unknown"
    
    @staticmethod
    def format_contract_age(age_days: Any) -> str:
        """Format contract age"""
        if age_days is None:
            return "Unknown"
        
        try:
            days = int(age_days)
            if days < 1:
                return "🚨 Just Deployed"
            elif days < 7:
                return "⚠️ Very New (< 1 week)"
            elif days < 30:
                return "🟡 New (< 1 month)"
            elif days < 90:
                return "🟢 Established (< 3 months)"
            else:
                return "✅ Mature (> 3 months)"
        except (ValueError, TypeError):
            return "Unknown"
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and sanitize text"""
        if not text or not isinstance(text, str):
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters that might break Telegram formatting
        text = re.sub(r'[^\w\s\-.,!?@#$%&*()+=:;"\'<>/\\|`~]', '', text)
        
        return text
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100) -> str:
        """Truncate text to maximum length"""
        if not text or not isinstance(text, str):
            return ""
        
        if len(text) <= max_length:
            return text
        
        return text[:max_length-3] + "..."
    
    @staticmethod
    def format_telegram_message(text: str) -> str:
        """Format text for Telegram (escape special characters)"""
        if not text or not isinstance(text, str):
            return ""
        
        # Escape special characters for Telegram Markdown
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        
        return text



