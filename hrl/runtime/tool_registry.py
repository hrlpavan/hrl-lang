"""
HRL Tool Registry and Reachability Safety Filter.
Author: Pavan Kumar Sadashiv (HRL International Pvt. Ltd.)
"""

import asyncio
from typing import Dict, Any, Callable, List, Optional
from hrl.ast_nodes import ToolDefNode


class GuardViolationError(Exception):
    pass


class ToolRegistry:
    def __init__(self):
        self.definitions: Dict[str, ToolDefNode] = {}
        self.implementations: Dict[str, Callable] = {}

    def register_def(self, tool_def: ToolDefNode):
        self.definitions[tool_def.name] = tool_def

    def register_impl(self, name: str, func: Callable):
        self.implementations[name] = func

    async def call_tool(self, name: str, kwargs: Dict[str, Any], guard_evaluator: Optional[Callable] = None) -> Any:
        if name not in self.definitions and name not in self.implementations:
            raise KeyError(f"Tool '{name}' is not registered")

        tool_def = self.definitions.get(name)

        # Check guards if any
        if tool_def and tool_def.guards and guard_evaluator:
            for guard_expr in tool_def.guards:
                passed = guard_evaluator(guard_expr, kwargs)
                if not passed:
                    raise GuardViolationError(f"Reachability guard violated for tool '{name}' with arguments {kwargs}")

        impl = self.implementations.get(name)
        if not impl:
            # Return synthetic structured result for simulation/dry-run
            return {
                "status": "success",
                "tool": name,
                "input": kwargs,
                "output": f"Simulated output from tool '{name}' with args {kwargs}"
            }

        timeout = (tool_def.timeout_ms / 1000.0) if (tool_def and tool_def.timeout_ms) else None

        if asyncio.iscoroutinefunction(impl):
            if timeout:
                return await asyncio.wait_for(impl(**kwargs), timeout=timeout)
            return await impl(**kwargs)
        else:
            return impl(**kwargs)
