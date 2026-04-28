from fastapi import APIRouter

from hospital_ai.api.routes import audit, auth, chat, chat_threads, documents, hms, patients

api_router = APIRouter()


@api_router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(patients.router, prefix="/patients", tags=["patients"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(chat_threads.router, prefix="/chat-threads", tags=["chat-threads"])
api_router.include_router(hms.router, prefix="/hms", tags=["hms"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
