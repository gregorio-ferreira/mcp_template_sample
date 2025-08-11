"""Example LangGraph agent client using MultiServerMCPClient.

Provides an offline fallback when OPENAI_API_KEY is not set: it will list the
discovered tools and invoke them directly without an LLM.
"""
from __future__ import annotations

import asyncio
import os

from langchain_mcp_adapters.client import MultiServerMCPClient


async def _offline_demo(client: MultiServerMCPClient) -> None:
    """List tools and call them directly without an LLM (offline mode)."""
    tools = await client.get_tools()
    print("Offline mode: listing discovered tools:")
    for t in tools:
        print(f"- {t.name}: {t.description}")

    # Direct MCP tool invocation via client (bypasses agent / LLM)
    print("\nCalling convert_timezone tool directly (offline):")
    async with client as c:
        res = await c.call_tool(
            "convert_timezone",
            {
                "dt": "2025-08-10 09:30",
                "from_tz": "Europe/Madrid",
                "to_tz": "America/New_York",
            },
        )
        print(res)

        print("\nCalling to_unix_time tool directly (offline):")
        res2 = await c.call_tool(
            "to_unix_time",
            {"dt": "2025-08-10T09:30:00+02:00", "unit": "milliseconds"},
        )
        print(res2)


async def _agent_demo(client: MultiServerMCPClient) -> None:
    """Full agent demo using an OpenAI model (requires OPENAI_API_KEY)."""
    from langgraph.prebuilt import create_react_agent  # local import to avoid unused when offline
    from langchain.chat_models import init_chat_model

    tools = await client.get_tools()
    model = init_chat_model("openai:gpt-4o-mini")
    agent = create_react_agent(model, tools)

    print("Timezone conversion example:")
    res1 = await agent.ainvoke(
        {
            "messages": (
                "Convert '2025-08-10 09:30' from Europe/Madrid to America/New_York in ISO format."
            )
        }
    )
    print(res1["messages"][-1].content)

    print("Unix time example:")
    res2 = await agent.ainvoke(
        {"messages": "Convert '2025-08-10T09:30:00+02:00' to Unix time in milliseconds."}
    )
    print(res2["messages"][-1].content)


async def main() -> None:
    client = MultiServerMCPClient(
        {
            "time_tools": {
                "transport": "streamable_http",
                "url": "http://127.0.0.1:8000/mcp/",
            }
        }
    )
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set -> running offline fallback demo.")
        await _offline_demo(client)
        await client.close()
        return
    await _agent_demo(client)
    await client.close()


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(main())
