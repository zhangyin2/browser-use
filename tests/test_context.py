from browser_use.browser.context import BrowserContext, BrowserContextConfig
from unittest.mock import patch, MagicMock
import pytest
@pytest.mark.asyncio
async def test_is_url_allowed():
    """
    Test the _is_url_allowed method of BrowserContext.
    
    This test checks if the method correctly allows or disallows URLs based on the
    allowed_domains configuration. It tests various scenarios including:
    1. Allowed domain
    2. Subdomain of allowed domain
    3. Different domain (not allowed)
    4. Empty allowed_domains list (all domains allowed)
    """
    # Create a config with allowed domains
    config = BrowserContextConfig(allowed_domains=['example.com', 'test.com'])
    
    # Create a mock Browser instance
    mock_browser = MagicMock()
    
    # Create a BrowserContext instance
    browser_context = BrowserContext(mock_browser, config)
    
    # Test allowed domain
    assert browser_context._is_url_allowed('https://example.com/page') == True
    
    # Test subdomain of allowed domain
    assert browser_context._is_url_allowed('https://subdomain.example.com/page') == True
    
    # Test different domain (not allowed)
    assert browser_context._is_url_allowed('https://notallowed.com/page') == False
    
    # Test with empty allowed_domains (all domains should be allowed)
    browser_context.config.allowed_domains = []
    assert browser_context._is_url_allowed('https://any-domain.com/page') == True
