#!/usr/bin/env python3
"""Agent Client Example.

This example demonstrates creating an AI-powered conversational agent
that can use MCP tools through LangChain and LangGraph.
"""

from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Server configuration
SERVER_URL = "http://127.0.0.1:8000/mcp/"


async def main() -> None:
    """Example of creating an AI agent with MCP tools."""
    print("🤖 MCP Agent Example")
    print("=" * 40)

    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set")
        print("💡 Set your OpenAI API key in the .env file to run this example")
        print("💡 For a working example, use:")
        print("   uv run python tests/test_examples/mcp_chat_agent.py")
        return

    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
        from langchain.chat_models import init_chat_model
        from langgraph.prebuilt import create_react_agent
    except ImportError:
        print("❌ Agent dependencies not installed")
        print("💡 Install with: uv pip install -e '.[agent]'")
        return

    print(f"📍 Server URL: {SERVER_URL}")

    try:
        # Initialize MCP client
        client = MultiServerMCPClient(
            {
                "mcp_server": {
                    "transport": "streamable_http",
                    "url": SERVER_URL,
                }
            }
        )

        # Get available tools
        tools = await client.get_tools()
        print(f"✅ Connected to MCP server with {len(tools)} tools")

        # Initialize AI model and agent
        model = init_chat_model("openai:gpt-4o-mini")
        agent = create_react_agent(model, tools)

        # Example interactions
        example_queries = [
            "What time is it in Tokyo when it's 3 PM in London?",
            "Convert midnight UTC on New Year's Day 2025 to Unix timestamp",
        ]

        print("\n🎬 Example Agent Interactions:")
        print("=" * 50)

        for query in example_queries:
            print(f"\n👤 Human: {query}")
            print("🤖 Agent: ", end="", flush=True)

            result = await agent.ainvoke({"messages": [query]})
            response = result["messages"][-1].content
            print(response)

        print("\n✨ For interactive chat, run:")
        print("   uv run python tests/test_examples/mcp_chat_agent.py")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure:")
        print("   1. MCP server is running: uv run python scripts/run_server.py")
        print("   2. Agent dependencies installed: uv pip install -e '.[agent]'")
        print("   3. OpenAI API key is set in .env file")


if __name__ == "__main__":
    asyncio.run(main())
