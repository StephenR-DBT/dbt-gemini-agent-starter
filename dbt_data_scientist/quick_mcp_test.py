#!/usr/bin/env python3
"""Quick MCP connection test - minimal version."""

import os
import sys
import asyncio
from dotenv import load_dotenv

async def quick_test():
    """Quick test of MCP connectivity."""
    print("🧪 Quick MCP Connection Test")
    print("-" * 30)
    
    # Load environment
    load_dotenv()
    
    # Check basic env vars
    url = os.environ.get("DBT_MCP_URL")
    token = os.environ.get("DBT_TOKEN")
    user_id = os.environ.get("DBT_USER_ID")
    prod_env_id = os.environ.get("DBT_PROD_ENV_ID")
    
    required_vars = ["DBT_MCP_URL", "DBT_TOKEN", "DBT_USER_ID", "DBT_PROD_ENV_ID"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    print(f"✅ URL: {url}")
    print(f"✅ Token: {'*' * len(token)}")
    print(f"✅ User ID: {user_id}")
    print(f"✅ Prod Env ID: {prod_env_id}")
    
    try:
        # Import and test
        from tools.dbt_mcp import dbt_mcp_toolset, get_dbt_mcp_tools
        
        print("🔌 Testing MCP toolset connection...")
        
        # Test the toolset connection (no context manager needed)
        try:
            print("✅ MCP toolset initialized successfully")
            
            # Try to get tools using the async function
            tools = await get_dbt_mcp_tools()
            print(f"✅ Connected! Found {len(tools)} tools")
            
            if tools:
                print("📋 Available tools:")
                for i, tool in enumerate(tools[:5]):  # Show first 5 tools
                    tool_name = getattr(tool, 'name', f'tool_{i}')
                    print(f"  - {tool_name}")
                if len(tools) > 5:
                    print(f"  ... and {len(tools) - 5} more")
            
            return True
            
        except Exception as tools_error:
            print(f"❌ Error getting tools: {tools_error}")
            return False
        
        finally:
            # Properly close the toolset connection
            try:
                if hasattr(dbt_mcp_toolset, 'close'):
                    await dbt_mcp_toolset.close()
                elif hasattr(dbt_mcp_toolset, 'aclose'):
                    await dbt_mcp_toolset.aclose()
            except Exception as close_error:
                print(f"⚠️  Warning during cleanup: {close_error}")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        print(f"Full error details:\n{traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = asyncio.run(quick_test())
    if success:
        print("\n🎉 MCP connection is working!")
    else:
        print("\n💥 MCP connection failed!")
    sys.exit(0 if success else 1)
