from typing import Dict, Type

from core.interfaces.review_chain import ReviewChain
from core.interfaces.review_formatter import ReviewFormatter
from core.interfaces.review_tool import ReviewTool


class ComponentRegistry:
    """Registry for pluggable components."""

    def __init__(self):
        self._chains: Dict[str, Type[ReviewChain]] = {}
        self._formatters: Dict[str, Type[ReviewFormatter]] = {}
        self._tools: Dict[str, Type[ReviewTool]] = {}

    def register_chain(self, name: str, chain_class: Type[ReviewChain]):
        """Register a review chain class."""
        if not issubclass(chain_class, ReviewChain):
            raise TypeError(f"Class {chain_class.__name__} must inherit from ReviewChain")
        self._chains[name] = chain_class

    def register_formatter(self, name: str, formatter_class: Type[ReviewFormatter]):
        """Register a formatter class."""
        if not issubclass(formatter_class, ReviewFormatter):
            raise TypeError(f"Class {formatter_class.__name__} must inherit from ReviewFormatter")
        self._formatters[name] = formatter_class

    def register_tool(self, name: str, tool_class: Type[ReviewTool]):
        """Register a tool class."""
        if not issubclass(tool_class, ReviewTool):
            raise TypeError(f"Class {tool_class.__name__} must inherit from ReviewTool")
        self._tools[name] = tool_class

    def create_chain(self, name: str, *args, **kwargs) -> ReviewChain:
        """Create an instance of a registered chain."""
        if name not in self._chains:
            raise ValueError(f"Chain '{name}' not registered")
        return self._chains[name](*args, **kwargs)

    def create_formatter(self, name: str, *args, **kwargs) -> ReviewFormatter:
        """Create an instance of a registered formatter."""
        if name not in self._formatters:
            raise ValueError(f"Formatter '{name}' not registered")
        return self._formatters[name](*args, **kwargs)

    def create_tool(self, name: str, *args, **kwargs) -> ReviewTool:
        """Create an instance of a registered tool."""
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not registered")
        return self._tools[name](*args, **kwargs)


# Global registry instance
registry = ComponentRegistry()
