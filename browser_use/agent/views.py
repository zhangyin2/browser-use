from pydantic import Field

from browser_use.controller.views import ControllerAction, ControllerActionResult


class AgentOutput(ControllerAction):
	valuation: str = Field(
		description='Valuation of last action, e.g. "Failed to click x because ..."'
	)
	memory: str = Field(
		description='Memory of the overall task, e.g. "Found 3/10 results. 1. ... 2. ... 3. ..."'
	)
	next_goal: str = Field(description='Next concrete immediate goal achievable by the next action')


class AgentHistory(AgentOutput, ControllerActionResult):  # ControllerPageState
	pass
