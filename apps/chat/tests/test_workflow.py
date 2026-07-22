import pytest
from unittest.mock import MagicMock, patch
from src.graph.workflow import create_main_graph, route_after_memory, route_learning_flow, route_after_tutor
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import END

def dummy_node(state):
    return state

@pytest.fixture
def mock_nodes():
    with patch("src.graph.workflow.assessor_node", side_effect=dummy_node) as assessor, \
         patch("src.graph.workflow.memory_node", side_effect=dummy_node) as memory, \
         patch("src.graph.workflow.curriculum_node", side_effect=dummy_node) as curriculum, \
         patch("src.graph.workflow.tutor_node", side_effect=dummy_node) as tutor, \
         patch("src.graph.workflow.grammar_node", side_effect=dummy_node) as grammar, \
         patch("src.graph.workflow.networking_node", side_effect=dummy_node) as networking:
        yield {
            "assessor": assessor,
            "memory": memory,
            "curriculum": curriculum,
            "tutor": tutor,
            "grammar": grammar,
            "networking": networking
        }

def test_create_main_graph_structure(mock_nodes):
    """Test that the graph is created with expected nodes."""
    graph = create_main_graph()
    assert graph is not None

def test_route_after_memory_grammar_error():
    state = {"grammar_error": True}
    assert route_after_memory(state) == "tutor"

def test_route_after_memory_chat_keyword():
    state = {
        "grammar_error": False,
        "messages": [HumanMessage(content="I want to chat")]
    }
    assert route_after_memory(state) == "networking"

def test_route_after_memory_lesson_keyword():
    state = {
        "grammar_error": False,
        "messages": [HumanMessage(content="I want a lesson")]
    }
    assert route_after_memory(state) == "assessor"

def test_route_after_memory_default():
    state = {
        "grammar_error": False,
        "messages": [HumanMessage(content="hello")]
    }
    assert route_after_memory(state) == "assessor"

def test_route_learning_flow_new_topic():
    state = {"next_step": "new_topic"}
    assert route_learning_flow(state) == "curriculum"

def test_route_learning_flow_trigger_phrase():
    state = {
        "next_step": "continue",
        "messages": [HumanMessage(content="change topic")]
    }
    assert route_learning_flow(state) == "curriculum"

def test_route_learning_flow_default():
    state = {
        "next_step": "continue",
        "messages": [HumanMessage(content="hello")]
    }
    assert route_learning_flow(state) == "tutor"

def test_route_after_tutor_passed():
    state = {
        "messages": [AIMessage(content="Great job! [PASSED]")]
    }
    assert route_after_tutor(state) == "curriculum"

def test_route_after_tutor_not_passed():
    state = {
        "messages": [AIMessage(content="Try again.")]
    }
    assert route_after_tutor(state) == END

def test_route_after_tutor_no_messages():
    state = {}
    assert route_after_tutor(state) == END
