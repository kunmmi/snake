"""
DexScreener API service for BearTech Token Analysis Bot
"""
import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal
from ..config import DEXSCREENER_BASE_URL, REQUEST_TIMEOUT
from ..models.token import TokenMarketData, TokenHolderData, ChainType
from ..utils.chain_detector import ChainDetector

logger = logging.getLogger(__name__)


class DexScreenerService:
    """DexScreener API service for market data"""
    
    def __init__(self):
        self.base_url = DEXSCREENER_BASE_URL
        self.timeout = REQUEST_TIMEOUT
    
    async def get_token_data(self, address: str, chain: ChainType) -> Dict[str, Any]:
        """
        Get token data from DexScreener
        """
        try:
            # Get chain identifier for DexScreener
            chain_id = self._get_chain_identifier(chain)
            if not chain_id:
                logger.error(f"Unsupported chain for DexScreener: {chain}")
                return {}
            
            # Make API request - DexScreener API works with just the address
            url = f"{self.base_url}/dex/tokens/{address}"
            
            # Create SSL context to handle SSL issues
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_token_response(data, address)
                    else:
                        logger.error(f"DexScreener API error: {response.status}")
                        return {}
        
        except asyncio.TimeoutError:
            logger.error("DexScreener API timeout")
            return {}
        except Exception as e:
            logger.error(f"DexScreener API error: {str(e)}")
            return {}
    
    async def get_pair_data(self, address: str, chain: ChainType) -> Dict[str, Any]:
        """
        Get pair data from DexScreener
        """
        try:
            chain_id = self._get_chain_identifier(chain)
            if not chain_id:
                return {}
            
            url = f"{self.base_url}/dex/tokens/{address}"
            
            # Create SSL context to handle SSL issues
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_pair_response(data, address)
                    else:
                        logger.error(f"DexScreener pair API error: {response.status}")
                        return {}
        
        except Exception as e:
            logger.error(f"DexScreener pair API error: {str(e)}")
            return {}
    
    async def search_token(self, query: str) -> Dict[str, Any]:
        """
        Search for token by name or symbol
        """
        try:
            url = f"{self.base_url}/dex/search"
            params = {"q": query}
            
            # Create SSL context to handle SSL issues
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_search_response(data)
                    else:
                        logger.error(f"DexScreener search API error: {response.status}")
                        return {}
        
        except Exception as e:
            logger.error(f"DexScreener search API error: {str(e)}")
            return {}
    
    def _get_chain_identifier(self, chain: ChainType) -> Optional[str]:
        """Get chain identifier for DexScreener API"""
        chain_id_map = {
            ChainType.ETHEREUM: "ethereum",
            ChainType.BASE: "base"
        }
        return chain_id_map.get(chain)
    
    def _parse_token_response(self, data: Dict[str, Any], address: str) -> Dict[str, Any]:
        """Parse DexScreener token response"""
        result = {}
        
        try:
            if "pairs" in data and data["pairs"]:
                # Get the first pair (usually the most liquid)
                pair = data["pairs"][0]
                
                # Basic token info
                if "baseToken" in pair:
                    base_token = pair["baseToken"]
                    result["name"] = base_token.get("name")
                    result["symbol"] = base_token.get("symbol")
                    result["address"] = base_token.get("address")
                    result["decimals"] = base_token.get("decimals")
                
                # Market data
                result["price_usd"] = self._safe_decimal(pair.get("priceUsd"))
                result["price_change_24h"] = self._safe_decimal(pair.get("priceChange", {}).get("h24"))
                result["volume_24h"] = self._safe_decimal(pair.get("volume", {}).get("h24"))
                result["liquidity_usd"] = self._safe_decimal(pair.get("liquidity", {}).get("usd"))
                result["fdv"] = self._safe_decimal(pair.get("fdv"))
                
                # Market cap calculation
                if result["price_usd"] and result.get("decimals"):
                    # Get total supply from pair info if available
                    total_supply = self._safe_decimal(pair.get("totalSupply"))
                    if total_supply:
                        # Adjust for decimals
                        adjusted_supply = total_supply / (10 ** result["decimals"])
                        result["market_cap"] = result["price_usd"] * adjusted_supply
                
                # Pair information
                result["pair_address"] = pair.get("pairAddress")
                result["pair_created_at"] = pair.get("pairCreatedAt")
                result["dex_id"] = pair.get("dexId")
                result["url"] = pair.get("url")
                
                # Calculate token age from pair creation date
                token_age_info = self._calculate_token_age(pair.get("pairCreatedAt"))
                result.update(token_age_info)
                
                # Chain information
                result["chain_id"] = pair.get("chainId")
                result["chain"] = pair.get("chainId")
                
                # Additional metrics
                result["price_change_1h"] = self._safe_decimal(pair.get("priceChange", {}).get("h1"))
                result["price_change_6h"] = self._safe_decimal(pair.get("priceChange", {}).get("h6"))
                result["volume_1h"] = self._safe_decimal(pair.get("volume", {}).get("h1"))
                result["volume_6h"] = self._safe_decimal(pair.get("volume", {}).get("h6"))
                
                # Liquidity information
                result["liquidity_eth"] = self._safe_decimal(pair.get("liquidity", {}).get("eth"))
                result["liquidity_btc"] = self._safe_decimal(pair.get("liquidity", {}).get("btc"))
                
                # Trading information
                result["txns_1h"] = pair.get("txns", {}).get("h1", {}).get("buys", 0) + pair.get("txns", {}).get("h1", {}).get("sells", 0)
                result["txns_6h"] = pair.get("txns", {}).get("h6", {}).get("buys", 0) + pair.get("txns", {}).get("h6", {}).get("sells", 0)
                result["txns_24h"] = pair.get("txns", {}).get("h24", {}).get("buys", 0) + pair.get("txns", {}).get("h24", {}).get("sells", 0)
                
                # Buy/sell ratio
                buys_24h = pair.get("txns", {}).get("h24", {}).get("buys", 0)
                sells_24h = pair.get("txns", {}).get("h24", {}).get("sells", 0)
                if buys_24h + sells_24h > 0:
                    result["buy_sell_ratio"] = buys_24h / (buys_24h + sells_24h)
                
                # Basic liquidity lock detection based on available data
                lock_info = self._detect_basic_liquidity_lock(pair)
                result.update(lock_info)
                
                # Source information
                result["source"] = "DexScreener"
                result["analysis_timestamp"] = self._get_current_timestamp()
                
        except Exception as e:
            logger.error(f"Error parsing DexScreener token response: {str(e)}")
        
        return result
    
    def _parse_pair_response(self, data: Dict[str, Any], address: str) -> Dict[str, Any]:
        """Parse DexScreener pair response"""
        result = {}
        
        try:
            if "pairs" in data and data["pairs"]:
                pairs = data["pairs"]
                
                # Get all pairs for this token
                result["pairs"] = []
                total_liquidity = Decimal("0")
                total_volume_24h = Decimal("0")
                
                for pair in pairs:
                    pair_data = {
                        "pair_address": pair.get("pairAddress"),
                        "dex_id": pair.get("dexId"),
                        "liquidity_usd": self._safe_decimal(pair.get("liquidity", {}).get("usd")),
                        "volume_24h": self._safe_decimal(pair.get("volume", {}).get("h24")),
                        "price_usd": self._safe_decimal(pair.get("priceUsd")),
                        "url": pair.get("url")
                    }
                    
                    result["pairs"].append(pair_data)
                    
                    # Sum up totals
                    if pair_data["liquidity_usd"]:
                        total_liquidity += pair_data["liquidity_usd"]
                    if pair_data["volume_24h"]:
                        total_volume_24h += pair_data["volume_24h"]
                
                result["total_liquidity_usd"] = total_liquidity
                result["total_volume_24h"] = total_volume_24h
                result["pair_count"] = len(pairs)
                
                # Get the most liquid pair
                if pairs:
                    most_liquid_pair = max(pairs, key=lambda p: float(p.get("liquidity", {}).get("usd", 0) or 0))
                    result["most_liquid_pair"] = {
                        "pair_address": most_liquid_pair.get("pairAddress"),
                        "dex_id": most_liquid_pair.get("dexId"),
                        "liquidity_usd": self._safe_decimal(most_liquid_pair.get("liquidity", {}).get("usd")),
                        "url": most_liquid_pair.get("url")
                    }
                
        except Exception as e:
            logger.error(f"Error parsing DexScreener pair response: {str(e)}")
        
        return result
    
    def _parse_search_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse DexScreener search response"""
        result = {}
        
        try:
            if "pairs" in data:
                result["pairs"] = data["pairs"]
                result["pair_count"] = len(data["pairs"])
            
            if "tokens" in data:
                result["tokens"] = data["tokens"]
                result["token_count"] = len(data["tokens"])
            
        except Exception as e:
            logger.error(f"Error parsing DexScreener search response: {str(e)}")
        
        return result
    
    def _safe_decimal(self, value: Any) -> Optional[Decimal]:
        """Safely convert value to Decimal"""
        if value is None:
            return None
        
        try:
            if isinstance(value, str):
                # Remove commas and convert
                value = value.replace(',', '')
                return Decimal(value)
            elif isinstance(value, (int, float)):
                return Decimal(str(value))
            else:
                return None
        except (ValueError, TypeError, ArithmeticError):
            return None
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    async def get_comprehensive_market_data(self, address: str, chain: ChainType) -> Dict[str, Any]:
        """
        Get comprehensive market data from DexScreener
        """
        try:
            # Get token and pair data concurrently
            token_task = self.get_token_data(address, chain)
            pair_task = self.get_pair_data(address, chain)
            
            token_data, pair_data = await asyncio.gather(
                token_task, pair_task, return_exceptions=True
            )
            
            # Combine results
            result = {}
            
            if isinstance(token_data, dict):
                result.update(token_data)
            
            if isinstance(pair_data, dict):
                result.update(pair_data)
            
            # Add source information
            result["source"] = "DexScreener"
            result["analysis_timestamp"] = self._get_current_timestamp()
            
            return result
        
        except Exception as e:
            logger.error(f"Error in comprehensive DexScreener analysis: {str(e)}")
            return {}
    
    def is_low_liquidity(self, market_data: Dict[str, Any]) -> bool:
        """Check if token has low liquidity"""
        if not market_data:
            return True
        
        liquidity = market_data.get("liquidity_usd")
        if liquidity is None:
            return True
        
        return float(liquidity) < 1000  # Less than $1000 liquidity
    
    def is_honeypot_candidate(self, market_data: Dict[str, Any]) -> bool:
        """Check if token is a honeypot candidate based on market data"""
        if not market_data:
            return True
        
        # Check for zero liquidity
        liquidity = market_data.get("liquidity_usd")
        if liquidity is not None and float(liquidity) == 0:
            return True
        
        # Check for very low volume
        volume_24h = market_data.get("volume_24h")
        if volume_24h is not None and float(volume_24h) == 0:
            return True
        
        # Check for no trading activity
        txns_24h = market_data.get("txns_24h", 0)
        if txns_24h == 0:
            return True
        
        return False
    
    def get_market_health_score(self, market_data: Dict[str, Any]) -> int:
        """Get market health score (0-100)"""
        if not market_data:
            return 0
        
        score = 100
        
        # Deduct points for low liquidity
        liquidity = market_data.get("liquidity_usd")
        if liquidity is not None:
            if float(liquidity) == 0:
                score -= 50
            elif float(liquidity) < 1000:
                score -= 30
            elif float(liquidity) < 10000:
                score -= 15
        
        # Deduct points for low volume
        volume_24h = market_data.get("volume_24h")
        if volume_24h is not None:
            if float(volume_24h) == 0:
                score -= 20
            elif float(volume_24h) < 1000:
                score -= 10
        
        # Deduct points for low trading activity
        txns_24h = market_data.get("txns_24h", 0)
        if txns_24h == 0:
            score -= 15
        elif txns_24h < 10:
            score -= 10
        
        # Deduct points for negative price change
        price_change_24h = market_data.get("price_change_24h")
        if price_change_24h is not None and float(price_change_24h) < -50:
            score -= 10
        
        return max(0, score)
    
    def _detect_basic_liquidity_lock(self, pair_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect basic liquidity lock information from DexScreener data"""
        lock_info = {
            "liquidity_locked": False,
            "liquidity_lock_percentage": None,
            "liquidity_lock_platform": None
        }
        
        try:
            # Get pair creation date
            pair_created_at = pair_data.get("pairCreatedAt")
            liquidity_usd = pair_data.get("liquidity", {}).get("usd")
            
            if pair_created_at and liquidity_usd and float(liquidity_usd) > 0:
                from datetime import datetime, timezone
                try:
                    # Parse timestamp (could be Unix timestamp in milliseconds or ISO format)
                    if isinstance(pair_created_at, (int, float)):
                        # Check if it's in milliseconds (13 digits) or seconds (10 digits)
                        if pair_created_at > 1e12:  # Milliseconds
                            creation_date = datetime.fromtimestamp(pair_created_at / 1000, tz=timezone.utc)
                        else:  # Seconds
                            creation_date = datetime.fromtimestamp(pair_created_at, tz=timezone.utc)
                    else:
                        # Try to parse as ISO format
                        creation_date = datetime.fromisoformat(str(pair_created_at).replace('Z', '+00:00'))
                    
                    now = datetime.now(timezone.utc)
                    age_days = (now - creation_date).days
                    
                    # More conservative approach - only detect locks for very new tokens with significant liquidity
                    # This reduces false positives
                    if age_days < 7 and float(liquidity_usd) > 10000:
                        lock_info["liquidity_locked"] = True
                        lock_info["liquidity_lock_platform"] = "Likely Locked"
                        lock_info["liquidity_lock_percentage"] = 100.0
                        
                except (ValueError, TypeError) as e:
                    logger.error(f"Error parsing pair creation date: {str(e)}")
            
            # Additional heuristics based on trading patterns
            volume_24h = pair_data.get("volume", {}).get("h24")
            txns_24h = pair_data.get("txns", {}).get("h24", {}).get("buys", 0) + pair_data.get("txns", {}).get("h24", {}).get("sells", 0)
            
            # If there's significant liquidity but very low trading activity, it might indicate locked liquidity
            if liquidity_usd and float(liquidity_usd) > 100000 and volume_24h and float(volume_24h) < 500 and txns_24h < 3:
                if not lock_info["liquidity_locked"]:
                    lock_info["liquidity_locked"] = True
                    lock_info["liquidity_lock_platform"] = "Suspected Lock"
                    lock_info["liquidity_lock_percentage"] = 100.0
            
        except Exception as e:
            logger.error(f"Error in basic liquidity lock detection: {str(e)}")
        
        return lock_info
    
    def _calculate_token_age(self, pair_created_at: Any) -> Dict[str, Any]:
        """Calculate token age from pair creation date"""
        age_info = {
            "token_age_days": None,
            "pair_created_at": None
        }
        
        if not pair_created_at:
            return age_info
        
        try:
            from datetime import datetime, timezone
            
            # Parse timestamp (could be Unix timestamp in milliseconds or ISO format)
            if isinstance(pair_created_at, (int, float)):
                # Check if it's in milliseconds (13 digits) or seconds (10 digits)
                if pair_created_at > 1e12:  # Milliseconds
                    creation_date = datetime.fromtimestamp(pair_created_at / 1000, tz=timezone.utc)
                else:  # Seconds
                    creation_date = datetime.fromtimestamp(pair_created_at, tz=timezone.utc)
            else:
                # Try to parse as ISO format
                creation_date = datetime.fromisoformat(str(pair_created_at).replace('Z', '+00:00'))
            
            now = datetime.now(timezone.utc)
            age_days = (now - creation_date).days
            
            age_info["token_age_days"] = age_days
            age_info["pair_created_at"] = creation_date.isoformat()
            
        except (ValueError, TypeError) as e:
            logger.error(f"Error calculating token age: {str(e)}")
        
        return age_info
