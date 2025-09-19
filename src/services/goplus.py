"""
GoPlus Security API Integration
Provides comprehensive token security analysis including tax information
"""

import aiohttp
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from ..config import get_env_var

logger = logging.getLogger(__name__)

class GoPlusService:
    """GoPlus Security API service for token analysis"""
    
    def __init__(self):
        self.api_key = get_env_var("GOPLUS_API_KEY", "Y0ZVbTgCm8G40GbczyAD")
        self.base_url = "https://api.gopluslabs.io/api/v1"
        self.timeout = 30
        
        if not self.api_key or self.api_key == "your_goplus_api_key_here":
            logger.warning("GoPlus API key not configured")
    
    def _get_chain_id(self, chain: str) -> str:
        """Convert chain name to GoPlus chain ID"""
        chain_mapping = {
            "ethereum": "1",
            "base": "8453"
        }
        return chain_mapping.get(chain.lower(), "1")
    
    def _convert_to_bool(self, value) -> bool:
        """Convert various value types to boolean"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ['true', '1', 'yes', 'on']
        if isinstance(value, (int, float)):
            return bool(value)
        return False
    
    async def get_token_security(self, address: str, chain: str) -> Dict[str, Any]:
        """
        Get comprehensive security analysis for a token
        
        Args:
            address: Token contract address
            chain: Blockchain network (ethereum, base)
            
        Returns:
            Dict containing security analysis data
        """
        if not self.api_key:
            return {
                "source": "GoPlus",
                "error": "API key not configured"
            }
        
        chain_id = self._get_chain_id(chain)
        url = f"{self.base_url}/token_security/{chain_id}"
        
        params = {
            "contract_addresses": address
        }
        
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            # Create SSL context to handle SSL issues
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(
                    url, 
                    params=params, 
                    headers=headers, 
                    timeout=self.timeout
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"GoPlus API response: {data}")
                        
                        if data.get("code") == 1 and data.get("result"):
                            result = data["result"]
                            if address.lower() in result:
                                token_data = result[address.lower()]
                                # Add the token address to the data for contract holdings calculation
                                token_data["token_address"] = address.lower()
                                return self._parse_security_data(token_data)
                            else:
                                return {
                                    "source": "GoPlus",
                                    "error": "Token not found in response"
                                }
                        else:
                            error_msg = data.get("message", "Unknown error")
                            return {
                                "source": "GoPlus",
                                "error": f"API error: {error_msg}"
                            }
                    else:
                        return {
                            "source": "GoPlus",
                            "error": f"HTTP {response.status}: {await response.text()}"
                        }
                        
        except Exception as e:
            logger.error(f"GoPlus API error: {e}")
            return {
                "source": "GoPlus",
                "error": str(e)
            }
    
    def _parse_security_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse GoPlus security data into standardized format"""
        try:
            # Extract tax information
            buy_tax = None
            sell_tax = None
            
            if "buy_tax" in data:
                buy_tax = float(data["buy_tax"]) if data["buy_tax"] else None
            if "sell_tax" in data:
                sell_tax = float(data["sell_tax"]) if data["sell_tax"] else None
            
            # Extract security flags (convert string values to booleans)
            is_honeypot = self._convert_to_bool(data.get("is_honeypot", False))
            is_open_source = self._convert_to_bool(data.get("is_open_source", False))
            is_proxy = self._convert_to_bool(data.get("is_proxy", False))
            is_mintable = self._convert_to_bool(data.get("is_mintable", False))
            is_pausable = self._convert_to_bool(data.get("is_pausable", False))
            
            # Extract risk level
            risk_level = data.get("risk_level", "unknown")
            
            # Extract warnings
            warnings = []
            if is_honeypot:
                warnings.append("🚨 HONEYPOT DETECTED - DO NOT BUY!")
            if is_proxy:
                warnings.append("⚠️ Proxy contract detected")
            if is_mintable:
                warnings.append("⚠️ Token can be minted (inflation risk)")
            if is_pausable:
                warnings.append("⚠️ Token can be paused")

            # Calculate top 10 holders ratio from holders data (excluding contract and Uniswap)
            top_holders_ratio, contract_holding_percentage = self._calculate_top_holders_ratio(data)
            
            # If we don't have contract holdings from holders data, try to get it from the existing top_holders_ratio
            # This is a fallback when GoPlus doesn't provide detailed holders data
            if contract_holding_percentage is None:
                # Try to extract from existing data or default to 0%
                contract_holding_percentage = 0.0
            
            # Calculate burn information from holders data
            burn_info = self._calculate_burn_info(data)
            
            # Extract liquidity lock information
            liquidity_lock_info = self._extract_liquidity_lock_info(data)

            return {
                "source": "GoPlus",
                "name": data.get("token_name"),
                "symbol": data.get("token_symbol"),
                "buy_tax": buy_tax,
                "sell_tax": sell_tax,
                "is_honeypot": is_honeypot,
                "is_open_source": is_open_source,
                "is_proxy": is_proxy,
                "is_mintable": is_mintable,
                "is_pausable": is_pausable,
                "risk_level": risk_level,
                "warnings": warnings,
                "verified": self._convert_to_bool(data.get("is_verified", False)),
                "holder_count": data.get("holder_count"),
                "total_supply": data.get("total_supply"),
                "contract_creator": data.get("creator_address"),
                "top_holders_ratio": top_holders_ratio,
                "contract_holding_percentage": contract_holding_percentage,  # "Clog" field
                "burn_info": burn_info,
                "liquidity": data.get("liquidity"),
                "liquidity_lock_platform": liquidity_lock_info.get("platform"),
                "liquidity_lock_unlock_time": liquidity_lock_info.get("unlock_time"),
                "market_cap": data.get("market_cap"),
                "price": data.get("price"),
                "price_change_24h": data.get("price_change_24h"),
                "volume_24h": data.get("volume_24h"),
                "analysis_timestamp": self._get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error parsing GoPlus data: {e}")
            return {
                "source": "GoPlus",
                "error": f"Data parsing error: {str(e)}"
            }
    
    async def test_api(self) -> Dict[str, Any]:
        """Test GoPlus API connectivity"""
        if not self.api_key:
            return {
                "status": "error",
                "message": "API key not configured"
            }
        
        # Test with a known token (USDC on Ethereum)
        test_address = "0xA0b86a33E6441b8c4C8C0C4C0C4C0C4C0C4C0C4C"  # Invalid address for testing
        result = await self.get_token_security(test_address, "ethereum")
        
        if "error" in result:
            return {
                "status": "error",
                "message": result["error"]
            }
        else:
            return {
                "status": "success",
                "message": "API is working"
            }
    
    def _get_current_timestamp(self) -> str:
        """Get current UTC timestamp in ISO format"""
        return datetime.utcnow().isoformat() + "Z"
    
    def _calculate_top_holders_ratio(self, data: Dict[str, Any]) -> tuple[Optional[float], Optional[float]]:
        """Calculate top 10 holders ratio from holders data, excluding contract, Uniswap and dead addresses
        Returns: (top_holders_ratio, contract_holding_percentage)
        """
        try:
            holders = data.get("holders", [])
            total_supply = data.get("total_supply")
            token_address = data.get("token_address", "").lower()
            
            # If we don't have holders data, we can't calculate contract holdings
            if not holders or not total_supply:
                # Return the existing top_holders_ratio if available, but default contract holdings to 0%
                existing_ratio = data.get("top_holders_ratio")
                return existing_ratio, 0.0
            
            # Convert total supply to float for calculation
            try:
                total_supply_float = float(total_supply)
                if total_supply_float == 0:
                    return None, None
            except (ValueError, TypeError):
                return None, None
            
            # Addresses to exclude from top holders calculation
            excluded_addresses = {
                # Dead/burn addresses
                "0x000000000000000000000000000000000000dead",
                "0x0000000000000000000000000000000000000000",
                "0x0000000000000000000000000000000000000001",
                "0x0000000000000000000000000000000000000002",
                # Common Uniswap V2 addresses (these can vary by chain)
                "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",  # Uniswap V2 Router
                "0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f",  # Uniswap V2 Factory
                # Common Uniswap V3 addresses
                "0xe592427a0aece92de3edee1f18e0157c05861564",  # Uniswap V3 Router
                "0x1f98431c8ad98523631ae4a59f267346ea31f984",  # Uniswap V3 Factory
                # Base chain specific Uniswap addresses
                "0x4752ba5dbc23f44d87826276bf6fd6b1c372ad24",  # Base Uniswap V3 Router
                "0x33128a8fc17869897dce68ed026d694621f6fdfd",  # Base Uniswap V3 Factory
                # Add the token contract address itself
                token_address
            }
            
            # Filter out excluded addresses and get top 10 real holders
            filtered_holders = []
            contract_balance = 0
            
            for holder in holders:
                if isinstance(holder, dict) and "address" in holder:
                    address = holder["address"].lower()
                    
                    # Check if this is the contract address
                    if address == token_address:
                        try:
                            contract_balance = float(holder["balance"]) if holder["balance"] else 0
                        except (ValueError, TypeError):
                            contract_balance = 0
                        continue  # Skip contract address from top holders
                    
                    # Skip excluded addresses
                    if address in excluded_addresses:
                        continue
                    
                    # Skip addresses that look like burn addresses (starting with 0x000)
                    if address.startswith("0x000") and len(address) > 10:
                        continue
                    
                    # Skip addresses that contain "uniswap" in the name (if available)
                    holder_name = holder.get("name", "").lower()
                    if "uniswap" in holder_name or "pool" in holder_name:
                        continue
                    
                    filtered_holders.append(holder)
            
            # Get top 10 filtered holders (or all if less than 10)
            top_holders = filtered_holders[:10]
            
            # Calculate total balance of top holders
            top_holders_balance = 0
            for holder in top_holders:
                if isinstance(holder, dict) and "balance" in holder:
                    try:
                        balance = float(holder["balance"]) if holder["balance"] else 0
                        top_holders_balance += balance
                    except (ValueError, TypeError):
                        continue  # Skip invalid balance values
            
            # Calculate percentages
            top_holders_ratio = None
            if top_holders_balance > 0:
                ratio = (top_holders_balance / total_supply_float) * 100
                top_holders_ratio = round(ratio, 2)
            
            contract_holding_percentage = 0.0  # Default to 0% if no contract balance
            if contract_balance > 0:
                contract_ratio = (contract_balance / total_supply_float) * 100
                contract_holding_percentage = round(contract_ratio, 2)
            
            return top_holders_ratio, contract_holding_percentage
            
        except Exception as e:
            logger.error(f"Error calculating top holders ratio: {e}")
            return None, None
    
    def _calculate_burn_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate burn information from holders data"""
        try:
            holders = data.get("holders", [])
            total_supply = data.get("total_supply")
            
            if not holders or not total_supply:
                return {
                    "burned_amount": None,
                    "burn_percentage": None,
                    "burn_addresses": []
                }
            
            # Convert total supply to float for calculation
            try:
                total_supply_float = float(total_supply)
                if total_supply_float == 0:
                    return {
                        "burned_amount": None,
                        "burn_percentage": None,
                        "burn_addresses": []
                    }
            except (ValueError, TypeError):
                return {
                    "burned_amount": None,
                    "burn_percentage": None,
                    "burn_addresses": []
                }
            
            # Common burn addresses
            burn_address_patterns = [
                "0x000000000000000000000000000000000000dead",
                "0x0000000000000000000000000000000000000000",
                "0x0000000000000000000000000000000000000001",
                "0x0000000000000000000000000000000000000002"
            ]
            
            total_burned = 0
            burn_addresses = []
            
            for holder in holders:
                if isinstance(holder, dict) and "address" in holder and "balance" in holder:
                    address = holder["address"].lower()
                    balance = holder["balance"]
                    
                    # Check if this is a burn address
                    is_burn_address = False
                    for pattern in burn_address_patterns:
                        if address == pattern.lower():
                            is_burn_address = True
                            break
                    
                    # Also check for addresses with "burn" in the name or very low addresses
                    if not is_burn_address:
                        if (address.startswith("0x000") and len(address) > 10) or "burn" in address:
                            is_burn_address = True
                    
                    if is_burn_address:
                        try:
                            burned_amount = float(balance) if balance else 0
                            total_burned += burned_amount
                            burn_addresses.append({
                                "address": holder["address"],
                                "balance": burned_amount
                            })
                        except (ValueError, TypeError):
                            continue
            
            # Calculate burn percentage
            burn_percentage = None
            if total_burned > 0 and total_supply_float > 0:
                burn_percentage = (total_burned / total_supply_float) * 100
                burn_percentage = round(burn_percentage, 2)
            
            return {
                "burned_amount": total_burned if total_burned > 0 else None,
                "burn_percentage": burn_percentage,
                "burn_addresses": burn_addresses
            }
            
        except Exception as e:
            logger.error(f"Error calculating burn info: {e}")
            return {
                "burned_amount": None,
                "burn_percentage": None,
                "burn_addresses": []
            }
    
    def _extract_liquidity_lock_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract liquidity lock information from GoPlus data"""
        try:
            platform = None
            unlock_time = None
            
            # Check for LP holders data (this contains the lock information)
            lp_holders = data.get("lp_holders", [])
            if lp_holders and isinstance(lp_holders, list):
                for lp_holder in lp_holders:
                    if isinstance(lp_holder, dict):
                        # Check if this holder has locked tokens
                        is_locked = lp_holder.get("is_locked")
                        if is_locked == 1 or is_locked == "1":  # Locked
                            # Get lock details
                            locked_detail = lp_holder.get("locked_detail", [])
                            if locked_detail and isinstance(locked_detail, list):
                                for lock in locked_detail:
                                    if isinstance(lock, dict):
                                        # Extract unlock time
                                        end_time = lock.get("end_time")
                                        if end_time:
                                            unlock_time = end_time
                                        
                                        # Extract platform from tag field
                                        tag = lock.get("tag", "").lower()
                                        if "pinklock" in tag:
                                            platform = "PinkSale"
                                        elif "unicrypt" in tag:
                                            platform = "Unicrypt"
                                        elif "team" in tag:
                                            if "finance" in tag:
                                                platform = "Team Finance"
                                            else:
                                                platform = "Team Lock"
                                        elif "liquidity" in tag:
                                            platform = "Liquidity Lock"
                                        else:
                                            # Fallback: try to determine platform from holder info
                                            holder_name = lp_holder.get("name", "").lower()
                                            if "unicrypt" in holder_name:
                                                platform = "Unicrypt"
                                            elif "team" in holder_name:
                                                if "finance" in holder_name:
                                                    platform = "Team Finance"
                                                else:
                                                    platform = "Team Lock"
                                            elif "liquidity" in holder_name:
                                                platform = "Liquidity Lock"
                                            else:
                                                platform = "Unknown Platform"
                                        
                                        # If we found lock info, we can break
                                        if unlock_time:
                                            break
                            
                            # If we found lock info, we can break
                            if unlock_time:
                                break
            
            # Fallback: Check for other lock information fields
            if not unlock_time:
                # Check for lock information in the data
                lock_info = data.get("lock_info", {})
                if not lock_info:
                    # Try alternative field names that GoPlus might use
                    lock_info = data.get("liquidity_lock", {})
                
                # Extract platform information
                if lock_info:
                    platform = lock_info.get("platform") or lock_info.get("locker")
                    unlock_time = lock_info.get("unlock_time") or lock_info.get("unlock_date")
            
            # Format unlock time if it's a timestamp
            if unlock_time:
                try:
                    # If it's a Unix timestamp
                    if isinstance(unlock_time, (int, float)):
                        from datetime import datetime
                        unlock_time = datetime.fromtimestamp(unlock_time).isoformat()
                    # If it's already a string, keep it as is
                    elif isinstance(unlock_time, str):
                        pass
                except (ValueError, TypeError):
                    # If we can't parse it, keep the original value
                    pass
            
            return {
                "platform": platform,
                "unlock_time": unlock_time
            }
            
        except Exception as e:
            logger.error(f"Error extracting liquidity lock info: {e}")
            return {
                "platform": None,
                "unlock_time": None
            }
    
    async def _get_contract_holdings_from_rpc(self, token_address: str, chain: str) -> Optional[float]:
        """Get contract holdings percentage using RPC calls"""
        try:
            # Import RPC service
            from ..services.rpc import RPCService
            from ..models.token import ChainType
            
            # Map chain string to ChainType
            chain_map = {
                'ethereum': ChainType.ETHEREUM,
                'base': ChainType.BASE,
                'bsc': ChainType.BSC
            }
            
            chain_type = chain_map.get(chain.lower())
            if not chain_type:
                return None
            
            rpc_service = RPCService()
            
            # Get token info to get total supply
            token_info = await rpc_service.get_basic_token_info(token_address, chain_type)
            total_supply = token_info.get('total_supply')
            
            if not total_supply:
                return None
            
            # Get contract balance (contract holding its own tokens)
            contract_balance = await rpc_service.get_balance(token_address, chain_type)
            
            if contract_balance and total_supply:
                try:
                    balance_float = float(contract_balance)
                    supply_float = float(total_supply)
                    
                    if supply_float > 0:
                        percentage = (balance_float / supply_float) * 100
                        return round(percentage, 2)
                except (ValueError, TypeError):
                    pass
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting contract holdings from RPC: {e}")
            return None
