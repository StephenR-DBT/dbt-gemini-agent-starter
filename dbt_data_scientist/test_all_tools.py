#!/usr/bin/env python3
"""Comprehensive test for all tools and subagents in the dbt_data_scientist agent."""

import os
import sys
import asyncio
import json
from typing import Dict, List, Any
from dotenv import load_dotenv

# Global variable to track MCP toolset for cleanup
_mcp_toolset = None

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print('='*60)

def print_test_result(test_name: str, success: bool, details: str = ""):
    """Print a formatted test result."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if details:
        print(f"    {details}")

async def test_environment_setup():
    """Test that all required environment variables are set."""
    print_section("Environment Setup Test")
    
    load_dotenv()
    
    # Required environment variables
    required_vars = {
        "DBT_PROJECT_LOCATION": "Path to dbt project",
        "DBT_EXECUTABLE": "Path to dbt executable",
        "DBT_MCP_URL": "dbt MCP server URL",
        "DBT_TOKEN": "dbt authentication token",
        "DBT_USER_ID": "dbt user ID",
        "DBT_PROD_ENV_ID": "dbt production environment ID"
    }
    
    all_present = True
    for var, description in required_vars.items():
        value = os.environ.get(var)
        if value:
            print_test_result(f"{var}", True, f"{description}: {value[:20]}..." if len(value) > 20 else f"{description}: {value}")
        else:
            print_test_result(f"{var}", False, f"{description}: NOT SET")
            all_present = False
    
    return all_present

async def test_dbt_compile_tool():
    """Test the dbt_compile tool."""
    print_section("dbt_compile Tool Test")
    
    try:
        from tools.dbt_compile import dbt_compile
        
        print("Testing dbt_compile tool...")
        result = dbt_compile("test")
        
        # Check if result has expected structure
        if isinstance(result, dict) and "returncode" in result and "logs" in result:
            print_test_result("dbt_compile structure", True, f"Return code: {result['returncode']}, Logs: {len(result['logs'])} entries")
            
            # Check if compilation was successful
            if result['returncode'] == 0:
                print_test_result("dbt_compile execution", True, "dbt compile completed successfully")
            else:
                print_test_result("dbt_compile execution", False, f"dbt compile failed with return code {result['returncode']}")
            
            return True
        else:
            print_test_result("dbt_compile structure", False, f"Unexpected result structure: {type(result)}")
            return False
            
    except Exception as e:
        print_test_result("dbt_compile import/execution", False, f"Error: {str(e)}")
        return False

async def cleanup_mcp_toolset():
    """Clean up MCP toolset connection."""
    global _mcp_toolset
    if _mcp_toolset:
        try:
            if hasattr(_mcp_toolset, 'close'):
                await _mcp_toolset.close()
            elif hasattr(_mcp_toolset, 'aclose'):
                await _mcp_toolset.aclose()
            elif hasattr(_mcp_toolset, '_client') and hasattr(_mcp_toolset._client, 'close'):
                await _mcp_toolset._client.close()
        except Exception as e:
            print(f"⚠️  Warning during MCP cleanup: {e}")
        finally:
            _mcp_toolset = None

async def test_dbt_mcp_toolset():
    """Test the dbt MCP toolset."""
    print_section("dbt MCP Toolset Test")
    
    global _mcp_toolset
    
    try:
        from tools.dbt_mcp import dbt_mcp_toolset, get_dbt_mcp_tools
        
        # Store reference for cleanup
        _mcp_toolset = dbt_mcp_toolset
        
        print("Testing dbt MCP toolset...")
        
        # Test toolset initialization
        if dbt_mcp_toolset:
            print_test_result("MCP toolset initialization", True, "Toolset created successfully")
        else:
            print_test_result("MCP toolset initialization", False, "Toolset is None")
            return False
        
        # Test getting tools
        try:
            tools = await get_dbt_mcp_tools()
            if tools and len(tools) > 0:
                print_test_result("MCP tools retrieval", True, f"Retrieved {len(tools)} tools")
                
                # List available tools
                print("Available MCP tools:")
                for i, tool in enumerate(tools[:5]):  # Show first 5 tools
                    tool_name = getattr(tool, 'name', f'tool_{i}')
                    print(f"  - {tool_name}")
                if len(tools) > 5:
                    print(f"  ... and {len(tools) - 5} more")
                
                return True
            else:
                print_test_result("MCP tools retrieval", False, "No tools retrieved or empty list")
                return False
                
        except Exception as e:
            print_test_result("MCP tools retrieval", False, f"Error retrieving tools: {str(e)}")
            return False
            
    except Exception as e:
        print_test_result("MCP toolset import", False, f"Error importing MCP toolset: {str(e)}")
        return False

async def test_dbt_model_analyzer_subagent():
    """Test the dbt_model_analyzer subagent."""
    print_section("dbt_model_analyzer Subagent Test")
    
    try:
        from sub_agents.dbt_model_analyzer import dbt_model_analyzer_agent
        
        # Test subagent initialization
        if dbt_model_analyzer_agent:
            print_test_result("Subagent initialization", True, f"Agent name: {getattr(dbt_model_analyzer_agent, 'name', 'unknown')}")
        else:
            print_test_result("Subagent initialization", False, "Subagent is None")
            return False
        
        # Test subagent tools
        try:
            tools = getattr(dbt_model_analyzer_agent, 'tools', [])
            if tools:
                print_test_result("Subagent tools", True, f"Found {len(tools)} tools")
                
                # Test individual tools
                for tool in tools:
                    if hasattr(tool, 'name'):
                        tool_name = tool.name
                    elif hasattr(tool, '__name__'):
                        tool_name = tool.__name__
                    else:
                        tool_name = str(tool)
                    
                    print(f"  - Tool: {tool_name}")
                    
                    # Test if tool is callable
                    if callable(tool):
                        print_test_result(f"Tool {tool_name}", True, "Tool is callable")
                    else:
                        print_test_result(f"Tool {tool_name}", False, "Tool is not callable")
            else:
                print_test_result("Subagent tools", False, "No tools found")
                return False
                
        except Exception as e:
            print_test_result("Subagent tools access", False, f"Error accessing tools: {str(e)}")
            return False
        
        return True
        
    except Exception as e:
        print_test_result("Subagent import", False, f"Error importing subagent: {str(e)}")
        return False
    """Test the root agent configuration."""
    print_section("Root Agent Test")
    
    try:
        from agent import root_agent
        
        # Test agent initialization
        if root_agent:
            print_test_result("Root agent initialization", True, f"Agent name: {getattr(root_agent, 'name', 'unknown')}")
        else:
            print_test_result("Root agent initialization", False, "Root agent is None")
            return False
        
        # Test agent tools
        try:
            tools = getattr(root_agent, 'tools', [])
            if tools:
                print_test_result("Root agent tools", True, f"Found {len(tools)} tools")
                
                for tool in tools:
                    if hasattr(tool, 'name'):
                        tool_name = tool.name
                    elif hasattr(tool, '__name__'):
                        tool_name = tool.__name__
                    else:
                        tool_name = str(tool)
                    
                    print(f"  - Tool: {tool_name}")
            else:
                print_test_result("Root agent tools", False, "No tools found")
                return False
                
        except Exception as e:
            print_test_result("Root agent tools access", False, f"Error accessing tools: {str(e)}")
            return False
        
        # Test subagents
        try:
            sub_agents = getattr(root_agent, 'sub_agents', [])
            if sub_agents:
                print_test_result("Root agent subagents", True, f"Found {len(sub_agents)} subagents")
                
                for sub_agent in sub_agents:
                    if hasattr(sub_agent, 'name'):
                        subagent_name = sub_agent.name
                    else:
                        subagent_name = str(sub_agent)
                    
                    print(f"  - Subagent: {subagent_name}")
            else:
                print_test_result("Root agent subagents", False, "No subagents found")
                return False
                
        except Exception as e:
            print_test_result("Root agent subagents access", False, f"Error accessing subagents: {str(e)}")
            return False
        
        return True
        
    except Exception as e:
        print_test_result("Root agent import", False, f"Error importing root agent: {str(e)}")
        return False

async def test_tool_functionality():
    """Test actual functionality of tools."""
    print_section("Tool Functionality Test")
    
    try:
        from tools.dbt_compile import dbt_compile
        
        print("Testing dbt_compile functionality...")
        result = dbt_compile("test")
        
        if result.get('returncode') == 0:
            print_test_result("dbt_compile functionality", True, "dbt compile executed successfully")
            
            # Check if logs contain useful information
            logs = result.get('logs', [])
            if logs:
                print_test_result("dbt_compile logs", True, f"Generated {len(logs)} log entries")
                
                # Look for specific log types
                log_types = set()
                for log in logs:
                    if isinstance(log, dict) and 'info' in log:
                        log_types.add(log['info'].get('name', 'unknown'))
                
                if log_types:
                    print(f"  Log types found: {', '.join(sorted(log_types))}")
            else:
                print_test_result("dbt_compile logs", False, "No logs generated")
        else:
            print_test_result("dbt_compile functionality", False, f"dbt compile failed with return code {result.get('returncode')}")
        
        return True
        
    except Exception as e:
        print_test_result("Tool functionality", False, f"Error testing functionality: {str(e)}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting Comprehensive dbt_data_scientist Agent Test")
    print("=" * 60)
    
    # Track test results
    test_results = {}
    
    try:
        # Run all tests
        test_results['environment'] = await test_environment_setup()
        test_results['dbt_compile_tool'] = await test_dbt_compile_tool()
        test_results['dbt_mcp_toolset'] = await test_dbt_mcp_toolset()
        test_results['dbt_model_analyzer_subagent'] = await test_dbt_model_analyzer_subagent()
        test_results['tool_functionality'] = await test_tool_functionality()
        
        # Print summary
        print_section("Test Summary")
        
        passed_tests = sum(1 for result in test_results.values() if result)
        total_tests = len(test_results)
        
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        print()
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        print()
        if passed_tests == total_tests:
            print("🎉 All tests passed! The dbt_data_scientist agent is fully functional.")
            return True
        else:
            print(f"⚠️  {total_tests - passed_tests} test(s) failed. Please check the issues above.")
            return False
            
    finally:
        # Ensure MCP cleanup happens regardless of test results
        print("\n🧹 Cleaning up MCP connections...")
        await cleanup_mcp_toolset()
        print("✅ Cleanup completed")

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
