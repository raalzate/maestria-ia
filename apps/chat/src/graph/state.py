from typing import TypedDict, Annotated, List, Union
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage

class AgentState(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
    current_level: str
    user_memory: List[str]
    current_topic: str
    next_step: str
    grammar_error: bool
    correction: str
    is_lesson: bool
    audio_content: str
    progress: dict
    current_mode: str  # 'chat' or 'teach'
    student_name: str
    student_interests: List[str]
    student_goals: List[str]
    discovery_completed: bool
    
    # NEW: Separated Memory Contexts
    networking_memory: List[str]  # Interests/hobbies from casual chat
    learning_progress: dict  # Lesson-specific progress tracking
