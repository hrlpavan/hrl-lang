"""
HRL Runtime Execution Context.
Author: Pavan Kumar Sadashiv (HRL International Pvt. Ltd.)
"""

from typing import Dict, Any, Optional, List


class RuntimeError(Exception):
    pass


class ExecutionContext:
    def __init__(self, parent: Optional['ExecutionContext'] = None):
        self.parent = parent
        self.variables: Dict[str, Any] = {}
        self.events: List[Dict[str, Any]] = []

    def create_child(self) -> 'ExecutionContext':
        return ExecutionContext(parent=self)

    def set(self, name: str, value: Any):
        self.variables[name] = value

    def get(self, name: str) -> Any:
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.get(name)
        raise RuntimeError(f"Undefined variable '{name}'")

    def has(self, name: str) -> bool:
        if name in self.variables:
            return True
        if self.parent:
            return self.parent.has(name)
        return False

    def emit_event(self, event_name: str, payload: Any):
        event = {"event": event_name, "payload": payload}
        self.events.append(event)
        if self.parent:
            self.parent.emit_event(event_name, payload)
