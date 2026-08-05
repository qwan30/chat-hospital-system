"""Database models and session helpers."""

from __future__ import annotations

# Side-effect imports: ensure all SQLAlchemy model submodules are registered
# with the shared Base metadata when the db package is imported.
from hospital_ai.db import clinical_documents as clinical_documents
from hospital_ai.db import clinical_graph as clinical_graph
from hospital_ai.db import settings_store as settings_store
from hospital_ai.services import metrics as metrics
