from langchain_core.messages import HumanMessage, SystemMessage

from browser_use.controller.views import ControllerAction, ControllerPageState


class AgentSystemPrompt:
	def __init__(self, task: str, default_action_description: str):
		self.task = task
		self.default_action_description = default_action_description

	@staticmethod
	def _get_response_format() -> str:
		return """
{
    "action_type": "action_name",    
    "params": {                      
        "param1": "value1"
    },
    "valuation": "Evaluation of the last goal, e.g. Failed to click x because ...", 
    "memory": "Your memory of the overall task, e.g. Found 3/10 results. 1. ... 2. ... 3. ...",   
    "next_goal": "Next single immediate goal achievable by the next action"        
}"""

	@staticmethod
	def _get_rules() -> str:
		return """
1. Only use index that exist in the input list (e.g. 33) for click_element and input_text
2. If you get stuck try it different ways, you can use extract_page_content, go_back, refresh_page or do a new search
3. Ask for human help only when completely stuck
4. Use extract_page_content followed by done action to complete task
5. If an image is provided, use it for context
6. ALWAYS respond in this RESPONSE FORMAT with valid JSON:
7. If the page is empty use actions to do searches or go directly to the url
8. If you are done with the task, use the done action with the final result of the task
9. In the valuation, always mention the evaluation of the last action
Remember: Choose EXACTLY ONE action per response. Invalid combinations or multiple actions will be rejected. Use exactly the parameters specified.

	"""

	@staticmethod
	def _get_example_response() -> str:
		return """
{
    "action_type": "click_element",
    "params": {
        "index": 44,
        "num_clicks": 1
    },
    "valuation": "Failed to click x because ...",
    "memory": "Found 3/10 results. 1. ... 2. ... 3. ...",
    "next_goal": "Click accept cookies button"
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
	- Clickable elements are numbered: "index: <button>Click me</button>" here the index is 33 
	- Context elements are marked with underscore: "_: <div>Context text</div>"

	Your RESPONSE FORMAT: 
	{AgentSystemPrompt._get_response_format()}

	Example:
	{AgentSystemPrompt._get_example_response()}

	AVAILABLE ACTIONS:
    {self.default_action_description}

	IMPORTANT RULES:
	{AgentSystemPrompt._get_rules()}
	Your task: {self.task}
    """
		return SystemMessage(content=AGENT_PROMPT)


class AgentMessagePrompt:
	def __init__(self, state: ControllerPageState, task: str, include_format: bool = False):
		self.state = state
		self.task = task
		self.include_format = include_format

	def get_user_message(self) -> HumanMessage:
		state_description = f"""
Current url: {self.state.url}
Available tabs:
{self.state.tab_infos}
Interactive elements:
{self.state.dom_items_to_string()}

        """

		if self.include_format:
			msg = f'Always answer in this format:\n{AgentSystemPrompt._get_response_format()}'
			msg += '\n AVAILABLE ACTIONS:\n'
			msg += f'{ControllerAction._get_action_description()}'
			msg += f'\nIMPORTANT RULES:\n{AgentSystemPrompt._get_rules()}'
			msg += f'\nYour task: {self.task}'
		state_description += msg

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
