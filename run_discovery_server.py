#!/usr/bin/env python3
"""
Entry point script for the fsc-dbt-mcp discovery server.
"""
import sys
import os

# Add src to Python path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

from fsc_dbt_mcp.server import main
import asyncio

if __name__ == "__main__":
    exit(asyncio.run(main()))