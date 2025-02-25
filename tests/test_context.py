import asyncio
import json
import os
import pytest
from browser_use.browser.context import (
    BrowserContext,
    BrowserContextConfig,
    BrowserError,
    URLNotAllowedError,
)
from browser_use.dom.views import (
    DOMElementNode,
)
from unittest.mock import (
    AsyncMock,
    Mock,
)


@pytest.mark.asyncio
async def test_navigate_to_disallowed_url():
    """
    Test that when navigating to a non-allowed URL, the BrowserContext
    raises a BrowserError. We simulate the browser, context and page using mocks.
    """
    fake_playwright_browser = AsyncMock()
    fake_playwright_browser.contexts = []
    fake_browser_context = AsyncMock()
    fake_page = AsyncMock()
    fake_page.goto = AsyncMock()
    fake_page.wait_for_load_state = AsyncMock()
    fake_browser_context.new_page.return_value = fake_page
    fake_browser_context.pages = [fake_page]
    fake_browser_context.tracing = AsyncMock()
    fake_browser = AsyncMock()
    fake_browser.get_playwright_browser.return_value = fake_playwright_browser
    fake_browser.new_context = AsyncMock(return_value=fake_browser_context)
    fake_browser.config = Mock()
    fake_browser.config.cdp_url = None
    fake_browser.config.chrome_instance_path = None
    config = BrowserContextConfig(allowed_domains=["example.com"])
    context_obj = BrowserContext(browser=fake_browser, config=config)
    await context_obj.__aenter__()
    disallowed_url = "http://disallowed.com"
    with pytest.raises(
        BrowserError, match=f"Navigation to non-allowed URL: {disallowed_url}"
    ):
        await context_obj.navigate_to(disallowed_url)
    await context_obj.close()


def test_enhanced_css_selector_for_element():
    """
    Test that the enhanced CSS selector is generated correctly from a DOMElementNode.
    This verifies that the XPath conversion, class appending and safe attribute handling work as expected.
    """
    dummy_element = DOMElementNode(
        tag_name="span",
        is_visible=True,
        parent=None,
        xpath="/div/span[1]",
        attributes={"class": "foo bar", "id": "my-id", "data-id": "123"},
        children=[],
    )
    result = BrowserContext._enhanced_css_selector_for_element(
        dummy_element, include_dynamic_attributes=True
    )
    expected_selector = 'div > span:nth-of-type(1).foo.bar[id="my-id"][data-id="123"]'
    assert result == expected_selector
