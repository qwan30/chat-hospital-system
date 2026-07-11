"""HMS REST API client — fetches data from the hospital-management-system.

Connects via HTTP to the HMS backend (Java Spring Boot, port 8080) to pull
clinical data that gets ingested as retrievable evidence chunks.
"""

import logging
from typing import Any

import httpx

from hospital_ai.core.config import Settings
from hospital_ai.core.errors import ExternalServiceError

logger = logging.getLogger(__name__)


class HmsApiClient:
    """Thin wrapper around the HMS REST API."""

    def __init__(self, settings: Settings) -> None:
        self.base_url = settings.hms_base_url.rstrip("/")
        self.api_key = settings.hms_api_key
        self.timeout = settings.hms_sync_timeout_seconds

    def _headers(self, jwt_token: str | None = None) -> dict[str, str]:
        headers: dict[str, str] = {"Accept": "application/json"}
        if jwt_token:
            headers["Authorization"] = f"Bearer {jwt_token}"
        elif self.api_key:
            headers["X-Api-Key"] = self.api_key
        return headers

    async def _get(self, path: str, *, jwt_token: str | None = None, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self._headers(jwt_token), params=params)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.warning("HMS API error: %s %s → %s", exc.request.method, exc.request.url, exc.response.status_code)
            raise ExternalServiceError(f"HMS API returned {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            logger.error("HMS API connection error: %s", exc)
            raise ExternalServiceError("HMS API is unreachable.") from exc

        data = response.json()
        # HMS uses an envelope: { success, data, message, error, pagination }
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        return data

    async def _post(
        self,
        path: str,
        *,
        jwt_token: str | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    headers=self._headers(jwt_token),
                    json=json,
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "HMS API error: %s %s -> %s",
                exc.request.method,
                exc.request.url,
                exc.response.status_code,
            )
            raise ExternalServiceError(f"HMS API returned {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            logger.error("HMS API connection error: %s", exc)
            raise ExternalServiceError("HMS API is unreachable.") from exc

        data = response.json()
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        return data

    def _validate_patient_id(self, patient_id: str) -> None:
        """Validate patient_id is a UUID before using in URL paths.

        Raises ExternalServiceError for non-UUID strings to prevent
        path-traversal or injection via the HMS URL path.
        """
        import uuid as _uuid

        try:
            _uuid.UUID(patient_id)
        except (ValueError, AttributeError):
            raise ExternalServiceError(f"Invalid patient_id format: {patient_id!r}") from None

    # ── Patient integration endpoints ──────────────────────────────

    async def get_patient(self, patient_id: str, *, jwt_token: str | None = None) -> dict[str, Any]:
        self._validate_patient_id(patient_id)
        # Keeps legacy compatibility mapping but routes to snapshot
        return await self.get_patient_snapshot(patient_id, jwt_token=jwt_token)

    async def search_patients(self, query: str, *, jwt_token: str | None = None) -> list[dict[str, Any]]:
        result = await self._get("/ai/patients", jwt_token=jwt_token, params={"query": query})
        return result if isinstance(result, list) else []

    async def get_patient_snapshot(self, patient_id: str, *, jwt_token: str | None = None) -> dict[str, Any]:
        self._validate_patient_id(patient_id)
        return await self._get(f"/ai/patients/{patient_id}/snapshot", jwt_token=jwt_token)

    async def get_patient_timeline(self, patient_id: str, *, jwt_token: str | None = None) -> list[dict[str, Any]]:
        self._validate_patient_id(patient_id)
        result = await self._get(f"/ai/patients/{patient_id}/timeline", jwt_token=jwt_token)
        return result if isinstance(result, list) else []

    async def check_clinician_permissions(
        self, patient_id: str, user_id: str, *, jwt_token: str | None = None
    ) -> dict[str, Any]:
        self._validate_patient_id(patient_id)
        return await self._get(
            f"/ai/patients/{patient_id}/permissions", jwt_token=jwt_token, params={"userId": user_id}
        )

    async def request_patient_access(
        self,
        patient_id: str,
        clinician_user_id: str,
        justification: str,
        *,
        jwt_token: str | None = None,
    ) -> dict[str, Any]:
        """POST an access request to the HMS for audit and approval.

        Raises ExternalServiceError if the HMS is unreachable or returns
        a non-2xx status.
        """
        self._validate_patient_id(patient_id)
        return await self._post(
            f"/ai/patients/{patient_id}/access-requests",
            jwt_token=jwt_token,
            json={
                "userId": clinician_user_id,
                "justification": justification,
            },
        )

    async def get_incremental_changes(
        self, since: str | None = None, *, jwt_token: str | None = None
    ) -> dict[str, Any]:
        params = {"since": since} if since else {}
        return await self._get("/ai/changes", jwt_token=jwt_token, params=params)

    # ── Appointment endpoints ──────────────────────────────────────

    async def get_appointments(
        self,
        *,
        patient_id: str | None = None,
        jwt_token: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if patient_id:
            params["patientId"] = patient_id
        result = await self._get("/appointments", jwt_token=jwt_token, params=params)
        return result if isinstance(result, list) else []

    async def get_appointment(self, appointment_id: str, *, jwt_token: str | None = None) -> dict[str, Any]:
        return await self._get(f"/appointments/{appointment_id}", jwt_token=jwt_token)

    # ── Lab result endpoints ───────────────────────────────────────

    async def get_lab_results(
        self,
        *,
        patient_id: str | None = None,
        jwt_token: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if patient_id:
            params["patientId"] = patient_id
        result = await self._get("/lab-results", jwt_token=jwt_token, params=params)
        return result if isinstance(result, list) else []

    # ── Medical record endpoints ───────────────────────────────────

    async def get_medical_records(
        self,
        *,
        patient_id: str | None = None,
        jwt_token: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if patient_id:
            params["patientId"] = patient_id
        result = await self._get("/medical-records", jwt_token=jwt_token, params=params)
        return result if isinstance(result, list) else []

    # ── Vital signs ────────────────────────────────────────────────

    async def get_vital_signs(
        self,
        *,
        patient_id: str | None = None,
        jwt_token: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if patient_id:
            params["patientId"] = patient_id
        result = await self._get("/vital-signs", jwt_token=jwt_token, params=params)
        return result if isinstance(result, list) else []

    # ── Health check ───────────────────────────────────────────────

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/ai/health")
                return response.status_code == 200
        except httpx.HTTPError:
            return False
