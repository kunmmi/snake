#!/usr/bin/env python3
"""
BearTech Token Analysis Bot - Launcher Script
"""
import sys
import os
import asyncio
import logging
import importlib.metadata

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
        try:
            ptb_version = importlib.metadata.version("python-telegram-bot")
            print(f"🔧 python-telegram-bot version: {ptb_version}")
        except Exception:
            print("🔧 python-telegram-bot version: unknown")

        try:
            import telegram
            import telegram.ext as tgext
            from telegram.ext import Updater as _Updater
            print(f"📦 telegram module: {getattr(telegram, '__file__', 'unknown')}")
            print(f"📦 telegram.ext module: {getattr(tgext, '__file__', 'unknown')}")
            print(f"📦 Updater class module: {getattr(_Updater, '__module__', 'unknown')}")
            print(f"📦 Updater class dict/slots: has __dict__? {hasattr(_Updater, '__dict__')} | has __slots__? {hasattr(_Updater, '__slots__')}")
        except Exception as diag_e:
            print(f"📦 telegram diagnostics failed: {diag_e}")
        run_bot()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
