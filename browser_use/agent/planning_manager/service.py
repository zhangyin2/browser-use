from __future__ import annotations

import logging
from typing import Any, Optional, Type

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from browser_use.agent.planning_manager.views import TaskPlan
from browser_use.agent.views import (
	ActionResult,
	AgentError,
	AgentHistory,
	AgentHistoryList,
	AgentOutput,
	AgentStepInfo,
)

logger = logging.getLogger(__name__)


class PlanningManager:
	def __init__(
		self,
		llm: BaseChatModel,
		outputModel: Type[AgentOutput],
	):
		self.llm = llm
		self.outputModel = outputModel

	def _get_planning_system_prompt(self) -> SystemMessage:
		"""Get system prompt for task planning"""
		# get schema of the output model
		actions = self.outputModel.model_json_schema()['$defs']['ActionModel']['properties'].keys()
		logger.info(f'Available actions: {actions}')
		return SystemMessage(
			content=f"""You are a task planning assistant of browser_use. Your role is to:
Create a well-structured, clear version of the task

Do not invent any new things, only use the available actions.

Respond with the provided sturcture in JSON format.


After you browser_use will execute your plan he will start with an open browser, his available actions are:
- Available actions: {{actions}}


End with the done action there browser_use will provide the answer to the user

If the task is already a clear plan, just return it.
Otherwise, keep the reformulated task focused while maintaining all important details from the original task."""
		)

	def plan_task(self, raw_task: str) -> TaskPlan:
		"""Generate structured task plan from raw task description"""

		# Create messages for the LLM
		messages = [
			self._get_planning_system_prompt(),
			HumanMessage(content=f' {raw_task}'),
		]

		# Get structured output using TaskPlan model
		structured_llm = self.llm.with_structured_output(TaskPlan, include_raw=True)
		response: dict[str, Any] = structured_llm.invoke(messages)  # type: ignore
		task_plan: Optional[TaskPlan] = response['parsed']

		if task_plan is None:
			raise ValueError('Could not parse task plan response')

		logger.info(f'Generated task plan with difficulty {task_plan.estimated_difficulty}')
		logger.debug(f'Task tags: {", ".join(task_plan.tags)}')

		return task_plan
