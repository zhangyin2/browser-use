import pytest
from unittest.mock import Mock
from browser_use.dom.service import DomService
from browser_use.dom.views import DOMElementNode, DOMTextNode


@pytest.mark.asyncio
async def test_create_selector_map():
    """
    Test the _create_selector_map method of DomService to ensure it correctly creates a selector map.
    This test checks if:
    1. The method correctly identifies nodes with highlight indices.
    2. The method correctly maps highlight indices to their corresponding nodes.
    3. The method ignores nodes without highlight indices.
    4. The method handles nested structures correctly.
    """
    # Create a mock Page object
    mock_page = Mock()

    # Create a DomService instance
    dom_service = DomService(mock_page)

    # Create a mock DOM tree
    root = DOMElementNode(
        tag_name="div",
        xpath="/html/body/div",
        attributes={},
        children=[],
        is_visible=True,
        is_interactive=False,
        is_top_element=True,
        highlight_index=1,
        shadow_root=False,
        parent=None
    )

    child1 = DOMElementNode(
        tag_name="p",
        xpath="/html/body/div/p[1]",
        attributes={},
        children=[],
        is_visible=True,
        is_interactive=False,
        is_top_element=False,
        highlight_index=2,
        shadow_root=False,
        parent=root
    )

    child2 = DOMElementNode(
        tag_name="p",
        xpath="/html/body/div/p[2]",
        attributes={},
        children=[],
        is_visible=True,
        is_interactive=False,
        is_top_element=False,
        highlight_index=None,
        shadow_root=False,
        parent=root
    )

    text_node = DOMTextNode(
        text="Hello",
        is_visible=True,
        parent=child2
    )

    root.children = [child1, child2]
    child2.children = [text_node]

    # Call the _create_selector_map method
    selector_map = dom_service._create_selector_map(root)

    # Assert that the selector map is correct
    assert len(selector_map) == 2
    assert selector_map[1] == root
    assert selector_map[2] == child1
    assert 3 not in selector_map  # child2 has no highlight_index
    assert None not in selector_map  # text_node should not be in the map
