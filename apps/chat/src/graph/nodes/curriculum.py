from src.graph.state import AgentState
from src.services.progress_service import ProgressService

def curriculum_node(state: AgentState):
    """
    Updates the state with the current curriculum progress.
    """
    progress_service = ProgressService()
    progress = progress_service.complete_current_topic()
    return {
        "current_topic": progress["current_topic"],
        "current_level": progress["current_level"],
        "progress": progress
    }
