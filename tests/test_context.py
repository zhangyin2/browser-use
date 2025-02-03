import pytest

from browser_use.browser.context import BrowserContext
from browser_use.dom.views import DOMElementNode

class TestBrowserContext:
    """Test suite for BrowserContext functionality."""

    def test_enhanced_css_selector_for_element(self):
        """
        Test that the enhanced CSS selector generator correctly converts a DOMElementNode
        with a given XPath that contains an index and with specified attributes (including a valid
        class and additional attributes) into the expected CSS selector string.
        """
        # Create a minimal DOMElementNode instance with a sample XPath and attributes.
        # The XPath "/html/body/div[2]/span" should be converted to:
        # "html > body > div:nth-of-type(2) > span"
        # and the attributes 'class', 'data-id', and 'name' should be appended accordingly.
        element = DOMElementNode(
            tag_name="span",
            is_visible=True,
            parent=None,
            xpath="/html/body/div[2]/span",
            attributes={"class": "my_class", "data-id": "123", "name": "test"},
            children=[],
        )
        # Arbitrary highlight index to avoid fallback in case
        element.highlight_index = 1

        # Call the class method to generate the enhanced CSS selector.
        result_selector = BrowserContext._enhanced_css_selector_for_element(element, include_dynamic_attributes=True)

        # The expected selector is:
        # "html > body > div:nth-of-type(2) > span.my_class[data-id="123"][name="test"]"
        expected_selector = 'html > body > div:nth-of-type(2) > span.my_class[data-id="123"][name="test"]'

        # Assert that the generated selector matches the expected output.
        assert result_selector == expected_selector