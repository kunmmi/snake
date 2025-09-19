#!/usr/bin/env python3
"""
BearTech Token Analysis Bot - Launcher Script
"""
import sys
import os
import asyncio
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.bot.main import run_bot

if __name__ == "__main__":
    print("🤖 Starting BearTech Token Analysis Bot...")
    print("📊 Comprehensive token analysis with security, market data, and risk assessment")
    print("🔒 Honeypot detection and security analysis")
    print("💰 Real-time market data from multiple sources")
    print("🌐 Multi-chain support: Ethereum, Base")
    print("=" * 60)
    
    try:
        run_bot()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
