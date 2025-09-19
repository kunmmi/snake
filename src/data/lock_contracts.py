"""
Known liquidity locking contract addresses and platforms
"""

# Known liquidity locking platforms and their contract addresses
LIQUIDITY_LOCK_CONTRACTS = {
    # Team Finance (Ethereum)
    "ethereum": {
        "team_finance": {
            "name": "Team Finance",
            "contracts": [
                "0x5a6A4D5445683286c73A6bA4dE2C60d1Cce2f8e5",  # Team Finance V2
                "0x87Dce67002e66C17BC449EfB2992b9A4B6667AB",   # Team Finance V1
            ],
            "website": "https://team.finance",
            "description": "Team Finance liquidity locking platform"
        },
        "unicrypt": {
            "name": "Unicrypt",
            "contracts": [
                "0x663A5C229c09b049E36dCc11a9B0d4a8Eb9db214",  # Unicrypt V2
                "0x17e00383a843A9922bCA3B280C0ADE9f8BA48449",  # Unicrypt V1
            ],
            "website": "https://unicrypt.network",
            "description": "Unicrypt decentralized liquidity locking"
        },
        "dxsale": {
            "name": "DxSale",
            "contracts": [
                "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",  # DxSale Router (also Uniswap)
                "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",  # DxSale Factory
            ],
            "website": "https://dxsale.app",
            "description": "DxSale token launch platform with locking"
        },
        "pinksale": {
            "name": "PinkSale",
            "contracts": [
                "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",  # PinkSale Router
                "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",  # PinkSale Factory
            ],
            "website": "https://pinksale.finance",
            "description": "PinkSale token launch platform"
        },
        "liquidity_locker": {
            "name": "Liquidity Locker",
            "contracts": [
                "0x407993575c91ce7643a4d4cCACc9A98c36eE1BBE",  # Liquidity Locker
            ],
            "website": "https://liquiditylocker.net",
            "description": "Liquidity Locker platform"
        },
        "coin_tool": {
            "name": "CoinTool",
            "contracts": [
                "0x1eE3151c7d4c76e2c265CA2882b73B4b3b31470b",  # CoinTool Locker
            ],
            "website": "https://cointool.app",
            "description": "CoinTool liquidity locking service"
        }
    },
    
    # Base Chain
    "base": {
        "team_finance": {
            "name": "Team Finance",
            "contracts": [
                "0x5a6A4D5445683286c73A6bA4dE2C60d1Cce2f8e5",  # Team Finance Base
            ],
            "website": "https://team.finance",
            "description": "Team Finance liquidity locking platform"
        },
        "unicrypt": {
            "name": "Unicrypt",
            "contracts": [
                "0x663A5C229c09b049E36dCc11a9B0d4a8Eb9db214",  # Unicrypt Base
            ],
            "website": "https://unicrypt.network",
            "description": "Unicrypt decentralized liquidity locking"
        },
        "base_locker": {
            "name": "Base Locker",
            "contracts": [
                "0x407993575c91ce7643a4d4cCACc9A98c36eE1BBE",  # Base Locker
            ],
            "website": "https://baselocker.com",
            "description": "Base chain liquidity locking service"
        }
    }
}

# Common LP token patterns to identify liquidity pools
LP_TOKEN_PATTERNS = {
    "uniswap_v2": {
        "name": "Uniswap V2",
        "factory": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
        "router": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
        "description": "Uniswap V2 liquidity pools"
    },
    "uniswap_v3": {
        "name": "Uniswap V3",
        "factory": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
        "router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "description": "Uniswap V3 liquidity pools"
    },
    "sushiswap": {
        "name": "SushiSwap",
        "factory": "0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac",
        "router": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
        "description": "SushiSwap liquidity pools"
    },
    "pancakeswap": {
        "name": "PancakeSwap",
        "factory": "0xcA143Ce0Fe65960e6Aa4D42C8d3cE161c2B6604f",
        "router": "0x10ED43C718714eb63d5aA57B78B54704E256024E",
        "description": "PancakeSwap liquidity pools"
    }
}

# Base chain specific LP patterns
BASE_LP_PATTERNS = {
    "uniswap_v3_base": {
        "name": "Uniswap V3 Base",
        "factory": "0x33128a8fC17869897dcE68Ed026d694621f6fdfd",
        "router": "0x4752ba5dbc23f44d87826276bf6fd6b1c372ad24",
        "description": "Uniswap V3 on Base chain"
    },
    "sushiswap_base": {
        "name": "SushiSwap Base",
        "factory": "0x71524B4f93c58fcbF659783284E38825f0622859",
        "router": "0x6BDED42c6DA8FBf0d2bA55B2fa120C5e0c8D7891",
        "description": "SushiSwap on Base chain"
    }
}

def get_lock_contracts_for_chain(chain: str) -> dict:
    """Get locking contracts for a specific chain"""
    return LIQUIDITY_LOCK_CONTRACTS.get(chain.lower(), {})

def get_all_lock_contracts() -> list:
    """Get all known locking contract addresses"""
    all_contracts = []
    for chain_data in LIQUIDITY_LOCK_CONTRACTS.values():
        for platform_data in chain_data.values():
            all_contracts.extend(platform_data["contracts"])
    return all_contracts

def is_known_lock_contract(address: str, chain: str = None) -> dict:
    """Check if an address is a known locking contract"""
    address = address.lower()
    
    if chain:
        # Check specific chain
        chain_data = LIQUIDITY_LOCK_CONTRACTS.get(chain.lower(), {})
        for platform, data in chain_data.items():
            if address in [addr.lower() for addr in data["contracts"]]:
                return {
                    "is_lock_contract": True,
                    "platform": platform,
                    "name": data["name"],
                    "website": data["website"],
                    "description": data["description"]
                }
    else:
        # Check all chains
        for chain_name, chain_data in LIQUIDITY_LOCK_CONTRACTS.items():
            for platform, data in chain_data.items():
                if address in [addr.lower() for addr in data["contracts"]]:
                    return {
                        "is_lock_contract": True,
                        "chain": chain_name,
                        "platform": platform,
                        "name": data["name"],
                        "website": data["website"],
                        "description": data["description"]
                    }
    
    return {"is_lock_contract": False}

def get_lp_patterns_for_chain(chain: str) -> dict:
    """Get LP token patterns for a specific chain"""
    if chain.lower() == "base":
        return {**LP_TOKEN_PATTERNS, **BASE_LP_PATTERNS}
    return LP_TOKEN_PATTERNS



