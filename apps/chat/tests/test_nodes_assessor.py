import pytest
from unittest.mock import MagicMock, patch
from src.graph.nodes.assessor import assessor_node, _get_intent
from langchain_core.messages import HumanMessage, AIMessage

def test_get_intent_valid_json():
    response = '{"intent": "TEST_INTENT"}'
    assert _get_intent(response) == "TEST_INTENT"

def test_get_intent_json_in_text():
    response = 'Some text {"intent": "TEST_INTENT"} more text'
    assert _get_intent(response) == "TEST_INTENT"

def test_get_intent_fallback_stop():
    response = "I want to STOP now"
    assert _get_intent(response) == "STOP"

def test_get_intent_fallback_discovery():
    response = "This is a DISCOVERY response"
    assert _get_intent(response) == "DISCOVERY_RESPONSE"

def test_get_intent_fallback_request():
    response = "I REQUEST a lesson"
    assert _get_intent(response) == "REQUEST_LESSON"

def test_get_intent_default():
    response = "Just chatting"
    assert _get_intent(response, default="DEFAULT") == "DEFAULT"

def test_get_intent_invalid_json():
    response = '{"intent": "TEST_INTENT"' # Missing closing brace
    assert _get_intent(response, default="DEFAULT") == "DEFAULT"

@patch("src.graph.nodes.assessor.Llama3Wrapper")
def test_assessor_node_teach_stop(mock_llm_wrapper):
    mock_llm = MagicMock()
    mock_llm_wrapper.return_value = mock_llm
    mock_llm.invoke.return_value = '{"intent": "STOP_TEACH"}'
    
    state = {
        "messages": [HumanMessage(content="stop")],
        "current_mode": "teach"
    }
    
    result = assessor_node(state)
    
    assert result["next_step"] == "chat"
    assert result["current_mode"] == "chat"
    assert result["is_lesson"] is False

@patch("src.graph.nodes.assessor.Llama3Wrapper")
def test_assessor_node_teach_restart(mock_llm_wrapper):
    mock_llm = MagicMock()
    mock_llm_wrapper.return_value = mock_llm
    mock_llm.invoke.return_value = '{"intent": "REQUEST_RESTART"}'
    
    state = {
        "messages": [HumanMessage(content="restart")],
        "current_mode": "teach"
    }
    
    result = assessor_node(state)
    
    assert result["next_step"] == "teach"
    assert result["is_lesson"] is True

@patch("src.graph.nodes.assessor.Llama3Wrapper")
def test_assessor_node_teach_continue(mock_llm_wrapper):
    mock_llm = MagicMock()
    mock_llm_wrapper.return_value = mock_llm
    mock_llm.invoke.return_value = '{"intent": "CONTINUE_TEACH"}'
    
    state = {
        "messages": [HumanMessage(content="answer")],
        "current_mode": "teach"
    }
    
    result = assessor_node(state)
    
    assert result["next_step"] == "evaluate_lesson"
    assert result["is_lesson"] is True

@patch("src.graph.nodes.assessor.Llama3Wrapper")
def test_assessor_node_chat_request_lesson(mock_llm_wrapper):
    mock_llm = MagicMock()
    mock_llm_wrapper.return_value = mock_llm
    mock_llm.invoke.return_value = '{"intent": "REQUEST_LESSON"}'
    
    state = {
        "messages": [HumanMessage(content="teach me")],
        "current_mode": "chat"
    }
    
    result = assessor_node(state)
    
    assert result["next_step"] == "teach"
    assert result["current_mode"] == "teach"
    assert result["is_lesson"] is True

@patch("src.graph.nodes.assessor.Llama3Wrapper")
def test_assessor_node_chat_topic_change(mock_llm_wrapper):
    mock_llm = MagicMock()
    mock_llm_wrapper.return_value = mock_llm
    mock_llm.invoke.return_value = '{"intent": "TOPIC_CHANGE"}'
    
    state = {
        "messages": [HumanMessage(content="change topic")],
        "current_mode": "chat"
    }
    
    result = assessor_node(state)
    
    assert result["next_step"] == "new_topic"
    assert result["current_mode"] == "chat"

@patch("src.graph.nodes.assessor.Llama3Wrapper")
def test_assessor_node_chat_default(mock_llm_wrapper):
    mock_llm = MagicMock()
    mock_llm_wrapper.return_value = mock_llm
    mock_llm.invoke.return_value = '{"intent": "CHAT"}'
    
    state = {
        "messages": [HumanMessage(content="hello")],
        "current_mode": "chat"
    }
    
    result = assessor_node(state)
    
    assert result["next_step"] == "chat"
    assert result["current_mode"] == "chat"

@patch("src.graph.nodes.assessor.Llama3Wrapper")
def test_assessor_node_context_extraction(mock_llm_wrapper):
    mock_llm = MagicMock()
    mock_llm_wrapper.return_value = mock_llm
    mock_llm.invoke.return_value = '{"intent": "CHAT"}'
    
    state = {
        "messages": [
            AIMessage(content="Hello"),
            AIMessage(content="Correction: typo"), # Should be skipped
            HumanMessage(content="Hi")
        ],
        "current_mode": "chat"
    }
    
    assessor_node(state)
    
    # Verify prompt contains "Hello" and not "Correction: typo"
    call_args = mock_llm.invoke.call_args[0][0]
    assert 'Last AI Question/Statement: "Hello"' in call_args
    assert 'User Response: "Hi"' in call_args

@patch("src.graph.nodes.assessor.Llama3Wrapper")
def test_assessor_node_exception(mock_llm_wrapper):
    mock_llm_wrapper.side_effect = Exception("Test error")
    
    state = {"messages": []}
    result = assessor_node(state)
    
    assert result["next_step"] == "chat"
