import asyncio
from hospital_ai.core.config import get_settings
from hospital_ai.services.llm.stub_provider import StubLLM
from hospital_ai.services.llm.base import LLMMessage
from hospital_ai.services.chat_utils import is_chitchat_query

async def main():
    llm = StubLLM("test")
    messages = [
        LLMMessage(
            role="system",
            content="You are a friendly hospital knowledge assistant..."
        ),
        LLMMessage(role="user", content="cảm ơn"),
    ]
    print(f"Is chitchat: {is_chitchat_query('cảm ơn')}")
    print("Streaming chitchat:")
    async for token in llm.stream(messages):
        print(token, end="")
    print("\nDone")

asyncio.run(main())
