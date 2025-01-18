from datetime import datetime
from typing import List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from browser_use.agent.views import ActionResult, AgentStepInfo
from browser_use.browser.views import BrowserState


class SystemPrompt:
	def __init__(
		self, action_description: str, current_date: datetime, max_actions_per_step: int = 10
	):
		self.default_action_description = action_description
		self.current_date = current_date
		self.max_actions_per_step = max_actions_per_step

	def important_rules(self) -> str:
		"""
		Returns the important rules for the agent.
		"""
		text = """

2. ACTIONS: You can specify multiple actions in the list to be executed in sequence. But always specify only one action name per item. 

   Common action sequences:
    - Form filling: action : [
       {"input_text": {"index": 1, "text": "username"}},
       {"input_text": {"index": 2, "text": "password"}},
       {"click_element": {"index": 3}}
     ]
   - Navigation and extraction: action : [
       {"open_new_tab": {}},
       {"go_to_url": {"url": "https://example.com"}},
       {"extract_page_content": {}}
     ]

3. ELEMENT INTERACTION:
   - Only use indexes that exist in the provided element list
   - Each element has a unique index number (e.g., "33[:]<button>")
   - Elements marked with "_[:]" are non-interactive (for context only)

4. NAVIGATION & ERROR HANDLING:
   - If no suitable interactive elements exist, use other functions to complete the task
   - If stuck, try alternative approaches
   - If popups block you, accept them

5. TASK COMPLETION:
   - Use the done action only when the task is completed. But also no step longer.
   - Don't hallucinate actions
   - If the task requires specific information - make sure to include everything in the done function. This is what the user will see.
   - If you are running out of steps (current step), think about speeding it up

6. VISUAL CONTEXT:
   - When an image is provided, use it to understand the page layout
   - Bounding boxes with labels correspond to element indexes
   - Each bounding box and its label have the same color
   - Most often the label is inside the bounding box, on the top right
   - Visual context helps verify element locations and relationships
   - sometimes labels overlap, so use the context to verify the correct element

7. Form filling:
   - If you fill an input field and your action sequence is interrupted, most often a list with suggestions popped up under the field and you need to first select the right element from the suggestion list.

8. ACTION SEQUENCING:
   - Actions are executed in the order they appear in the list 
   - Each action should logically follow from the previous one
   - If the page changes after an action, the sequence is interrupted and you get the new state.
   - If content only disappears the sequence continues.
   - Only provide the action sequence until you think the page will change.
   - Try to be efficient, e.g. fill forms at once, or chain actions where nothing changes on the page like saving, extracting, checkboxes...
   - only use multiple actions if it makes sense. 

"""
		text += f'   - use maximum {self.max_actions_per_step} actions per sequence'
		return text

	def input_format(self) -> str:
		return """

Your input is always:
 1. system message
 2. ultimate goal
 3. Summaries of previous steps
 4. your previous output with eval, memory, next goal and actions
 5. the result of the previous action (if any) with action result and errors
 6. the current state of the browser:
    - Current URL: The webpage you're currently on
    - Available Tabs: List of open browser tabs
    - Interactive Elements: List in the format:
      - index[:]<element_type>element_text</element_type>
      - index: Numeric identifier for interaction
      - element_type: HTML element type (button, input, etc.)
      - element_text: Visible text or element description
Example:
33[:]<button>Submit Form</button>
_[:] Non-interactive text

Notes:
- Only elements with numeric indexes are interactive
- _[:] elements provide context but cannot be interacted with

"""

	def get_system_message(self) -> str:
		"""
		Get the system prompt for the agent.

		Returns:
		    str: Formatted system prompt
		"""
		time_str = self.current_date.strftime('%Y-%m-%d %H:%M')

		AGENT_PROMPT = f"""You are a precise browser automation agent that interacts with websites through structured commands. Your role is to:
1. Analyze the provided webpage elements and structure
2. Plan a sequence of actions to accomplish the given task


Current date and time: {time_str}


{self.important_rules()}

{self.input_format()}

Your responses must be valid JSON matching the specified format. Each action in the sequence must be valid."""
		return AGENT_PROMPT


# Example:
# {self.example_response()}
# Your AVAILABLE ACTIONS:
# {self.default_action_description}


class AgentMessagePrompt:
	def __init__(
		self,
		state: BrowserState,
		result: Optional[List[ActionResult]] = None,
		include_attributes: list[str] = [],
		max_error_length: int = 400,
		step_info: Optional[AgentStepInfo] = None,
	):
		self.state = state
		self.result = result
		self.max_error_length = max_error_length
		self.include_attributes = include_attributes
		self.step_info = step_info

	def get_state_description(self) -> str:
		if self.step_info:
			step_info_description = (
				f'Current step: {self.step_info.step_number + 1}/{self.step_info.max_steps}'
			)
		else:
			step_info_description = ''

		elements_text = self.state.element_tree.clickable_elements_to_string(
			include_attributes=self.include_attributes
		)
		if elements_text != '':
			extra = '... Cut off - use extract content or scroll to get more ...'
			elements_text = f'{extra}\n{elements_text}\n{extra}'
		else:
			elements_text = 'empty page'

		state_description = f"""
{step_info_description}
Current url: {self.state.url}
Available tabs:
{self.state.tabs}
Interactive elements from current page view:
{elements_text}
		"""
		return state_description

	def get_result_and_error_description(self) -> str:
		result_and_error = ''
		if self.result:
			for i, result in enumerate(self.result):
				if result.extracted_content:
					result_and_error += (
						f'\nAction result {i + 1}/{len(self.result)}: {result.extracted_content}'
					)
				if result.error:
					# only use last x characters of error for the model
					error = result.error[-self.max_error_length :]
					result_and_error += f'\nAction error {i + 1}/{len(self.result)}: ...{error}'

		return result_and_error

	def get_user_message(self) -> str:
		return self.get_state_description() + self.get_result_and_error_description()
