from typing import Any, List, Optional, Mapping
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.llms import LLM
from src.llm import get_llm

class Llama3Wrapper(LLM):
    """Wrapper for our existing Llama-3 instance to work with LangChain."""
    
    @property
    def _llm_type(self) -> str:
        return "llama-3-custom"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        llm = get_llm()
        if not llm:
            raise ValueError("Model not loaded")

        # Parse prompt to extract system and user messages
        # Expected format: "System: <system_prompt>\nUser: <user_message>"
        lines = prompt.split('\n')
        system_content = ""
        user_content = ""
        
        for line in lines:
            if line.startswith("System:"):
                system_content = line.replace("System:", "").strip()
            elif line.startswith("User:"):
                user_content = line.replace("User:", "").strip()
        
        # If no proper format, treat entire prompt as user message
        if not system_content and not user_content:
            user_content = prompt
            system_content = "You are a helpful assistant."
        
        # Use chat completion format (proper for Llama-3)
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]
        
        # Generate response using chat format
        output = llm.create_chat_completion(
            messages=messages,
            max_tokens=kwargs.get("max_tokens", 200),
            stop=stop or ["<|eot_id|>"],
            stream=False
        )
        
        return output["choices"][0]["message"]["content"]

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        return {"model_name": "Llama-3 Custom"}
