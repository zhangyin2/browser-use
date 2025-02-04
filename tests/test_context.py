from browser_use.browser.context import BrowserContext, BrowserContextConfig
import pytest
from unittest.mock import MagicMock




def test_is_url_allowed():
    """
    Test the _is_url_allowed method of BrowserContext with various URL scenarios.
    This test ensures that the method correctly filters URLs based on the configured allowed domains.
    """
    # Mock the Browser class
    mock_browser = MagicMock()

    # Create a BrowserContextConfig with specific allowed domains
    config = BrowserContextConfig(allowed_domains=["example.com", "test.com"])

    # Create a BrowserContext instance
    context = BrowserContext(mock_browser, config)

    # Test cases
    assert context._is_url_allowed("https://example.com") == True
    assert context._is_url_allowed("http://example.com") == True
    assert context._is_url_allowed("https://subdomain.example.com") == True
    assert context._is_url_allowed("https://test.com") == True
    assert context._is_url_allowed("https://example.org") == False
    assert context._is_url_allowed("https://malicious.com") == False
    assert context._is_url_allowed("http://test.com:8080") == True
    assert context._is_url_allowed("https://example.com/path/to/page") == True

    # Test with no allowed domains (should allow all)
    unrestricted_config = BrowserContextConfig(allowed_domains=None)
    unrestricted_context = BrowserContext(mock_browser, unrestricted_config)
    assert unrestricted_context._is_url_allowed("https://any-domain.com") == True
