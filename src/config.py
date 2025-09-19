"""
Configuration settings for BearTech Token Analysis Bot
"""
import os
from typing import Dict, Any

# Load environment variables
def get_env_var(key: str, default: str = None) -> str:
    """Get environment variable with fallback to default value"""
    return os.getenv(key, default)

# API Keys - Production environment variables
TELEGRAM_BOT_TOKEN = get_env_var("TELEGRAM_BOT_TOKEN", "8313948824:AAFXwqqzT1c6bQG49s2EtlKKxnBKoectN7I")
GOPLUS_API_KEY = get_env_var("GOPLUS_API_KEY", "Y0ZVbTgCm8G40GbczyAD")
ETHERSCAN_API_KEY = get_env_var("ETHERSCAN_API_KEY", "Q94DIFTQ31YXWHBINHTDSCRMBUEQXY4VC5")
BASESCAN_API_KEY = get_env_var("BASESCAN_API_KEY")
REF_TAG = get_env_var("REF_TAG", "beartech")

# API Endpoints - Only free/working APIs
DEXSCREENER_BASE_URL = "https://api.dexscreener.com/latest"

# Explorer API Endpoints - Using Etherscan Multichain API
EXPLORER_APIS = {
    "ethereum": {
        "name": "Etherscan",
        "base_url": "https://api.etherscan.io/api",
        "api_key": ETHERSCAN_API_KEY,
        "chain_id": 1
    },
    "base": {
        "name": "Etherscan Multichain",
        "base_url": "https://api.etherscan.io/v2/api",
        "api_key": ETHERSCAN_API_KEY,
        "chain_id": 8453
    }
}

# RPC Endpoints with fallbacks - Only Ethereum and Base
RPC_ENDPOINTS = {
    "ethereum": [
        "https://eth.llamarpc.com",
        "https://ethereum.publicnode.com",
        "https://rpc.ankr.com/eth"
    ],
    "base": [
        "https://mainnet.base.org",
        "https://base.publicnode.com",
        "https://base.blockpi.network/v1/rpc/public"
    ]
}

# Cache Settings
CACHE_TTL = 300  # 5 minutes
MAX_CACHE_SIZE = 1000

# Bot Settings
MAX_MESSAGE_LENGTH = 4096
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3

# Risk Assessment Thresholds
RISK_THRESHOLDS = {
    "honeypot": {
        "liquidity_threshold": 0,
        "tax_threshold": 20,
        "holder_threshold": 10
    },
    "high_risk": {
        "tax_threshold": 15,
        "holder_threshold": 50,
        "liquidity_threshold": 1000
    },
    "medium_risk": {
        "tax_threshold": 10,
        "holder_threshold": 100,
        "liquidity_threshold": 10000
    }
}

# Supported Chains - Only Ethereum and Base
SUPPORTED_CHAINS = {
    "ethereum": {
        "name": "Ethereum",
        "symbol": "ETH",
        "explorer": "etherscan.io",
        "chain_id": 1
    },
    "base": {
        "name": "Base",
        "symbol": "ETH",
        "explorer": "basescan.org",
        "chain_id": 8453
    }
}

# Error Messages
ERROR_MESSAGES = {
    "invalid_address": "❌ Invalid contract address format",
    "api_error": "⚠️ API service temporarily unavailable",
    "not_found": "🔍 Token not found on this chain",
    "rate_limit": "⏳ Rate limit exceeded, please try again later",
    "network_error": "🌐 Network connection error"
}

# Success Messages
SUCCESS_MESSAGES = {
    "analysis_complete": "✅ Token analysis completed",
    "honeypot_detected": "🚨 HONEYPOT DETECTED!",
    "safe_token": "✅ Token appears safe",
    "high_risk": "⚠️ High risk token detected"
}