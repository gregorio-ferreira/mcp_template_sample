#!/usr/bin/env -S uv run python
"""MCP Conversational Agent for Emplifi Listening API.

This script creates an interactive chat agent that can use Emplifi MCP tools.
It supports both LLM-powered conversations (with OpenAI API key) and
offline tool testing mode for social media listening data.
"""

from __future__ import annotations

import asyncio
import os
import sys

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import centralized configuration
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from mcp_server.core.config import get_openai_api_key

# Server configuration
SERVER_URL = "http://127.0.0.1:8000/mcp/"


class MCPConversationalAgent:
    """A conversational agent powered by MCP tools."""

    def __init__(self, server_url: str = SERVER_URL) -> None:
        self.server_url = server_url
        self.client = None
        self.agent = None
        self.tools = []
        self.conversation_history: list[dict[str, str]] = []

    async def initialize(self, skip_ai: bool = False) -> bool:
        """Initialize the agent with MCP tools.

        Args:
            skip_ai: If True, only connect to MCP server without AI initialization

        Returns:
            True if successfully initialized with LLM, False for offline mode.
        """
        print("🤖 Initializing MCP Conversational Agent...")
        print(f"📍 Server URL: {self.server_url}")

        # Check for LangChain dependencies
        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient
        except ImportError:
            print("❌ LangChain MCP adapters not installed.")
            print("   Install with: uv pip install -e '.[agent]'")
            return False

        # Initialize MCP client
        self.client = MultiServerMCPClient(
            {
                "mcp_server": {
                    "transport": "streamable_http",
                    "url": self.server_url,
                }
            }
        )

        try:
            # Discover available tools
            self.tools = await self.client.get_tools()
            print("✅ Connected to MCP server")
            print(f"🔧 Found {len(self.tools)} tools:")
            for tool in self.tools:
                print(f"   • {tool.name}: {tool.description}")

            # Skip AI initialization if requested
            if skip_ai:
                print("\n🔧 Skipping AI initialization (offline mode)")
                return False

            # Try to initialize LLM-powered agent
            openai_key = get_openai_api_key()
            if openai_key:
                return await self._initialize_llm_agent()
            else:
                print("\n⚠️  OPENAI_API_KEY not set")
                print("   💡 Set your API key to enable AI conversations")
                print("   🔧 Running in offline tool testing mode")
                return False

        except Exception as e:
            print(f"❌ Failed to connect to MCP server: {e}")
            print(f"   💡 Make sure the server is running at {self.server_url}")
            print("   🚀 Start server: uv run python scripts/run_server.py")
            return False

    async def _initialize_llm_agent(self) -> bool:
        """Initialize the LLM-powered agent."""
        try:
            from langchain.chat_models import init_chat_model
            from langgraph.prebuilt import create_react_agent

            model = init_chat_model("openai:gpt-5-mini-2025-08-07")
            self.agent = create_react_agent(model, self.tools)
            print("✅ AI agent initialized with OpenAI gpt-5-mini-2025-08-07")
            return True

        except ImportError:
            print("❌ LangGraph/LangChain dependencies missing")
            print("   Install with: uv pip install -e '.[agent]'")
            return False
        except Exception as e:
            print(f"❌ Failed to initialize AI agent: {e}")
            return False

    async def chat_interactive(self) -> None:
        """Start an interactive chat session."""
        if self.agent:
            await self._ai_chat_mode()
        else:
            await self._offline_chat_mode()

    async def _ai_chat_mode(self) -> None:
        """AI-powered chat mode with conversation memory."""
        print("\n🤖 AI Chat Mode - Ask me about social media listening!")
        print("💬 The AI can use Emplifi tools to fetch posts and analyze data")
        print("⌨️  Type 'quit', 'exit', or press Ctrl+C to exit")
        print("=" * 60)

        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                if user_input.lower() in ["quit", "exit", "q"]:
                    break

                if not user_input:
                    continue

                print("\n🤖 Assistant: ", end="", flush=True)
                response = await self._get_ai_response(user_input)
                print(response)

                # Store conversation
                self.conversation_history.append({"user": user_input, "assistant": response})

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except EOFError:
                print("\n\n📄 End of input reached. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")

    async def _get_ai_response(self, message: str) -> str:
        """Get response from the AI agent with conversation context."""
        try:
            # Build context from recent conversation history
            messages = []

            # Add system context
            system_context = (
                "You are a helpful assistant with access to Emplifi social "
                "media listening tools. Help users analyze social media posts, "
                "brand mentions, and sentiment data. Be concise but informative. "
                "You can list listening queries, fetch recent posts, and retrieve "
                "posts from specific date ranges."
            )
            messages.append(system_context)

            # Add recent conversation history (last 3 exchanges)
            for exchange in self.conversation_history[-3:]:
                messages.append(f"Human: {exchange['user']}")
                messages.append(f"Assistant: {exchange['assistant']}")

            # Add current message
            messages.append(f"Human: {message}")

            full_prompt = "\n".join(messages)

            result = await self.agent.ainvoke({"messages": [full_prompt]})
            return result["messages"][-1].content

        except Exception as e:
            return f"Sorry, I encountered an error: {e}"

    async def _offline_chat_mode(self) -> None:
        """Offline mode - direct tool testing without AI."""
        print("\n🔧 Offline Tool Testing Mode")
        print("📋 Available commands:")
        print("   1. queries     - List listening queries")
        print("   2. recent      - Test recent posts retrieval")
        print("   3. fetch       - Test date range posts")
        print("   4. list        - List all available tools")
        print("   5. demo        - Run demo scenarios")
        print("   6. help        - Show this help")
        print("   7. quit        - Exit")
        print("=" * 60)

        while True:
            try:
                user_input = input("\n⌨️  Command: ").strip().lower()

                if user_input in ["quit", "exit", "q", "7"]:
                    break
                elif user_input in ["queries", "1"]:
                    await self._demo_list_queries()
                elif user_input in ["recent", "2"]:
                    await self._demo_recent_posts()
                elif user_input in ["fetch", "3"]:
                    await self._demo_fetch_posts()
                elif user_input in ["list", "4"]:
                    await self._list_tools()
                elif user_input in ["demo", "5"]:
                    await self._run_demo_scenarios()
                elif user_input in ["help", "6"]:
                    print("📋 Available commands:")
                    print("   1. queries | 2. recent | 3. fetch | 4. list")
                    print("   5. demo | 6. help | 7. quit")
                else:
                    print("❓ Unknown command. Type 'help' for commands.")

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except EOFError:
                print("\n\n📄 End of input reached. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    async def _list_tools(self) -> None:
        """Show available tools and their details."""
        print(f"\n📋 Available MCP Tools: ({len(self.tools)} found)")
        if not self.tools:
            print("   ❌ No tools available")
            return

        for tool in self.tools:
            print(f"\n🔧 {tool.name}")
            print(f"   📄 {tool.description}")
            # Show parameters if available
            if hasattr(tool, "args_schema") and tool.args_schema:
                print("   📝 Parameters:")
                fields = getattr(tool.args_schema, "model_fields", {})
                for param_name, param_info in fields.items():
                    param_type = getattr(
                        param_info.annotation, "__name__", str(param_info.annotation)
                    )
                    param_desc = getattr(param_info, "description", "No description")
                    print(f"     • {param_name} ({param_type}): {param_desc}")

    async def _demo_list_queries(self) -> None:
        """Demo listing available listening queries."""
        print("\n📋 Listening Queries Demo")

        try:
            # Find the list queries tool
            for tool in self.tools:
                if tool.name == "list_listening_queries":
                    print("   Fetching all listening queries...")
                    result = await tool.ainvoke({})
                    
                    # Handle string result (JSON) or list result
                    if isinstance(result, str):
                        import json
                        queries = json.loads(result)
                    elif isinstance(result, list):
                        queries = result
                    else:
                        queries = result.get('result', [])
                    
                    print(f"\n   📊 Found {len(queries)} listening queries")
                    
                    # Show first 5 queries as examples
                    print("\n   📝 Sample queries:")
                    for i, query in enumerate(queries[:5], 1):
                        if isinstance(query, dict):
                            name = query.get('name', 'Unknown')
                            status = query.get('status', 'Unknown')
                        else:
                            name = getattr(query, 'name', 'Unknown')
                            status = getattr(query, 'status', 'Unknown')
                        print(f"      {i}. {name} - Status: {status}")
                    
                    if len(queries) > 5:
                        print(f"      ... and {len(queries) - 5} more")
                    
                    break
            else:
                print("   ❌ list_listening_queries tool not found")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()

    async def _demo_recent_posts(self) -> None:
        """Demo recent posts retrieval."""
        print("\n📱 Recent Posts Demo")
        
        # BAYER query ID that we know works
        bayer_query_id = "LNQ_1140092_66fe2dcd3e9eb298096e8db3"

        try:
            # Find the recent posts tool
            for tool in self.tools:
                if tool.name == "get_recent_posts":
                    print("   Getting recent posts for BAYER query...")
                    result = await tool.ainvoke({
                        "query_id": bayer_query_id,
                        "days_back": 7,
                        "limit": 3
                    })
                    
                    # Handle string result (JSON) or list result
                    if isinstance(result, str):
                        import json
                        posts = json.loads(result)
                    elif isinstance(result, list):
                        posts = result
                    else:
                        posts = result.get('result', [])
                    
                    print(f"\n   📊 Found {len(posts)} recent posts")
                    
                    if posts:
                        print("\n   📝 Sample posts:")
                        for i, post in enumerate(posts[:3], 1):
                            if isinstance(post, dict):
                                platform = post.get('platform', 'Unknown')
                                interactions = post.get('interactions', 0)
                                sentiment = post.get('sentiment', 'Unknown')
                                message = post.get('message', '')[:80]
                            else:
                                platform = getattr(post, 'platform', 'Unknown')
                                interactions = getattr(post, 'interactions', 0)
                                sentiment = getattr(post, 'sentiment', 'Unknown')
                                message = getattr(post, 'message', '')[:80]
                            
                            print(f"      {i}. {platform.upper()} - "
                                  f"{interactions:,} interactions")
                            print(f"         Sentiment: {sentiment}")
                            print(f"         Message: {message}...")
                    else:
                        print("   No recent posts found")
                    
                    break
            else:
                print("   ❌ get_recent_posts tool not found")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    async def _demo_fetch_posts(self) -> None:
        """Demo fetching posts from specific date range."""
        print("\n📅 Date Range Posts Demo")
        
        # BAYER query ID and known working date range
        bayer_query_id = "LNQ_1140092_66fe2dcd3e9eb298096e8db3"
        start_date = "2025-08-05"
        end_date = "2025-08-12"

        try:
            # Find the fetch posts tool
            for tool in self.tools:
                if tool.name == "fetch_listening_posts":
                    print(f"   Fetching posts from {start_date} to {end_date}...")
                    result = await tool.ainvoke({
                        "query_ids": [bayer_query_id],
                        "date_start": start_date,
                        "date_end": end_date,
                        "limit": 5
                    })
                    
                    # Handle string result (JSON) or list result
                    if isinstance(result, str):
                        import json
                        posts = json.loads(result)
                    elif isinstance(result, list):
                        posts = result
                    else:
                        posts = result.get('result', [])
                    
                    print(f"\n   📊 Found {len(posts)} posts in date range")
                    
                    if posts:
                        print("\n   📝 Sample posts:")
                        for i, post in enumerate(posts[:3], 1):
                            if isinstance(post, dict):
                                platform = post.get('platform', 'Unknown')
                                created_time = post.get('created_time', 'Unknown')
                                created = created_time[:10]
                                interactions = post.get('interactions', 0)
                            else:
                                platform = getattr(post, 'platform', 'Unknown')
                                created_time = getattr(post, 'created_time', 'Unknown')
                                created = created_time[:10]
                                interactions = getattr(post, 'interactions', 0)
                            
                            print(f"      {i}. {platform.upper()} - {created}")
                            print(f"         Interactions: {interactions:,}")
                    else:
                        print("   No posts found in date range")
                    
                    break
            else:
                print("   ❌ fetch_listening_posts tool not found")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    async def _run_demo_scenarios(self) -> None:
        """Run a comprehensive demo of all capabilities."""
        print("\n🎬 Running Demo Scenarios...")
        await self._demo_list_queries()
        await self._demo_recent_posts()
        await self._demo_fetch_posts()

    async def run_example_conversations(self) -> None:
        """Run example conversations to demonstrate capabilities."""
        if not self.agent:
            print("⚠️  AI agent not available - running offline demos instead")
            await self._run_demo_scenarios()
            return

        example_queries = [
            "Show me recent posts about BAYER from the last week",
            "List all available listening queries",
            "Get posts about BAYER from August 5-12, 2025",
        ]

        print("\n🎬 Example AI Conversations:")
        print("=" * 60)

        for i, query in enumerate(example_queries, 1):
            print(f"\n{i}. 👤 Human: {query}")
            print("   🤖 Assistant: ", end="", flush=True)

            try:
                response = await self._get_ai_response(query)
                print(response)
            except Exception as e:
                print(f"Error: {e}")


async def main() -> int:
    """Main entry point for the conversational agent."""
    if "--help" in sys.argv or "-h" in sys.argv:
        print("MCP Conversational Agent for Emplifi Listening API")
        print("=" * 50)
        print("Usage:")
        print("  python mcp_chat_agent.py [OPTIONS]")
        print()
        print("Options:")
        print("  --demo       Run example conversations and exit")
        print("  --offline    Force offline mode (skip AI initialization)")
        print("  --help       Show this help message")
        print()
        print("Environment:")
        print("  OPENAI_API_KEY     Set to enable AI-powered conversations")
        print("  EMPLIFI_TOKEN      Required for Emplifi API access")
        print("  EMPLIFI_SECRET     Required for Emplifi API access")
        print()
        print("Examples:")
        print("  python mcp_chat_agent.py")
        print("  OPENAI_API_KEY=sk-... python mcp_chat_agent.py")
        print("  python mcp_chat_agent.py --demo")
        return 0

    agent = MCPConversationalAgent()

    try:
        # Initialize the agent
        force_offline = "--offline" in sys.argv
        has_ai = await agent.initialize(skip_ai=force_offline)

        if "--demo" in sys.argv:
            # Run examples and exit
            await agent.run_example_conversations()
            return 0

        # Start interactive session
        print("\n🚀 Starting interactive session...")
        if has_ai:
            print("💡 AI mode enabled - natural language conversations")
        else:
            print("🔧 Offline mode - direct tool testing available")

        await agent.chat_interactive()

        print("\n👋 Session ended. Goodbye!")
        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
