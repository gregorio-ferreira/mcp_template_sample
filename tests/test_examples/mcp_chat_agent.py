#!/usr/bin/env python3
"""MCP Conversational Agent.

This script creates an interactive chat agent that can use MCP tools.
It supports both LLM-powered conversations (with OpenAI API key) and
offline tool testing mode.
"""

from __future__ import annotations

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

    async def initialize(self) -> bool:
        """Initialize the agent with MCP tools.

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

            # Try to initialize LLM-powered agent
            if os.getenv("OPENAI_API_KEY"):
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

            model = init_chat_model("openai:gpt-4o-mini")
            self.agent = create_react_agent(model, self.tools)
            print("✅ AI agent initialized with OpenAI GPT-4o-mini")
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
        print("\n🤖 AI Chat Mode - Ask me anything about timezones and time!")
        print("💬 The AI can use timezone and time conversion tools")
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
            except Exception as e:
                print(f"\n❌ Error: {e}")

    async def _get_ai_response(self, message: str) -> str:
        """Get response from the AI agent with conversation context."""
        try:
            # Build context from recent conversation history
            messages = []

            # Add system context
            system_context = (
                "You are a helpful assistant with access to timezone and time "
                "conversion tools. Help users with time-related questions and "
                "conversions. Be concise but informative."
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
        print("   1. timezone    - Test timezone conversion")
        print("   2. unix        - Test Unix time conversion")
        print("   3. list        - List all available tools")
        print("   4. demo        - Run demo scenarios")
        print("   5. help        - Show this help")
        print("   6. quit        - Exit")
        print("=" * 60)

        while True:
            try:
                user_input = input("\n⌨️  Command: ").strip().lower()

                if user_input in ["quit", "exit", "q", "6"]:
                    break
                elif user_input in ["timezone", "1"]:
                    await self._demo_timezone_conversion()
                elif user_input in ["unix", "2"]:
                    await self._demo_unix_time()
                elif user_input in ["list", "3"]:
                    await self._list_tools()
                elif user_input in ["demo", "4"]:
                    await self._run_demo_scenarios()
                elif user_input in ["help", "5"]:
                    print("📋 Available commands:")
                    print("   1. timezone | 2. unix | 3. list | 4. demo | 5. help | 6. quit")
                else:
                    print("❓ Unknown command. Type 'help' for available commands.")

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
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

    async def _demo_timezone_conversion(self) -> None:
        """Demo timezone conversion with interactive input."""
        print("\n🌍 Timezone Conversion Demo")

        examples = [
            {
                "dt": "2025-08-11 15:30",
                "from_tz": "Europe/Madrid",
                "to_tz": "America/New_York",
                "desc": "Madrid afternoon to NYC",
            },
            {
                "dt": "2025-12-25 00:00",
                "from_tz": "Asia/Tokyo",
                "to_tz": "Europe/London",
                "desc": "Christmas midnight Tokyo to London",
            },
            {
                "dt": "2025-06-15T14:30:00",
                "from_tz": "America/Los_Angeles",
                "to_tz": "UTC",
                "desc": "LA time to UTC",
            },
        ]

        for i, example in enumerate(examples, 1):
            print(f"\n{i}. {example['desc']}:")
            try:
                # Find the timezone conversion tool
                for tool in self.tools:
                    if tool.name == "convert_timezone":
                        result = await tool.ainvoke(
                            {
                                "dt": example["dt"],
                                "from_tz": example["from_tz"],
                                "to_tz": example["to_tz"],
                            }
                        )
                        print(f"   📅 {example['dt']} ({example['from_tz']})")
                        print(f"   ➡️  {result} ({example['to_tz']})")
                        break
                else:
                    print("   ❌ Timezone conversion tool not found")
            except Exception as e:
                print(f"   ❌ Error: {e}")

    async def _demo_unix_time(self) -> None:
        """Demo Unix time conversion."""
        print("\n⏰ Unix Time Conversion Demo")

        examples = [
            {"dt": "2025-01-01T00:00:00Z", "unit": "seconds", "desc": "New Year 2025 in seconds"},
            {
                "dt": "2025-08-11T12:00:00+02:00",
                "unit": "milliseconds",
                "desc": "Today noon CEST in milliseconds",
            },
        ]

        for i, example in enumerate(examples, 1):
            print(f"\n{i}. {example['desc']}:")
            try:
                for tool in self.tools:
                    if tool.name == "to_unix_time":
                        result = await tool.ainvoke({"dt": example["dt"], "unit": example["unit"]})
                        print(f"   📅 {example['dt']}")
                        print(f"   ➡️  {result} {example['unit']}")
                        break
                else:
                    print("   ❌ Unix time conversion tool not found")
            except Exception as e:
                print(f"   ❌ Error: {e}")

    async def _run_demo_scenarios(self) -> None:
        """Run a comprehensive demo of all capabilities."""
        print("\n🎬 Running Demo Scenarios...")
        await self._demo_timezone_conversion()
        await self._demo_unix_time()

    async def run_example_conversations(self) -> None:
        """Run example conversations to demonstrate capabilities."""
        if not self.agent:
            print("⚠️  AI agent not available - running offline demos instead")
            await self._run_demo_scenarios()
            return

        example_queries = [
            "Convert 2:30 PM Madrid time today to New York time",
            "What's the Unix timestamp for New Year's Eve 2025 at midnight UTC?",
            "Convert 9 AM Tokyo time on Christmas Day 2025 to Los Angeles time",
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
        print("MCP Conversational Agent")
        print("=" * 30)
        print("Usage:")
        print("  python mcp_chat_agent.py [OPTIONS]")
        print()
        print("Options:")
        print("  --demo       Run example conversations and exit")
        print("  --offline    Force offline mode (skip AI initialization)")
        print("  --help       Show this help message")
        print()
        print("Environment:")
        print("  OPENAI_API_KEY   Set to enable AI-powered conversations")
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
        has_ai = False if force_offline else await agent.initialize()

        if "--demo" in sys.argv:
            # Run examples and exit
            await agent.run_example_conversations()
            return 0

        # Start interactive session
        print("\n🚀 Starting interactive session...")
        if has_ai:
            print("💡 AI mode enabled - natural language conversations available")
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
