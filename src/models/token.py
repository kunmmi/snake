"""
Token data models for BearTech Token Analysis Bot
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from decimal import Decimal
from enum import Enum


class RiskLevel(Enum):
    """Risk level enumeration"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    HONEYPOT = "honeypot"


class ChainType(Enum):
    """Supported blockchain types"""
    ETHEREUM = "ethereum"
    BASE = "base"


@dataclass
class TokenBasicInfo:
    """Basic token information"""
    address: str
    name: Optional[str] = None
    symbol: Optional[str] = None
    decimals: Optional[int] = None
    total_supply: Optional[Decimal] = None
    chain: Optional[ChainType] = None
    burned_amount: Optional[Decimal] = None
    burn_percentage: Optional[float] = None
    token_age_days: Optional[int] = None  # Token age in days from pair creation
    pair_created_at: Optional[str] = None  # Pair creation timestamp


@dataclass
class TokenMarketData:
    """Token market data"""
    price_usd: Optional[Decimal] = None
    price_change_24h: Optional[Decimal] = None
    market_cap: Optional[Decimal] = None
    volume_24h: Optional[Decimal] = None
    liquidity_usd: Optional[Decimal] = None
    fdv: Optional[Decimal] = None  # Fully Diluted Valuation
    market_cap_rank: Optional[int] = None


@dataclass
class TokenSecurityData:
    """Token security analysis data"""
    is_verified: bool = False
    is_honeypot: bool = False
    buy_tax: Optional[Decimal] = None
    sell_tax: Optional[Decimal] = None
    max_tax: Optional[Decimal] = None
    can_take_back_ownership: bool = False
    can_pause: bool = False
    can_mint: bool = False
    can_blacklist: bool = False
    is_proxy: bool = False
    is_open_source: bool = False
    is_anti_whale: bool = False
    trading_cooldown: Optional[int] = None
    max_transaction_amount: Optional[Decimal] = None


@dataclass
class TokenLiquidityData:
    """Token liquidity information"""
    liquidity_usd: Optional[Decimal] = None
    liquidity_eth: Optional[Decimal] = None
    liquidity_locked: bool = False
    liquidity_lock_percentage: Optional[Decimal] = None
    liquidity_lock_platform: Optional[str] = None
    liquidity_lock_unlock_time: Optional[str] = None  # When liquidity unlocks
    liquidity_pools: List[Dict[str, Any]] = field(default_factory=list)
    burn_percentage: Optional[Decimal] = None
    is_burned: bool = False


@dataclass
class TokenHolderData:
    """Token holder information"""
    holder_count: Optional[int] = None
    top_holders_ratio: Optional[float] = None
    top_10_holders_percentage: Optional[Decimal] = None
    top_50_holders_percentage: Optional[Decimal] = None
    contract_holding_percentage: Optional[float] = None  # "Clog" - contract address holding percentage
    holder_distribution: Dict[str, Any] = field(default_factory=dict)
    whale_holders: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class TokenDeployerData:
    """Token deployer information"""
    deployer_address: Optional[str] = None
    contract_creator: Optional[str] = None
    deployer_balance: Optional[Decimal] = None
    deployer_age_days: Optional[int] = None
    deployer_tx_count: Optional[int] = None
    deployer_contracts_created: Optional[int] = None
    is_verified_deployer: bool = False
    deployer_risk_score: Optional[int] = None
    creator_token_balance: Optional[Decimal] = None  # Creator's balance of the token
    creator_token_percentage: Optional[float] = None  # Creator's percentage of total supply


@dataclass
class TokenContractData:
    """Token contract information"""
    contract_creation_date: Optional[str] = None
    contract_age_days: Optional[int] = None
    contract_verification_status: Optional[str] = None
    contract_source_code: Optional[str] = None
    contract_abi: Optional[List[Dict[str, Any]]] = None
    contract_bytecode: Optional[str] = None
    gas_used_creation: Optional[int] = None
    gas_price_creation: Optional[Decimal] = None


@dataclass
class TokenRiskAssessment:
    """Token risk assessment"""
    overall_risk: RiskLevel = RiskLevel.MEDIUM
    risk_score: int = 50  # 0-100 scale
    risk_factors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    is_safe_to_buy: bool = False
    is_safe_to_sell: bool = False


@dataclass
class TokenAnalysisResult:
    """Complete token analysis result"""
    basic_info: TokenBasicInfo
    market_data: TokenMarketData
    security_data: TokenSecurityData
    liquidity_data: TokenLiquidityData
    holder_data: TokenHolderData
    deployer_data: TokenDeployerData
    contract_data: TokenContractData
    risk_assessment: TokenRiskAssessment
    analysis_timestamp: str
    data_sources: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def has_errors(self) -> bool:
        """Check if analysis has errors"""
        return len(self.errors) > 0
    
    def is_honeypot(self) -> bool:
        """Check if token is a honeypot"""
        return self.security_data.is_honeypot or self.risk_assessment.overall_risk == RiskLevel.HONEYPOT
    
    def get_risk_level_emoji(self) -> str:
        """Get emoji for risk level"""
        emoji_map = {
            RiskLevel.SAFE: "✅",
            RiskLevel.LOW: "🟢",
            RiskLevel.MEDIUM: "🟡",
            RiskLevel.HIGH: "🔴",
            RiskLevel.HONEYPOT: "🚨"
        }
        return emoji_map.get(self.risk_assessment.overall_risk, "❓")
    
    def get_chain_emoji(self) -> str:
        """Get emoji for chain"""
        emoji_map = {
            ChainType.ETHEREUM: "🔷",
            ChainType.BASE: "🔵"
        }
        return emoji_map.get(self.basic_info.chain, "❓")
