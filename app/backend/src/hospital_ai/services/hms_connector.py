"""HMS REST API client — fetches data from the hospital-management-system.
Máy khách giao tiếp REST API tới Hệ thống Quản lý Bệnh viện (HMS).

Connects via HTTP to the HMS backend (Java Spring Boot, port 8080) to pull
clinical data that gets ingested as retrievable evidence chunks.
Kết nối qua HTTP tới backend HMS (Java Spring Boot, cổng 8080) để lấy
dữ liệu lâm sàng, phục vụ cho việc lập chỉ mục và truy xuất (retrievable evidence chunks).
"""

import logging
from typing import Any

import httpx

from hospital_ai.core.config import Settings
from hospital_ai.core.errors import ExternalServiceError

logger = logging.getLogger(__name__)


class HmsApiClient:
    """Thin wrapper around the HMS REST API.
    Lớp bao bọc mỏng (thin wrapper) cho các giao tiếp REST API tới hệ thống quản lý bệnh viện (HMS).
    """

    def __init__(self, settings: Settings) -> None:
        """Khởi tạo HmsApiClient với cấu hình URL, API Key và thời gian timeout."""
        self.base_url = settings.hms_base_url.rstrip("/")
        self.api_key = settings.hms_api_key
        self.timeout = settings.hms_sync_timeout_seconds

    def _headers(self, jwt_token: str | None = None) -> dict[str, str]:
        """Tạo từ điển header HTTP, tự động thêm Authorization Bearer JWT hoặc X-Api-Key."""
        headers: dict[str, str] = {"Accept": "application/json"}
        if jwt_token:
            headers["Authorization"] = f"Bearer {jwt_token}"
        elif self.api_key:
            headers["X-Api-Key"] = self.api_key
        return headers

    async def _get(self, path: str, *, jwt_token: str | None = None, params: dict[str, Any] | None = None) -> Any:
        """Gửi yêu cầu HTTP GET bất đồng bộ và bóc tách dữ liệu từ vỏ bọc (envelope) `{success, data, ...}` của HMS."""
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
        """Gửi yêu cầu HTTP POST bất đồng bộ và bóc tách trường `data` trong phản hồi JSON từ HMS."""
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
        Kiểm tra định dạng `patient_id` có chuẩn UUID hay không trước khi ghép vào đường dẫn URL.

        Raises ExternalServiceError for non-UUID strings to prevent
        path-traversal or injection via the HMS URL path.
        Ném ra ExternalServiceError nếu chuỗi không phải UUID nhằm ngăn chặn lỗ hổng
        Path Traversal hoặc Injection qua đường dẫn URL HMS.
        """
        import uuid as _uuid

        try:
            _uuid.UUID(patient_id)
        except (ValueError, AttributeError):
            raise ExternalServiceError(f"Invalid patient_id format: {patient_id!r}") from None

    # ── Patient integration endpoints ──────────────────────────────

    async def get_patient(self, patient_id: str, *, jwt_token: str | None = None) -> dict[str, Any]:
        """Lấy thông tin tổng quan hồ sơ bệnh nhân (chuyển tiếp tới endpoint `get_patient_snapshot`)."""
        self._validate_patient_id(patient_id)
        # Keeps legacy compatibility mapping but routes to snapshot
        return await self.get_patient_snapshot(patient_id, jwt_token=jwt_token)

    async def search_patients(self, query: str, *, jwt_token: str | None = None) -> list[dict[str, Any]]:
        """Tìm kiếm danh sách bệnh nhân trên HMS theo từ khóa truy vấn (`query`)."""
        result = await self._get("/ai/patients", jwt_token=jwt_token, params={"query": query})
        return result if isinstance(result, list) else []

    async def get_patient_snapshot(self, patient_id: str, *, jwt_token: str | None = None) -> dict[str, Any]:
        """Lấy bản chụp toàn diện (snapshot) dữ liệu lâm sàng hiện tại của bệnh nhân
        (bệnh án, xét nghiệm, đơn thuốc).
        """
        self._validate_patient_id(patient_id)
        return await self._get(f"/ai/patients/{patient_id}/snapshot", jwt_token=jwt_token)

    async def get_patient_timeline(self, patient_id: str, *, jwt_token: str | None = None) -> list[dict[str, Any]]:
        """Lấy dòng thời gian các sự kiện y khoa (tái khám, nhập viện, phẫu thuật) của bệnh nhân."""
        self._validate_patient_id(patient_id)
        result = await self._get(f"/ai/patients/{patient_id}/timeline", jwt_token=jwt_token)
        return result if isinstance(result, list) else []

    async def check_clinician_permissions(
        self, patient_id: str, user_id: str, *, jwt_token: str | None = None
    ) -> dict[str, Any]:
        """Kiểm tra quyền truy cập lâm sàng của bác sĩ/nhân viên y tế đối với hồ sơ bệnh nhân cụ thể."""
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
        Gửi yêu cầu xin cấp quyền truy cập khẩn cấp/đặc biệt tới hồ sơ bệnh nhân kèm lý do biện minh lâm sàng.

        Raises ExternalServiceError if the HMS is unreachable or returns
        a non-2xx status.
        Ném ra ExternalServiceError nếu hệ thống HMS không kết nối được hoặc trả về mã lỗi HTTP khác 2xx.
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
        """Lấy danh sách các thay đổi dữ liệu tăng cường (incremental sync) kể từ mốc thời gian `since`."""
        params = {"since": since} if since else {}
        return await self._get("/ai/changes", jwt_token=jwt_token, params=params)

    # ── Appointment endpoints ──────────────────────────────────────

    async def get_appointments(
        self,
        *,
        patient_id: str | None = None,
        jwt_token: str | None = None,
    ) -> list[dict[str, Any]]:
        """Lấy danh sách cuộc hẹn khám bệnh từ hệ thống HMS (có thể lọc theo `patient_id`)."""
        params: dict[str, Any] = {}
        if patient_id:
            params["patientId"] = patient_id
        result = await self._get("/appointments", jwt_token=jwt_token, params=params)
        return result if isinstance(result, list) else []

    async def get_appointment(self, appointment_id: str, *, jwt_token: str | None = None) -> dict[str, Any]:
        """Lấy chi tiết một cuộc hẹn khám bệnh cụ thể theo ID."""
        return await self._get(f"/appointments/{appointment_id}", jwt_token=jwt_token)

    # ── Lab result endpoints ───────────────────────────────────────

    async def get_lab_results(
        self,
        *,
        patient_id: str | None = None,
        jwt_token: str | None = None,
    ) -> list[dict[str, Any]]:
        """Lấy danh sách các kết quả xét nghiệm lâm sàng từ HMS."""
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
        """Lấy danh sách hồ sơ bệnh án khám chữa bệnh từ HMS."""
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
        """Lấy danh sách chỉ số sinh hiệu (huyết áp, nhịp tim, nhiệt độ, SpO2) của bệnh nhân."""
        params: dict[str, Any] = {}
        if patient_id:
            params["patientId"] = patient_id
        result = await self._get("/vital-signs", jwt_token=jwt_token, params=params)
        return result if isinstance(result, list) else []

    # ── Health check ───────────────────────────────────────────────

    async def health_check(self) -> bool:
        """Kiểm tra tình trạng sức khỏe kết nối (health check) tới máy chủ HMS (`/ai/health`)."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/ai/health")
                return response.status_code == 200
        except httpx.HTTPError:
            return False
