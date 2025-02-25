import pytest
from browser_use.agent.prompts import (
    AgentMessagePrompt,
    HumanMessage,
    PlannerPrompt,
    SystemMessage,
    SystemPrompt,
)
from datetime import (
    datetime,
)

try:
    from browser_use.browser.views import BrowserState
except ImportError:

    class BrowserState:
        pass


try:
    from browser_use.agent.views import AgentStepInfo
except ImportError:

    class AgentStepInfo:

        def __init__(self, step_number, max_steps):
            self.step_number = step_number
            self.max_steps = max_steps


try:
    DummyActionResult
except NameError:

    class DummyActionResult:
        """A dummy ActionResult to test inclusion of extracted content and errors in the state description."""

        def __init__(self, extracted_content, error):
            self.extracted_content = extracted_content
            self.error = error


class DummyElementTree:

    def clickable_elements_to_string(self, include_attributes):
        return "<button>Test Button</button>"


class DummyBrowserState:

    def __init__(self, screenshot="TEST_BASE64"):
        self.url = "http://example.com"
        self.tabs = "['tab1','tab2']"
        self.element_tree = DummyElementTree()
        self.pixels_above = 10
        self.pixels_below = 15
        self.screenshot = screenshot


def test_agent_message_prompt_with_screenshot():
    """
    Test that AgentMessagePrompt.get_user_message returns a vision-enabled message
    (i.e. a list containing text and image messages) when a valid screenshot is provided.
    """
    dummy_state = DummyBrowserState(screenshot="TEST_BASE64")
    prompt = AgentMessagePrompt(state=dummy_state)
    message = prompt.get_user_message(use_vision=True)
    assert isinstance(message, HumanMessage)
    assert isinstance(message.content, list)
    assert len(message.content) == 2
    text_message, image_message = message.content
    assert isinstance(text_message, dict)
    assert text_message.get("type") == "text"
    assert "Current url: http://example.com" in text_message.get("text")
    assert isinstance(image_message, dict)
    assert image_message.get("type") == "image_url"
    image_url = image_message.get("image_url", {}).get("url")
    assert image_url is not None
    assert image_url.startswith("data:image/png;base64,TEST_BASE64")


class DummyActionResult:
    """A dummy ActionResult to test inclusion of extracted content and errors in the state description."""

    def __init__(self, extracted_content, error):
        self.extracted_content = extracted_content
        self.error = error


def test_agent_message_prompt_without_vision():
    """
    Test that AgentMessagePrompt.get_user_message returns a plain text message (i.e., a string)
    when vision is disabled and no screenshot is provided, and that it properly includes action
    results and errors in the state description.
    """
    dummy_state = DummyBrowserState(screenshot=None)

    class DummyActionResult:

        def __init__(self, extracted_content, error):
            self.extracted_content = extracted_content
            self.error = error

    dummy_result = DummyActionResult("dummy result", "dummy error text")
    prompt = AgentMessagePrompt(state=dummy_state, result=[dummy_result])
    message = prompt.get_user_message(use_vision=False)
    assert isinstance(message, HumanMessage)
    assert isinstance(message.content, str)
    assert "Current url: http://example.com" in message.content
    assert "dummy result" in message.content
    assert "dummy error text" in message.content


def test_planner_prompt_get_system_message():
    """
    Test that PlannerPrompt.get_system_message returns a valid system message with planning instructions.
    """
    planner_prompt = PlannerPrompt("Dummy action description")
    system_message = planner_prompt.get_system_message()
    assert isinstance(system_message, SystemMessage)
    content = system_message.content
    assert "planning agent" in content
    assert "Analyze the current state and history" in content
    assert "state_analysis" in content
    assert "progress_evaluation" in content
    assert "challenges" in content
    assert "next_steps" in content
    assert "reasoning" in content


class DummyElementTreeEmpty:

    def clickable_elements_to_string(self, include_attributes):
        return ""


def test_agent_message_prompt_with_step_info():
    """
    Test that AgentMessagePrompt.get_user_message properly includes step info and indicates when the page is empty,
    as well as includes the current date and time.
    """
    dummy_state = DummyBrowserState(screenshot=None)
    dummy_state.element_tree = DummyElementTreeEmpty()
    step_info = AgentStepInfo(step_number=1, max_steps=3)
    prompt = AgentMessagePrompt(state=dummy_state, step_info=step_info)
    message = prompt.get_user_message(use_vision=False)
    assert isinstance(message, HumanMessage)
    assert isinstance(message.content, str)
    assert "empty page" in message.content
    assert "Current step: 2/3" in message.content
    assert "Current date and time:" in message.content


