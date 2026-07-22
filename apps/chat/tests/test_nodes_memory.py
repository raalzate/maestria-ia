import pytest
from unittest.mock import MagicMock, patch
from src.graph.nodes.memory import memory_node, _clean_value, _parse_llm_json, _merge_unique_items
from langchain_core.messages import HumanMessage

def test_clean_value():
    assert _clean_value(" test ") == "test"
    assert _clean_value('"test"') == "test"
    assert _clean_value("NONE") is None
    assert _clean_value("") is None
    assert _clean_value(None) is None

def test_parse_llm_json():
    assert _parse_llm_json('{"key": "value"}') == {"key": "value"}
    assert _parse_llm_json('text {"key": "value"} text') == {"key": "value"}
    assert _parse_llm_json('invalid') == {}

def test_merge_unique_items():
    current = ["a", "b"]
    new = ["b", "c", "A"]
    result = _merge_unique_items(current, new)
    assert result == ["a", "b", "c"] # "A" is duplicate of "a" (case-insensitive check but preserves original case if not added? Logic says: if clean.lower() not in current_lower. "a" is in current_lower. So "A" is skipped.)

@patch("src.graph.nodes.memory.ProgressService")
@patch("src.graph.nodes.memory.Llama3Wrapper")
def test_memory_node_update_name(mock_llm_wrapper, mock_progress_service):
    mock_llm = MagicMock()
    mock_llm_wrapper.return_value = mock_llm
    mock_llm.invoke.return_value = '{"name": "Raul"}'
    
    mock_ps = MagicMock()
    mock_progress_service.return_value = mock_ps
    mock_ps.load_progress.return_value = {"student_name": "Unknown"}
    mock_ps.current_progress = {}
    
    state = {
        "messages": [HumanMessage(content="My name is Raul")],
        "current_mode": "chat"
    }
    
    result = memory_node(state)
    
    assert result["student_name"] == "Raul"
    mock_ps.save_progress.assert_called_once()

@patch("src.graph.nodes.memory.ProgressService")
@patch("src.graph.nodes.memory.Llama3Wrapper")
def test_memory_node_update_interests(mock_llm_wrapper, mock_progress_service):
    mock_llm = MagicMock()
    mock_llm_wrapper.return_value = mock_llm
    mock_llm.invoke.return_value = '{"interests": ["Coding"]}'
    
    mock_ps = MagicMock()
    mock_progress_service.return_value = mock_ps
    mock_ps.load_progress.return_value = {"student_interests": []}
    mock_ps.current_progress = {}
    
    state = {
        "messages": [HumanMessage(content="I like coding")],
        "current_mode": "chat"
    }
    
    result = memory_node(state)
    
    assert "Coding" in result["student_interests"]
    mock_ps.save_progress.assert_called_once()

@patch("src.graph.nodes.memory.ProgressService")
@patch("src.graph.nodes.memory.Llama3Wrapper")
def test_memory_node_no_changes(mock_llm_wrapper, mock_progress_service):
    mock_llm = MagicMock()
    mock_llm_wrapper.return_value = mock_llm
    mock_llm.invoke.return_value = '{}'
    
    mock_ps = MagicMock()
    mock_progress_service.return_value = mock_ps
    mock_ps.load_progress.return_value = {"student_name": "Raul"}
    
    state = {
        "messages": [HumanMessage(content="Hello")],
        "current_mode": "chat"
    }
    
    result = memory_node(state)
    
    assert result == {}
    mock_ps.save_progress.assert_not_called()

@patch("src.graph.nodes.memory.ProgressService")
@patch("src.graph.nodes.memory.Llama3Wrapper")
def test_memory_node_not_chat_mode(mock_llm_wrapper, mock_progress_service):
    mock_ps = MagicMock()
    mock_progress_service.return_value = mock_ps
    mock_ps.load_progress.return_value = {"student_name": "Raul"}
    
    state = {
        "messages": [HumanMessage(content="Hello")],
        "current_mode": "teach"
    }
    
    result = memory_node(state)
    
    # Should return current context without calling LLM
    assert result["student_name"] == "Raul"
    mock_llm_wrapper.return_value.invoke.assert_not_called()

@patch("src.graph.nodes.memory.ProgressService")
@patch("src.graph.nodes.memory.Llama3Wrapper")
def test_memory_node_vocabulary_filter(mock_llm_wrapper, mock_progress_service):
    mock_llm = MagicMock()
    mock_llm_wrapper.return_value = mock_llm
    # "hi" (2 chars) should be filtered, "hello" (5 chars) should be kept
    mock_llm.invoke.return_value = '{"vocabulary": ["hi", "hello"]}'
    
    mock_ps = MagicMock()
    mock_progress_service.return_value = mock_ps
    mock_ps.load_progress.return_value = {"user_memory": []}
    mock_ps.current_progress = {}
    
    state = {
        "messages": [HumanMessage(content="hi hello")],
        "current_mode": "chat"
    }
    
    result = memory_node(state)
    
    assert "Vocabulary: hello" in result["user_memory"]
    assert "Vocabulary: hi" not in result["user_memory"]
    mock_ps.save_progress.assert_called_once()

@patch("src.graph.nodes.memory.ProgressService")
@patch("src.graph.nodes.memory.Llama3Wrapper")
def test_memory_node_exception(mock_llm_wrapper, mock_progress_service):
    mock_progress_service.side_effect = Exception("Test error")
    
    state = {"messages": [HumanMessage(content="Hello")]}
    result = memory_node(state)
    
    assert result == {}
