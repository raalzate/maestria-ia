import pytest
from unittest.mock import MagicMock, patch
from src.graph.nodes.onboarding_node import onboarding_node
from langchain_core.messages import HumanMessage

@patch("src.graph.nodes.onboarding_node.ProgressService")
@patch("src.graph.nodes.onboarding_node.Llama3Wrapper")
def test_onboarding_node_ask_name(mock_llm_wrapper, mock_progress_service):
    mock_llm = MagicMock()
    mock_llm_wrapper.return_value = mock_llm
    mock_llm.stream.return_value = iter(["What is your name?"])
    
    mock_ps = MagicMock()
    mock_progress_service.return_value = mock_ps
    mock_ps.load_progress.return_value = {} # Empty progress
    
    state = {"messages": []}
    
    result = onboarding_node(state)
    
    assert result["next_step"] == "continue_onboarding"
    assert result["messages"][0].content == "What is your name?"
    
    # Verify prompt key
    call_args = mock_llm.stream.call_args[0][0]
    assert "Ask for the user's name" in call_args

@patch("src.graph.nodes.onboarding_node.ProgressService")
@patch("src.graph.nodes.onboarding_node.Llama3Wrapper")
def test_onboarding_node_ask_goals(mock_llm_wrapper, mock_progress_service):
    mock_llm = MagicMock()
    mock_llm_wrapper.return_value = mock_llm
    mock_llm.stream.return_value = iter(["What are your goals?"])
    
    mock_ps = MagicMock()
    mock_progress_service.return_value = mock_ps
    mock_ps.load_progress.return_value = {"student_name": "Raul"}
    
    state = {"messages": [HumanMessage(content="My name is Raul")]}
    
    result = onboarding_node(state)
    
    assert result["next_step"] == "continue_onboarding"
    assert result["messages"][0].content == "What are your goals?"
    
    # Verify prompt key
    call_args = mock_llm.stream.call_args[0][0]
    assert "Ask why they are learning English" in call_args

@patch("src.graph.nodes.onboarding_node.ProgressService")
@patch("src.graph.nodes.onboarding_node.Llama3Wrapper")
def test_onboarding_node_ask_interests(mock_llm_wrapper, mock_progress_service):
    mock_llm = MagicMock()
    mock_llm_wrapper.return_value = mock_llm
    mock_llm.stream.return_value = iter(["What are your interests?"])
    
    mock_ps = MagicMock()
    mock_progress_service.return_value = mock_ps
    mock_ps.load_progress.return_value = {
        "student_name": "Raul",
        "student_goals": ["Learn Python"]
    }
    
    state = {"messages": [HumanMessage(content="I want to learn Python")]}
    
    result = onboarding_node(state)
    
    assert result["next_step"] == "continue_onboarding"
    assert result["messages"][0].content == "What are your interests?"
    
    # Verify prompt key
    call_args = mock_llm.stream.call_args[0][0]
    assert "Ask about their hobbies" in call_args

@patch("src.graph.nodes.onboarding_node.ProgressService")
@patch("src.graph.nodes.onboarding_node.Llama3Wrapper")
def test_onboarding_node_complete(mock_llm_wrapper, mock_progress_service):
    mock_llm = MagicMock()
    mock_llm_wrapper.return_value = mock_llm
    mock_llm.stream.return_value = iter(["Welcome!"])
    
    mock_ps = MagicMock()
    mock_progress_service.return_value = mock_ps
    mock_ps.load_progress.return_value = {
        "student_name": "Raul",
        "student_goals": ["Learn Python"],
        "student_interests": ["Coding"]
    }
    mock_ps.current_progress = {}
    
    state = {"messages": [HumanMessage(content="I like coding")]}
    
    result = onboarding_node(state)
    
    assert result["next_step"] == "flow_selection"
    assert result["discovery_completed"] is True
    assert result["messages"][0].content == "Welcome!"
    
    # Verify prompt key
    call_args = mock_llm.stream.call_args[0][0]
    assert "Explain that they can now choose" in call_args
    
    # Verify save
    mock_ps.save_progress.assert_called_once()
    assert mock_ps.current_progress["discovery_completed"] is True

@patch("src.graph.nodes.onboarding_node.ProgressService")
@patch("src.graph.nodes.onboarding_node.Llama3Wrapper")
def test_onboarding_node_exception(mock_llm_wrapper, mock_progress_service):
    mock_progress_service.side_effect = Exception("Test error")
    
    state = {"messages": []}
    result = onboarding_node(state)
    
    assert result["next_step"] == "continue_onboarding"
    assert "I'm having a little trouble" in result["messages"][0].content
