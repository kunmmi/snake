"""
Explorer API services (Etherscan, BSCScan, BaseScan) for BearTech Token Analysis Bot
"""
import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal
from ..config import EXPLORER_APIS, REQUEST_TIMEOUT
from ..models.token import TokenContractData, TokenDeployerData, ChainType
from ..utils.chain_detector import ChainDetector
from ..data.lock_contracts import is_known_lock_contract, get_lock_contracts_for_chain

logger = logging.getLogger(__name__)


class ExplorerService:
    """Explorer API service for contract and deployer information"""
    
    def __init__(self):
        self.explorer_apis = EXPLORER_APIS
        self.timeout = REQUEST_TIMEOUT
    
    def _add_chainid_param(self, params: Dict[str, Any], explorer_config: Dict[str, Any]) -> Dict[str, Any]:
        """Add chainid parameter for multichain API calls"""
        if "v2" in explorer_config.get("base_url", "") and "chain_id" in explorer_config:
            params["chainid"] = explorer_config["chain_id"]
        return params
    
    async def get_contract_info(self, address: str, chain: ChainType) -> Dict[str, Any]:
        """
        Get contract information from explorer API
        """
        try:
            explorer_config = self.explorer_apis.get(chain.value)
            if not explorer_config:
                logger.error(f"No explorer config for chain: {chain}")
                return {}
            
            # Get contract source code and ABI
            source_data = await self._get_contract_source(address, explorer_config)
            
            # Get contract creation info
            creation_data = await self._get_contract_creation(address, explorer_config)
            
            # Get transaction count
            tx_count = await self._get_transaction_count(address, explorer_config)
            
            # Combine results
            result = {}
            result.update(source_data)
            result.update(creation_data)
            result["transaction_count"] = tx_count
            result["source"] = explorer_config["name"]
            result["analysis_timestamp"] = self._get_current_timestamp()
            
            return result
        
        except Exception as e:
            logger.error(f"Explorer API error for {chain}: {str(e)}")
            return {}
    
    async def get_deployer_info(self, deployer_address: str, chain: ChainType) -> Dict[str, Any]:
        """
        Get deployer information from explorer API
        """
        try:
            explorer_config = self.explorer_apis.get(chain.value)
            if not explorer_config:
                return {}
            
            # Get deployer balance
            balance = await self._get_balance(deployer_address, explorer_config)
            
            # Get deployer transaction count
            tx_count = await self._get_transaction_count(deployer_address, explorer_config)
            
            # Get deployer's contract creations
            contract_creations = await self._get_contract_creations(deployer_address, explorer_config)
            
            # Get deployer's first transaction (age calculation)
            first_tx = await self._get_first_transaction(deployer_address, explorer_config)
            
            result = {
                "deployer_address": deployer_address,
                "deployer_balance": balance,
                "deployer_tx_count": tx_count,
                "deployer_contracts_created": contract_creations,
                "deployer_first_tx": first_tx,
                "source": explorer_config["name"],
                "analysis_timestamp": self._get_current_timestamp()
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Explorer deployer API error for {chain}: {str(e)}")
            return {}
    
    async def get_token_info(self, address: str, chain: ChainType) -> Dict[str, Any]:
        """
        Get token information from explorer API
        """
        try:
            explorer_config = self.explorer_apis.get(chain.value)
            if not explorer_config:
                return {}
            
            # Get token info (name, symbol, decimals, total supply)
            token_data = await self._get_token_info(address, explorer_config)
            
            # Get token holders count
            holders_count = await self._get_token_holders_count(address, explorer_config)
            
            result = {}
            result.update(token_data)
            result["holders_count"] = holders_count
            result["source"] = explorer_config["name"]
            result["analysis_timestamp"] = self._get_current_timestamp()
            
            return result
        
        except Exception as e:
            logger.error(f"Explorer token API error for {chain}: {str(e)}")
            return {}
    
    async def _get_contract_source(self, address: str, explorer_config: Dict[str, Any]) -> Dict[str, Any]:
        """Get contract source code and ABI"""
        try:
            url = explorer_config["base_url"]
            params = {
                "module": "contract",
                "action": "getsourcecode",
                "address": address,
                "apikey": explorer_config["api_key"]
            }
            
            # Add chainid for multichain API (Base chain)
            params = self._add_chainid_param(params, explorer_config)
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "1" and data.get("result"):
                            result = data["result"][0]
                            return {
                                "contract_verification_status": "Verified" if result.get("SourceCode") else "Not Verified",
                                "contract_source_code": result.get("SourceCode"),
                                "contract_abi": result.get("ABI"),
                                "contract_name": result.get("ContractName"),
                                "compiler_version": result.get("CompilerVersion"),
                                "optimization_used": result.get("OptimizationUsed"),
                                "runs": result.get("Runs"),
                                "constructor_arguments": result.get("ConstructorArguments"),
                                "library": result.get("Library"),
                                "license_type": result.get("LicenseType"),
                                "is_verified": bool(result.get("SourceCode"))
                            }
            
            return {"is_verified": False, "contract_verification_status": "Not Verified"}
        
        except Exception as e:
            logger.error(f"Error getting contract source: {str(e)}")
            return {"is_verified": False}
    
    async def _get_contract_creation(self, address: str, explorer_config: Dict[str, Any]) -> Dict[str, Any]:
        """Get contract creation information"""
        try:
            url = explorer_config["base_url"]
            params = {
                "module": "contract",
                "action": "getcontractcreation",
                "contractaddresses": address,
                "apikey": explorer_config["api_key"]
            }
            
            # Add chainid for multichain API (Base chain)
            params = self._add_chainid_param(params, explorer_config)
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "1" and data.get("result"):
                            result = data["result"][0]
                            return {
                                "contract_creation_tx": result.get("txHash"),
                                "contract_creator": result.get("contractCreator"),
                                "contract_creation_date": result.get("creationDate")
                            }
            
            return {}
        
        except Exception as e:
            logger.error(f"Error getting contract creation: {str(e)}")
            return {}
    
    async def _get_transaction_count(self, address: str, explorer_config: Dict[str, Any]) -> Optional[int]:
        """Get transaction count for address"""
        try:
            url = explorer_config["base_url"]
            params = {
                "module": "proxy",
                "action": "eth_getTransactionCount",
                "address": address,
                "tag": "latest",
                "apikey": explorer_config["api_key"]
            }
            
            # Add chainid for multichain API (Base chain)
            params = self._add_chainid_param(params, explorer_config)
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("result"):
                            return int(data["result"], 16)
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting transaction count: {str(e)}")
            return None
    
    async def _get_balance(self, address: str, explorer_config: Dict[str, Any]) -> Optional[Decimal]:
        """Get balance for address"""
        try:
            url = explorer_config["base_url"]
            params = {
                "module": "account",
                "action": "balance",
                "address": address,
                "tag": "latest",
                "apikey": explorer_config["api_key"]
            }
            
            # Add chainid for multichain API (Base chain)
            params = self._add_chainid_param(params, explorer_config)
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "1" and data.get("result"):
                            # Convert from Wei to ETH (18 decimals)
                            wei_balance = Decimal(data["result"])
                            eth_balance = wei_balance / Decimal("1000000000000000000")
                            return eth_balance
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting balance: {str(e)}")
            return None
    
    async def _get_contract_creations(self, address: str, explorer_config: Dict[str, Any]) -> Optional[int]:
        """Get number of contracts created by address"""
        try:
            url = explorer_config["base_url"]
            params = {
                "module": "account",
                "action": "txlist",
                "address": address,
                "startblock": 0,
                "endblock": 99999999,
                "page": 1,
                "offset": 1000,
                "sort": "asc",
                "apikey": explorer_config["api_key"]
            }
            
            # Add chainid for multichain API (Base chain)
            params = self._add_chainid_param(params, explorer_config)
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "1" and data.get("result"):
                            # Count transactions that created contracts (to field is empty)
                            contract_creations = 0
                            for tx in data["result"]:
                                if not tx.get("to"):  # Contract creation transaction
                                    contract_creations += 1
                            return contract_creations
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting contract creations: {str(e)}")
            return None
    
    async def _get_first_transaction(self, address: str, explorer_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get first transaction for address"""
        try:
            url = explorer_config["base_url"]
            params = {
                "module": "account",
                "action": "txlist",
                "address": address,
                "startblock": 0,
                "endblock": 99999999,
                "page": 1,
                "offset": 1,
                "sort": "asc",
                "apikey": explorer_config["api_key"]
            }
            
            # Add chainid for multichain API (Base chain)
            params = self._add_chainid_param(params, explorer_config)
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "1" and data.get("result") and len(data["result"]) > 0:
                            first_tx = data["result"][0]
                            return {
                                "tx_hash": first_tx.get("hash"),
                                "timestamp": first_tx.get("timeStamp"),
                                "block_number": first_tx.get("blockNumber")
                            }
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting first transaction: {str(e)}")
            return None
    
    async def _get_token_info(self, address: str, explorer_config: Dict[str, Any]) -> Dict[str, Any]:
        """Get token information"""
        try:
            # Try to get token info from contract source first
            source_data = await self._get_contract_source(address, explorer_config)
            
            # If not verified, try to get basic info from token methods
            if not source_data.get("is_verified"):
                # This would require calling contract methods via RPC
                # For now, return basic info
                return {
                    "name": None,
                    "symbol": None,
                    "decimals": None,
                    "total_supply": None
                }
            
            # Extract token info from verified contract
            return {
                "name": source_data.get("contract_name"),
                "symbol": None,  # Would need to parse from source code
                "decimals": None,  # Would need to parse from source code
                "total_supply": None  # Would need to call contract method
            }
        
        except Exception as e:
            logger.error(f"Error getting token info: {str(e)}")
            return {}
    
    async def _get_token_holders_count(self, address: str, explorer_config: Dict[str, Any]) -> Optional[int]:
        """Get token holders count"""
        try:
            # This endpoint is not available in all explorers
            # For now, return None - would need to use other methods
            return None
        
        except Exception as e:
            logger.error(f"Error getting token holders count: {str(e)}")
            return None
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    async def get_comprehensive_analysis(self, address: str, chain: ChainType) -> Dict[str, Any]:
        """
        Get comprehensive analysis from explorer APIs
        """
        try:
            # Get all data concurrently
            contract_task = self.get_contract_info(address, chain)
            token_task = self.get_token_info(address, chain)
            
            contract_data, token_data = await asyncio.gather(
                contract_task, token_task, return_exceptions=True
            )
            
            # Combine results
            result = {}
            
            if isinstance(contract_data, dict):
                result.update(contract_data)
            
            if isinstance(token_data, dict):
                result.update(token_data)
            
            # Try to get deployer info if we have the deployer address
            deployer_address = result.get("contract_creator")
            if deployer_address:
                deployer_data = await self.get_deployer_info(deployer_address, chain)
                if isinstance(deployer_data, dict):
                    result.update(deployer_data)
            
            return result
        
        except Exception as e:
            logger.error(f"Error in comprehensive explorer analysis: {str(e)}")
            return {}
    
    def calculate_contract_age_days(self, creation_timestamp: str) -> Optional[int]:
        """Calculate contract age in days"""
        try:
            from datetime import datetime, timezone
            
            if not creation_timestamp:
                return None
            
            # Parse timestamp (could be Unix timestamp or ISO format)
            if creation_timestamp.isdigit():
                # Unix timestamp
                creation_date = datetime.fromtimestamp(int(creation_timestamp), tz=timezone.utc)
            else:
                # Try to parse as ISO format
                creation_date = datetime.fromisoformat(creation_timestamp.replace('Z', '+00:00'))
            
            # Calculate age
            now = datetime.now(timezone.utc)
            age_delta = now - creation_date
            return age_delta.days
        
        except Exception as e:
            logger.error(f"Error calculating contract age: {str(e)}")
            return None
    
    def calculate_deployer_age_days(self, first_tx_data: Dict[str, Any]) -> Optional[int]:
        """Calculate deployer age in days"""
        try:
            if not first_tx_data or not first_tx_data.get("timestamp"):
                return None
            
            from datetime import datetime, timezone
            
            timestamp = first_tx_data["timestamp"]
            if isinstance(timestamp, str) and timestamp.isdigit():
                first_tx_date = datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
            else:
                return None
            
            # Calculate age
            now = datetime.now(timezone.utc)
            age_delta = now - first_tx_date
            return age_delta.days
        
        except Exception as e:
            logger.error(f"Error calculating deployer age: {str(e)}")
            return None
    
    async def get_liquidity_lock_info(self, token_address: str, chain: ChainType) -> Dict[str, Any]:
        """
        Get liquidity lock information for a token
        """
        try:
            explorer_config = self.explorer_apis.get(chain.value)
            if not explorer_config:
                return {}
            
            # Get LP token holders to check for lock contracts
            lp_holders = await self._get_lp_token_holders(token_address, explorer_config)
            
            # Check if any holders are known lock contracts
            lock_info = await self._analyze_liquidity_locks(lp_holders, chain)
            
            return lock_info
        
        except Exception as e:
            logger.error(f"Error getting liquidity lock info: {str(e)}")
            return {}
    
    async def _get_lp_token_holders(self, token_address: str, explorer_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get LP token holders"""
        try:
            # This is a simplified approach - in reality, we'd need to:
            # 1. Find the LP token address for this token
            # 2. Get holders of the LP token
            # For now, we'll return empty list as this requires more complex logic
            return []
        
        except Exception as e:
            logger.error(f"Error getting LP token holders: {str(e)}")
            return []
    
    async def _analyze_liquidity_locks(self, lp_holders: List[Dict[str, Any]], chain: ChainType) -> Dict[str, Any]:
        """Analyze liquidity locks from LP token holders"""
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
            for holder in lp_holders:
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
                    
                    # Calculate lock percentage (simplified)
                    if holder_balance > 0:
                        # This would need total LP supply to calculate percentage
                        lock_info["liquidity_lock_percentage"] = 100.0  # Simplified
            
            return lock_info
        
        except Exception as e:
            logger.error(f"Error analyzing liquidity locks: {str(e)}")
            return {"liquidity_locked": False}
    
    async def _get_lock_duration(self, lock_contract_address: str, chain: ChainType) -> Optional[Dict[str, Any]]:
        """Get lock duration from lock contract"""
        try:
            # This would require calling contract methods to get lock duration
            # For now, return None as this requires RPC calls
            return None
        
        except Exception as e:
            logger.error(f"Error getting lock duration: {str(e)}")
            return None
    
    async def check_lp_token_locks(self, lp_token_address: str, chain: ChainType) -> Dict[str, Any]:
        """
        Check if LP tokens are locked by analyzing holders
        """
        try:
            explorer_config = self.explorer_apis.get(chain.value)
            if not explorer_config:
                return {}
            
            # Get LP token holders
            holders = await self._get_token_holders(lp_token_address, explorer_config)
            
            # Analyze for lock contracts
            lock_analysis = await self._analyze_liquidity_locks(holders, chain)
            
            return lock_analysis
        
        except Exception as e:
            logger.error(f"Error checking LP token locks: {str(e)}")
            return {}
    
    async def _get_token_holders(self, token_address: str, explorer_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get token holders (simplified version)"""
        try:
            # This would require calling the token contract to get holders
            # For now, return empty list as this requires RPC calls
            return []
        
        except Exception as e:
            logger.error(f"Error getting token holders: {str(e)}")
            return []
