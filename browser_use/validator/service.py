"""
Generic validation service for browser automation tasks.
"""

import json
from typing import Any, Dict, Optional, Tuple

from langchain_core.language_models import BaseLanguageModel

from browser_use.browser.views import BrowserState


class ValidationService:
	"""Service to validate if browser automation tasks were completed successfully"""

	def __init__(self, llm: BaseLanguageModel):
		self.llm = llm

	async def validate(
		self,
		task: str,
		state: BrowserState,
		result: Optional[str],
		context: Optional[Dict[str, Any]] = None,
	) -> Tuple[bool, str]:
		"""
		Validates if a task was completed successfully based on the final state
		and result.

		Args:
		    task: Original task description
		    state: Final state of the website
		    result: Result returned by the agent
		    context: Additional context for validation (optional)
				Can include:
				- expected_actions: List of expected actions
				- success_criteria: Specific criteria for success
				- website_data: Website-specific validation rules
				- custom_rules: Additional validation rules

		Returns:
		    tuple[bool, str]: (is_valid, reason)
		"""
		if result is None:
			return False, 'No result provided'

		prompt = self._build_validation_prompt(task, state, result, context)
		response = await self.llm.ainvoke({'content': prompt})

		try:
			# Parse JSON response
			validation_result = json.loads(response.content)
			is_valid = validation_result.get('is_valid', False)
			reason = validation_result.get('reason', 'No reason provided')
			return bool(is_valid), str(reason)
		except (json.JSONDecodeError, AttributeError):
			return False, 'Invalid validation response format'

	def _build_validation_prompt(
		self,
		task: str,
		state: BrowserState,
		result: str,
		context: Optional[Dict[str, Any]] = None,
	) -> str:
		"""
		Builds the validation prompt with flexible context support

		Args:
		    task: Task description
		    state: Browser state
		    result: Task result
		    context: Additional validation context
		"""
		prompt = [
			'You are a validation agent tasked with determining if a browser automation task was completed successfully.',
			'',
			f'Task: {task}',
			'',
			'Current website state:',
			str(state),
			'',
			'Task result:',
			str(result),
			'',
		]

		# Add context-specific validation criteria
		if context:
			if 'expected_actions' in context:
				prompt.extend(['Expected actions:', str(context['expected_actions']), ''])

			if 'success_criteria' in context:
				prompt.extend(['Success criteria:', str(context['success_criteria']), ''])

			if 'website_data' in context:
				prompt.extend(['Website-specific context:', str(context['website_data']), ''])

			if 'custom_rules' in context:
				prompt.extend(['Additional validation rules:', str(context['custom_rules']), ''])

		prompt.extend(
			[
				'Based on the above information, determine if the task was completed successfully.',
				'Respond with a JSON object containing:',
				'- is_valid: boolean indicating if task was successful',
				'- reason: detailed explanation of the validation decision',
				'',
				'Example response: {"is_valid": true, "reason": "Task completed successfully because..."}',
			]
		)

		return '\n'.join(prompt)

	async def validate_batch(
		self,
		tasks: list[Dict[str, Any]],
		states: list[BrowserState],
		results: list[Optional[str]],
		contexts: Optional[list[Dict[str, Any]]] = None,
	) -> list[Tuple[bool, str]]:
		"""
		Validate multiple tasks in batch

		Args:
		    tasks: List of task descriptions and metadata
		    states: List of final browser states
		    results: List of agent results
		    contexts: List of validation contexts (optional)

		Returns:
		    List of (is_valid, reason) tuples
		"""
		if contexts is None:
			contexts = [None] * len(tasks)

		validations = []
		for task_data, state, result, context in zip(tasks, states, results, contexts):
			# Extract task description from task data
			task = (
				task_data['confirmed_task']
				if isinstance(task_data, dict) and 'confirmed_task' in task_data
				else str(task_data)
			)

			# If task_data is a dict, merge it into context
			if isinstance(task_data, dict):
				merged_context = context or {}
				merged_context.update({k: v for k, v in task_data.items() if k != 'confirmed_task'})
			else:
				merged_context = context

			is_valid, reason = await self.validate(task, state, result, merged_context)
			validations.append((is_valid, reason))

		return validations
