import pytest
from src.graph.state import AgentState

def test_agent_state_structure():
    """Test that AgentState has the expected keys."""
    expected_keys = {
        "messages",
        "user_level",
        "user_memory",
        "current_topic",
        "next_step",
        "grammar_error",
        "correction",
        "is_lesson",
        "audio_content",
        "progress",
        "current_mode",
        "student_name",
        "student_interests",
        "student_goals",
        "discovery_completed",
        "networking_memory",
        "learning_progress"
    }
    
    # Since AgentState is a TypedDict, we can check its __annotations__
    assert set(AgentState.__annotations__.keys()) == expected_keys
