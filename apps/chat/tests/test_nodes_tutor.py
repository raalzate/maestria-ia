import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from src.graph.nodes.tutor import tutor_node, _get_profile_value, _generate_audio_html
from langchain_core.messages import HumanMessage, AIMessage

def test_get_profile_value():
    assert _get_profile_value(None) == "Unknown"
    assert _get_profile_value([]) == "Unknown"
    assert _get_profile_value(["a", "b"]) == "a, b"
    assert _get_profile_value("test") == "test"

def test_generate_audio_html():
    assert _generate_audio_html("") == ""
    assert "iframe" in _generate_audio_html("http://url", is_iframe=True)
    assert "audio" in _generate_audio_html("http://url", is_iframe=False)

@pytest.mark.asyncio
@patch("src.graph.nodes.tutor.Llama3Wrapper")
@patch("src.graph.nodes.tutor.create_interpreter_page", new_callable=AsyncMock)
@patch("src.graph.nodes.tutor.create_simple_audio", new_callable=AsyncMock)
async def test_tutor_node_grammar_error(mock_create_simple_audio, mock_create_interpreter_page, mock_llm_wrapper):
    mock_llm = MagicMock()
    mock_llm_wrapper.return_value = mock_llm
    mock_llm.stream.return_value = iter(["Correction"])
    mock_create_simple_audio.return_value = "http://audio"
    
    state = {
        "messages": [HumanMessage(content="error")],
        "grammar_error": True,
        "current_mode": "chat"
    }
    
    result = await tutor_node(state)
    
    assert result["grammar_error"] is True
    assert result["messages"][0].content == "Correction"
    assert "audio" in result["audio_content"]
    
    # Verify prompt key
    call_args = mock_llm.stream.call_args[0][0]
    assert "Identify the grammar error" in call_args

@pytest.mark.asyncio
@patch("src.graph.nodes.tutor.Llama3Wrapper")
@patch("src.graph.nodes.tutor.create_interpreter_page", new_callable=AsyncMock)
@patch("src.graph.nodes.tutor.create_simple_audio", new_callable=AsyncMock)
async def test_tutor_node_teach(mock_create_simple_audio, mock_create_interpreter_page, mock_llm_wrapper):
    mock_llm = MagicMock()
    mock_llm_wrapper.return_value = mock_llm
    mock_llm.stream.return_value = iter(["Lesson"])
    mock_create_interpreter_page.return_value = "http://interpreter"
    
    state = {
        "messages": [HumanMessage(content="teach me")],
        "next_step": "teach",
        "is_lesson": True
    }
    
    result = await tutor_node(state)
    
    assert result["current_mode"] == "teach"
    assert result["messages"][0].content == "Lesson"
    assert "iframe" in result["audio_content"]
    
    # Verify prompt key
    call_args = mock_llm.stream.call_args[0][0]
    assert "Emma, Expert English Coach" in call_args

@pytest.mark.asyncio
@patch("src.graph.nodes.tutor.Llama3Wrapper")
@patch("src.graph.nodes.tutor.create_interpreter_page", new_callable=AsyncMock)
@patch("src.graph.nodes.tutor.create_simple_audio", new_callable=AsyncMock)
async def test_tutor_node_evaluate_lesson(mock_create_simple_audio, mock_create_interpreter_page, mock_llm_wrapper):
    mock_llm = MagicMock()
    mock_llm_wrapper.return_value = mock_llm
    mock_llm.stream.return_value = iter(["Evaluation"])
    mock_create_simple_audio.return_value = "http://audio"
    
    state = {
        "messages": [HumanMessage(content="answer")],
        "next_step": "evaluate_lesson"
    }
    
    result = await tutor_node(state)
    
    assert result["current_mode"] == "evaluate_lesson"
    assert result["messages"][0].content == "Evaluation"
    
    # Verify prompt key
    call_args = mock_llm.stream.call_args[0][0]
    assert "Evaluating student answer" in call_args

@pytest.mark.asyncio
@patch("src.graph.nodes.tutor.Llama3Wrapper")
@patch("src.graph.nodes.tutor.create_interpreter_page", new_callable=AsyncMock)
@patch("src.graph.nodes.tutor.create_simple_audio", new_callable=AsyncMock)
async def test_tutor_node_new_topic(mock_create_simple_audio, mock_create_interpreter_page, mock_llm_wrapper):
    mock_llm = MagicMock()
    mock_llm_wrapper.return_value = mock_llm
    mock_llm.stream.return_value = iter(["New Topic"])
    mock_create_simple_audio.return_value = "http://audio"
    
    state = {
        "messages": [HumanMessage(content="next")],
        "next_step": "new_topic"
    }
    
    result = await tutor_node(state)
    
    assert result["current_mode"] == "new_topic"
    assert result["messages"][0].content == "New Topic"
    
    # Verify prompt key
    call_args = mock_llm.stream.call_args[0][0]
    assert "Jump into the topic naturally" in call_args

@pytest.mark.asyncio
@patch("src.graph.nodes.tutor.Llama3Wrapper")
async def test_tutor_node_exception(mock_llm_wrapper):
    mock_llm_wrapper.side_effect = Exception("Test error")
    
    state = {"messages": [HumanMessage(content="hello")]}
    result = await tutor_node(state)
    
    assert "I'm having a little trouble" in result["messages"][0].content
