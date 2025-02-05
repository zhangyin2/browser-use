from unittest.mock import Mock
from langchain_core.messages import HumanMessage
from browser_use.agent.prompts import AgentMessagePrompt
from browser_use.browser.views import BrowserState
def test_agent_message_prompt_without_vision():
    """
    Test AgentMessagePrompt.get_user_message method when use_vision is False
    and there's content above and below the visible area.
    """
    # Mock ElementTree
    class MockElementTree:
        def clickable_elements_to_string(self, include_attributes=None):
            return "Mock elements"

    # Mock BrowserState
    state = BrowserState(
        url="https://example.com",
        tabs=["Tab 1", "Tab 2"],
        element_tree=MockElementTree(),
        pixels_above=100,
        pixels_below=200,
        screenshot=None,
        selector_map={},  # Add empty selector_map
        title="Example Page"  # Add a title
    )
    
    # Create AgentMessagePrompt instance
    agent_prompt = AgentMessagePrompt(state)
    
    # Call get_user_message with use_vision=False
    message = agent_prompt.get_user_message(use_vision=False)
    
    # Assert that the message is a HumanMessage
    assert isinstance(message, HumanMessage)
    
    # Check for expected content in the message
    assert "Current url: https://example.com" in message.content
    assert "Available tabs:" in message.content
    assert "Tab 1" in message.content
    assert "Tab 2" in message.content
    assert "... 100 pixels above - scroll or extract content to see more ..." in message.content
    assert "... 200 pixels below - scroll or extract content to see more ..." in message.content
    assert "Mock elements" in message.content
    
    # Ensure that the screenshot is not included when use_vision is False
    assert "image_url" not in message.content
