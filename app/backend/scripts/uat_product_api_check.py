"""Run product-level UAT checks against a live Hospital AI API.

This script intentionally uses HTTP requests instead of in-process services so
it exercises the same API boundary the frontend uses during UAT.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import httpx


ALICE_PATIENT_ID = "20000000-0000-0000-0000-000000000001"
TOKENS = {
    "dev-doctor": "doctor@example.test",
    "dev-records": "records@example.test",
    "dev-security": "security@example.test",
    "dev-admin": "admin@example.test",
}
PHI_LEAK_TERMS = ("Alice Synthetic", "Blood pressure 128/78", "oxygen saturation 98")


@dataclass
class ApiEvidence:
    label: str
    method: str
    path: str
    status_code: int
    response: Any
    role: str


@dataclass
class ScenarioResult:
    name: str
    severity_on_fail: str
    passed: bool = True
    expected: str = ""
    actual: str = ""
    evidence_labels: List[str] = field(default_factory=list)

    def fail(self, actual: str) -> None:
        self.passed = False
        self.actual = actual


class UatApiRunner:
    def __init__(self, base_url: str, output_dir: Path) -> None:
        self.base_url = base_url.rstrip("/")
        self.output_dir = output_dir
        self.client = httpx.Client(timeout=30.0)
        self.evidence: List[ApiEvidence] = []
        self.identities: Dict[str, Dict[str, Any]] = {}
        self.created_threads: Dict[str, Dict[str, Any]] = {}

    def close(self) -> None:
        self.client.close()

    def request(
        self,
        label: str,
        method: str,
        path: str,
        *,
        token: Optional[str] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        headers = {"accept": "application/json"}
        role = token or "anonymous"
        if token:
            headers["authorization"] = f"Bearer {token}"
        response = self.client.request(
            method,
            f"{self.base_url}/api/v1{path}",
            headers=headers,
            json=json_body,
        )
        try:
            payload: Any = response.json()
        except ValueError:
            payload = response.text
        self.evidence.append(
            ApiEvidence(
                label=label,
                method=method,
                path=path,
                status_code=response.status_code,
                response=payload,
                role=role,
            )
        )
        return response

    def run(self) -> List[ScenarioResult]:
        return [
            self.auth_boundaries(),
            self.general_knowledge_chat(),
            self.hms_import_boundaries(),
            self.patient_linked_hms_answer(),
            self.denied_access_and_audit_trace(),
            self.shared_thread_lifecycle(),
        ]

    def auth_boundaries(self) -> ScenarioResult:
        result = ScenarioResult(
            name="auth and no-token boundary",
            severity_on_fail="P1 block",
            expected="Known dev tokens resolve to seeded users; no token and wrong token are blocked without PHI.",
        )

        anonymous = self.request("auth-anonymous", "GET", "/auth/me")
        wrong = self.request("auth-wrong-token", "GET", "/auth/me", token="wrong-token")
        result.evidence_labels.extend(["auth-anonymous", "auth-wrong-token"])
        if anonymous.status_code != 401 or wrong.status_code != 401:
            result.fail(f"Expected two 401 responses, got {anonymous.status_code} and {wrong.status_code}.")
            return result
        if response_contains_phi([anonymous, wrong]):
            result.fail("A blocked auth response exposed seeded patient content.")
            return result

        for token, expected_email in TOKENS.items():
            response = self.request(f"auth-{token}", "GET", "/auth/me", token=token)
            result.evidence_labels.append(f"auth-{token}")
            if response.status_code != 200:
                result.fail(f"{token} did not authenticate; status {response.status_code}.")
                return result
            payload = response.json()
            if payload.get("email") != expected_email:
                result.fail(f"{token} resolved to {payload.get('email')}, expected {expected_email}.")
                return result
            self.identities[token] = payload

        result.actual = "All seeded tokens authenticated; anonymous and wrong-token requests returned 401."
        return result

    def general_knowledge_chat(self) -> ScenarioResult:
        result = ScenarioResult(
            name="general knowledge thread answer",
            severity_on_fail="P2 fix before sign-off",
            expected="A general thread answers from approved non-PHI evidence with no patient_id.",
        )
        thread = self.create_thread(
            label="general-thread-create",
            token="dev-doctor",
            payload={
                "title": f"UAT general knowledge {short_run_id()}",
                "scope": "general",
                "patient_id": None,
                "visibility": "private",
            },
        )
        result.evidence_labels.append("general-thread-create")
        if thread is None:
            result.fail("General thread creation failed.")
            return result

        response = self.request(
            "general-thread-message",
            "POST",
            f"/chat-threads/{thread['id']}/messages",
            token="dev-doctor",
            json_body={
                "question": "What should a ward transfer request include?",
                "top_k": 5,
            },
        )
        result.evidence_labels.append("general-thread-message")
        if response.status_code != 200:
            result.fail(f"General question returned status {response.status_code}.")
            return result
        assistant = response.json()["assistant_message"]
        citations = assistant.get("citations", [])
        if assistant.get("patient_id") is not None or assistant.get("patient_permission_state") != "not-required":
            result.fail("General answer carried patient context or required patient permission.")
            return result
        if not citations:
            result.fail("General answer returned no approved citation for a seeded policy question.")
            return result
        metadata = citations[0].get("metadata", {})
        if metadata.get("approved_non_phi") is not True or metadata.get("contains_phi") is not False:
            result.fail(f"General citation metadata was not approved non-PHI: {metadata}.")
            return result
        result.actual = "General thread returned an approved non-PHI citation and no patient context."
        self.created_threads["general"] = thread
        return result

    def hms_import_boundaries(self) -> ScenarioResult:
        result = ScenarioResult(
            name="HMS appointment import role boundary",
            severity_on_fail="P1 block",
            expected="Records staff or admin can import appointment summaries; doctor import is denied.",
        )
        payload = appointment_payload(uuid.uuid4())
        records_response = self.request(
            "hms-import-records",
            "POST",
            "/hms/appointments/import",
            token="dev-records",
            json_body=payload,
        )
        doctor_response = self.request(
            "hms-import-doctor-denied",
            "POST",
            "/hms/appointments/import",
            token="dev-doctor",
            json_body=appointment_payload(uuid.uuid4()),
        )
        result.evidence_labels.extend(["hms-import-records", "hms-import-doctor-denied"])
        if records_response.status_code != 200:
            result.fail(f"Records import returned status {records_response.status_code}.")
            return result
        records_payload = records_response.json()
        if records_payload.get("source_family") != "appointments":
            result.fail(f"Records import did not preserve appointments family: {records_payload}.")
            return result
        if doctor_response.status_code != 403:
            result.fail(f"Doctor import should be denied with 403, got {doctor_response.status_code}.")
            return result
        if response_contains_phi([doctor_response]):
            result.fail("Denied doctor import response exposed seeded appointment content.")
            return result
        result.actual = "Records import succeeded with appointments lineage; doctor import was denied."
        return result

    def patient_linked_hms_answer(self) -> ScenarioResult:
        result = ScenarioResult(
            name="doctor patient-linked HMS appointment answer",
            severity_on_fail="P1 block",
            expected="Doctor asks about Alice and receives appointment evidence with source_family appointments.",
        )
        thread = self.create_thread(
            label="patient-thread-create",
            token="dev-doctor",
            payload={
                "title": f"UAT Alice appointment {short_run_id()}",
                "scope": "patient-linked",
                "patient_id": ALICE_PATIENT_ID,
                "visibility": "private",
            },
        )
        result.evidence_labels.append("patient-thread-create")
        if thread is None:
            result.fail("Doctor could not create Alice patient-linked thread.")
            return result
        self.created_threads["patient"] = thread

        response = self.request(
            "patient-thread-message",
            "POST",
            f"/chat-threads/{thread['id']}/messages",
            token="dev-doctor",
            json_body={
                "question": "What is the appointment status and vital signs?",
                "top_k": 5,
            },
        )
        result.evidence_labels.append("patient-thread-message")
        if response.status_code != 200:
            result.fail(f"Patient-linked question returned status {response.status_code}.")
            return result
        assistant = response.json()["assistant_message"]
        citations = assistant.get("citations", [])
        if assistant.get("patient_permission_state") != "allowed":
            result.fail(f"Patient answer permission state was {assistant.get('patient_permission_state')}.")
            return result
        appointment_citation = first_matching(
            citations,
            lambda item: item.get("metadata", {}).get("source_family") == "appointments",
        )
        if appointment_citation is None:
            result.fail(f"No appointment citation found in {len(citations)} citation(s).")
            return result
        metadata = appointment_citation.get("metadata", {})
        if metadata.get("source_system") != "hospital-management-system":
            result.fail(f"Appointment citation source system was wrong: {metadata}.")
            return result
        if metadata.get("patient_permission_required") is not True:
            result.fail(f"Appointment citation did not preserve patient permission flag: {metadata}.")
            return result
        result.actual = "Doctor answer cited HMS appointment evidence with source_family appointments."
        return result

    def denied_access_and_audit_trace(self) -> ScenarioResult:
        result = ScenarioResult(
            name="denied patient access and audit trace",
            severity_on_fail="P1 block",
            expected="A role without Alice read access is denied before evidence; security can review denial logs.",
        )
        denied = self.request(
            "records-patient-thread-denied",
            "POST",
            "/chat-threads",
            token="dev-records",
            json_body={
                "title": f"UAT records denied {short_run_id()}",
                "scope": "patient-linked",
                "patient_id": ALICE_PATIENT_ID,
                "visibility": "private",
            },
        )
        result.evidence_labels.append("records-patient-thread-denied")
        if denied.status_code != 403:
            result.fail(f"Records patient-linked thread creation should be denied, got {denied.status_code}.")
            return result
        if response_contains_phi([denied]):
            result.fail("Denied patient-linked response exposed seeded patient evidence.")
            return result

        audit = self.request("security-audit-events", "GET", "/audit/events?limit=20", token="dev-security")
        doctor_audit = self.request("doctor-audit-denied", "GET", "/audit/events?limit=5", token="dev-doctor")
        result.evidence_labels.extend(["security-audit-events", "doctor-audit-denied"])
        if audit.status_code != 200:
            result.fail(f"Security audit request returned status {audit.status_code}.")
            return result
        if doctor_audit.status_code != 403:
            result.fail(f"Doctor audit request should be denied with 403, got {doctor_audit.status_code}.")
            return result
        denied_event = first_matching(
            audit.json().get("items", []),
            lambda item: item.get("outcome") == "denied",
        )
        if denied_event is None:
            result.fail("Security audit feed did not include a denied event from the UAT pass.")
            return result
        result.actual = "Records access was denied, and security could review a denied audit event."
        return result

    def shared_thread_lifecycle(self) -> ScenarioResult:
        result = ScenarioResult(
            name="shared thread rename, share, reload, archive",
            severity_on_fail="P2 fix before sign-off",
            expected="Doctor can rename/share/archive a thread; admin sees shared persisted thread after reload.",
        )
        admin_id = self.identities.get("dev-admin", {}).get("id")
        if not admin_id:
            result.fail("Admin identity was not loaded before shared-thread scenario.")
            return result
        thread = self.create_thread(
            label="shared-thread-create",
            token="dev-doctor",
            payload={
                "title": f"UAT shared thread {short_run_id()}",
                "scope": "general",
                "patient_id": None,
                "visibility": "private",
            },
        )
        result.evidence_labels.append("shared-thread-create")
        if thread is None:
            result.fail("Shared general thread creation failed.")
            return result

        renamed_title = f"UAT renamed shared thread {short_run_id()}"
        rename = self.request(
            "shared-thread-rename",
            "PATCH",
            f"/chat-threads/{thread['id']}",
            token="dev-doctor",
            json_body={"title": renamed_title},
        )
        share = self.request(
            "shared-thread-share-admin",
            "POST",
            f"/chat-threads/{thread['id']}/participants",
            token="dev-doctor",
            json_body={"user_id": admin_id, "access_level": "read", "can_share": False},
        )
        admin_list = self.request("shared-thread-admin-reload", "GET", "/chat-threads", token="dev-admin")
        archive = self.request(
            "shared-thread-archive",
            "DELETE",
            f"/chat-threads/{thread['id']}",
            token="dev-doctor",
        )
        detail = self.request(
            "shared-thread-archived-detail",
            "GET",
            f"/chat-threads/{thread['id']}",
            token="dev-doctor",
        )
        result.evidence_labels.extend(
            [
                "shared-thread-rename",
                "shared-thread-share-admin",
                "shared-thread-admin-reload",
                "shared-thread-archive",
                "shared-thread-archived-detail",
            ]
        )
        if rename.status_code != 200 or rename.json().get("title") != renamed_title:
            result.fail(f"Rename failed or title did not persist: status {rename.status_code}.")
            return result
        if share.status_code != 200:
            result.fail(f"Share to admin failed with status {share.status_code}.")
            return result
        admin_threads = admin_list.json().get("items", []) if admin_list.status_code == 200 else []
        if not any(item.get("id") == thread["id"] and item.get("title") == renamed_title for item in admin_threads):
            result.fail("Admin reload did not show the shared renamed thread.")
            return result
        if archive.status_code != 200 or detail.status_code != 200 or detail.json().get("status") != "archived":
            result.fail("Archive did not persist to the thread detail response.")
            return result
        result.actual = "Rename, share, reload, and archive all persisted through backend APIs."
        return result

    def create_thread(
        self,
        *,
        label: str,
        token: str,
        payload: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        response = self.request(label, "POST", "/chat-threads", token=token, json_body=payload)
        if response.status_code != 200:
            return None
        return response.json()

    def write_artifacts(self, results: List[ScenarioResult]) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        evidence_payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "base_url": self.base_url,
            "results": [result.__dict__ for result in results],
            "requests": [evidence.__dict__ for evidence in self.evidence],
        }
        evidence_path = self.output_dir / "api-evidence.json"
        evidence_path.write_text(json.dumps(evidence_payload, indent=2, default=str) + "\n", encoding="utf-8")

        report_path = self.output_dir / "api-uat-summary.md"
        report_path.write_text(render_markdown_report(results, evidence_path), encoding="utf-8")
        return report_path


def appointment_payload(source_appointment_id: uuid.UUID) -> Dict[str, Any]:
    return {
        "source_appointment_id": str(source_appointment_id),
        "patient_id": ALICE_PATIENT_ID,
        "source_patient_id": ALICE_PATIENT_ID,
        "appointment_date": "2026-04-28",
        "status": "CHECKED_IN",
        "department": "Internal Medicine",
        "doctor_name": "Dr. Dev Doctor",
        "start_time": "09:00",
        "end_time": "09:30",
        "reason": "Synthetic follow-up visit",
        "symptoms": "Synthetic dizziness and medication review notes.",
        "vital_signs_summary": "Blood pressure 128/78, heart rate 78, oxygen saturation 98%.",
        "follow_up_summary": "Review symptoms and medication reconciliation at discharge planning.",
        "metadata": {"uat_run": True},
    }


def response_contains_phi(responses: Iterable[httpx.Response]) -> bool:
    for response in responses:
        text = response.text
        if any(term in text for term in PHI_LEAK_TERMS):
            return True
    return False


def first_matching(items: Iterable[Dict[str, Any]], predicate) -> Optional[Dict[str, Any]]:
    for item in items:
        if predicate(item):
            return item
    return None


def short_run_id() -> str:
    return uuid.uuid4().hex[:8]


def default_output_dir() -> Path:
    repo_root = Path(__file__).resolve().parents[3]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return repo_root / "history" / "kotaemon-chat-assistant-ui" / "uat-evidence" / timestamp


def render_markdown_report(results: List[ScenarioResult], evidence_path: Path) -> str:
    lines = [
        "# API UAT Summary",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Evidence JSON: `{evidence_path.name}`",
        "",
        "| Scenario | Severity if failed | Result | Evidence |",
        "|---|---|---|---|",
    ]
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        labels = ", ".join(f"`{label}`" for label in result.evidence_labels)
        lines.append(f"| {result.name} | {result.severity_on_fail} | {status} | {labels} |")

    lines.extend(["", "## Details", ""])
    for result in results:
        lines.extend(
            [
                f"### {result.name}",
                "",
                f"- Expected: {result.expected}",
                f"- Actual: {result.actual or 'No result recorded.'}",
                f"- Severity if failed: {result.severity_on_fail}",
                "",
            ]
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8000", help="Live FastAPI base URL.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_output_dir(),
        help="Directory for API UAT JSON and Markdown artifacts.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    runner = UatApiRunner(args.base_url, args.output_dir)
    try:
        results = runner.run()
        report_path = runner.write_artifacts(results)
    finally:
        runner.close()

    failed = [result for result in results if not result.passed]
    print(f"Wrote API UAT report to {report_path}")
    if failed:
        for result in failed:
            print(f"FAILED [{result.severity_on_fail}] {result.name}: {result.actual}", file=sys.stderr)
        return 1
    print("API UAT scenarios passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
