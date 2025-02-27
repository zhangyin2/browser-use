import pytest
from browser_use.omniparser.views import OmniParserSettings

def test_omniparser_settings_custom_values():
    """Test OmniParserSettings with custom non-default parameters."""
    settings = OmniParserSettings(
        enabled=True,
        confidence_threshold=0.8,
        weights_dir="/path/to/weights",
        prefer_over_dom=True,
        captcha_detection=False,
        merge_with_dom=False,
        use_api=True,
        api_key="dummy_api_key"
    )

    assert settings.enabled is True
    assert settings.confidence_threshold == 0.8
    assert settings.weights_dir == "/path/to/weights"
    assert settings.prefer_over_dom is True
    assert settings.captcha_detection is False
    assert settings.merge_with_dom is False
    assert settings.use_api is True
    assert settings.api_key == "dummy_api_key"
    
def test_omniparser_settings_default_values():
    """Test OmniParserSettings with default parameters."""
    default_settings = OmniParserSettings()
    
    assert default_settings.enabled is False
    assert default_settings.confidence_threshold == 0.5
    assert default_settings.weights_dir is None
    assert default_settings.prefer_over_dom is False
    assert default_settings.captcha_detection is True
    assert default_settings.merge_with_dom is True
    assert default_settings.use_api is False
    assert default_settings.api_key is None
def test_omniparser_settings_api_without_key():
    """Test OmniParserSettings when use_api is True but no api_key is provided."""
    settings = OmniParserSettings(use_api=True)
    assert settings.use_api is True
    assert settings.api_key is None
def test_omniparser_settings_mutability():
    """Test that OmniParserSettings attributes can be modified after creation."""
    settings = OmniParserSettings()
    settings.enabled = True
    settings.confidence_threshold = 0.9
    settings.weights_dir = "/updated/path"
    settings.prefer_over_dom = True
    settings.captcha_detection = False
    settings.merge_with_dom = False
    settings.use_api = True
    settings.api_key = "updated_api_key"
    assert settings.enabled is True
    assert settings.confidence_threshold == 0.9
    assert settings.weights_dir == "/updated/path"
    assert settings.prefer_over_dom is True
    assert settings.captcha_detection is False
    assert settings.merge_with_dom is False
    assert settings.use_api is True
    assert settings.api_key == "updated_api_key"