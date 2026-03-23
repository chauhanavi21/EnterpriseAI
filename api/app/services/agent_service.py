"""
Agent service: tool execution, web search, internal actions.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ToolResult:
    def __init__(self, tool_name: str, success: bool, data: Any, error: str = None):
        self.tool_name = tool_name
        self.success = success
        self.data = data
        self.error = error

    def to_dict(self) -> dict:
        return {
            "tool_name": self.tool_name,
            "success": self.success,
            "data": self.data,
            "error": self.error,
        }


class AgentService:
    """
    Agent that can execute tools/actions based on user queries.
    Tools: web_search, calculator, knowledge_lookup, summarize.
    """

    AVAILABLE_TOOLS = {
        "web_search": "Search the web for current information",
        "calculator": "Perform mathematical calculations",
        "knowledge_lookup": "Search the internal knowledge base",
        "summarize_document": "Summarize a specific document",
    }

    def __init__(self):
        self.settings = get_settings()

    async def determine_tools(self, query: str) -> List[str]:
        """
        Determine which tools to use based on the query.

        COMMENTED OUT: Uses LLM for tool selection.
        Fallback: simple keyword matching.
        """
        # ────────────────────────────────────────────────────
        # COMMENTED OUT: LLM-based tool routing
        # ────────────────────────────────────────────────────
        # from openai import AsyncOpenAI
        # client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        # response = await client.chat.completions.create(
        #     model=self.settings.openai_model,
        #     messages=[
        #         {"role": "system", "content": "Select tools..."},
        #         {"role": "user", "content": query},
        #     ],
        #     tools=[...],
        # )
        # ────────────────────────────────────────────────────

        tools = []
        query_lower = query.lower()
        if any(kw in query_lower for kw in ["search", "find", "latest", "current", "news"]):
            tools.append("web_search")
        if any(kw in query_lower for kw in ["calculate", "math", "compute", "sum", "average"]):
            tools.append("calculator")
        if any(kw in query_lower for kw in ["document", "knowledge", "internal", "our"]):
            tools.append("knowledge_lookup")
        if any(kw in query_lower for kw in ["summarize", "summary", "brief"]):
            tools.append("summarize_document")

        return tools or ["knowledge_lookup"]  # Default to knowledge lookup

    async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        """Execute a specific tool."""
        try:
            if tool_name == "web_search":
                return await self._web_search(params.get("query", ""))
            elif tool_name == "calculator":
                return await self._calculator(params.get("expression", ""))
            elif tool_name == "knowledge_lookup":
                return ToolResult(
                    tool_name="knowledge_lookup",
                    success=True,
                    data={"message": "Knowledge lookup delegated to retrieval pipeline"},
                )
            elif tool_name == "summarize_document":
                return await self._summarize(params.get("document_id", ""))
            else:
                return ToolResult(tool_name=tool_name, success=False, data=None, error="Unknown tool")
        except Exception as e:
            logger.error("tool_execution_failed", tool=tool_name, error=str(e))
            return ToolResult(tool_name=tool_name, success=False, data=None, error=str(e))

    async def run_agent(self, query: str, context: dict = None) -> dict:
        """
        Main agent loop:
        1. Determine tools to use
        2. Execute tools
        3. Synthesize results

        Returns dict with tool_calls and synthesized answer.
        """
        start_time = time.time()
        tools_to_use = await self.determine_tools(query)

        tool_results = []
        for tool_name in tools_to_use:
            result = await self.execute_tool(tool_name, {"query": query})
            tool_results.append(result.to_dict())

        latency_ms = int((time.time() - start_time) * 1000)

        return {
            "tools_used": tools_to_use,
            "tool_results": tool_results,
            "latency_ms": latency_ms,
        }

    async def _web_search(self, query: str) -> ToolResult:
        """
        Web search tool.

        COMMENTED OUT: Requires search API (Brave, Serper, etc.)
        """
        # ────────────────────────────────────────────────────
        # COMMENTED OUT: Actual web search
        # ────────────────────────────────────────────────────
        # import httpx
        # async with httpx.AsyncClient() as client:
        #     response = await client.get(
        #         "https://api.search.brave.com/res/v1/web/search",
        #         headers={"X-Subscription-Token": settings.brave_api_key},
        #         params={"q": query, "count": 5},
        #     )
        #     results = response.json()
        # ────────────────────────────────────────────────────

        return ToolResult(
            tool_name="web_search",
            success=True,
            data={
                "message": "Web search API not configured. Set BRAVE_API_KEY or SERPER_API_KEY.",
                "query": query,
                "results": [],
            },
        )

    async def _calculator(self, expression: str) -> ToolResult:
        """Safe calculator tool."""
        try:
            # Only allow safe math operations
            allowed = set("0123456789+-*/.() ")
            if not all(c in allowed for c in expression):
                return ToolResult(
                    tool_name="calculator",
                    success=False,
                    data=None,
                    error="Invalid expression: only numbers and +-*/() allowed",
                )
            result = eval(expression, {"__builtins__": {}}, {})  # noqa: S307
            return ToolResult(tool_name="calculator", success=True, data={"result": result})
        except Exception as e:
            return ToolResult(tool_name="calculator", success=False, data=None, error=str(e))

    async def _summarize(self, document_id: str) -> ToolResult:
        """
        Summarize a document.

        COMMENTED OUT: Requires LLM.
        """
        return ToolResult(
            tool_name="summarize_document",
            success=True,
            data={"message": "Summarization requires LLM. Set OPENAI_API_KEY."},
        )
