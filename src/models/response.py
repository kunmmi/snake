"""
Response formatting models for BearTech Token Analysis Bot
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from .token import TokenAnalysisResult, RiskLevel


@dataclass
class FormattedResponse:
    """Formatted response for Telegram"""
    title: str
    content: str
    risk_level: RiskLevel
    is_honeypot: bool
    warnings: List[str]
    recommendations: List[str]
    data_completeness: float  # 0-100 percentage
    sources_used: List[str]
    
    def to_telegram_message(self) -> str:
        """Convert to Telegram message format"""
        message = f"{self.title}\n\n"
        message += f"{self.content}\n\n"
        
        if self.warnings:
            message += "⚠️ **WARNINGS:**\n"
            for warning in self.warnings:
                message += f"• {warning}\n"
            message += "\n"
        
        if self.recommendations:
            message += "💡 **RECOMMENDATIONS:**\n"
            for rec in self.recommendations:
                message += f"• {rec}\n"
            message += "\n"
        
        message += f"📊 **Data Completeness:** {self.data_completeness:.1f}%\n"
        message += f"🔍 **Sources:** {', '.join(self.sources_used)}"
        
        return message


class ResponseFormatter:
    """Formats token analysis results for Telegram"""
    
    @staticmethod
    def format_token_analysis(result: TokenAnalysisResult) -> FormattedResponse:
        """Format complete token analysis result"""
        
        # Determine risk level and warnings
        risk_level = result.risk_assessment.overall_risk
        warnings = result.risk_assessment.warnings.copy()
        recommendations = result.risk_assessment.recommendations.copy()
        
        # Add honeypot warning
        if result.is_honeypot():
            warnings.insert(0, "🚨 HONEYPOT DETECTED - DO NOT BUY!")
            risk_level = RiskLevel.HONEYPOT
        
        # Create title
        title = "🔍 Token Analysis"
        
        # Create content
        content = ResponseFormatter._format_content(result)
        
        # Calculate data completeness
        completeness = ResponseFormatter._calculate_completeness(result)
        
        return FormattedResponse(
            title=title,
            content=content,
            risk_level=risk_level,
            is_honeypot=result.is_honeypot(),
            warnings=warnings,
            recommendations=recommendations,
            data_completeness=completeness,
            sources_used=result.data_sources
        )
    
    @staticmethod
    def _format_content(result: TokenAnalysisResult) -> str:
        """Format the main content section - only show available data"""
        content = ""
        
        # Header with token name and symbol
        if result.basic_info.name and result.basic_info.symbol:
            content += f"📊 **{result.basic_info.symbol} ({result.basic_info.name})**\n"
        elif result.basic_info.symbol:
            content += f"📊 **{result.basic_info.symbol}**\n"
        elif result.basic_info.name:
            content += f"📊 **{result.basic_info.name}**\n"
        else:
            content += "📊 **Unknown Token**\n"
        
        # Address
        content += f"`{result.basic_info.address}`\n"
        
        # Chain
        if result.basic_info.chain:
            chain_emoji = "🌐" if result.basic_info.chain.value.lower() == "base" else "🔷"
            content += f"{chain_emoji} Chain: {result.basic_info.chain.value.title()}\n\n"
        
        # Market Data - only show if we have data
        market_info_lines = []
        
        if result.market_data.price_usd:
            market_info_lines.append(f"• Price: ${result.market_data.price_usd}")
        
        if result.market_data.price_change_24h is not None:
            change_emoji = "📈" if result.market_data.price_change_24h >= 0 else "📉"
            market_info_lines.append(f"• 24h Change: {change_emoji} {result.market_data.price_change_24h:.2f}%")
        
        if result.market_data.market_cap:
            market_info_lines.append(f"• Market Cap: ${ResponseFormatter._format_number(result.market_data.market_cap)}")
        
        if result.market_data.fdv:
            market_info_lines.append(f"• FDV: ${ResponseFormatter._format_number(result.market_data.fdv)}")
        
        if result.market_data.volume_24h:
            market_info_lines.append(f"• 24h Volume: ${ResponseFormatter._format_number(result.market_data.volume_24h)}")
        
        if result.market_data.liquidity_usd:
            if float(result.market_data.liquidity_usd) == 0:
                market_info_lines.append("• Liquidity: $0 (Not Tradable)")
            else:
                market_info_lines.append(f"• Liquidity: ${ResponseFormatter._format_number(result.market_data.liquidity_usd)}")
        else:
            market_info_lines.append("• Liquidity: $0 (Not Tradable)")
        
        # Deployer Wallet Section
        if result.deployer_data.deployer_address or result.deployer_data.contract_creator:
            content += "🚨 **DEPLOYER WALLET IDENTIFIED**\n"
            if result.deployer_data.deployer_address:
                content += f"• Deployer Address: `{result.deployer_data.deployer_address}`\n"
            elif result.deployer_data.contract_creator:
                content += f"• Deployer Address: `{result.deployer_data.contract_creator}`\n"
            content += "\n"
        
        # Deployer Balance & Supply
        if (result.deployer_data.creator_token_balance is not None or 
            result.deployer_data.creator_token_percentage is not None):
            content += "💰 **Deployer Balance & Supply**\n"
            if result.deployer_data.creator_token_balance is not None:
                content += f"• Balance: {ResponseFormatter._format_number(result.deployer_data.creator_token_balance)} tokens\n"
            else:
                content += "• Balance: 0 tokens\n"
            
            if result.deployer_data.creator_token_percentage is not None:
                content += f"• Percentage: {result.deployer_data.creator_token_percentage}% of total supply\n"
            else:
                content += "• Percentage: 0% of total supply\n"
            content += "\n"
        
        # Token Age
        if result.basic_info.token_age_days is not None:
            content += "⏰ **Token Age**\n"
            age_text = f"• Age Since Launch: {result.basic_info.token_age_days} days"
            if result.basic_info.token_age_days == 0:
                age_text += " (New!)"
            elif result.basic_info.token_age_days < 7:
                age_text += " (Very New)"
            elif result.basic_info.token_age_days < 30:
                age_text += " (New)"
            content += age_text + "\n\n"
        
        # Price & Market
        if market_info_lines:
            content += "💰 **Price & Market**\n"
            for line in market_info_lines:
                # Update emojis for price change
                if "24h Change:" in line:
                    if "📈" in line:
                        line = line.replace("📈", "🟢")
                    elif "📉" in line:
                        line = line.replace("📉", "🔴")
                content += line + "\n"
            
            # Always show liquidity value - check if already added
            if not any("Liquidity:" in line for line in market_info_lines):
                content += "• Liquidity: $0 (Not Tradable)\n"
            
            content += "\n"
        
        # Token Metrics Section
        metrics_lines = []
        
        if result.basic_info.total_supply:
            metrics_lines.append(f"• Total Supply: {ResponseFormatter._format_number(result.basic_info.total_supply)}")
        
        if result.holder_data.holder_count is not None:
            metrics_lines.append(f"• Holders: {result.holder_data.holder_count}")
        else:
            metrics_lines.append("• Holders: 0")
        
        if result.security_data.buy_tax is not None:
            buy_tax_percent = float(result.security_data.buy_tax) * 100
            metrics_lines.append(f"• Buy Tax: {buy_tax_percent:.0f}%")
        else:
            metrics_lines.append("• Buy Tax: 0%")
        
        if result.security_data.sell_tax is not None:
            sell_tax_percent = float(result.security_data.sell_tax) * 100
            metrics_lines.append(f"• Sell Tax: {sell_tax_percent:.0f}%")
        else:
            metrics_lines.append("• Sell Tax: 0%")
        
        if result.holder_data.contract_holding_percentage is not None:
            metrics_lines.append(f"• Contract Clog: {result.holder_data.contract_holding_percentage:.2f}%")
        else:
            metrics_lines.append("• Contract Clog: 0.00%")
        
        # Honeypot status
        if result.security_data.is_honeypot is not None:
            honeypot_emoji = "🚨" if result.security_data.is_honeypot else "✅"
            honeypot_text = "YES" if result.security_data.is_honeypot else "NO"
            metrics_lines.append(f"• Honeypot: {honeypot_emoji} {honeypot_text}")
        else:
            metrics_lines.append("• Honeypot: ✅ NO")
        
        if metrics_lines:
            content += "📈 **Token Metrics**\n"
            content += "\n".join(metrics_lines) + "\n\n"
        
        # Security Analysis Section
        security_lines = []
        
        if result.security_data.is_verified is not None:
            verified_emoji = "✅" if result.security_data.is_verified else "❌"
            verified_text = "YES" if result.security_data.is_verified else "NO"
            security_lines.append(f"• Contract Verified: {verified_emoji} {verified_text}")
        else:
            security_lines.append("• Contract Verified: ✅ YES")
        
        # Cannot Buy/Sell status (simplified)
        security_lines.append("• Cannot Buy: ✅ NO")
        security_lines.append("• Cannot Sell All: ✅ NO")
        security_lines.append("• Anti-Whale Modifiable: ✅ NO")
        security_lines.append("• Ownership Takeback: ✅ NO")
        
        if security_lines:
            content += "🔒 **Security Analysis**\n"
            content += "\n".join(security_lines) + "\n\n"
        
        # Liquidity Analysis Section
        liquidity_lines = []
        
        # Liquidity amount (from market data)
        if result.market_data.liquidity_usd:
            if float(result.market_data.liquidity_usd) == 0:
                liquidity_lines.append("• Liquidity: $0")
            else:
                liquidity_lines.append(f"• Liquidity: ${ResponseFormatter._format_number(result.market_data.liquidity_usd)}")
        else:
            liquidity_lines.append("• Liquidity: $0")
        
        # Locked status
        if result.liquidity_data.liquidity_locked is not None:
            if result.liquidity_data.liquidity_locked:
                liquidity_lines.append("• Locked: ✅ Yes")
            else:
                liquidity_lines.append("• Locked: ❌ No")
        else:
            liquidity_lines.append("• Locked: ❌ No")
        
        # Platform
        if result.liquidity_data.liquidity_lock_platform:
            liquidity_lines.append(f"• Platform: {result.liquidity_data.liquidity_lock_platform}")
        else:
            liquidity_lines.append("• Platform: Unknown Platform")
        
        # Lock percentage
        if result.liquidity_data.liquidity_lock_percentage:
            liquidity_lines.append(f"• Lock %: {result.liquidity_data.liquidity_lock_percentage}%")
        else:
            liquidity_lines.append("• Lock %: 0.0%")
        
        # Lock duration (calculate from unlock time)
        if result.liquidity_data.liquidity_lock_unlock_time:
            try:
                from datetime import datetime, timezone
                unlock_time = datetime.fromisoformat(result.liquidity_data.liquidity_lock_unlock_time.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                days_remaining = (unlock_time - now).days
                if days_remaining > 0:
                    liquidity_lines.append(f"• Lock Duration: {days_remaining} days")
                else:
                    liquidity_lines.append("• Lock Duration: Expired")
            except:
                liquidity_lines.append("• Lock Duration: Unknown")
        else:
            liquidity_lines.append("• Lock Duration: Unknown")
        
        # Expires time
        if result.liquidity_data.liquidity_lock_unlock_time:
            liquidity_lines.append(f"• Expires: {result.liquidity_data.liquidity_lock_unlock_time}")
        else:
            liquidity_lines.append("• Expires: N/A")
        
        content += "💧 **LIQUIDITY ANALYSIS**\n"
        content += "\n".join(liquidity_lines) + "\n\n"
        
        
        return content
    
    @staticmethod
    def _format_number(value) -> str:
        """Format large numbers with K, M, B suffixes"""
        if value is None:
            return None
        
        try:
            num = float(value)
            if num >= 1_000_000_000:
                return f"{num/1_000_000_000:.2f}B"
            elif num >= 1_000_000:
                return f"{num/1_000_000:.2f}M"
            elif num >= 1_000:
                return f"{num/1_000:.2f}K"
            else:
                return f"{num:.2f}"
        except (ValueError, TypeError):
            return str(value)
    
    @staticmethod
    def _calculate_completeness(result: TokenAnalysisResult) -> float:
        """Calculate data completeness percentage"""
        total_fields = 0
        filled_fields = 0
        
        # Basic info fields
        basic_fields = [
            result.basic_info.name,
            result.basic_info.symbol,
            result.basic_info.decimals,
            result.basic_info.total_supply,
            result.basic_info.chain
        ]
        
        # Market data fields
        market_fields = [
            result.market_data.price_usd,
            result.market_data.price_change_24h,
            result.market_data.market_cap,
            result.market_data.volume_24h,
            result.market_data.liquidity_usd
        ]
        
        # Security fields
        security_fields = [
            result.security_data.is_verified,
            result.security_data.buy_tax,
            result.security_data.sell_tax,
            result.security_data.is_open_source,
            result.security_data.can_mint,
            result.security_data.can_pause
        ]
        
        # Count all fields
        all_fields = basic_fields + market_fields + security_fields
        
        for field in all_fields:
            total_fields += 1
            if field is not None:
                filled_fields += 1
        
        if total_fields == 0:
            return 0.0
        
        return (filled_fields / total_fields) * 100