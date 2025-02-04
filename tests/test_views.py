import pytest
from browser_use.agent.message_manager.views import MessageHistory, BaseMessage, MessageMetadata, HumanMessage, AIMessage




def test_remove_message_from_middle():
    """
    Test removing a message from the middle of the MessageHistory.
    This checks if the remove_message method works correctly with a non-default index
    and if the total token count is updated appropriately.
    """
    history = MessageHistory()
    
    # Add three messages to the history
    message1 = HumanMessage(content="Hello")
    metadata1 = MessageMetadata(input_tokens=5)
    history.add_message(message1, metadata1)
    
    message2 = AIMessage(content="Hi there")
    metadata2 = MessageMetadata(input_tokens=8)
    history.add_message(message2, metadata2)
    
    message3 = HumanMessage(content="How are you?")
    metadata3 = MessageMetadata(input_tokens=12)
    history.add_message(message3, metadata3)
    
    # Check initial state
    assert len(history.messages) == 3
    assert history.total_tokens == 25
    
    # Remove the middle message (index 1)
    history.remove_message(1)
    
    # Check final state
    assert len(history.messages) == 2
    assert history.total_tokens == 17
    assert history.messages[0].message == message1
    assert history.messages[1].message == message3
