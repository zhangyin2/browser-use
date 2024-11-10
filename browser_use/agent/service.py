import json
import os
from typing import Any

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from pydantic import BaseModel

from browser_use.agent.prompts import AgentMessagePrompt, AgentSystemPrompt
from browser_use.agent.views import (
	AgentHistory,
	AgentOutput,
)
from browser_use.controller.service import ControllerService
from browser_use.controller.views import (
	ControllerAction,
	ControllerActionResult,
	ControllerPageState,
)
from browser_use.utils import logger, time_execution_async

load_dotenv()


class AgentService:
	def __init__(
		self,
		task: str,
		llm: BaseChatModel,
		controller: ControllerService | None = None,
		use_vision: bool = True,
		save_conversation_path: str | None = None,
		allow_terminal_input: bool = True,
		include_format: bool = True,
	):
		"""
		Agent service.

		Args:
			task (str): Task to be performed.
			llm (AvailableModel): Model to be used.
			controller (ControllerService | None): You can reuse an existing or (automatically) create a new one.
			allow_terminal_input (bool): Flag to allow or disallow terminal input to resolve uncertanty or if the agent is stuck.
			include_format (bool): Flag to always include the response format in the messages.
		"""
		self.task = task
		self.use_vision = use_vision
		self.allow_terminal_input = allow_terminal_input

		self.controller_injected = controller is not None
		self.controller = controller or ControllerService()

		self.llm = llm
		system_prompt = AgentSystemPrompt(
			task, default_action_description=ControllerAction._get_action_description()
		).get_system_message()

		# Init messages
		first_message = HumanMessage(content=f'Your task is: {task}')
		self.messages: list[BaseMessage] = [system_prompt, first_message]
		self.include_format = include_format
		self.n = 0

		self.save_conversation_path = save_conversation_path
		if save_conversation_path is not None:
			logger.info(f'Saving conversation to {save_conversation_path}')

		self.action_history: list[AgentHistory] = []

	async def run(self, max_steps: int = 100) -> tuple[ControllerActionResult, list[AgentHistory]]:
		"""
		Execute the task.

		@dev ctrl+c to interrupt
		"""

		try:
			logger.info('\n' + '=' * 50)
			logger.info(f'🚀 Starting task: {self.task}')
			logger.info('=' * 50)

			for i in range(max_steps):
				logger.info(f'\n📍 Step {i+1}')

				history_item, result = await self.step()

				if result.is_done:
					logger.info('\n✅ Task completed successfully')
					# logger.info(f'Extracted content: \n{result.extracted_content}')
					return result, self.action_history

			logger.info('\n' + '=' * 50)
			logger.info('❌ Failed to complete task in maximum steps')
			logger.info('=' * 50)
			return result, self.action_history
		finally:
			if not self.controller_injected:
				self.controller.browser.close()

	@time_execution_async('--step')
	async def step(self) -> tuple[AgentHistory, ControllerActionResult]:
		state = self.controller.get_current_state(screenshot=self.use_vision)
		action = await self.get_next_action(state)
		result = self.controller.act(action)

		if result.error:
			self.messages.append(
				HumanMessage(content=f'Error: {result.error}  stick to the rules and try again')
			)
			logger.debug(f'Trying again because of error: {result.error}')
		if result.extracted_content:
			self.messages.append(
				HumanMessage(content=f'Extracted content:\n {result.extracted_content}')
			)
		if result.human_input:
			self.messages.append(HumanMessage(content=f'Human input: {result.human_input}'))

		# Convert action to history and update click/input fields if present
		history_item = self._make_history_item(action, result)
		self.action_history.append(history_item)
		self.n += 1

		return history_item, result

	def _make_history_item(
		self, action: AgentOutput, result: ControllerActionResult
	) -> AgentHistory:
		# Create base history item
		history = AgentHistory(
			action_type=action.action_type,
			params=action.params,
			valuation=action.valuation,
			memory=action.memory,
			next_goal=action.next_goal,
			url=result.url,
			is_done=result.is_done,
			extracted_content=result.extracted_content,
			error=result.error,
			human_input=result.human_input,
			clicked_element=result.clicked_element,
			inputed_element=result.inputed_element,
		)

		return history

	@time_execution_async('--get_next_action')
	async def get_next_action(self, state: ControllerPageState) -> AgentOutput:
		new_message = AgentMessagePrompt(
			state, self.task, include_format=self.include_format
		).get_user_message()
		input_messages = self.messages + [new_message]
		structured_llm = self.llm.with_structured_output(AgentOutput, include_raw=True)

		# TODO: handle connection error
		response: dict[str, Any] | BaseModel = await structured_llm.ainvoke(input_messages)

		# include_raw = True -> dict
		if isinstance(response, dict):
			parsed_response: AgentOutput | None = response['parsed']
			raw_response = response['raw'].content
			parsing_error = response['parsing_error']

			if parsed_response is None:  # try to parse the raw response as Output
				try:
					parsed_response = AgentOutput.model_validate_json(raw_response)
				except Exception as e:
					raise ValueError(
						f'No parsed response from the model raw response: {raw_response} \n with parsing error: {parsing_error}'
					) from e
			if parsing_error:
				logger.debug(f'Parsing error in get_next_action: {parsing_error}')

		elif isinstance(response, AgentOutput):
			# include_raw = False -> BaseModel
			parsed_response = response

		# Only append the output message
		history_new_message = AgentMessagePrompt(state, self.task).get_message_for_history()
		self.messages.append(history_new_message)

		self.messages.append(HumanMessage(content=parsed_response.model_dump_json()))
		logger.info(f'Response: {parsed_response.model_dump_json(indent=2)}\n')
		self._save_conversation(input_messages, parsed_response)

		return parsed_response

	def _save_conversation(self, input_messages: list[BaseMessage], response: AgentOutput):
		if self.save_conversation_path is not None:
			os.makedirs(self.save_conversation_path, exist_ok=True)
			with open(self.save_conversation_path + f'_{self.n}.txt', 'w') as f:
				# Write messages with proper formatting
				for message in input_messages:
					f.write('=' * 33 + f' {message.__class__.__name__} ' + '=' * 33 + '\n\n')

					# Handle different content types
					if isinstance(message.content, list):
						# Handle vision model messages
						for item in message.content:
							if isinstance(item, dict) and item.get('type') == 'text':
								f.write(item['text'].strip() + '\n')
					elif isinstance(message.content, str):
						try:
							# Try to parse and format JSON content
							content = json.loads(message.content)
							f.write(json.dumps(content, indent=2) + '\n')
						except json.JSONDecodeError:
							# If not JSON, write as regular text
							f.write(message.content.strip() + '\n')

					f.write('\n')

				# Write final response as formatted JSON
				f.write('=' * 33 + ' Response ' + '=' * 33 + '\n\n')
				f.write(json.dumps(json.loads(response.model_dump_json()), indent=2))
