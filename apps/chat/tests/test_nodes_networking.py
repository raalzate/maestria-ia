import pytest
from unittest.mock import MagicMock, patch
from src.graph.nodes.networking_node import networking_node, _get_profile_value, _generate_audio_html
from langchain_core.messages import HumanMessage, AIMessage

def test_get_profile_value():
    assert _get_profile_value(None, "default") == "default"
    assert _get_profile_value([], "default") == "default"
    assert _get_profile_value(["a", "b"]) == "a, b"
    assert _get_profile_value("val") == "val"

def test_generate_audio_html():
    assert _generate_audio_html("") == ""
    assert "audio" in _generate_audio_html("http://url")

@patch("src.graph.nodes.networking_node.Llama3Wrapper")
def test_networking_node_chat(mock_llm_wrapper):
    mock_llm = MagicMock()
    mock_llm_wrapper.return_value = mock_llm
    mock_llm.stream.return_value = iter(["Chat response"])
    
    state = {
        "messages": [HumanMessage(content="Hello")],
        "student_name": "Raul",
        "student_interests": ["Coding"],
        "networking_memory": ["Python"]
    }
    
    result = networking_node(state)
    
    assert result["current_mode"] == "networking"
    assert result["next_step"] == "networking"
    assert result["messages"][0].content == "Chat response"
    
    # Verify prompt context
    call_args = mock_llm.stream.call_args[0][0]
    assert "Raul" in call_args
    assert "Coding" in call_args
    assert "Python" in call_args

@patch("src.graph.nodes.networking_node.Llama3Wrapper")
def test_networking_node_no_messages(mock_llm_wrapper):
    state = {"messages": []}
    result = networking_node(state)
    assert "Let's chat!" in result["messages"][0].content

@patch("src.graph.nodes.networking_node.Llama3Wrapper")
def test_networking_node_exception(mock_llm_wrapper):
    mock_llm_wrapper.side_effect = Exception("Test error")
    
    state = {"messages": [HumanMessage(content="Hello")]}
    result = networking_node(state)
    
    assert "Sorry, I lost my train of thought" in result["messages"][0].content
