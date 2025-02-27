"""
Tests for the CAPTCHA detector.
"""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from browser_use.dom.views import DOMElementNode, DOMState
from browser_use.dom.history_tree_processor.view import CoordinateSet, Coordinates, ViewportInfo
from browser_use.omniparser.captcha import CaptchaDetector
from browser_use.omniparser.service import OmniParserService
from browser_use.omniparser.views import OmniParserSettings


class TestCaptchaDetector(unittest.TestCase):
    """Tests for the CaptchaDetector class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the OmniParser service
        self.omniparser_service = MagicMock(spec=OmniParserService)
        
        # Sample DOM state
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
        
        # Sample CAPTCHA elements
        self.sample_captcha_elements = [
            {
                "x": 150,
                "y": 150,
                "width": 100,
                "height": 30,
                "element_type": "checkbox",
                "text": "I am not a robot",
                "confidence": 0.95
            },
            {
                "x": 300,
                "y": 300,
                "width": 150,
                "height": 40,
                "element_type": "image",
                "text": "select all images with traffic lights",
                "confidence": 0.89
            }
        ]
        
        # Create the detector
        self.detector = CaptchaDetector(
            self.omniparser_service,
            OmniParserSettings(captcha_detection=True)
        )
    
    async def test_detect_captchas(self):
        """Test detecting CAPTCHA elements."""
        # Mock OmniParser service to return sample elements
        self.omniparser_service.detect_interactive_elements = AsyncMock(
            return_value=self.sample_captcha_elements
        )
        
        # Call the method
        result = await self.detector.detect_captchas("test_screenshot")
        
        # Verify the service was called
        self.omniparser_service.detect_interactive_elements.assert_called_once_with(
            "test_screenshot", 
            confidence_threshold=self.detector.settings.confidence_threshold
        )
        
        # Verify all CAPTCHA elements were detected (using our mock sample)
        self.assertEqual(len(result), 2)
    
    def test_is_likely_captcha(self):
        """Test CAPTCHA likelihood detection logic."""
        # Test cases with various element types and text content
        test_cases = [
            # Checkboxes are commonly used in reCAPTCHA
            ({"element_type": "checkbox"}, True),
            
            # Text matches for common CAPTCHA providers
            ({"element_type": "div", "text": "complete recaptcha verification"}, True),
            ({"element_type": "div", "text": "hcaptcha challenge"}, True),
            
            # Text matches for common CAPTCHA phrases
            ({"element_type": "div", "text": "verify you're human"}, True),
            ({"element_type": "div", "text": "i am not a robot"}, True),
            
            # Image challenges in CAPTCHAs
            ({"element_type": "image", "text": "select all traffic lights"}, True),
            
            # Non-CAPTCHA elements
            ({"element_type": "button", "text": "submit form"}, False),
            ({"element_type": "input", "text": "enter your name"}, False)
        ]
        
        # Test each case
        for element, expected in test_cases:
            with self.subTest(element=element):
                result = self.detector._is_likely_captcha(element)
                self.assertEqual(result, expected)
    
    def test_enhance_dom_with_captchas(self):
        """Test enhancing the DOM with CAPTCHA information."""
        # Call the method
        enhanced_dom = self.detector.enhance_dom_with_captchas(
            self.sample_dom_state,
            self.sample_captcha_elements
        )
        
        # Verify the DOM was modified (not the same object)
        self.assertIsNot(enhanced_dom, self.sample_dom_state)
        
        # Verify CAPTCHA information was added to the DOM
        # This is a complex check since we're modifying a tree structure
        # We'll just verify some key properties are present
        
        # Check if new CAPTCHA elements were added
        # The sample CAPTCHA doesn't overlap with the existing element
        # so we should have one new element in the selector map
        self.assertGreater(len(enhanced_dom.selector_map), len(self.sample_dom_state.selector_map))
        
        # Find elements with CAPTCHA markers
        captcha_elements = []
        
        def find_captcha_elements(element):
            if element is None:
                return
            
            if element.attributes and "data-captcha" in element.attributes:
                captcha_elements.append(element)
            
            if element.children:
                for child in element.children:
                    find_captcha_elements(child)
        
        find_captcha_elements(enhanced_dom.element_tree)
        
        # Verify we found at least one CAPTCHA element
        self.assertGreater(len(captcha_elements), 0)

    def test_enhance_dom_with_no_dom_tree(self):
        """Test that enhance_dom_with_captchas creates a minimal DOM tree when none exists."""
        # Create a new DOMState with no DOM tree and an empty selector_map.
        empty_dom_state = type(self.sample_dom_state)(element_tree=None, selector_map={})
        # Define a sample CAPTCHA element to force creation of a new element
        sample_captcha = [{
            "x": 10,
            "y": 20,
            "width": 50,

            "height": 30,
            "element_type": "div",
            "text": "captcha challenge",
            "confidence": 0.99
        }]
        # Enhance the DOM using the new captcha
        enhanced_dom = self.detector.enhance_dom_with_captchas(empty_dom_state, sample_captcha)
        # Verify that a new DOM tree (with a "body" tag) was created
        self.assertIsNotNone(enhanced_dom.element_tree)
        self.assertEqual(enhanced_dom.element_tree.tag_name, "body")
        # Verify that the selector map now contains at least one element.
        self.assertGreaterEqual(len(enhanced_dom.selector_map), 1)
        # Verify that at least one element in the DOM is marked as a CAPTCHA element.
        def find_captcha(element):
            if element.attributes and element.attributes.get("data-captcha") == "true":
                return True
            for child in element.children or []:
                if find_captcha(child):
                    return True
            return False
        self.assertTrue(find_captcha(enhanced_dom.element_tree))
    def test_elements_overlap(self):
        """Test the _elements_overlap method with overlapping and non-overlapping elements."""
        # Create a dummy DOMElementNode with explicit page_coordinates
        dom = DOMElementNode(
            tag_name="div",
            xpath="/div",
            attributes={},
            children=[],
            is_visible=True,
            is_interactive=True,
            is_top_element=True,
            is_in_viewport=True,
            highlight_index=10,
            shadow_root=False,
            parent=None,
            page_coordinates=CoordinateSet(
                top_left=Coordinates(x=50, y=50),
                top_right=Coordinates(x=150, y=50),
                bottom_left=Coordinates(x=50, y=150),
                bottom_right=Coordinates(x=150, y=150),
                center=Coordinates(x=100, y=100),
                width=100,
                height=100
            )
        )
        # Define a CAPTCHA element that overlaps with the DOM element
        captcha_overlap = {
            "x": 70,
            "y": 70,
            "width": 50,
            "height": 50,
            "element_type": "div",
            "text": "captcha challenge",
            "confidence": 0.9
        }
        # Define a CAPTCHA element that does not overlap with the DOM element
        captcha_non_overlap = {
            "x": 200,
            "y": 200,
            "width": 50,
            "height": 50,
            "element_type": "div",
            "text": "captcha challenge",
            "confidence": 0.9
        }
        # Overlap check should return True
        self.assertTrue(self.detector._elements_overlap(dom, captcha_overlap))
        # Non-overlap check should return False
        self.assertFalse(self.detector._elements_overlap(dom, captcha_non_overlap))
    def test_force_add_when_all_captchas_handled(self):
        """Test that a forced CAPTCHA element is added when all CAPTCHA elements are already handled due to overlap."""
        # Create a DOM state with a body element covering the full area and a child that fully overlaps the CAPTCHA regions.
        body_dom = DOMElementNode(
            tag_name="body",
            xpath="/body",
            attributes={},
            children=[
                DOMElementNode(
                    tag_name="div",
                    xpath="/body/div",
                    attributes={"id": "overlap-div"},
                    children=[],
                    is_visible=True,
                    is_interactive=True,
                    is_top_element=True,
                    is_in_viewport=True,
                    highlight_index=1,
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

                )
            ],
            is_visible=True,
            is_interactive=False,
            is_top_element=True,
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
        )
        dom_state = DOMState(
            element_tree=body_dom,
            selector_map={0: "body", 1: "#overlap-div"}
        )
        # Define two CAPTCHA elements that overlap with the existing div.
        captcha_elems = [
            {
                "x": 100,
                "y": 100,
                "width": 50,
                "height": 50,
                "element_type": "div",
                "text": "captcha challenge",
                "confidence": 0.8
            },
            {
                "x": 150,
                "y": 150,
                "width": 60,
                "height": 60,
                "element_type": "div",
                "text": "verify you're human",
                "confidence": 0.85
            }
        ]
        enhanced_dom = self.detector.enhance_dom_with_captchas(dom_state, captcha_elems)
        # Verify that a forced CAPTCHA element (with id 'captcha-0') was added to the selector map.
        forced_ids = [v for k, v in enhanced_dom.selector_map.items() if "captcha-" in v]
        self.assertIn("/body/div[@id='captcha-0']", forced_ids)
    def test_elements_overlap_no_coordinates(self):
        """Test that _elements_overlap returns False when the DOM element has no coordinate information."""
        dom = DOMElementNode(
            tag_name="div",
            xpath="/div",
            attributes={},
            children=[],
            is_visible=True,
            is_interactive=True,
            is_top_element=True,
            is_in_viewport=True,
            highlight_index=99,
            shadow_root=False,
            parent=None,
            page_coordinates=None,
            viewport_coordinates=None
        )
        captcha = {
            "x": 20,
            "y": 20,
            "width": 60,
            "height": 60,
            "element_type": "div",
            "text": "captcha challenge",
            "confidence": 0.85
        }
        self.assertFalse(self.detector._elements_overlap(dom, captcha))
if __name__ == "__main__":
    unittest.main()