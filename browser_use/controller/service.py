from browser_use.browser.service import BrowserService
from browser_use.controller.views import (
	AVAILABLE_ACTIONS,
	ControllerAction,
	ControllerActionResult,
	ControllerPageState,
)
from browser_use.utils import time_execution_sync


class ControllerService:
	"""
	Controller service that interacts with the browser.

	Right now this is just a LLM friendly wrapper around the browser service.
	In the future we can add the functionality that this is a self-contained agent that can plan and act single steps.

	TODO: easy hanging fruit: pass in a list of actions, compare html that changed and self assess if goal is done -> makes clicking MUCH MUCH faster and cheaper.

	TODO#2: from the state generate functions that can be passed directly into the LLM as function calls. Then it could actually in the same call request for example multiple actions and new state.
	"""

	def __init__(self, keep_open: bool = False):
		self.browser = BrowserService(keep_open=keep_open)

	def get_current_state(self, screenshot: bool = False) -> ControllerPageState:
		return self.browser.get_current_state(screenshot=screenshot)

	@time_execution_sync('--act')
	def act(self, action: ControllerAction) -> ControllerActionResult:
		try:
			# Validate action exists in available actions
			if action.action_type not in AVAILABLE_ACTIONS:
				raise ValueError(f'Unknown action: {action.action_type}')

			# Get the method from browser service
			method = getattr(self.browser, action.action_type)

			# Call the method with the params
			result = method(**action.params)

			# Handle special return cases
			if action.action_type == 'done':
				return ControllerActionResult(done=True, extracted_content=result)
			elif action.action_type == 'extract_page_content':
				return ControllerActionResult(done=False, extracted_content=result)

			return ControllerActionResult(done=False)

		except Exception as e:
			return ControllerActionResult(done=False, error=f'Error executing action: {str(e)}')
