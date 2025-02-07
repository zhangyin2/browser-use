import pytest
import asyncio
from types import SimpleNamespace
from unittest.mock import Mock, AsyncMock
from browser_use.browser.context import BrowserContext, BrowserSession
from browser_use.browser.views import BrowserState, BrowserError
from browser_use.dom.views import DOMElementNode
from unittest.mock import Mock
from browser_use.browser.context import BrowserContext
import os
import json
from unittest.mock import AsyncMock, Mock

def test_css_selector_generation():
    """
    Test the conversion of simple XPath expressions to CSS selectors and the generation of an enhanced CSS selector
    for a DOM element node. This verifies that the static methods _convert_simple_xpath_to_css_selector and
    _enhanced_css_selector_for_element produce the expected output.
    """
    # Test _convert_simple_xpath_to_css_selector with a sample XPath expression.
    xpath = "/html/body/div[1]/span[last()]"
    expected_css = "html > body > div:nth-of-type(1) > span:last-of-type"
    result_css = BrowserContext._convert_simple_xpath_to_css_selector(xpath)
    assert result_css == expected_css, f"Expected '{expected_css}', got '{result_css}'"
    
    # Test _enhanced_css_selector_for_element.
    dummy_node = DOMElementNode(
        tag_name="div",
        is_visible=True,
        parent=None,
        xpath="/html/div[2]",
        attributes={"class": "foo bar", "id": "myid"},
        children=[],
        highlight_index=1
    )
    enhanced_selector = BrowserContext._enhanced_css_selector_for_element(dummy_node, include_dynamic_attributes=True)
    expected_enhanced = 'html > div:nth-of-type(2).foo.bar[id="myid"]'
    assert enhanced_selector == expected_enhanced, f"Expected '{expected_enhanced}', got '{enhanced_selector}'"
def test_get_initial_state():
    """
    Test that _get_initial_state returns a BrowserState with an empty url when no page is provided
    and with the correct url when a dummy page is provided.
    """
    dummy_browser = Mock()
    ctx = BrowserContext(browser=dummy_browser)
    
    state_without_page = ctx._get_initial_state()
    assert state_without_page.url == "", "Expected empty url when no page is provided."
    assert state_without_page.title == "", "Expected empty title in initial state."
    assert state_without_page.screenshot is None, "Expected screenshot to be None."
    assert state_without_page.selector_map == {}, "Expected selector_map to be empty."
    assert state_without_page.tabs == [], "Expected tabs list to be empty."
    assert state_without_page.element_tree.tag_name == "root", "Expected root tag_name in element_tree."
    
    dummy_page = SimpleNamespace(url="https://example.com")
    state_with_page = ctx._get_initial_state(dummy_page)
    assert state_with_page.url == "https://example.com", "Expected the state's url to match dummy page's url."
@pytest.mark.asyncio
async def test_switch_to_invalid_tab():
    """
    Test that switching to an invalid tab index raises BrowserError.
    This simulates having a browser context with a single page and attempts to switch to a non-existent page index.
    """
    dummy_browser = Mock()
    ctx = BrowserContext(browser=dummy_browser)
    ctx.config.allowed_domains = None  # Disable domain restrictions for this test
    dummy_page = AsyncMock()
    dummy_page.url = "https://example.com"
    dummy_page.bring_to_front = AsyncMock()
    dummy_page.wait_for_load_state = AsyncMock()
    dummy_context = Mock()
    dummy_context.pages = [dummy_page]
    dummy_state = ctx._get_initial_state()
    ctx.session = BrowserSession(
        context=dummy_context,
        current_page=dummy_page,
        cached_state=dummy_state,
    )
    with pytest.raises(BrowserError) as exc_info:
        await ctx.switch_to_tab(5)
    
    assert "No tab found with page_id: 5" in str(exc_info.value)
@pytest.mark.asyncio
async def test_navigate_to_disallowed_url():
    """
    Test that navigate_to raises BrowserError when a URL is not allowed.
    The BrowserContext is configured with allowed_domains containing only "example.com".
    Attempting to navigate to "https://notallowed.com" should raise a BrowserError.
    """
    dummy_browser = Mock()
    ctx = BrowserContext(browser=dummy_browser)
    ctx.config.allowed_domains = ["example.com"]
    disallowed_url = "https://notallowed.com"
    with pytest.raises(BrowserError) as exc_info:
        await ctx.navigate_to(disallowed_url)
    assert disallowed_url in str(exc_info.value)
