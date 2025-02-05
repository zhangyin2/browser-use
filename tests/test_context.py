import pytest
from unittest.mock import MagicMock
from browser_use.browser.context import BrowserContext, BrowserContextConfig

def test_is_url_allowed():
    """
    Test the _is_url_allowed method of BrowserContext.
    
    This test covers:
    1. Allowing all URLs when no allowed_domains are specified.
    2. Allowing exact domain matches.
    3. Allowing subdomains of allowed domains.
    4. Disallowing unrelated domains.
    5. Handling URLs with ports.
    """
    # Mock the Browser class
    mock_browser = MagicMock()
    
    # Create a BrowserContextConfig with allowed domains
    config = BrowserContextConfig(allowed_domains=['example.com', 'test.com'])
    
    # Create a BrowserContext instance
    context = BrowserContext(mock_browser, config)
    
    # Test case 1: No allowed domains specified
    context.config.allowed_domains = None
    assert context._is_url_allowed('https://any-domain.com') == True
    
    # Reset allowed domains
    context.config.allowed_domains = ['example.com', 'test.com']
    
    # Test case 2: Exact domain match
    assert context._is_url_allowed('https://example.com') == True
    assert context._is_url_allowed('http://test.com') == True
    
    # Test case 3: Subdomain match
    assert context._is_url_allowed('https://subdomain.example.com') == True
    assert context._is_url_allowed('https://another.sub.test.com') == True
    
    # Test case 4: Unrelated domain
    assert context._is_url_allowed('https://unrelated.com') == False
    
    # Test case 5: URL with port
    assert context._is_url_allowed('https://example.com:8080') == True
    assert context._is_url_allowed('http://test.com:443') == True
    assert context._is_url_allowed('https://unrelated.com:8080') == False

def test_convert_simple_xpath_to_css_selector():
    """
    Test the _convert_simple_xpath_to_css_selector method of BrowserContext.
    
    This test covers:
    1. Converting a simple XPath with tag names.
    2. Converting XPath with numeric indices.
    3. Converting XPath with the last() function.
    4. Converting XPath with the position() function.
    5. Converting a complex XPath with multiple levels and indices.
    """
    # Test case 1: Simple XPath with tag names
    assert BrowserContext._convert_simple_xpath_to_css_selector('/html/body/div') == 'html > body > div'
    
    # Test case 2: XPath with numeric index
    assert BrowserContext._convert_simple_xpath_to_css_selector('/html/body/div[2]') == 'html > body > div:nth-of-type(2)'
    
    # Test case 3: XPath with last() function
    assert BrowserContext._convert_simple_xpath_to_css_selector('/html/body/div[last()]') == 'html > body > div:last-of-type'
    
    # Test case 4: XPath with position() function
    assert BrowserContext._convert_simple_xpath_to_css_selector('/html/body/div[position()>1]') == 'html > body > div:nth-of-type(n+2)'
    
    # Test case 5: Complex XPath with multiple levels and indices
    complex_xpath = '/html/body/div[2]/span[last()]/a[position()>1]'
    expected_css = 'html > body > div:nth-of-type(2) > span:last-of-type > a:nth-of-type(n+2)'
    assert BrowserContext._convert_simple_xpath_to_css_selector(complex_xpath) == expected_css
