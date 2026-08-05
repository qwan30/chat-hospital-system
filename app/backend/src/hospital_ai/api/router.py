from fastapi import APIRouter

from hospital_ai.api.routes import (
    access_requests,
    audit,
    auth,
    chat,
    chat_stream,
    chat_threads,
    dashboard,
    documents,
    document_uploads,
    document_revisions,
    document_generations,
    document_graph,
    feedback,
    graph,
    hms,
    medication_safety,
    metrics_endpoint,
    patients,
    rag_trace,
    search,
    settings,
    timeline,
)

api_router = APIRouter()


@api_router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(patients.router, prefix="/patients", tags=["patients"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(document_uploads.router, prefix="/documents", tags=["documents"])
api_router.include_router(document_revisions.router, prefix="/documents", tags=["documents"])
api_router.include_router(document_generations.router, prefix="/documents", tags=["documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(chat_stream.router, prefix="/chat", tags=["chat-stream"])
api_router.include_router(rag_trace.router, prefix="/chat", tags=["rag-trace"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
api_router.include_router(chat_threads.router, prefix="/chat-threads", tags=["chat-threads"])
api_router.include_router(hms.router, prefix="/hms", tags=["hms"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(document_graph.router, prefix="/documents", tags=["document_graph"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(access_requests.router, prefix="/access-requests", tags=["access-requests"])
api_router.include_router(graph.router, prefix="/graph", tags=["graph"])
api_router.include_router(medication_safety.router, prefix="/medication-safety", tags=["medication-safety"])
api_router.include_router(timeline.router)
api_router.include_router(metrics_endpoint.router, tags=["metrics"])
