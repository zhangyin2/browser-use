"""
Tests for the hybrid extractor.
"""

import base64
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from browser_use.dom.views import DOMElementNode, DOMState
from browser_use.dom.history_tree_processor.view import CoordinateSet, Coordinates, ViewportInfo
from browser_use.omniparser.hybrid_extractor import HybridExtractor
from browser_use.omniparser.views import OmniParserSettings


class TestHybridExtractor(unittest.TestCase):
    """Tests for the HybridExtractor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the DOM service
        self.dom_service = MagicMock()
        self.dom_service.page = MagicMock()
        
        # Create sample DOM state for testing
        self.sample_dom_state = DOMState(
            element_tree=DOMElementNode(
                tag_name="body",
                xpath="/body",
                attributes={},
                children=[
                    DOMElementNode(
                        tag_name="div",
                        xpath="/body/div",
                        attributes={"id": "test-div"},
                        children=[],
                        is_visible=True,
                        is_interactive=True,
                        is_top_element=True,
                        is_in_viewport=True,
                        highlight_index=1,
                        shadow_root=False,
                        parent=None,
                        page_coordinates=CoordinateSet(
                            top_left=Coordinates(x=100, y=100),
                            top_right=Coordinates(x=300, y=100),
                            bottom_left=Coordinates(x=100, y=150),
                            bottom_right=Coordinates(x=300, y=150),
                            center=Coordinates(x=200, y=125),
                            width=200,
                            height=50
                        )
                    )
                ],
                is_visible=True,
                is_interactive=False,
                is_top_element=False,
                is_in_viewport=True,
                highlight_index=0,
                shadow_root=False,
                parent=None,
                page_coordinates=CoordinateSet(
                    top_left=Coordinates(x=0, y=0),
                    top_right=Coordinates(x=1280, y=0),
                    bottom_left=Coordinates(x=0, y=720),
                    bottom_right=Coordinates(x=1280, y=720),
                    center=Coordinates(x=640, y=360),
                    width=1280,
                    height=720
                )
            ),
            selector_map={
                0: "body",
                1: "#test-div"
            }
        )
        
        # Mock DOM service get_clickable_elements method
        self.dom_service.get_clickable_elements = AsyncMock(return_value=self.sample_dom_state)
        
        # Sample screenshot
        self.sample_screenshot = b"test_screenshot_data"
        self.dom_service.page.screenshot = AsyncMock(return_value=self.sample_screenshot)
        
        # Sample OmniParser results
        self.sample_omni_elements = [
            {
                "x": 150,
                "y": 150,
                "width": 100,
                "height": 30,
                "element_type": "button",
                "text": "Click Me",
                "confidence": 0.95
            },
            {
                "x": 300,
                "y": 300,
                "width": 150,
                "height": 40,
                "element_type": "checkbox",
                "text": "I am not a robot",
                "confidence": 0.89
            }
        ]
    
    @patch("browser_use.omniparser.service.OmniParserService")
    @patch("browser_use.omniparser.captcha.CaptchaDetector")
    async def test_get_elements_dom_only(self, mock_captcha_detector, mock_omniparser_service):
        """Test getting elements with DOM-only mode."""
        # Create settings with OmniParser disabled
        settings = OmniParserSettings(enabled=False)
        
        # Create the hybrid extractor
        extractor = HybridExtractor(self.dom_service, settings)
        
        # Get elements
        result = await extractor.get_elements()
        
        # Verify that only DOM extraction was used
        self.dom_service.get_clickable_elements.assert_called_once()
        self.assertEqual(result, self.sample_dom_state)
        
        # Verify OmniParser was not used
        mock_omniparser_service.return_value.detect_interactive_elements.assert_not_called()
    
    @patch("browser_use.omniparser.service.OmniParserService")
    @patch("browser_use.omniparser.captcha.CaptchaDetector")
    async def test_get_elements_with_omniparser_prefer(self, mock_captcha_detector, mock_omniparser_service):
        """Test getting elements with OmniParser preferred over DOM."""
        # Create settings with OmniParser enabled and preferred
        settings = OmniParserSettings(enabled=True, prefer_over_dom=True)
        
        # Create the hybrid extractor
        extractor = HybridExtractor(self.dom_service, settings)
        
        # Mock OmniParser service
        omniparser_mock = mock_omniparser_service.return_value
        omniparser_mock.create_dom_state_from_screenshot = AsyncMock(return_value=self.sample_dom_state)
        
        # Get elements
        result = await extractor.get_elements()
        
        # Verify that both extraction methods were used
        self.dom_service.get_clickable_elements.assert_called_once()
        omniparser_mock.create_dom_state_from_screenshot.assert_called_once()
        
        # Verify OmniParser result was used
        self.assertEqual(result, self.sample_dom_state)
    
    @patch("browser_use.omniparser.service.OmniParserService")
    @patch("browser_use.omniparser.captcha.CaptchaDetector")
    async def test_get_elements_with_captcha_detection(self, mock_captcha_detector, mock_omniparser_service):
        """Test getting elements with CAPTCHA detection enabled."""
        # Create settings with CAPTCHA detection enabled
        settings = OmniParserSettings(enabled=True, captcha_detection=True)
        
        # Create the hybrid extractor
        extractor = HybridExtractor(self.dom_service, settings)
        
        # Mock CAPTCHA detector
        captcha_detector_mock = mock_captcha_detector.return_value
        captcha_detector_mock.detect_captchas = AsyncMock(return_value=self.sample_omni_elements)
        captcha_detector_mock.enhance_dom_with_captchas = MagicMock(return_value=self.sample_dom_state)
        
        # Get elements
        result = await extractor.get_elements()
        
        # Verify that CAPTCHA detection was used
        captcha_detector_mock.detect_captchas.assert_called_once()
        captcha_detector_mock.enhance_dom_with_captchas.assert_called_once()
        
        # Verify the enhanced DOM was returned
        self.assertEqual(result, self.sample_dom_state)
    
    @patch("browser_use.omniparser.service.OmniParserService")
    @patch("browser_use.omniparser.captcha.CaptchaDetector")
    async def test_get_elements_with_merge(self, mock_captcha_detector, mock_omniparser_service):
        """Test getting elements with merging enabled."""
        # Create settings with merging enabled
        settings = OmniParserSettings(enabled=True, merge_with_dom=True)
        
        # Create the hybrid extractor
        extractor = HybridExtractor(self.dom_service, settings)
        
        # Mock OmniParser service
        omniparser_mock = mock_omniparser_service.return_value
        omniparser_mock.detect_interactive_elements = AsyncMock(return_value=self.sample_omni_elements)
        
        # Create a spy for _merge_with_dom
        original_merge = extractor._merge_with_dom
        merge_spy = MagicMock(side_effect=original_merge)
        extractor._merge_with_dom = merge_spy
        
        # Get elements
        result = await extractor.get_elements()
        
        # Verify that merging was used
        omniparser_mock.detect_interactive_elements.assert_called_once()
        merge_spy.assert_called_once()
        
        # The result should be the merged result
        self.assertEqual(merge_spy.return_value, result)

    @patch("browser_use.omniparser.service.OmniParserService")
    @patch("browser_use.omniparser.captcha.CaptchaDetector")
    async def test_get_elements_with_exception(self, mock_captcha_detector, mock_omniparser_service):
        """Test that an exception in OmniParser extraction yields a fallback to the DOM-based state."""
        # Create settings with OmniParser enabled and preferred so that the OmniParser branch is taken.
        settings = OmniParserSettings(enabled=True, prefer_over_dom=True)
        # Create the hybrid extractor
        extractor = HybridExtractor(self.dom_service, settings)
        
        # Set up OmniParserService.create_dom_state_from_screenshot to raise an exception
        omniparser_mock = mock_omniparser_service.return_value
        omniparser_mock.create_dom_state_from_screenshot = AsyncMock(side_effect=Exception("Test exception"))
        
        # Get elements; should catch the exception and return the DOM state
        result = await extractor.get_elements()
        
        # Verify that the DOM service was called and the fallback DOM state is returned
        self.dom_service.get_clickable_elements.assert_called_once()
        self.assertEqual(result, self.sample_dom_state)

    @patch("browser_use.omniparser.service.OmniParserService")
    @patch("browser_use.omniparser.captcha.CaptchaDetector")
    async def test_get_elements_with_captcha_detection_no_result(self, mock_captcha_detector, mock_omniparser_service):
        """Test getting elements with CAPTCHA detection enabled but no CAPTCHA found."""
        # Create settings with CAPTCHA detection enabled, but without prefer_over_dom or merge_with_dom enabled
        settings = OmniParserSettings(enabled=True, captcha_detection=True)
        extractor = HybridExtractor(self.dom_service, settings)

        # Set up the CAPTCHA detector to return an empty list for detect_captchas
        captcha_detector_mock = mock_captcha_detector.return_value
        captcha_detector_mock.detect_captchas = AsyncMock(return_value=[])
        captcha_detector_mock.enhance_dom_with_captchas = MagicMock()

        # Get elements; since no captchas were detected, it should fallback to the DOM state
        result = await extractor.get_elements()

        # Verify that CAPTCHA detection was attempted but no enhancement occurred
        captcha_detector_mock.detect_captchas.assert_called_once()
        captcha_detector_mock.enhance_dom_with_captchas.assert_not_called()
        # Verify that the result is the initial DOM state returned by the DOM service
        self.assertEqual(result, self.sample_dom_state)
    @patch("browser_use.omniparser.service.OmniParserService")
    @patch("browser_use.omniparser.captcha.CaptchaDetector")
    async def test_get_elements_enabled_default(self, mock_captcha_detector, mock_omniparser_service):
        """Test getting elements with OmniParser enabled in default mode (no merging, no preference, no captcha)
        ensuring that the original DOM-based state is returned."""
        # Create settings with OmniParser enabled but with all extra options off
        settings = OmniParserSettings(enabled=True, prefer_over_dom=False, merge_with_dom=False, captcha_detection=False)
        extractor = HybridExtractor(self.dom_service, settings)
        
        # Set up the OmniParser service mocks to ensure they are not used in the default case
        omniparser_mock = mock_omniparser_service.return_value
        omniparser_mock.create_dom_state_from_screenshot = AsyncMock()
        omniparser_mock.detect_interactive_elements = AsyncMock()
        
        # Invoke the extraction process
        result = await extractor.get_elements()
        
        # Verify that the DOM service was called once
        self.dom_service.get_clickable_elements.assert_called_once()
        
        # Verify that none of the OmniParser methods were called since no special option is enabled
        omniparser_mock.create_dom_state_from_screenshot.assert_not_called()
        omniparser_mock.detect_interactive_elements.assert_not_called()
        
        # The result should be the initial DOM state provided by dom_service.get_clickable_elements
        self.assertEqual(result, self.sample_dom_state)
    
    @patch("browser_use.omniparser.service.OmniParserService")
    @patch("browser_use.omniparser.captcha.CaptchaDetector")
    async def test_merge_with_missing_dom_tree(self, mock_captcha_detector, mock_omniparser_service):
        """Test merging behavior when the initial DOM state has no element tree,
        forcing the creation of a default body element and merging the OmniParser results."""
        # Create settings with merging enabled
        settings = OmniParserSettings(enabled=True, merge_with_dom=True)
        
        # Create a DOMState with no element_tree and an empty selector_map
        from browser_use.dom.views import DOMState
        custom_dom_state = DOMState(
            element_tree=None,
            selector_map={}
        )
        self.dom_service.get_clickable_elements = AsyncMock(return_value=custom_dom_state)
        
        # Setup OmniParser to return one omni element that won't overlap (since no tree exists)
        new_omni_element = {
            "x": 500,
            "y": 500,
            "width": 50,
            "height": 50,
            "element_type": "link",
            "text": "New Link",
            "confidence": 0.9
        }
        omniparser_mock = mock_omniparser_service.return_value
        omniparser_mock.detect_interactive_elements = AsyncMock(return_value=[new_omni_element])
        
        # Create the hybrid extractor with the modified DOM service and settings
        extractor = HybridExtractor(self.dom_service, settings)
        
        # Invoke the extraction process
        result = await extractor.get_elements()
        
        # Verify that a new DOM tree was created (a body element)
        self.assertIsNotNone(result.element_tree)
        self.assertEqual(result.element_tree.tag_name, "body")
        
        # Verify that the omni element was added as a new child of the body element
        self.assertEqual(len(result.element_tree.children), 1)
        added_element = result.element_tree.children[0]
        self.assertEqual(added_element.attributes.get("data-omniparser-detected"), "true")
        self.assertEqual(added_element.attributes.get("data-omniparser-type"), "link")
        
        # Verify that the selector_map was updated with the new element's highlight index
        self.assertIn(added_element.highlight_index, result.selector_map)
    async def test_merge_overlapping_and_non_overlapping(self):
        """Test merging behavior for overlapping OmniParser elements and non-overlapping ones.
        The overlapping element should update attributes, while the non-overlapping element
        should be added as a new DOM element.
        """
        # Create two OmniParser elements: one overlapping with the existing div and one separate.
        omni_overlap = {
            "x": 150, "y": 110, "width": 50, "height": 20,
            "element_type": "input", "text": "Overlap", "confidence": 0.8
        }
        omni_non_overlap = {
            "x": 500, "y": 500, "width": 40, "height": 40,
            "element_type": "link", "text": "New Link", "confidence": 0.9
        }
        # Create settings with merging enabled.
        settings = OmniParserSettings(enabled=True, merge_with_dom=True)
        extractor = HybridExtractor(self.dom_service, settings)
        # Call _merge_with_dom directly on the sample DOM state and our two OmniParser elements.
        merged_state = extractor._merge_with_dom(self.sample_dom_state, [omni_overlap, omni_non_overlap])
        # Verify that the overlapping OmniParser element updated the existing DOM element.
        overlapping_updated = False
        for child in merged_state.element_tree.children:
            if child.xpath == "/body/div":
                self.assertEqual(child.attributes.get("data-omniparser-detected"), "true")
                self.assertEqual(child.attributes.get("data-omniparser-type"), "input")
                self.assertEqual(child.attributes.get("data-omniparser-confidence"), "0.8")
                overlapping_updated = True
        self.assertTrue(overlapping_updated, "Overlapping element was not updated with OmniParser info")
        # Verify that a new DOM element was added for the non-overlapping OmniParser element.
        new_element_added = any(child.attributes.get("data-omniparser-type") == "link" for child in merged_state.element_tree.children)
        self.assertTrue(new_element_added, "Non-overlapping OmniParser element was not added as new DOM element")
        # Verify that the selector map was updated with a new entry for the added element.
        self.assertTrue(any("omniparser-" in xpath for key, xpath in merged_state.selector_map.items() if key not in [0, 1]))
    @patch("browser_use.omniparser.service.OmniParserService")
    @patch("browser_use.omniparser.captcha.CaptchaDetector")
    async def test_get_elements_with_merge_exception(self, mock_captcha_detector, mock_omniparser_service):
        """Test that an exception thrown during merge (detect_interactive_elements) leads to fallback to the original DOM state."""
        settings = OmniParserSettings(enabled=True, merge_with_dom=True)
        extractor = HybridExtractor(self.dom_service, settings)
        omniparser_mock = mock_omniparser_service.return_value
        # Force an exception in the merge branch
        omniparser_mock.detect_interactive_elements = AsyncMock(side_effect=Exception("Merge exception"))
        result = await extractor.get_elements()
        # Verify fallback to DOM-based extraction on exception
        self.dom_service.get_clickable_elements.assert_called_once()
        self.assertEqual(result, self.sample_dom_state)
    async def test_get_elements_parameter_forwarding(self):
        """Test that the get_elements method forwards parameters to the DOM service correctly."""
        # Create settings with OmniParser disabled to force DOM-only extraction
        settings = OmniParserSettings(enabled=False)
        extractor = HybridExtractor(self.dom_service, settings)
        # Call get_elements with non-default parameters
        result = await extractor.get_elements(highlight_elements=False, focus_element=5, viewport_expansion=1000)
        # Assert that the DOM service was called with the correct parameters
        self.dom_service.get_clickable_elements.assert_called_once_with(
            highlight_elements=False,
            focus_element=5,
            viewport_expansion=1000
        )
        # Verify that the returned DOM state matches the sample DOM state
        self.assertEqual(result, self.sample_dom_state)
    @patch("browser_use.omniparser.service.OmniParserService")
    @patch("browser_use.omniparser.captcha.CaptchaDetector")
    async def test_get_elements_screenshot_exception(self, mock_captcha_detector, mock_omniparser_service):
        """Test that an exception during page screenshot leads to fallback to the DOM-based extraction."""
        settings = OmniParserSettings(enabled=True)
        extractor = HybridExtractor(self.dom_service, settings)
        # Force the screenshot method to raise an exception
        self.dom_service.page.screenshot = AsyncMock(side_effect=Exception("screenshot error"))
        result = await extractor.get_elements()
        self.dom_service.get_clickable_elements.assert_called_once()
        self.assertEqual(result, self.sample_dom_state)
    @patch("browser_use.omniparser.service.OmniParserService")
    @patch("browser_use.omniparser.captcha.CaptchaDetector")
    async def test_get_elements_with_invalid_prefer_over_dom(self, mock_captcha_detector, mock_omniparser_service):
        """Test that when prefer_over_dom is enabled but OmniParser returns an invalid result,
        the extractor falls back to the DOM-based extraction."""
    @patch("browser_use.omniparser.service.OmniParserService")
    @patch("browser_use.omniparser.captcha.CaptchaDetector")
    async def test_get_elements_with_merge_none(self, mock_captcha_detector, mock_omniparser_service):
        """Test that when detect_interactive_elements returns None, the extractor falls back to the original DOM-based state."""
        settings = OmniParserSettings(enabled=True, merge_with_dom=True, prefer_over_dom=False, captcha_detection=False)
        extractor = HybridExtractor(self.dom_service, settings)
        omniparser_mock = mock_omniparser_service.return_value
        omniparser_mock.detect_interactive_elements = AsyncMock(return_value=None)
        result = await extractor.get_elements()
        # Verify that detect_interactive_elements was called and the fallback DOM state is returned
        omniparser_mock.detect_interactive_elements.assert_called_once()
        self.assertEqual(result, self.sample_dom_state)
        from browser_use.dom.views import DOMState
        # Create settings with OmniParser enabled and preferred, but merging and CAPTCHA disabled
        settings = OmniParserSettings(enabled=True, prefer_over_dom=True, merge_with_dom=False, captcha_detection=False)
        extractor = HybridExtractor(self.dom_service, settings)
        # Configure OmniParser's create_dom_state_from_screenshot to return an invalid result:
        # an object with no element_tree and an empty selector_map.
        invalid_omni_state = DOMState(element_tree=None, selector_map={})
        mock_omniparser_service.return_value.create_dom_state_from_screenshot = AsyncMock(return_value=invalid_omni_state)
        result = await extractor.get_elements()
        # Since OmniParser did not return a valid result, the extractor should return the DOM service result.
        self.assertEqual(result, self.sample_dom_state)
if __name__ == "__main__":
    unittest.main()
