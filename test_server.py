#!/usr/bin/env python3
"""
Simple test for Luvya MCP Server
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from luvya_server import mcp
    print("SUCCESS: MCP server imported successfully")
    print(f"Server name: {mcp.name}")
    print("MCP server is ready to run!")
except Exception as e:
    print(f"ERROR: Failed to import MCP server: {e}")
    sys.exit(1)