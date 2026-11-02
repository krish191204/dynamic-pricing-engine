"""Base type for a specialist agent.

Every clerk is a subclass of Agent. `run` does the work. `note` appends
one line to agent_log so a successful run always has ten lines.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.context import RunContext


class Agent(ABC):
    name: str
    arena: str
    owner: str

    @abstractmethod
    def run(self, ctx: RunContext) -> RunContext:
        """Update ctx. Skip heavy work when ctx.failed is already set."""

    def note(self, ctx: RunContext, message: str) -> None:
        ctx.agent_log.append(f"{self.name}: {message}")
