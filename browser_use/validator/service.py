"""
Generic validation service for browser automation tasks.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Sequence, Tuple

from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import HumanMessage

from browser_use.browser.views import BrowserState

logger = logging.getLogger(__name__)


class ValidationService:
	"""Service to validate if browser automation tasks were completed successfully"""

	def __init__(self, llm: BaseLanguageModel):
		self.llm = llm

	async def validate(
		self,
		task: str,
		state: BrowserState,
		result: Optional[str],
		expected_actions: Optional[Sequence[str]] = None,
	) -> Tuple[bool, str]:
		"""
		Validates if a task was completed successfully based on the final state
		and result.

		Args:
		    task: Original task description
		    state: Final state of the website
		    result: Result returned by the agent
		    expected_actions: List of expected actions (optional)

		Returns:
		    tuple[bool, str]: (is_valid, reason)
		"""
		if result is None:
			return False, 'No result provided'

		prompt = self._build_validation_prompt(task, state, result, expected_actions)

		# Create a message for the LLM
		message = HumanMessage(content=prompt)
		response = await self.llm.ainvoke([message])

		try:
			# Parse JSON response
			validation_result = json.loads(response.content)
			is_valid = validation_result.get('is_valid', False)
			reason = validation_result.get('reason', 'No reason provided')
			return bool(is_valid), str(reason)
		except (json.JSONDecodeError, AttributeError) as e:
			logger.error(f'Failed to parse validation response: {e}')
			return False, 'Invalid validation response format'

	def _build_validation_prompt(
		self,
		task: str,
		state: BrowserState,
		result: str,
		expected_actions: Optional[Sequence[str]] = None,
	) -> str:
		"""
		Builds the validation prompt

		Args:
		    task: Task description
		    state: Browser state
		    result: Task result
		    expected_actions: Expected sequence of actions
		"""
		# Extract website from task if available
		website = None
		if 'go to' in task.lower():
			# Try to extract website from task
			words = task.lower().split()
			try:
				idx = words.index('to') + 1
				if idx < len(words):
					website = words[idx].strip('.,')
			except ValueError:
				pass

		prompt = [
			'You are a validation agent tasked with determining if a browser automation task was completed successfully.',
			'',
			f'Task: {task}',
		]

		if website:
			prompt.extend([f'Target Website: {website}', ''])

		prompt.extend(
			[
				'Current website state:',
				str(state),
				'',
				'Task result:',
				str(result),
				'',
			]
		)

		if expected_actions:
			prompt.extend(
				[
					'Expected sequence of actions:',
					*[f'- {action}' for action in expected_actions],
					'',
				]
			)

		prompt.extend(
			[
				'Based on the above information, determine if the task was completed successfully.',
				'Consider:',
				'1. Was the correct website accessed?',
				'2. Were all required actions completed?',
				'3. Does the final state match the task requirements?',
				'4. Was the task completed successfully?',
				'',
				'Respond with a JSON object: {"is_valid": boolean, "reason": "detailed explanation"}',
			]
		)

		return '\n'.join(prompt)

	async def validate_batch(
		self,
		tasks: List[Dict[str, Any]],
		states: List[BrowserState],
		results: List[Optional[str]],
	) -> List[Tuple[bool, str]]:
		"""
		Validate multiple tasks in batch

		Args:
		    tasks: List of task descriptions and metadata
		    states: List of final browser states
		    results: List of agent results

		Returns:
		    List of (is_valid, reason) tuples
		"""
		validations = []
		for task_data, state, result in zip(tasks, states, results):
			# Extract task description and actions
			task = (
				task_data['confirmed_task']
				if isinstance(task_data, dict) and 'confirmed_task' in task_data
				else str(task_data)
			)

			expected_actions = (
				task_data.get('action_reprs') if isinstance(task_data, dict) else None
			)

			is_valid, reason = await self.validate(task, state, result, expected_actions)
			validations.append((is_valid, reason))

		return validations
