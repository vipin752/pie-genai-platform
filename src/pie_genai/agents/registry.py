from __future__ import annotations

from pie_genai.agents.base import Agent


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, Agent] = {}

    def register(self, agent: Agent) -> None:
        self._agents[agent.spec.id] = agent

    def get(self, agent_id: str) -> Agent | None:
        return self._agents.get(agent_id)

    def list(self) -> list[Agent]:
        return list(self._agents.values())

    def ids(self) -> frozenset[str]:
        return frozenset(self._agents.keys())