@pytest.mark.asyncio
async def test_execute_javascript():
    """
    Test that execute_javascript returns the expected result from page.evaluate.
    A dummy page is used to simulate the evaluate behavior.
    """
    # Create a dummy page with an AsyncMock for evaluate()
    dummy_page = AsyncMock()
    dummy_page.evaluate.return_value = "expected result"
    
    # Create a dummy browser context and assign dummy_page as the current page.
    dummy_context = Mock()
    dummy_context.pages = [dummy_page]
    dummy_browser = Mock()
    ctx = BrowserContext(browser=dummy_browser)
    
    # Set up session to have our dummy_page as current page.
    ctx.session = BrowserSession(
        context=dummy_context,
        current_page=dummy_page,
        cached_state=ctx._get_initial_state(dummy_page)
    )
    
    # Call execute_javascript and verify it returns the expected dummy evaluation result.
    result = await ctx.execute_javascript("return 1+1;")
    assert result == "expected result", f"Expected 'expected result', got {result}"
@pytest.mark.asyncio
async def test_reset_context():
    """
    Test that reset_context properly closes all existing pages, resets the cached state, and creates a new page.
    It verifies that each existing page's close() method is called and that the new page becomes the current page.
    """
    # Create dummy pages (simulate existing closed tabs)
    dummy_page1 = AsyncMock()
    dummy_page2 = AsyncMock()
    
    # Create a dummy new page to be returned by context.new_page()
    dummy_new_page = AsyncMock()
    dummy_new_page.wait_for_load_state = AsyncMock()
    
    # Create a dummy context with pages containing our two dummy pages and a new_page() method.
    dummy_context = Mock()
    dummy_context.pages = [dummy_page1, dummy_page2]
    dummy_context.new_page = AsyncMock(return_value=dummy_new_page)
    
    # Create a dummy BrowserContext, then assign a BrowserSession with the dummy_context.
    dummy_browser = Mock()
    ctx = BrowserContext(browser=dummy_browser)
    initial_state = ctx._get_initial_state()
    ctx.session = BrowserSession(
        context=dummy_context,
        current_page=dummy_page1,
        cached_state=initial_state,
    )
    
    # Call reset_context - this should close all pages and create a new page.
    await ctx.reset_context()
    
    # Verify that close() was called on each of the old pages.
    dummy_page1.close.assert_awaited_once()
    dummy_page2.close.assert_awaited_once()
    
    # Verify that new_page() was called and its result is set as the new current_page.
    dummy_context.new_page.assert_awaited_once()
    session = await ctx.get_session()
    assert session.current_page == dummy_new_page, "Expected the new page to be set as current_page"
    
    # Verify that the cached state is reset to an initial state.
    new_state = session.cached_state
    assert new_state.url == "", "Expected the reset cached state's url to be empty"
    assert new_state.title == "", "Expected the reset cached state's title to be empty"
    assert new_state.screenshot is None, "Expected the reset cached state's screenshot to be None"
    assert new_state.selector_map == {}, "Expected the reset cached state's selector_map to be empty"
    assert new_state.tabs == [], "Expected the reset cached state's tabs to be empty"
    assert new_state.element_tree.tag_name == "root", "Expected the element_tree to have tag_name 'root'"
@pytest.mark.asyncio
async def test_is_file_uploader():
    """
    Test that is_file_uploader correctly identifies file uploader elements.
    It verifies:
    - that an input element with type 'file' is detected as a file uploader,
    - that an input element with type 'text' is not detected as a file uploader,
    - and that an element containing a descendant input of type 'file' is detected as a file uploader.
    """
    dummy_browser = Mock()
    ctx = BrowserContext(browser=dummy_browser)
    
    # Test direct file input node.
    file_input_node = DOMElementNode(
        tag_name="input",
        is_visible=True,
        parent=None,
        xpath="/html/body/input[1]",
        attributes={"type": "file"},
        children=[],
        highlight_index=0,
    )
    is_uploader = await ctx.is_file_uploader(file_input_node)
    assert is_uploader is True, "Expected direct file input node to be identified as file uploader."
    
    # Test non-file input node.
    text_input_node = DOMElementNode(
        tag_name="input",
        is_visible=True,
        parent=None,
        xpath="/html/body/input[2]",
        attributes={"type": "text"},
        children=[],
        highlight_index=1,
    )
    is_uploader = await ctx.is_file_uploader(text_input_node)
    assert is_uploader is False, "Expected text input node not to be identified as file uploader."
    
    # Test nested structure where a descendant is a file uploader.
    child_uploader = DOMElementNode(
        tag_name="input",
        is_visible=True,
        parent=None,
        xpath="/html/body/div/input[1]",
        attributes={"type": "file"},
        children=[],
        highlight_index=2,
    )
    parent_node = DOMElementNode(
        tag_name="div",
        is_visible=True,
        parent=None,
        xpath="/html/body/div",
        attributes={},
        children=[child_uploader],
        highlight_index=3,
    )
    # Set the child's parent pointer for completeness.
    child_uploader.parent = parent_node
    
    is_uploader = await ctx.is_file_uploader(parent_node)
    assert is_uploader is True, "Expected parent node with a descendant file input to be identified as file uploader."
