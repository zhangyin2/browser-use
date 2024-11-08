from langchain_core.messages import HumanMessage, SystemMessage

from browser_use.controller.views import ControllerPageState


class AgentSystemPrompt:
	def __init__(self, task: str, default_action_description: str):
		self.task = task
		self.default_action_description = default_action_description

	def _get_response_format(self) -> str:
		return """
{
    "action_type": "action_name",    
    "params": {                      
        "param1": "value1",
        "param2": "value2"
    },
    "valuation": "Valuation of last action, e.g. Failed to click x because ...", 
    "memory": "Memory of the overall task, e.g. Found 3/10 results. 1. ... 2. ... 3. ...",   
    "next_goal": "Next concrete immediate goal achievable by the next action"        
}"""

	def _get_example_response(self) -> str:
		return """
{
    "action_type": "click_element",
    "params": {
        "index": 44,
        "num_clicks": 1
    },
    "valuation": "Successfully clicked the element accept cookies",
    "memory": "Found 3/10 results. 1. ... 2. ... 3. ...",
    "next_goal": "Click the first result with title '..."
}"""

	def get_system_message(self) -> SystemMessage:
		"""
		Get the system prompt for the agent.

		Returns:
		    str: Formatted system prompt
		"""

		AGENT_PROMPT = f"""
    
	You are an expert AI agent that interacts with websites for users. You get a task as input and must interact with the internet until the task is complete.
	You receive a list of interactive elements from the current webpage and must respond with one specific action.

	INPUT FORMAT:
	- You get processed html elements from the current webpage
	- Clickable elements are numbered: "33: <button>Click me</button>"
	- Context elements are marked with underscore: "_: <div>Context text</div>"

	Your RESPONSE FORMAT: 
	{self._get_response_format()}

	Example:
	{self._get_example_response()}

	AVAILABLE ACTIONS:
    {self.default_action_description}


	IMPORTANT RULES:
	1. Only use element IDs that exist in the input list
	3. If stuck, you can extract_page_content, go_back, refresh_page, or ask for human help
	4. Ask for human help only when completely stuck
	5. Use extract_page_content followed by done action to complete task
	6. If an image is provided, use it for context
	7. ALWAYS respond in this RESPONSE FORMAT with valid JSON:
	8. If the page is empty use actions to do searches or go directly to the url

	Remember: Choose EXACTLY ONE action per response. Invalid combinations or multiple actions will be rejected. Use exactly the parameters specified.
    """
		return SystemMessage(content=AGENT_PROMPT)


class AgentMessagePrompt:
	def __init__(self, state: ControllerPageState):
		self.state = state

	def get_user_message(self) -> HumanMessage:
		state_description = f"""
Current url: {self.state.url}
Available tabs:
{self.state.tab_infos}
Interactive elements:
{self.state.dom_items_to_string()}
        """

		if self.state.screenshot:
			# Format message for vision model
			return HumanMessage(
				content=[
					{'type': 'text', 'text': state_description},
					{
						'type': 'image_url',
						'image_url': {'url': f'data:image/png;base64,{self.state.screenshot}'},
					},
				]
			)

		return HumanMessage(content=state_description)

	def get_message_for_history(self) -> HumanMessage:
		if self.state.url in ['data:,', 'about:blank', '']:
			return HumanMessage(content=f'Step url: {self.state.url} (empty page)')
		else:
			return HumanMessage(content=f'Step url: {self.state.url}')
