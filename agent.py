from profile import OperatorProfile
from prompt_builder import build_system_prompt


class ShopfloorAgent:
    def __init__(self, profile: OperatorProfile):
        self.profile = profile
        self.chat_history: list[dict] = []

    def start_session(self) -> None:
        pass

    def send_message(self, message: str) -> str:
        pass

    def _call_llm(self, messages: list[dict]) -> str:
        pass

    def _handle_tool_call(self, tool_name: str, tool_args: dict) -> str:
        pass
