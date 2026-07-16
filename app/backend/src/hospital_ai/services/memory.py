import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.config import Settings
from hospital_ai.db.models import ChatSessionMemory
from hospital_ai.services.llm import LLMManager
from hospital_ai.services.llm.base import LLMMessage

logger = logging.getLogger(__name__)


class MemoryService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    async def update_session_memory(
        self,
        thread_id: UUID,
        patient_id: UUID | None,
        new_question: str,
        new_answer: str,
        source_ids: list[str],
    ) -> None:
        """Update or create the ChatSessionMemory for a given thread asynchronously."""
        try:
            # 1. Fetch existing memory
            result = await self.session.execute(
                select(ChatSessionMemory).where(ChatSessionMemory.thread_id == thread_id).with_for_update()
            )
            memory = result.scalar_one_or_none()

            # 2. Build the summarization prompt
            existing_summary = memory.summary if memory else ""
            prompt = (
                "You are an AI assistant tasked with maintaining a concise clinical summary of a chat session.\n"
                f"Existing Summary: {existing_summary}\n\n"
                f"New User Question: {new_question}\n"
                f"New Assistant Answer: {new_answer}\n\n"
                "Please provide an updated, concise clinical summary incorporating the new exchange. "
                "Do not include PHI if it is irrelevant. Keep it brief."
            )

            llm_manager = LLMManager(self.settings)
            llm = llm_manager.get()

            # Use non-streaming inference for the summary
            messages = [
                LLMMessage(role="system", content="You summarize clinical conversations concisely."),
                LLMMessage(role="user", content=prompt),
            ]

            # Simple summarization call
            # Notice we capture the full response
            summary_response = ""
            async for chunk in llm.stream(messages):
                summary_response += chunk

            # Extract active entities from question/answer loosely
            # A simple rule-based approach for the portfolio demo
            active_entities = []
            if memory and memory.active_entities:
                active_entities = list(memory.active_entities)
            # Add simple heuristic entities (capitalized words or specific patterns if we had a NER)
            # For this MVP we just store the summary.

            # Combine source_ids
            combined_source_ids = []
            if memory and memory.source_ids:
                combined_source_ids = list(memory.source_ids)
            for sid in source_ids:
                if sid not in combined_source_ids:
                    combined_source_ids.append(sid)

            if memory:
                memory.summary = summary_response.strip()
                memory.active_entities = active_entities
                memory.source_ids = combined_source_ids
                memory.active_patient_id = patient_id
                memory.updated_at = datetime.now(UTC)
            else:
                memory = ChatSessionMemory(
                    thread_id=thread_id,
                    active_patient_id=patient_id,
                    summary=summary_response.strip(),
                    active_entities=active_entities,
                    source_ids=combined_source_ids,
                )
                self.session.add(memory)

            await self.session.flush()

        except Exception as e:
            safe_thread = str(thread_id).replace("\r", "").replace("\n", "")
            logger.warning("Failed to update session memory for thread %s: %s", safe_thread, e, exc_info=True)