def test_agent_message_prompt_error_truncation():
    """
    Test that AgentMessagePrompt.get_user_message truncates long error messages according
    to the max_error_length parameter.
    """
    dummy_state = DummyBrowserState(screenshot=None)
    long_error = "0123456789ABCDEF"
    expected_truncated = long_error[-10:]
    dummy_result = DummyActionResult("error truncation test", long_error)
    prompt = AgentMessagePrompt(
        state=dummy_state, result=[dummy_result], max_error_length=10
    )
    message = prompt.get_user_message(use_vision=False)
    assert isinstance(message, HumanMessage)
    assert isinstance(message.content, str)
    assert expected_truncated in message.content


def test_system_prompt_includes_action_description():
    """
    Test that SystemPrompt.get_system_message returns a SystemMessage containing the default action description
    and that the important rules include the correct maximum actions per step.
    This ensures that the SystemPrompt builds its output correctly.
    """
    action_description = "dummy action description"
    max_actions = 5
    prompt = SystemPrompt(action_description, max_actions)
    system_message = prompt.get_system_message()
    assert isinstance(system_message, SystemMessage)
    content = system_message.content
    assert isinstance(content, str)
    assert action_description in content
    assert f"use maximum {max_actions} actions per sequence" in content


def test_system_prompt_input_format():
    """
    Test that SystemPrompt.input_format returns a string that describes the expected input structure.
    This ensures that the method correctly produces the help-text outlining the browser input details.
    """
    prompt = SystemPrompt("dummy action description", max_actions_per_step=5)
    input_format_text = prompt.input_format()
    assert "INPUT STRUCTURE:" in input_format_text
    assert "1. Current URL:" in input_format_text
    assert "2. Available Tabs:" in input_format_text
    assert "3. Interactive Elements:" in input_format_text
    assert "[33]<button>Submit Form</button>" in input_format_text
    assert "Non-interactive text" in input_format_text


def test_agent_message_prompt_no_scroll_markers():
    """
    Test that AgentMessagePrompt.get_user_message returns a plain text message with the correct
    start and end markers when no scrollable content exists (i.e., pixels_above and pixels_below are 0).
    This ensures that the message does not include additional scroll indicators when not needed.
    """
    dummy_state = DummyBrowserState(screenshot=None)
    dummy_state.pixels_above = 0
    dummy_state.pixels_below = 0

    class DummyElementTreeNonScroll:

        def clickable_elements_to_string(self, include_attributes):
            return "<button>Click me</button>"

    dummy_state.element_tree = DummyElementTreeNonScroll()
    prompt = AgentMessagePrompt(state=dummy_state)
    message = prompt.get_user_message(use_vision=False)
    assert isinstance(message, HumanMessage)
    assert isinstance(message.content, str)
    assert "[Start of page]" in message.content
    assert "[End of page]" in message.content
    assert "pixels above" not in message.content
    assert "pixels below" not in message.content


class DummyElementTreeWithAttributes:

    def clickable_elements_to_string(self, include_attributes):
        return f"<button attributes: {include_attributes}>Click me</button>"


class DummyBrowserStateWithAttributes:

    def __init__(self, screenshot=None, include_attributes=None):
        self.url = "http://example-attributes.com"
        self.tabs = "['tabA','tabB']"
        self.element_tree = DummyElementTreeWithAttributes()
        self.pixels_above = 5
        self.pixels_below = 5
        self.screenshot = screenshot


def test_agent_message_prompt_include_attributes():
    """
    Test that AgentMessagePrompt.get_user_message passes the include_attributes to the element_tree
    and that the returned content properly reflects those attributes.
    """
    include_attrs = ["data-test", "aria-label"]
    dummy_state = DummyBrowserStateWithAttributes(screenshot=None)
    prompt = AgentMessagePrompt(state=dummy_state, include_attributes=include_attrs)
    message = prompt.get_user_message(use_vision=False)
    assert isinstance(message, HumanMessage)
    assert isinstance(message.content, str)
    expected_fragment = f"<button attributes: {include_attrs}>Click me</button>"
    assert expected_fragment in message.content
