"""BaseTool + ToolResult — abstract interface for all tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ToolResult:
    """Standardized result returned by any tool."""
    success: bool = True
    data: dict = field(default_factory=dict)
    error: str | None = None


class BaseTool(ABC):
    """
    Abstract tool interface.

    Every tool has a name and description (for LLM to understand what it does),
    and an async execute() method.

    Subclasses should set `name` and `description` as class attributes.
    """

    name: str = "base_tool"
    description: str = "Abstract base tool"

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters. Returns ToolResult."""
        ...

    def to_dict(self) -> dict:
        """Serialize tool metadata for LLM context."""
        return {
            "name": self.name,
            "description": self.description,
        }
