"""ToolRegistry — manages available tools, lets LLM choose which to use."""

from __future__ import annotations

import logging

from app.tools.base import BaseTool

logger = logging.getLogger("crawler.tools.registry")


class ToolRegistry:
    """
    Registry of available tools.

    Usage:
        registry = ToolRegistry()
        registry.register(PlaywrightTool())
        registry.register(HttpTool())

        tool = registry.get("playwright")
        result = await tool.execute(url="https://example.com")

        # For LLM: get descriptions of all tools
        descriptions = registry.describe_all()
    """

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool by its name."""
        self._tools[tool.name] = tool
        logger.debug("Registered tool: %s", tool.name)

    def get(self, name: str) -> BaseTool | None:
        """Get a tool by name. Returns None if not found."""
        return self._tools.get(name)

    def list_names(self) -> list[str]:
        """Return all registered tool names."""
        return list(self._tools.keys())

    def describe_all(self) -> list[dict]:
        """Return metadata for all tools (for LLM context)."""
        return [t.to_dict() for t in self._tools.values()]

    def describe_all_text(self) -> str:
        """Return a text summary of all tools (for LLM prompts)."""
        lines = []
        for t in self._tools.values():
            lines.append(f"- {t.name}: {t.description}")
        return "\n".join(lines)


def create_default_registry() -> ToolRegistry:
    """Create a registry with all built-in tools pre-registered."""
    from app.tools.http_tool import HttpTool
    from app.tools.playwright_tool import PlaywrightTool
    from app.tools.screenshot_tool import ScreenshotTool
    from app.tools.search_tool import GoogleSearchTool
    from app.tools.stealth_tool import StealthBrowserTool

    registry = ToolRegistry()
    registry.register(HttpTool())
    registry.register(PlaywrightTool())
    registry.register(StealthBrowserTool())
    registry.register(GoogleSearchTool())
    registry.register(ScreenshotTool())

    logger.info(
        "Default registry created with %d tools: %s",
        len(registry.list_names()),
        ", ".join(registry.list_names()),
    )
    return registry
