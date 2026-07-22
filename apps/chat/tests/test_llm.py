import pytest
from unittest.mock import MagicMock, patch
from src.graph.llm import Llama3Wrapper
from langchain_core.outputs import GenerationChunk

@pytest.fixture
def mock_llm_instance():
    with patch("src.graph.llm.get_llm") as mock_get_llm:
        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm
        yield mock_llm

def test_llm_type():
    wrapper = Llama3Wrapper()
    assert wrapper._llm_type == "llama-3-custom"

def test_call_no_model_loaded():
    with patch("src.graph.llm.get_llm", return_value=None):
        wrapper = Llama3Wrapper()
        with pytest.raises(ValueError, match="Model not loaded"):
            wrapper._call("test prompt")

def test_call_json_prompt(mock_llm_instance):
    mock_llm_instance.create_chat_completion.return_value = {
        "choices": [{"message": {"content": "response"}}]
    }
    wrapper = Llama3Wrapper()
    prompt = '[{"role": "user", "content": "hello"}]'
    response = wrapper._call(prompt)
    
    assert response == "response"
    mock_llm_instance.create_chat_completion.assert_called_once()
    call_args = mock_llm_instance.create_chat_completion.call_args[1]
    assert call_args["messages"] == [{"role": "user", "content": "hello"}]
    assert call_args["stream"] is False

def test_call_text_prompt_with_system_user(mock_llm_instance):
    mock_llm_instance.create_chat_completion.return_value = {
        "choices": [{"message": {"content": "response"}}]
    }
    wrapper = Llama3Wrapper()
    prompt = "System: be helpful\nUser: hello"
    response = wrapper._call(prompt)
    
    assert response == "response"
    call_args = mock_llm_instance.create_chat_completion.call_args[1]
    assert call_args["messages"] == [
        {"role": "system", "content": "be helpful"},
        {"role": "user", "content": "hello"}
    ]

def test_call_text_prompt_simple(mock_llm_instance):
    mock_llm_instance.create_chat_completion.return_value = {
        "choices": [{"message": {"content": "response"}}]
    }
    wrapper = Llama3Wrapper()
    prompt = "hello"
    response = wrapper._call(prompt)
    
    assert response == "response"
    call_args = mock_llm_instance.create_chat_completion.call_args[1]
    assert call_args["messages"] == [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "hello"}
    ]

def test_stream_no_model_loaded():
    with patch("src.graph.llm.get_llm", return_value=None):
        wrapper = Llama3Wrapper()
        with pytest.raises(ValueError, match="Model not loaded"):
            list(wrapper._stream("test prompt"))

def test_stream_json_prompt(mock_llm_instance):
    mock_llm_instance.create_chat_completion.return_value = iter([
        {"choices": [{"delta": {"content": "chunk1"}}]},
        {"choices": [{"delta": {"content": "chunk2"}}]}
    ])
    wrapper = Llama3Wrapper()
    prompt = '[{"role": "user", "content": "hello"}]'
    chunks = list(wrapper._stream(prompt))
    
    assert len(chunks) == 2
    assert isinstance(chunks[0], GenerationChunk)
    assert chunks[0].text == "chunk1"
    assert chunks[1].text == "chunk2"
    
    call_args = mock_llm_instance.create_chat_completion.call_args[1]
    assert call_args["messages"] == [{"role": "user", "content": "hello"}]
    assert call_args["stream"] is True

def test_identifying_params():
    wrapper = Llama3Wrapper()
    assert wrapper._identifying_params == {"model_name": "Llama-3 Custom"}
