"""
Chain detection logic for BearTech Token Analysis Bot
"""
import re
from typing import Optional, Dict, Any
from ..models.token import ChainType
from ..config import SUPPORTED_CHAINS


class ChainDetector:
    """Detects blockchain network for contract addresses"""
    
    # Common contract address patterns
    ETHEREUM_PATTERN = re.compile(r'^0x[a-fA-F0-9]{40}$')
    BASE_PATTERN = re.compile(r'^0x[a-fA-F0-9]{40}$')  # Same format as Ethereum
    
    @staticmethod
    def detect_chain_by_address(address: str) -> Optional[ChainType]:
        """
        Detect chain by contract address format
        Note: Since all chains use the same address format, we'll need to use other methods
        """
        if not ChainDetector._is_valid_address(address):
            return None
        
        # All supported chains use the same address format
        # We'll need to use API calls to determine the actual chain
        return None  # Will be determined by API calls
    
    @staticmethod
    def detect_chain_by_api_response(response_data: Dict[str, Any], address: str) -> Optional[ChainType]:
        """
        Detect chain by analyzing API response data
        """
        if not response_data:
            return None
        
        # Check for chain-specific indicators in the response
        if 'chainId' in response_data:
            chain_id = response_data['chainId']
            return ChainDetector._get_chain_by_id(chain_id)
        
        # Check for chain-specific fields
        if 'chain' in response_data:
            chain_name = response_data['chain'].lower()
            if 'ethereum' in chain_name or 'eth' in chain_name:
                return ChainType.ETHEREUM
            elif 'base' in chain_name:
                return ChainType.BASE
        
        # Check for network-specific contract addresses or patterns
        if 'network' in response_data:
            network = response_data['network'].lower()
            if 'ethereum' in network:
                return ChainType.ETHEREUM
            elif 'base' in network:
                return ChainType.BASE
        
        return None
    
    @staticmethod
    def get_chain_info(chain_type: ChainType) -> Dict[str, Any]:
        """Get chain information"""
        return SUPPORTED_CHAINS.get(chain_type.value, {})
    
    @staticmethod
    def get_all_supported_chains() -> Dict[str, Dict[str, Any]]:
        """Get all supported chains"""
        return SUPPORTED_CHAINS
    
    @staticmethod
    def is_supported_chain(chain_type: ChainType) -> bool:
        """Check if chain is supported"""
        return chain_type.value in SUPPORTED_CHAINS
    
    @staticmethod
    def _is_valid_address(address: str) -> bool:
        """Validate contract address format"""
        if not address or not isinstance(address, str):
            return False
        
        # Check if it's a valid Ethereum-style address
        return bool(ETHEREUM_PATTERN.match(address))
    
    @staticmethod
    def _get_chain_by_id(chain_id: int) -> Optional[ChainType]:
        """Get chain type by chain ID"""
        chain_id_map = {
            1: ChainType.ETHEREUM,
            8453: ChainType.BASE
        }
        return chain_id_map.get(chain_id)
    
    @staticmethod
    def get_chain_emoji(chain_type: ChainType) -> str:
        """Get emoji for chain type"""
        emoji_map = {
            ChainType.ETHEREUM: "🔷",
            ChainType.BASE: "🔵"
        }
        return emoji_map.get(chain_type, "❓")
    
    @staticmethod
    def get_chain_name(chain_type: ChainType) -> str:
        """Get human-readable chain name"""
        chain_info = ChainDetector.get_chain_info(chain_type)
        return chain_info.get('name', chain_type.value.title())
    
    @staticmethod
    def get_explorer_url(chain_type: ChainType, address: str) -> str:
        """Get explorer URL for address"""
        chain_info = ChainDetector.get_chain_info(chain_type)
        explorer = chain_info.get('explorer', 'etherscan.io')
        return f"https://{explorer}/token/{address}"
    
    @staticmethod
    def get_rpc_endpoint(chain_type: ChainType) -> Optional[str]:
        """Get RPC endpoint for chain"""
        from ..config import RPC_ENDPOINTS
        return RPC_ENDPOINTS.get(chain_type.value)
    
    @staticmethod
    def get_explorer_api_config(chain_type: ChainType) -> Optional[Dict[str, Any]]:
        """Get explorer API configuration for chain"""
        from ..config import EXPLORER_APIS
        return EXPLORER_APIS.get(chain_type.value)
