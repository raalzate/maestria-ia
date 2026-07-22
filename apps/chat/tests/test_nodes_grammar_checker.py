import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from src.graph.nodes.grammar_checker import grammar_node
from langchain_core.messages import HumanMessage

@pytest.mark.asyncio
@patch("src.graph.nodes.grammar_checker.check_grammar", new_callable=AsyncMock)
async def test_grammar_node_with_errors(mock_check_grammar):
    mock_check_grammar.return_value = ("Corrected text", True, ["correction"])
    
    state = {
        "messages": [HumanMessage(content="error text")]
    }
    
    result = await grammar_node(state)
    
    assert result["grammar_error"] is True
    assert result["correction"] == "Corrected text"
    assert "Corrected text" in result["messages"][0].content

@pytest.mark.asyncio
@patch("src.graph.nodes.grammar_checker.check_grammar", new_callable=AsyncMock)
async def test_grammar_node_no_errors(mock_check_grammar):
    mock_check_grammar.return_value = ("None", False, [])
    
    state = {
        "messages": [HumanMessage(content="correct text")]
    }
    
    result = await grammar_node(state)
    
    assert result["grammar_error"] is False
    assert result["correction"] == ""
    assert "messages" not in result or result["messages"] == state.get("messages", [])
