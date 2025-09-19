"""
RPC service for BearTech Token Analysis Bot (fallback service)
"""
import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal
from ..config import RPC_ENDPOINTS, REQUEST_TIMEOUT
from ..models.token import TokenBasicInfo, ChainType
from ..utils.chain_detector import ChainDetector
from ..data.lock_contracts import is_known_lock_contract, get_lock_contracts_for_chain

logger = logging.getLogger(__name__)


class RPCService:
    """RPC service for basic contract information"""
    
    def __init__(self):
        self.rpc_endpoints = RPC_ENDPOINTS
        self.timeout = REQUEST_TIMEOUT
    
    async def get_basic_token_info(self, address: str, chain: ChainType) -> Dict[str, Any]:
        """
        Get basic token information via RPC calls
        """
        try:
            rpc_urls = self.rpc_endpoints.get(chain.value)
            if not rpc_urls:
                logger.error(f"No RPC endpoints for chain: {chain}")
                return {}
            
            # Try each RPC endpoint until one works
            for rpc_url in rpc_urls:
                try:
                    # Get token name, symbol, decimals, and total supply
                    name = await self._call_contract_method(address, "name()", rpc_url)
                    symbol = await self._call_contract_method(address, "symbol()", rpc_url)
                    decimals = await self._call_contract_method(address, "decimals()", rpc_url)
                    total_supply = await self._call_contract_method(address, "totalSupply()", rpc_url)
                    
                    result = {
                        "name": self._decode_string(name) if name else None,
                        "symbol": self._decode_string(symbol) if symbol else None,
                        "decimals": self._decode_uint(decimals) if decimals else None,
                        "total_supply": self._decode_uint(total_supply) if total_supply else None,
                        "source": "RPC",
                        "analysis_timestamp": self._get_current_timestamp()
                    }
                    
                    return result
                    
                except Exception as e:
                    logger.debug(f"RPC endpoint {rpc_url} failed: {str(e)}")
                    continue
            
            logger.error(f"All RPC endpoints failed for chain: {chain}")
            return {}
        
        except Exception as e:
            logger.error(f"RPC service error: {str(e)}")
            return {}
    
    async def get_token_balance(self, token_address: str, holder_address: str, chain: ChainType) -> Optional[Decimal]:
        """
        Get token balance for a specific holder
        """
        try:
            rpc_url = self.rpc_endpoints.get(chain.value)
            if not rpc_url:
                return None
            
            # Call balanceOf method
            balance_data = await self._call_contract_method(
                token_address, 
                f"balanceOf(address)", 
                rpc_url, 
                [holder_address]
            )
            
            if balance_data:
                return self._decode_uint(balance_data)
            
            return None
        
        except Exception as e:
            logger.error(f"RPC balance error: {str(e)}")
            return None
    
    async def get_contract_code(self, address: str, chain: ChainType) -> Dict[str, Any]:
        """
        Get contract bytecode
        """
        try:
            rpc_url = self.rpc_endpoints.get(chain.value)
            if not rpc_url:
                return {}
            
            # Get contract code
            code = await self._get_code(address, rpc_url)
            
            result = {
                "bytecode": code,
                "is_contract": bool(code and code != "0x"),
                "source": "RPC",
                "analysis_timestamp": self._get_current_timestamp()
            }
            
            return result
        
        except Exception as e:
            logger.error(f"RPC contract code error: {str(e)}")
            return {}
    
    async def get_transaction_count(self, address: str, chain: ChainType) -> Optional[int]:
        """
        Get transaction count for address
        """
        try:
            rpc_url = self.rpc_endpoints.get(chain.value)
            if not rpc_url:
                return None
            
            # Get transaction count
            tx_count = await self._get_transaction_count(address, rpc_url)
            
            return tx_count
        
        except Exception as e:
            logger.error(f"RPC transaction count error: {str(e)}")
            return None
    
    async def get_balance(self, address: str, chain: ChainType) -> Optional[Decimal]:
        """
        Get native token balance
        """
        try:
            rpc_url = self.rpc_endpoints.get(chain.value)
            if not rpc_url:
                return None
            
            # Get balance
            balance = await self._get_balance(address, rpc_url)
            
            return balance
        
        except Exception as e:
            logger.error(f"RPC balance error: {str(e)}")
            return None
    
    async def _call_contract_method(self, contract_address: str, method_signature: str, rpc_url: str, params: List[str] = None) -> Optional[str]:
        """Call contract method via RPC"""
        try:
            # Encode method call
            data = self._encode_method_call(method_signature, params or [])
            
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_call",
                "params": [
                    {
                        "to": contract_address,
                        "data": data
                    },
                    "latest"
                ],
                "id": 1
            }
            
            # Create SSL context to handle SSL issues
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(rpc_url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        if "result" in result:
                            return result["result"]
            
            return None
        
        except Exception as e:
            logger.error(f"RPC method call error: {str(e)}")
            return None
    
    async def _get_code(self, address: str, rpc_url: str) -> Optional[str]:
        """Get contract code via RPC"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_getCode",
                "params": [address, "latest"],
                "id": 1
            }
            
            # Create SSL context to handle SSL issues
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(rpc_url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        if "result" in result:
                            return result["result"]
            
            return None
        
        except Exception as e:
            logger.error(f"RPC get code error: {str(e)}")
            return None
    
    async def _get_transaction_count(self, address: str, rpc_url: str) -> Optional[int]:
        """Get transaction count via RPC"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_getTransactionCount",
                "params": [address, "latest"],
                "id": 1
            }
            
            # Create SSL context to handle SSL issues
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(rpc_url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        if "result" in result:
                            return int(result["result"], 16)
            
            return None
        
        except Exception as e:
            logger.error(f"RPC get transaction count error: {str(e)}")
            return None
    
    async def _get_balance(self, address: str, rpc_url: str) -> Optional[Decimal]:
        """Get balance via RPC"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_getBalance",
                "params": [address, "latest"],
                "id": 1
            }
            
            # Create SSL context to handle SSL issues
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(rpc_url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        if "result" in result:
                            wei_balance = int(result["result"], 16)
                            # Convert from Wei to ETH (18 decimals)
                            eth_balance = Decimal(wei_balance) / Decimal("1000000000000000000")
                            return eth_balance
            
            return None
        
        except Exception as e:
            logger.error(f"RPC get balance error: {str(e)}")
            return None
    
    def _encode_method_call(self, method_signature: str, params: List[str]) -> str:
        """Encode method call data"""
        try:
            import hashlib
            
            # Get method selector (first 4 bytes of keccak256 hash)
            method_hash = hashlib.sha3_256(method_signature.encode()).digest()[:4]
            method_selector = "0x" + method_hash.hex()
            
            # For simple methods without parameters, just return the selector
            if not params:
                return method_selector
            
            # For methods with parameters, we would need to encode them
            # This is a simplified version - in production, you'd use a proper ABI encoder
            return method_selector
        
        except Exception as e:
            logger.error(f"Method encoding error: {str(e)}")
            return "0x"
    
    def _decode_string(self, hex_data: str) -> Optional[str]:
        """Decode string from hex data"""
        try:
            if not hex_data or hex_data == "0x":
                return None
            
            # Remove 0x prefix
            hex_data = hex_data[2:]
            
            # Skip the first 64 characters (offset and length)
            if len(hex_data) < 128:
                return None
            
            # Get string length
            length_hex = hex_data[64:128]
            length = int(length_hex, 16)
            
            # Get string data
            string_hex = hex_data[128:128 + length * 2]
            
            # Convert to string
            string_bytes = bytes.fromhex(string_hex)
            return string_bytes.decode('utf-8')
        
        except Exception as e:
            logger.error(f"String decoding error: {str(e)}")
            return None
    
    def _decode_uint(self, hex_data: str) -> Optional[Decimal]:
        """Decode uint from hex data"""
        try:
            if not hex_data or hex_data == "0x":
                return None
            
            # Remove 0x prefix and convert to int
            hex_data = hex_data[2:]
            return Decimal(int(hex_data, 16))
        
        except Exception as e:
            logger.error(f"Uint decoding error: {str(e)}")
            return None
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    async def get_comprehensive_basic_info(self, address: str, chain: ChainType) -> Dict[str, Any]:
        """
        Get comprehensive basic information via RPC
        """
        try:
            # Run all RPC calls concurrently
            token_info_task = self.get_basic_token_info(address, chain)
            contract_code_task = self.get_contract_code(address, chain)
            tx_count_task = self.get_transaction_count(address, chain)
            balance_task = self.get_balance(address, chain)
            
            token_info, contract_code, tx_count, balance = await asyncio.gather(
                token_info_task, contract_code_task, tx_count_task, balance_task, return_exceptions=True
            )
            
            # Combine results
            result = {}
            
            if isinstance(token_info, dict):
                result.update(token_info)
            
            if isinstance(contract_code, dict):
                result.update(contract_code)
            
            if isinstance(tx_count, int):
                result["transaction_count"] = tx_count
            
            if isinstance(balance, Decimal):
                result["balance"] = balance
            
            # Add source information
            result["source"] = "RPC"
            result["analysis_timestamp"] = self._get_current_timestamp()
            
            return result
        
        except Exception as e:
            logger.error(f"Error in comprehensive RPC analysis: {str(e)}")
            return {}
    
    def is_contract_address(self, address: str, chain: ChainType) -> bool:
        """Check if address is a contract"""
        try:
            # This would require an async call, so we'll return a placeholder
            # In a real implementation, you'd call get_contract_code and check if bytecode exists
            return True  # Assume it's a contract for now
        
        except Exception as e:
            logger.error(f"Contract check error: {str(e)}")
            return False
    
    def validate_address(self, address: str) -> bool:
        """Validate Ethereum-style address format"""
        try:
            if not address or not isinstance(address, str):
                return False
            
            # Check if it starts with 0x and has correct length
            if not address.startswith("0x"):
                return False
            
            if len(address) != 42:
                return False
            
            # Check if it's valid hex
            int(address[2:], 16)
            return True
        
        except ValueError:
            return False
    
    async def get_liquidity_lock_info(self, token_address: str, chain: ChainType) -> Dict[str, Any]:
        """
        Get liquidity lock information via RPC calls
        """
        try:
            rpc_urls = self.rpc_endpoints.get(chain.value)
            if not rpc_urls:
                return {}
            
            # Try each RPC endpoint until one works
            for rpc_url in rpc_urls:
                try:
                    # Get LP token address for this token
                    lp_token_address = await self._get_lp_token_address(token_address, rpc_url)
                    
                    if lp_token_address:
                        # Get LP token holders
                        holders = await self._get_token_holders(lp_token_address, rpc_url)
                        
                        # Analyze for lock contracts
                        lock_info = await self._analyze_liquidity_locks(holders, chain)
                        
                        if lock_info.get("liquidity_locked"):
                            return lock_info
                    
                    # If no LP token found, try direct lock contract detection
                    lock_info = await self._check_direct_lock_contracts(token_address, chain, rpc_url)
                    if lock_info.get("liquidity_locked"):
                        return lock_info
                    
                except Exception as e:
                    logger.error(f"RPC endpoint error: {str(e)}")
                    continue
            
            return {"liquidity_locked": False}
        
        except Exception as e:
            logger.error(f"Error getting liquidity lock info: {str(e)}")
            return {"liquidity_locked": False}
    
    async def _get_lp_token_address(self, token_address: str, rpc_url: str) -> Optional[str]:
        """Get LP token address for a given token"""
        try:
            # This would require finding the LP token address
            # For Uniswap V2, we'd need to call the factory contract
            # For now, return None as this requires complex logic
            return None
        
        except Exception as e:
            logger.error(f"Error getting LP token address: {str(e)}")
            return None
    
    async def _get_token_holders(self, token_address: str, rpc_url: str) -> List[Dict[str, Any]]:
        """Get token holders via RPC"""
        try:
            # This would require calling the token contract to get holders
            # For ERC-20 tokens, we'd need to scan Transfer events
            # For now, return empty list as this requires complex logic
            return []
        
        except Exception as e:
            logger.error(f"Error getting token holders: {str(e)}")
            return []
    
    async def _analyze_liquidity_locks(self, holders: List[Dict[str, Any]], chain: ChainType) -> Dict[str, Any]:
        """Analyze liquidity locks from token holders"""
        try:
            lock_info = {
                "liquidity_locked": False,
                "liquidity_lock_percentage": None,
                "liquidity_lock_days": None,
                "liquidity_lock_expiry": None,
                "liquidity_lock_platform": None,
                "liquidity_lock_contract": None
            }
            
            # Check each holder against known lock contracts
            for holder in holders:
                holder_address = holder.get("address", "").lower()
                holder_balance = holder.get("balance", 0)
                
                # Check if this holder is a known lock contract
                lock_contract_info = is_known_lock_contract(holder_address, chain.value)
                
                if lock_contract_info.get("is_lock_contract"):
                    lock_info["liquidity_locked"] = True
                    lock_info["liquidity_lock_platform"] = lock_contract_info.get("name")
                    lock_info["liquidity_lock_contract"] = holder_address
                    
                    # Try to get lock duration from the contract
                    lock_duration = await self._get_lock_duration(holder_address, chain)
                    if lock_duration:
                        lock_info["liquidity_lock_days"] = lock_duration.get("days")
                        lock_info["liquidity_lock_expiry"] = lock_duration.get("expiry")
                    
                    # Calculate lock percentage
                    if holder_balance > 0:
                        total_supply = holder.get("total_supply", 0)
                        if total_supply > 0:
                            percentage = (holder_balance / total_supply) * 100
                            lock_info["liquidity_lock_percentage"] = round(percentage, 2)
            
            return lock_info
        
        except Exception as e:
            logger.error(f"Error analyzing liquidity locks: {str(e)}")
            return {"liquidity_locked": False}
    
    async def _get_lock_duration(self, lock_contract_address: str, chain: ChainType) -> Optional[Dict[str, Any]]:
        """Get lock duration from lock contract"""
        try:
            rpc_urls = self.rpc_endpoints.get(chain.value)
            if not rpc_urls:
                return None
            
            for rpc_url in rpc_urls:
                try:
                    # Try to call common lock contract methods
                    # Different platforms have different method names
                    methods_to_try = [
                        "unlockTime()",
                        "releaseTime()",
                        "endTime()",
                        "lockTime()",
                        "expiry()"
                    ]
                    
                    for method in methods_to_try:
                        result = await self._call_contract_method(lock_contract_address, method, rpc_url)
                        if result:
                            timestamp = self._decode_uint(result)
                            if timestamp and timestamp > 0:
                                # Convert timestamp to days and expiry date
                                from datetime import datetime, timezone
                                expiry_date = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                                now = datetime.now(timezone.utc)
                                days_remaining = (expiry_date - now).days
                                
                                return {
                                    "days": max(0, days_remaining),
                                    "expiry": expiry_date.isoformat(),
                                    "timestamp": timestamp
                                }
                    
                except Exception as e:
                    logger.error(f"RPC endpoint error for lock duration: {str(e)}")
                    continue
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting lock duration: {str(e)}")
            return None
    
    async def _check_direct_lock_contracts(self, token_address: str, chain: ChainType, rpc_url: str) -> Dict[str, Any]:
        """Check for direct lock contracts without LP token analysis"""
        try:
            lock_info = {
                "liquidity_locked": False,
                "liquidity_lock_percentage": None,
                "liquidity_lock_days": None,
                "liquidity_lock_expiry": None,
                "liquidity_lock_platform": None,
                "liquidity_lock_contract": None
            }
            
            # Get known lock contracts for this chain
            lock_contracts = get_lock_contracts_for_chain(chain.value)
            
            # Check if any known lock contracts have this token locked
            for platform, platform_data in lock_contracts.items():
                for contract_address in platform_data["contracts"]:
                    try:
                        # Try to call lock contract to see if it has this token
                        # This would require knowing the specific method names for each platform
                        # For now, we'll skip this complex logic
                        pass
                    except Exception as e:
                        logger.error(f"Error checking lock contract {contract_address}: {str(e)}")
                        continue
            
            return lock_info
        
        except Exception as e:
            logger.error(f"Error checking direct lock contracts: {str(e)}")
            return {"liquidity_locked": False}
