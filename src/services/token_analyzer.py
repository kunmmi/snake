"""
Main token analysis service that combines all APIs
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime

from ..models.token import (
    TokenAnalysisResult, TokenBasicInfo, TokenMarketData, TokenSecurityData,
    TokenLiquidityData, TokenHolderData, TokenDeployerData, TokenContractData,
    TokenRiskAssessment, RiskLevel, ChainType
)
from ..models.response import ResponseFormatter
from ..utils.chain_detector import ChainDetector
from ..utils.cache import cache_manager
from .dexscreener import DexScreenerService
from .explorer import ExplorerService
from .rpc import RPCService
from .goplus import GoPlusService

logger = logging.getLogger(__name__)


class TokenAnalyzer:
    """Main token analysis service that orchestrates all API calls"""
    
    def __init__(self):
        self.dexscreener_service = DexScreenerService()
        self.explorer_service = ExplorerService()
        self.rpc_service = RPCService()
        self.goplus_service = GoPlusService()
        self.chain_detector = ChainDetector()
        self.formatter = ResponseFormatter()
    
    async def analyze_token(self, address: str, chain: Optional[ChainType] = None) -> TokenAnalysisResult:
        """
        Perform comprehensive token analysis
        """
        try:
            # Validate address
            if not self._validate_address(address):
                raise ValueError("Invalid contract address format")
            
            # Detect chain if not provided
            if not chain:
                chain = await self._detect_chain(address)
            
            if not chain:
                raise ValueError("Could not detect chain for address")
            
            logger.info(f"Starting analysis for {address} on {chain.value}")
            
            # Check cache first
            cached_result = await cache_manager.get_token_analysis(address, chain.value)
            if cached_result:
                logger.info(f"Returning cached analysis for {address}")
                # Convert cached dict back to TokenAnalysisResult
                try:
                    # Extract the actual data from cache entry
                    cached_data = cached_result.get("data", cached_result)
                    return TokenAnalysisResult(**cached_data)
                except Exception as e:
                    logger.warning(f"Failed to deserialize cached result: {e}, running fresh analysis")
                    # Clear the corrupted cache entry
                    await cache_manager.invalidate_token(address, chain.value)
            
            # Initialize result structure
            result = TokenAnalysisResult(
                basic_info=TokenBasicInfo(address=address, chain=chain),
                market_data=TokenMarketData(),
                security_data=TokenSecurityData(),
                liquidity_data=TokenLiquidityData(),
                holder_data=TokenHolderData(),
                deployer_data=TokenDeployerData(),
                contract_data=TokenContractData(),
                risk_assessment=TokenRiskAssessment(),
                analysis_timestamp=self._get_current_timestamp()
            )
            
            # Gather data from all sources with timeouts
            tasks = []
            
            # GoPlus (security analysis and tax info) - Reasonable timeout for slow connections
            tasks.append(self._safe_api_call(
                lambda: self.goplus_service.get_token_security(address, chain.value),
                "GoPlus",
                timeout=8  # 8 seconds with retries
            ))
            
            # DexScreener (market data) - Reasonable timeout
            tasks.append(self._safe_api_call(
                lambda: self.dexscreener_service.get_token_data(address, chain),
                "DexScreener",
                timeout=10  # 10 seconds with retries
            ))
            
            # Explorer (contract info) - for Ethereum and Base - Reasonable timeout
            if chain in [ChainType.ETHEREUM, ChainType.BASE]:
                tasks.append(self._safe_api_call(
                    lambda: self.explorer_service.get_contract_info(address, chain),
                    "Explorer",
                    timeout=12  # 12 seconds with retries
                ))
            
            # RPC (basic blockchain data) - Reasonable timeout
            tasks.append(self._safe_api_call(
                lambda: self.rpc_service.get_basic_token_info(address, chain),
                "RPC",
                timeout=10  # 10 seconds with retries
            ))
            
            # Note: Liquidity lock detection is now handled by DexScreener service
            
            # Wait for all tasks with timeout
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=30  # Increased to 30 seconds for very slow connections
                )
            except asyncio.TimeoutError:
                logger.warning(f"Analysis timeout for {address}")
                results = []
            
            # Combine results
            combined_data = self._combine_api_results(results)
            result.data_sources = combined_data.get("sources", [])
            result.errors = combined_data.get("errors", [])
            
            # Process the combined data
            self._process_basic_info(result, combined_data.get("data", {}))
            self._process_market_data(result, combined_data.get("data", {}))
            self._process_security_data(result, combined_data.get("data", {}))
            self._process_liquidity_data(result, combined_data.get("data", {}))
            self._process_holder_data(result, combined_data.get("data", {}))
            self._process_deployer_data(result, combined_data.get("data", {}))
            self._process_contract_data(result, combined_data.get("data", {}))
            
            # Get creator's token balance if we have creator address
            await self._fetch_creator_token_balance(result, address, chain)
            
            # Perform risk assessment
            self._assess_risk(result)
            
            # Cache the result
            await cache_manager.set_token_analysis(address, chain.value, result.__dict__)
            
            logger.info(f"Analysis completed for {address}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing token {address}: {str(e)}")
            # Return minimal result with error
            return TokenAnalysisResult(
                basic_info=TokenBasicInfo(address=address, chain=chain),
                market_data=TokenMarketData(),
                security_data=TokenSecurityData(),
                liquidity_data=TokenLiquidityData(),
                holder_data=TokenHolderData(),
                deployer_data=TokenDeployerData(),
                contract_data=TokenContractData(),
                risk_assessment=TokenRiskAssessment(
                    overall_risk=RiskLevel.HIGH,
                    warnings=[f"Analysis failed: {str(e)}"]
                ),
                analysis_timestamp=self._get_current_timestamp(),
                errors=[str(e)]
            )
    
    async def _detect_chain(self, address: str) -> Optional[ChainType]:
        """Detect chain for address with smart prioritization"""
        # Try each supported chain and collect data from all sources
        # Priority: Ethereum first (main chain), then Base
        chain_priority = [ChainType.ETHEREUM, ChainType.BASE]
        chain_scores = {}

        for chain_type in chain_priority:
            try:
                score = 0
                chain_data = {}

                # Method 1: Try GoPlus (security data)
                try:
                    security_data = await self.goplus_service.get_token_security(address, chain_type.value)
                    if (security_data and 
                        security_data.get("name") and 
                        security_data.get("name") != "Unknown" and
                        "error" not in security_data):
                        score += 10
                        chain_data["goplus"] = security_data
                except:
                    pass

                # Method 2: Try DexScreener (market data)
                try:
                    market_data = await self.dexscreener_service.get_token_data(address, chain_type)
                    if market_data and market_data.get("name") and market_data.get("name") != "Unknown":
                        score += 8
                        chain_data["dexscreener"] = market_data
                        
                        # Bonus points for higher liquidity/volume (indicates main chain)
                        liquidity = market_data.get("liquidity_usd", 0)
                        if liquidity and float(liquidity) > 100000:  # > $100k liquidity
                            score += 5
                        elif liquidity and float(liquidity) > 10000:  # > $10k liquidity
                            score += 2
                except:
                    pass

                # Method 3: Try Explorer API (contract verification)
                if chain_type in [ChainType.ETHEREUM, ChainType.BASE]:
                    try:
                        explorer_data = await self.explorer_service.get_contract_info(address, chain_type)
                        if (explorer_data and
                            explorer_data.get("is_verified") is not None and
                            (explorer_data.get("name") or explorer_data.get("transaction_count", 0) > 0)):
                            score += 6
                            chain_data["explorer"] = explorer_data
                            
                            # Bonus points for verified contracts
                            if explorer_data.get("is_verified"):
                                score += 3
                            
                            # Bonus points for higher transaction count (more activity)
                            tx_count = explorer_data.get("transaction_count", 0)
                            if tx_count > 1000:
                                score += 3
                            elif tx_count > 100:
                                score += 1
                    except:
                        pass

                # Method 4: Try RPC (basic contract data)
                try:
                    rpc_data = await self.rpc_service.get_basic_token_info(address, chain_type)
                    if rpc_data and rpc_data.get("name") and rpc_data.get("name") != "Unknown":
                        score += 4
                        chain_data["rpc"] = rpc_data
                except:
                    pass

                # Store the score and data for this chain
                if score > 0:
                    chain_scores[chain_type] = {
                        "score": score,
                        "data": chain_data
                    }

            except Exception as e:
                logger.debug(f"Chain detection failed for {chain_type.value}: {str(e)}")
                continue

        # Determine the best chain based on scores
        if chain_scores:
            # Sort by score (highest first)
            best_chain = max(chain_scores.keys(), key=lambda k: chain_scores[k]["score"])
            best_score = chain_scores[best_chain]["score"]
            
            logger.info(f"Chain detected: {best_chain.value} (score: {best_score})")
            return best_chain

        # If all methods fail, default to Ethereum (main chain)
        logger.warning(f"Could not detect chain for {address}, defaulting to Ethereum")
        return ChainType.ETHEREUM
    
    def _combine_api_results(self, results: List[Any]) -> Dict[str, Any]:
        """Combine results from all API calls"""
        combined = {
            "sources": [],
            "errors": [],
            "data": {}
        }

        for result in results:
            if isinstance(result, dict):
                if "error" in result:
                    combined["errors"].append(f"{result.get('source', 'Unknown')}: {result['error']}")
                else:
                    source = result.get("source", "Unknown")
                    combined["sources"].append(source)
                    logger.debug(f"Combining data from {source}: {result}")
                    # Only update with non-null values to avoid overwriting good data
                    # Prioritize specific sources for specific fields
                    for key, value in result.items():
                        if value is not None:
                            # For security-related fields, prioritize GoPlus over other sources
                            if source == "GoPlus" and key in ["is_honeypot", "buy_tax", "sell_tax", "is_open_source", "is_mintable", "is_pausable", "risk_level"]:
                                combined["data"][key] = value
                            # For verification status, prioritize Explorer over GoPlus
                            elif source == "Explorer" and key in ["is_verified", "contract_verification_status"]:
                                combined["data"][key] = value
                            elif key not in combined["data"] or combined["data"][key] is None:
                                combined["data"][key] = value
            elif isinstance(result, Exception):
                combined["errors"].append(f"API call failed: {str(result)}")

        # Ensure we have at least some basic data
        if not combined["data"]:
            combined["data"] = {
                "source": "Fallback",
                "analysis_timestamp": self._get_current_timestamp()
            }

        logger.debug(f"Final combined data: {combined}")
        return combined
    
    async def _safe_api_call(self, coro_func, source_name: str, timeout: int = 5, max_retries: int = 2) -> Dict[str, Any]:
        """Safely call an API with error handling, individual timeout, and retry logic"""
        for attempt in range(max_retries + 1):
            try:
                # Create a new coroutine for each attempt
                coro = coro_func()
                result = await asyncio.wait_for(coro, timeout=timeout)
                if isinstance(result, dict):
                    result["source"] = source_name
                return result
            except asyncio.TimeoutError:
                if attempt < max_retries:
                    logger.warning(f"{source_name} API timeout after {timeout}s, retrying... (attempt {attempt + 1}/{max_retries + 1})")
                    await asyncio.sleep(1)  # Wait 1 second before retry
                    continue
                else:
                    logger.warning(f"{source_name} API timeout after {timeout}s (final attempt)")
                    return {"error": f"Timeout after {timeout}s", "source": source_name}
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"{source_name} API error: {str(e)}, retrying... (attempt {attempt + 1}/{max_retries + 1})")
                    await asyncio.sleep(1)  # Wait 1 second before retry
                    continue
                else:
                    logger.error(f"{source_name} API error: {str(e)} (final attempt)")
                    return {"error": str(e), "source": source_name}
        
        return {"error": "Max retries exceeded", "source": source_name}
    
    async def _fetch_creator_token_balance(self, result: TokenAnalysisResult, token_address: str, chain: ChainType):
        """Fetch creator's token balance"""
        try:
            # Get creator address from deployer data
            creator_address = None
            if result.deployer_data.contract_creator:
                creator_address = result.deployer_data.contract_creator
            elif result.deployer_data.deployer_address:
                creator_address = result.deployer_data.deployer_address
            
            if not creator_address:
                logger.debug("No creator address found, skipping token balance fetch")
                return
            
            # Get creator's token balance via RPC
            creator_balance = await self.rpc_service.get_token_balance(token_address, creator_address, chain)
            
            if creator_balance is not None:
                result.deployer_data.creator_token_balance = creator_balance
                
                # Calculate percentage if we have total supply
                if result.basic_info.total_supply and result.basic_info.total_supply > 0:
                    percentage = (float(creator_balance) / float(result.basic_info.total_supply)) * 100
                    result.deployer_data.creator_token_percentage = round(percentage, 2)
                
                logger.debug(f"Creator {creator_address} holds {creator_balance} tokens ({result.deployer_data.creator_token_percentage}%)")
            else:
                logger.debug(f"Could not fetch token balance for creator {creator_address}")
                
        except Exception as e:
            logger.error(f"Error fetching creator token balance: {str(e)}")
    
    def _validate_address(self, address: str) -> bool:
        """Validate Ethereum address format"""
        if not address or not isinstance(address, str):
            return False
        
        # Remove 0x prefix if present
        if address.startswith("0x"):
            address = address[2:]
        
        # Check if it's a valid hex string and 40 characters long
        try:
            int(address, 16)
            return len(address) == 40
        except ValueError:
            return False
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp as string"""
        return datetime.now().isoformat()
    
    def _process_basic_info(self, result: TokenAnalysisResult, data: Dict[str, Any]):
        """Process basic token information"""
        logger.debug(f"Processing basic info with data: {data}")
        if "name" in data and data["name"]:
            result.basic_info.name = data["name"]
            logger.debug(f"Set name to: {data['name']}")
        if "symbol" in data and data["symbol"]:
            result.basic_info.symbol = data["symbol"]
            logger.debug(f"Set symbol to: {data['symbol']}")
        if "decimals" in data and data["decimals"] is not None:
            result.basic_info.decimals = data["decimals"]
        if "total_supply" in data and data["total_supply"]:
            result.basic_info.total_supply = Decimal(str(data["total_supply"]))
        
        # Process burn information
        if "burn_info" in data and data["burn_info"]:
            burn_info = data["burn_info"]
            if burn_info.get("burned_amount"):
                result.basic_info.burned_amount = Decimal(str(burn_info["burned_amount"]))
            if burn_info.get("burn_percentage"):
                result.basic_info.burn_percentage = burn_info["burn_percentage"]
        
        # Process token age information
        if "token_age_days" in data and data["token_age_days"] is not None:
            result.basic_info.token_age_days = data["token_age_days"]
        if "pair_created_at" in data and data["pair_created_at"]:
            result.basic_info.pair_created_at = data["pair_created_at"]
    
    def _process_market_data(self, result: TokenAnalysisResult, data: Dict[str, Any]):
        """Process market data"""
        if "price_usd" in data and data["price_usd"]:
            result.market_data.price_usd = Decimal(str(data["price_usd"]))
        if "price_change_24h" in data and data["price_change_24h"] is not None:
            result.market_data.price_change_24h = Decimal(str(data["price_change_24h"]))
        if "market_cap" in data and data["market_cap"]:
            result.market_data.market_cap = Decimal(str(data["market_cap"]))
        if "fdv" in data and data["fdv"]:
            result.market_data.fdv = Decimal(str(data["fdv"]))
        if "volume_24h" in data and data["volume_24h"]:
            result.market_data.volume_24h = Decimal(str(data["volume_24h"]))
        if "liquidity_usd" in data and data["liquidity_usd"]:
            result.market_data.liquidity_usd = Decimal(str(data["liquidity_usd"]))
        
        # Enhanced market cap calculation if not provided
        if not result.market_data.market_cap and result.market_data.price_usd and result.basic_info.total_supply:
            try:
                # Calculate market cap = price * circulating supply
                # For now, use total supply as circulating supply (this could be enhanced)
                result.market_data.market_cap = result.market_data.price_usd * result.basic_info.total_supply
                logger.debug(f"Calculated market cap: {result.market_data.market_cap}")
            except Exception as e:
                logger.error(f"Error calculating market cap: {str(e)}")
    
    def _process_security_data(self, result: TokenAnalysisResult, data: Dict[str, Any]):
        """Process security data"""
        if "is_verified" in data:
            result.security_data.is_verified = data["is_verified"]
        if "is_honeypot" in data:
            result.security_data.is_honeypot = data["is_honeypot"]
        if "buy_tax" in data and data["buy_tax"] is not None:
            result.security_data.buy_tax = Decimal(str(data["buy_tax"]))
        if "sell_tax" in data and data["sell_tax"] is not None:
            result.security_data.sell_tax = Decimal(str(data["sell_tax"]))
        if "can_mint" in data:
            result.security_data.can_mint = data["can_mint"]
        if "can_pause" in data:
            result.security_data.can_pause = data["can_pause"]
        if "is_open_source" in data:
            result.security_data.is_open_source = data["is_open_source"]
    
    def _process_liquidity_data(self, result: TokenAnalysisResult, data: Dict[str, Any]):
        """Process liquidity data"""
        if "liquidity_usd" in data and data["liquidity_usd"]:
            result.liquidity_data.liquidity_usd = Decimal(str(data["liquidity_usd"]))
        if "liquidity_locked" in data:
            result.liquidity_data.liquidity_locked = data["liquidity_locked"]
        if "liquidity_lock_percentage" in data and data["liquidity_lock_percentage"]:
            result.liquidity_data.liquidity_lock_percentage = Decimal(str(data["liquidity_lock_percentage"]))
        if "liquidity_lock_platform" in data and data["liquidity_lock_platform"]:
            result.liquidity_data.liquidity_lock_platform = data["liquidity_lock_platform"]
        if "liquidity_lock_unlock_time" in data and data["liquidity_lock_unlock_time"]:
            result.liquidity_data.liquidity_lock_unlock_time = data["liquidity_lock_unlock_time"]
        if "is_burned" in data:
            result.liquidity_data.is_burned = data["is_burned"]
    
    def _process_holder_data(self, result: TokenAnalysisResult, data: Dict[str, Any]):
        """Process holder data"""
        if "holder_count" in data and data["holder_count"]:
            # Convert to int if it's a string
            try:
                result.holder_data.holder_count = int(data["holder_count"])
            except (ValueError, TypeError):
                result.holder_data.holder_count = data["holder_count"]
        if "top_holders_ratio" in data and data["top_holders_ratio"]:
            result.holder_data.top_holders_ratio = data["top_holders_ratio"]
        if "contract_holding_percentage" in data and data["contract_holding_percentage"] is not None:
            result.holder_data.contract_holding_percentage = data["contract_holding_percentage"]
    
    def _process_deployer_data(self, result: TokenAnalysisResult, data: Dict[str, Any]):
        """Process deployer data"""
        if "deployer_address" in data:
            result.deployer_data.deployer_address = data["deployer_address"]
        if "contract_creator" in data and data["contract_creator"]:
            result.deployer_data.contract_creator = data["contract_creator"]
        if "deployer_balance" in data and data["deployer_balance"]:
            result.deployer_data.deployer_balance = Decimal(str(data["deployer_balance"]))
        if "deployer_age_days" in data and data["deployer_age_days"]:
            result.deployer_data.deployer_age_days = data["deployer_age_days"]
        if "deployer_contracts_created" in data and data["deployer_contracts_created"]:
            result.deployer_data.deployer_contracts_created = data["deployer_contracts_created"]
        if "is_verified_deployer" in data:
            result.deployer_data.is_verified_deployer = data["is_verified_deployer"]
        if "creator_token_balance" in data and data["creator_token_balance"]:
            result.deployer_data.creator_token_balance = Decimal(str(data["creator_token_balance"]))
        if "creator_token_percentage" in data and data["creator_token_percentage"] is not None:
            result.deployer_data.creator_token_percentage = data["creator_token_percentage"]
    
    def _process_contract_data(self, result: TokenAnalysisResult, data: Dict[str, Any]):
        """Process contract data"""
        if "contract_creation_date" in data:
            result.contract_data.contract_creation_date = data["contract_creation_date"]
        if "contract_age_days" in data and data["contract_age_days"]:
            result.contract_data.contract_age_days = data["contract_age_days"]
        if "gas_used_creation" in data and data["gas_used_creation"]:
            result.contract_data.gas_used_creation = data["gas_used_creation"]
        if "contract_verification_status" in data:
            result.contract_data.contract_verification_status = data["contract_verification_status"]
        if "contract_source_code" in data:
            result.contract_data.contract_source_code = data["contract_source_code"]
        if "contract_abi" in data:
            result.contract_data.contract_abi = data["contract_abi"]
    
    def _assess_risk(self, result: TokenAnalysisResult):
        """Perform risk assessment"""
        risk_factors = []
        warnings = []
        recommendations = []
        
        # Check for honeypot indicators
        if result.security_data.is_honeypot:
            result.risk_assessment.overall_risk = RiskLevel.HONEYPOT
            warnings.append("🚨 HONEYPOT DETECTED - DO NOT BUY!")
            recommendations.append("DO NOT BUY THIS TOKEN")
            return
        
        # Check liquidity
        if (result.market_data.liquidity_usd and 
            result.market_data.liquidity_usd <= 0):
            risk_factors.append("Zero or negative liquidity")
            warnings.append("⚠️ Zero liquidity detected")
        
        # Check taxes
        if result.security_data.buy_tax and result.security_data.buy_tax > 10:
            risk_factors.append(f"High buy tax: {result.security_data.buy_tax}%")
            warnings.append(f"⚠️ High buy tax: {result.security_data.buy_tax}%")
        
        if result.security_data.sell_tax and result.security_data.sell_tax > 10:
            risk_factors.append(f"High sell tax: {result.security_data.sell_tax}%")
            warnings.append(f"⚠️ High sell tax: {result.security_data.sell_tax}%")
        
        # Check holder count
        if result.holder_data.holder_count:
            try:
                holder_count = int(result.holder_data.holder_count)
                if holder_count < 10:
                    risk_factors.append(f"Low holder count: {holder_count}")
                    warnings.append(f"⚠️ Very low holder count: {holder_count}")
            except (ValueError, TypeError):
                pass  # Skip if holder_count is not a valid number
        
        # Check if contract is verified
        if not result.security_data.is_verified:
            risk_factors.append("Unverified contract")
            warnings.append("⚠️ Contract not verified")
        
        # Determine overall risk level
        if len(risk_factors) >= 3:
            result.risk_assessment.overall_risk = RiskLevel.HIGH
            recommendations.append("⚠️ High risk token - proceed with extreme caution")
        elif len(risk_factors) >= 2:
            result.risk_assessment.overall_risk = RiskLevel.MEDIUM
            recommendations.append("⚠️ Medium risk token - proceed with caution")
        elif len(risk_factors) >= 1:
            result.risk_assessment.overall_risk = RiskLevel.LOW
            recommendations.append("🟢 Token has low risk - proceed with caution")
        else:
            result.risk_assessment.overall_risk = RiskLevel.SAFE
            recommendations.append("✅ Token appears safe")
        
        result.risk_assessment.risk_factors = risk_factors
        result.risk_assessment.warnings = warnings
        result.risk_assessment.recommendations = recommendations
        result.risk_assessment.is_safe_to_buy = result.risk_assessment.overall_risk in [RiskLevel.SAFE, RiskLevel.LOW]
        result.risk_assessment.is_safe_to_sell = result.risk_assessment.overall_risk != RiskLevel.HONEYPOT