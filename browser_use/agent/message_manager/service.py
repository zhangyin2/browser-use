from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional, Type

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
	AIMessage,
	BaseMessage,
	HumanMessage,
	SystemMessage,
	ToolMessage,
)
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from browser_use.agent.message_manager.views import MessageHistory, MessageMetadata
from browser_use.agent.prompts import SystemPrompt
from browser_use.agent.views import ActionResult, AgentOutput, AgentStepInfo
from browser_use.browser.context import BrowserContext
from browser_use.browser.views import BrowserState

logger = logging.getLogger(__name__)


class MessageManager:
	def __init__(
		self,
		task: str,
		action_descriptions: str,
		system_prompt_class: Type[SystemPrompt],
		include_attributes: list[str] = [],
		max_error_length: int = 200,
		max_num_of_msg_in_history: int = 15,
		use_vision: bool = True,
		max_actions_per_step: int = 10,
	):
		self.task = task
		self.include_attributes = include_attributes
		self.max_error_length = max_error_length
		self.max_num_of_msg_in_history = max_num_of_msg_in_history
		self.use_vision = use_vision

		# Initialize system prompt
		self.system_prompt = system_prompt_class(
			action_descriptions,
			current_date=datetime.now(),
			max_actions_per_step=max_actions_per_step,
		)

		# History tracking
		self.past_steps: list[tuple[AgentOutput, List[ActionResult]]] = []
		self.tool_call_id = 1

	def _format_results(self, results: List[ActionResult]) -> str:
		"""Format results into a message string"""
		message = ''
		for i, result in enumerate(results, 1):
			if result.extracted_content:
				message += f'\nAction result {i}/{len(results)}: {result.extracted_content}'
			if result.error:
				error = result.error[-self.max_error_length :]  # Only use last part of error
				message += f'\nAction error {i}/{len(results)}: ...{error}'
		return message

	@property
	def system_message(self) -> SystemMessage:
		return SystemMessage(content=self.system_prompt.get_system_message())

	@property
	def task_message(self) -> HumanMessage:
		return HumanMessage(
			content=f'Your ultimate task is: {self.task}. If you achieved your ultimate task, stop everything and use the done action in the next step to complete the task. If not, continue as usual.'
		)

	async def get_messages(
		self,
		state: BrowserState,
		current_results: Optional[List[ActionResult]] = None,
		step_info: Optional[AgentStepInfo] = None,
	) -> list[BaseMessage]:
		"""Get all messages for the next model call"""
		messages = []
		logger.debug('Building message sequence...')

		# 1. System message
		messages.append(self.system_message)
		logger.debug('Added system message')

		# 2. Task message
		messages.append(self.task_message)
		logger.debug('Added task message')

		# 3. Past steps with their results (limited by max_num_of_msg_in_history)
		recent_steps = self.past_steps[-self.max_num_of_msg_in_history :] if self.past_steps else []
		logger.debug(f'Processing {len(recent_steps)} recent steps')

		# If no past steps, add a placeholder tool call and response
		if not recent_steps:
			logger.debug('No past steps, adding placeholder tool call')
			messages.append(
				AIMessage(
					content='',
					tool_calls=[
						{
							'name': 'AgentOutput',
							'args': {
								'current_state': {
									'evaluation_previous_goal': 'Success - First step',
									'memory': 'Starting new task - need to break down goal into subtasks',
									'next_goal': 'Start with the first subtask',
									'todo_subtasks': 'Break down goal into subtasks',
									'completed_subtask': 'None',
									'confidence': 90,
								}
							},
							'id': '1',
							'type': 'tool_call',
						}
					],
				)
			)

			# Combine initial response and current results into a single tool message
			response_content = 'Starting new task'
			if current_results:
				result_msg = self._format_results(current_results)
				if result_msg:
					response_content += result_msg

			messages.append(
				ToolMessage(
					content=response_content,
					tool_call_id='1',
				)
			)
			last_tool_call_id = '1'
			logger.debug('Added placeholder tool call and combined response')
		else:
			last_tool_call_id = None
			for i, (output, results) in enumerate(recent_steps):
				current_id = str(i + 1)
				logger.debug(f'Processing step {i + 1} with tool call ID {current_id}')

				# Add tool call
				messages.append(
					AIMessage(
						content='',
						tool_calls=[
							{
								'name': 'AgentOutput',
								'args': output.model_dump(exclude_none=True),
								'id': current_id,
								'type': 'tool_call',
							}
						],
					)
				)

				# Combine memory results and current results into a single tool message
				response_content = 'No results'
				memory_results = [r for r in results if r.include_in_memory]
				if memory_results:
					response_content = self._format_results(memory_results)

				# Add current results if this is the last step
				if current_results and i == len(recent_steps) - 1:
					result_msg = self._format_results(current_results)
					if result_msg:
						if response_content == 'No results':
							response_content = result_msg
						else:
							response_content += result_msg

				messages.append(ToolMessage(content=response_content, tool_call_id=current_id))
				last_tool_call_id = current_id
				logger.debug(f'Added step {i + 1} messages with combined response')

		# 4. Current state with scroll info
		state_msg = await self._get_state_description(state, step_info)
		human_msg = (
			'This is the current page, give me the next action to reach my ultimate goal: \n'
			+ state_msg
		)

		if self.use_vision and state.screenshot:
			messages.append(
				HumanMessage(
					content=[
						{'type': 'text', 'text': human_msg},
						{
							'type': 'image_url',
							'image_url': {'url': f'data:image/png;base64,{state.screenshot}'},
						},
					]
				)
			)
		else:
			messages.append(HumanMessage(content=human_msg))

		# Debug log the entire message sequence
		logger.debug('Final message sequence:')
		for i, msg in enumerate(messages):
			logger.debug(f'  {i}: {msg.__class__.__name__}')
			if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls'):
				logger.debug(f'    tool_calls: {msg.tool_calls[0]["id"]}')
			if isinstance(msg, ToolMessage):
				logger.debug(f'    tool_call_id: {msg.tool_call_id}')

		return messages

	async def _get_state_description(
		self,
		state: BrowserState,
		step_info: Optional[AgentStepInfo] = None,
	) -> str:
		"""Get state description with scroll info if available"""
		# Add step info if available
		if step_info:
			step_info_description = (
				f'Current step: {step_info.step_number + 1}/{step_info.max_steps}'
			)
		else:
			step_info_description = ''

		# Get clickable elements and scroll info
		elements_text = state.element_tree.clickable_elements_to_string(
			include_attributes=self.include_attributes
		)

		# Only add cut-off message if there are pixels above or below viewport
		has_content_above = (state.pixels_above or 0) > 0
		has_content_below = (state.pixels_below or 0) > 0

		if elements_text != '':
			if has_content_above:
				elements_text = f'... {state.pixels_above} pixels above - scroll or extract content to see more ...\n{elements_text}'
			if has_content_below:
				elements_text = f'{elements_text}\n... {state.pixels_below} pixels below - scroll or extract content to see more ...'
		else:
			elements_text = 'empty page'

		# Basic state description
		state_description = f"""
{step_info_description}
Current url: {state.url}
Available tabs:
{state.tabs}
Interactive elements from current page view:
{elements_text}
		"""

		return state_description

	def add_interaction(
		self, model_output: AgentOutput, results: Optional[List[ActionResult]] = None
	):
		"""Add a new interaction to the history"""
		self.tool_call_id += 1
		self.past_steps.append((model_output, results or []))
