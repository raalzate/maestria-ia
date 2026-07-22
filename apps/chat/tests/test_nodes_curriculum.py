import pytest
from unittest.mock import MagicMock, patch
from src.graph.nodes.curriculum import curriculum_node

@patch("src.graph.nodes.curriculum.ProgressService")
def test_curriculum_node(mock_progress_service):
    mock_ps = MagicMock()
    mock_progress_service.return_value = mock_ps
    mock_ps.complete_current_topic.return_value = {
        "current_topic": "Topic A",
        "current_level": "Level 1",
        "other_data": "data"
    }
    
    state = {}
    result = curriculum_node(state)
    
    assert result["current_topic"] == "Topic A"
    assert result["user_level"] == "Level 1"
    assert result["progress"]["other_data"] == "data"
    mock_ps.complete_current_topic.assert_called_once()
