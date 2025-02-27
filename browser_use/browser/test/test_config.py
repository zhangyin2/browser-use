import pytest
from browser_use.browser.config import BrowserExtractionConfig
from browser_use.omniparser.views import OmniParserSettings

def test_browser_extraction_config_default_values():
    """
    Test that BrowserExtractionConfig initializes with default values:
    - The omniparser field is an instance of OmniParserSettings.
    - The use_hybrid_extraction flag is False.
    """
    config = BrowserExtractionConfig()
    assert isinstance(config.omniparser, OmniParserSettings)
    assert config.use_hybrid_extraction is False
def test_browser_extraction_config_custom_values():
    """
    Test that BrowserExtractionConfig correctly assigns custom values when provided.
    """
    # Create a custom OmniParserSettings instance (using the default constructor for demonstration)
    custom_omni = OmniParserSettings()
    # Instantiate BrowserExtractionConfig with custom values
    config = BrowserExtractionConfig(omniparser=custom_omni, use_hybrid_extraction=True)
    # Assert that the custom values are correctly assigned
    assert config.omniparser is custom_omni
    assert config.use_hybrid_extraction is True
def test_browser_extraction_config_default_factory_creates_distinct_instances():
    """
    Test that each instantiation of BrowserExtractionConfig produces a distinct
    instance of OmniParserSettings via the default_factory.
    """
    instance1 = BrowserExtractionConfig()
    instance2 = BrowserExtractionConfig()
    # Ensure that their omniparser instances are not the same object.
    assert instance1.omniparser is not instance2.omniparser
def test_browser_extraction_config_mutability():
    """
    Test that BrowserExtractionConfig fields are mutable after initialization.
    This includes modifying the 'use_hybrid_extraction' flag and the 'omniparser' instance.
    """
    config = BrowserExtractionConfig()
    original_omni = config.omniparser
    # Modify the use_hybrid_extraction flag from its default False to True.
    config.use_hybrid_extraction = not config.use_hybrid_extraction
    # Replace the omniparser instance with a new one.
    new_omni = OmniParserSettings()
    config.omniparser = new_omni
    # Assert that the fields have been updated accordingly.
    assert config.use_hybrid_extraction is True  # since the default was False
    assert config.omniparser is new_omni
    # Confirm that the new omniparser instance is distinct from the original.
    assert original_omni is not new_omni