from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ActionViewModel:
    name: str
    value: str
    label: str
    description: str = ""

@dataclass
class MessageViewModel:
    content: str
    last_message: str
    author: str = "Emma"
    actions: List[ActionViewModel] = field(default_factory=list)
    audio_url: Optional[str] = None
    file_path: Optional[str] = None
    should_stream: bool = False
