import pytest
from browser_use.agent.message_manager.views import (
    MessageHistory,
    MessageMetadata,
)
from langchain_core.messages import (
    HumanMessage,
)


def test_message_history_insert_and_remove():
    """
    Test adding messages with insertion at specific positions and removal while updating token counts.

    This test verifies that:
    - Adding a message normally appends it to the history.
    - Inserting a message at a given position places it correctly in the history list.
    - total_tokens is updated properly after adding messages.
    - Removing a message (using the default index remove or a specified index) properly updates both the message list and total_tokens.
    """
    history = MessageHistory()
    message1 = HumanMessage(content="Hello, world!")
    metadata1 = MessageMetadata(input_tokens=5)
    message2 = HumanMessage(content="Greetings!")
    metadata2 = MessageMetadata(input_tokens=10)
    history.add_message(message1, metadata1)
    assert len(history.messages) == 1, "Expected message1 to be appended."
    assert history.total_tokens == 5, "Total tokens should reflect message1 tokens."
    history.add_message(message2, metadata2, position=0)
    assert len(history.messages) == 2, "Two messages should now be in history."
    assert (
        history.messages[0].message.content == "Greetings!"
    ), "Message2 should be at the beginning."
    assert history.messages[1].message.content == "Hello, world!"
    assert (
        history.total_tokens == 15
    ), "Total tokens should now equal the sum of both messages' tokens (10 + 5)."
    history.remove_message()
    assert len(history.messages) == 1, "One message should remain after removal."
    assert (
        history.messages[0].message.content == "Greetings!"
    ), "Remaining message should be message2."
    assert (
        history.total_tokens == 10
    ), "Total tokens should now reflect only message2 tokens."
    history.remove_message(index=0)
    assert (
        len(history.messages) == 0
    ), "History should be empty after removing the last message."
    assert (
        history.total_tokens == 0
    ), "Total tokens should be 0 after all messages are removed."


def test_edge_cases_empty_history_and_out_of_bound_insertion():
    """
    Test edge cases for MessageHistory:
    - Removing from an empty history should leave the history unchanged.
    - Inserting at a position greater than the current list length should append the message.
    """
    history = MessageHistory()
    history.remove_message()
    assert (
        len(history.messages) == 0
    ), "History should remain empty after a removal attempt on an empty history."
    assert (
        history.total_tokens == 0
    ), "Total tokens should remain 0 in an empty history."
    msg = HumanMessage(content="Out-of-bound insertion")
    md = MessageMetadata(input_tokens=20)
    history.add_message(msg, md, position=10)
    assert (
        len(history.messages) == 1
    ), "History should contain one message after out-of-bound insertion."
    assert (
        history.messages[-1].message.content == "Out-of-bound insertion"
    ), "The message should be appended at the end."
    assert (
        history.total_tokens == 20
    ), "Total tokens should reflect the tokens of the newly inserted message."


def test_negative_insertion_position():
    """
    Test inserting a message with a negative position.
    Inserting using a negative position should insert the message relative to the end of the message list.
    For example, inserting with position -1 in a list of two messages should place the new message at index 1.
    """
    history = MessageHistory()
    message1 = HumanMessage(content="First message")
    metadata1 = MessageMetadata(input_tokens=4)
    message2 = HumanMessage(content="Second message")
    metadata2 = MessageMetadata(input_tokens=6)
    message3 = HumanMessage(content="Inserted message at negative index")
    metadata3 = MessageMetadata(input_tokens=2)
    history.add_message(message1, metadata1)
    history.add_message(message2, metadata2)
    history.add_message(message3, metadata3, position=-1)
    assert (
        len(history.messages) == 3
    ), "Expected three messages in history after negative index insertion."
    assert (
        history.messages[0].message.content == "First message"
    ), "Message1 should be at index 0."
    assert (
        history.messages[1].message.content == "Inserted message at negative index"
    ), "Message3 should be inserted at index 1."
    assert (
        history.messages[2].message.content == "Second message"
    ), "Message2 should be at the end."
    assert (
        history.total_tokens == 12
    ), "Total tokens should be the sum of all messages tokens (4 + 2 + 6)."


def test_remove_middle_message():
    """
    Test removing a message from the middle of the MessageHistory.
    This test verifies that removing an element at a specific middle index correctly
    updates the order of messages and adjusts the total_tokens accordingly.
    """
    history = MessageHistory()
    msg1 = HumanMessage(content="Message 1")
    md1 = MessageMetadata(input_tokens=3)
    msg2 = HumanMessage(content="Message 2")
    md2 = MessageMetadata(input_tokens=5)
    msg3 = HumanMessage(content="Message 3")
    md3 = MessageMetadata(input_tokens=7)
    history.add_message(msg1, md1)
    history.add_message(msg2, md2)
    history.add_message(msg3, md3)
    assert len(history.messages) == 3, "Expected three messages in history."
    assert (
        history.total_tokens == 15
    ), "Total tokens should be the sum of all three messages."
    history.remove_message(index=1)
    assert (
        len(history.messages) == 2
    ), "Expected two messages in history after removing the middle message."
    assert (
        history.messages[0].message.content == "Message 1"
    ), "Message1 should remain at index 0."
    assert (
        history.messages[1].message.content == "Message 3"
    ), "Message3 should now be at index 1."
    assert (
        history.total_tokens == 10
    ), "Total tokens should reflect tokens from Message 1 and Message 3."
