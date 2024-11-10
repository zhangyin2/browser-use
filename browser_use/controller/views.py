from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from browser_use.browser.views import BrowserState


class ActionDefinition(BaseModel):
	"""Defines a single action and its parameters"""

	description: str
	params: dict[str, str] = Field(
		default_factory=dict, description='Parameter name to description mapping'
	)


# Define available actions
AVAILABLE_ACTIONS: Dict[str, ActionDefinition] = {
	'search_google': ActionDefinition(
		description='Search Google for a query', params={'query': 'The search terms to use'}
	),
	'click_element': ActionDefinition(
		description='Click on a page element',
		params={
			'index': 'Index of the element to click from the list of interactive elements',
			'num_clicks': 'Number of clicks (optional, default: 1)',
		},
	),
	'input_text': ActionDefinition(
		description='Input text into a field',
		params={
			'index': 'Index of the input element from the list of interactive elements',
			'input_text': 'Text to enter',
		},
	),
	'go_back': ActionDefinition(description='Go back to the previous page', params={}),
	'extract_page_content': ActionDefinition(description='Get the page content', params={}),
	'open_new_tab': ActionDefinition(
		description='Open a new tab', params={'url': 'The URL to navigate to'}
	),
	'switch_tab': ActionDefinition(
		description='Switch to a tab',
		params={'handle': 'The handle of the existing tab to switch to'},
	),
	'done': ActionDefinition(
		description='Call this when you are done with the task and want to return the result',
		params={'text': 'Final result of the task'},
	),
	'ask_human': ActionDefinition(
		description='Ask for human help / information / clarification',
		params={'text': 'Question to ask'},
	),
}


class ControllerAction(BaseModel):
	"""The actual action to execute"""

	action_type: str = Field(
		description=f'Type of action to perform from {list(AVAILABLE_ACTIONS.keys())}'
	)
	params: dict[str, Any] = Field(default_factory=dict, description='Parameters for the action')

	@staticmethod
	def _get_action_description() -> str:
		"""Get action descriptions from AVAILABLE_ACTIONS"""
		descriptions = []
		for action_name, action_def in AVAILABLE_ACTIONS.items():
			desc = [f'\n{action_name}: {action_def.description}']
			if action_def.params:
				desc.append('  Parameters:')
				for param, param_desc in action_def.params.items():
					desc.append(f'    - {param}: {param_desc}')
			descriptions.append('\n'.join(desc))
		return '\n'.join(descriptions)


class ClickElementControllerHistoryItem(BaseModel):
	xpath: str | None
	id: int | None
	num_clicks: int | None


class InputTextControllerHistoryItem(BaseModel):
	xpath: str | None
	id: int | None
	input_text: str | None


class ControllerActionResult(BaseModel):
	url: Optional[str] = None
	is_done: bool = False
	extracted_content: Optional[str] = None
	error: Optional[str] = None
	human_input: Optional[str] = None
	clicked_element: Optional[ClickElementControllerHistoryItem] = None
	inputed_element: Optional[InputTextControllerHistoryItem] = None


class ControllerPageState(BrowserState):
	screenshot: Optional[str] = None
