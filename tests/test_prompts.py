from unittest.mock import Mock, patch
from datetime import datetime
from browser_use.agent.prompts import AgentMessagePrompt
from browser_use.agent.views import AgentStepInfo
from browser_use.browser.views import BrowserState
from langchain_core.messages import HumanMessage


def test_agent_message_prompt_without_vision():
    """
    Test the AgentMessagePrompt's get_user_message method when use_vision is False.
    This test ensures that:
    1. The method returns a HumanMessage object
    2. The content is a string (not a list of dicts as in the vision case)
    3. The content includes all expected information from the BrowserState
    4. The datetime is correctly formatted in the output
    """
    # Mock BrowserState
    mock_state = Mock(spec=BrowserState)
    mock_state.url = "https://example.com"
    mock_state.tabs = ["Tab 1", "Tab 2"]
    mock_state.pixels_above = 100
    mock_state.pixels_below = 200
    mock_state.screenshot = None  # Not used when use_vision is False

    # Mock element_tree
    mock_element_tree = Mock()
    mock_element_tree.clickable_elements_to_string.return_value = "[1]<button>Click me</button>"
    mock_state.element_tree = mock_element_tree

    # Mock AgentStepInfo
    mock_step_info = Mock(spec=AgentStepInfo)
    mock_step_info.step_number = 2
    mock_step_info.max_steps = 5

    # Create AgentMessagePrompt instance
    prompt = AgentMessagePrompt(state=mock_state, step_info=mock_step_info)

    # Patch datetime.now() to return a fixed datetime
    mocked_datetime = datetime(2023, 1, 1, 12, 0)
    with patch('browser_use.agent.prompts.datetime') as mock_datetime:
        mock_datetime.now.return_value = mocked_datetime

        # Call get_user_message with use_vision=False
        message = prompt.get_user_message(use_vision=False)

    # Assertions
    assert isinstance(message, HumanMessage)
    assert isinstance(message.content, str)
    assert "Current url: https://example.com" in message.content
    assert "Available tabs:" in message.content
    assert "Tab 1" in message.content and "Tab 2" in message.content
    assert "[1]<button>Click me</button>" in message.content
    assert "100 pixels above" in message.content
    assert "200 pixels below" in message.content
    assert "Current step: 3/5" in message.content  # step_number + 1
    assert "Current date and time: 2023-01-01 12:00" in message.content
