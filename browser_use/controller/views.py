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
			'index': 'ID of the element to click',
			'num_clicks': 'Number of clicks (optional, default: 1)',
		},
	),
	'input_text': ActionDefinition(
		description='Input text into a field',
		params={'index': 'ID of the input element', 'input_text': 'Text to enter'},
	),
	'nothing': ActionDefinition(description='Do nothing', params={}),
	'go_to_url': ActionDefinition(
		description='Navigate to a URL', params={'url': 'The URL to navigate to'}
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
		description='Complete the task', params={'text': 'Final result of the task'}
	),
	'ask_human': ActionDefinition(
		description='Ask for human help / information', params={'text': 'Question to ask'}
	),
}


class ControllerAction(BaseModel):
	"""The actual action to execute"""

	action_type: str = Field(
		description=f'Type of action to perform from {list(AVAILABLE_ACTIONS.keys())}'
	)
	params: dict[str, Any] = Field(default_factory=dict, description='Parameters for the action')


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
