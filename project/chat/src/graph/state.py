from typing import TypedDict, Annotated, List, Union
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage

class AgentState(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
    user_level: str
    user_memory: List[str]
    current_topic: str
    next_step: str
    grammar_error: bool
    correction: str
    is_lesson: bool
    audio_content: str