@pytest.mark.asyncio
async def test_close_tracing_and_cookies(tmp_path):
    """
    Test the close() method when both trace_path and cookies_file are set.
    The test verifies that:
      - The tracing.stop method is called with the correct file path.
      - Cookies are saved to the specified cookies_file.
      - The context.close() method is awaited.
      - The session is reset to None after closing.
    """
    # Create temporary files for cookies and tracing
    cookies_file = tmp_path / "cookies.json"
    trace_dir = tmp_path / "trace"
    trace_dir.mkdir()
    
    # Create a dummy browser and configure BrowserContext settings
    dummy_browser = Mock()
    ctx = BrowserContext(browser=dummy_browser)
    ctx.config.cookies_file = str(cookies_file)
    ctx.config.trace_path = str(trace_dir)
    
    # Create a dummy page and dummy context that supports cookies,
    # tracing.stop and close operations.
    dummy_page = AsyncMock()
    dummy_page.url = "https://example.com"
    dummy_context = AsyncMock()
    dummy_context.cookies = AsyncMock(return_value=[{"name": "test", "value": "dummy"}])
    dummy_tracing = AsyncMock()
    dummy_tracing.stop = AsyncMock()
    dummy_context.tracing = dummy_tracing
    dummy_context.close = AsyncMock()
    dummy_context.pages = [dummy_page]
    
    # Initialize a BrowserSession and assign it to the context
    initial_state = ctx._get_initial_state(dummy_page)
    ctx.session = BrowserSession(
        context=dummy_context,
        current_page=dummy_page,
        cached_state=initial_state,
    )
    
    # Call close and verify correct behavior
    await ctx.close()
    
    # Verify that the tracing.stop was called with the proper file path
    expected_trace_file = os.path.join(ctx.config.trace_path, f"{ctx.context_id}.zip")
    dummy_tracing.stop.assert_awaited_once_with(path=expected_trace_file)
    
    # Verify that the context.close() method was called
    dummy_context.close.assert_awaited_once()
    
    # Verify that cookies were saved to file
    # Wait a moment to ensure file writing finishes.
    assert cookies_file.exists(), "Cookies file was not created."
    with open(cookies_file, 'r') as f:
        saved_cookies = json.load(f)
        assert isinstance(saved_cookies, list)
        assert any(cookie.get("name") == "test" for cookie in saved_cookies), "Saved cookies do not match expected data."
    
    # Verify that the session is set to None
    assert ctx.session is None, "Expected the session to be None after closing."
@pytest.mark.asyncio
async def test_refresh_page():
    """
    Test that refresh_page reloads the current page and waits for it to finish loading.
    This ensures that page.reload() and page.wait_for_load_state() are both called.
    """
    # Create a dummy browser and a dummy page with expected async methods.
    dummy_browser = Mock()
    dummy_page = AsyncMock()
    dummy_page.reload = AsyncMock()
    dummy_page.wait_for_load_state = AsyncMock()
    dummy_page.url = "https://example.com"
    
    # Create a dummy context with the dummy_page in its pages list.
    dummy_context = Mock()
    dummy_context.pages = [dummy_page]
    
    # Initialize a BrowserContext and assign a BrowserSession using the dummy context and page.
    ctx = BrowserContext(browser=dummy_browser)
    initial_state = ctx._get_initial_state(dummy_page)
    ctx.session = BrowserSession(
        context=dummy_context,
        current_page=dummy_page,
        cached_state=initial_state,
    )
    
    # Call refresh_page() and verify that the page methods were called as expected.
    await ctx.refresh_page()
    dummy_page.reload.assert_awaited_once()
    dummy_page.wait_for_load_state.assert_awaited_once()