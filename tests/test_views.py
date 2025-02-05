from browser_use.agent.message_manager.views import MessageHistory, MessageMetadata
from langchain_core.messages import HumanMessage
import pytest
def test_remove_message_from_non_empty_history():
    """
    Test removing a message from a non-empty message history.
    
    This test verifies that:
    1. Messages can be added to the history correctly.
    2. The total token count is updated when messages are added.
    3. A message can be removed from a specific index.
    4. The total token count is correctly updated after removal.
    """
    history = MessageHistory()
    
    # Add two messages
    message1 = HumanMessage(content="Hello")
    metadata1 = MessageMetadata(input_tokens=5)
    history.add_message(message1, metadata1)
    
    message2 = HumanMessage(content="World")
    metadata2 = MessageMetadata(input_tokens=5)
    history.add_message(message2, metadata2)
    
    # Check initial state
    assert len(history.messages) == 2
    assert history.total_tokens == 10
    
    # Remove the first message (index 0)
    history.remove_message(0)
    
    # Check final state
    assert len(history.messages) == 1
    assert history.total_tokens == 5
    assert history.messages[0].message.content == "World"
