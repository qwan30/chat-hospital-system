"""Deterministic Drug Interaction Catalog Service.

Loads clinical drug interaction matrix (CSV) and provides symmetric
lookups and mention-based pair matching.
"""

from __future__ import annotations

import csv
import functools
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from hospital_ai.services.graph_rag import ExtractedRelation

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CatalogInteraction:
    drug_a: str
    drug_b: str
    interaction_type: str
    severity: str
    mechanism_action: str
    clinical_recommendation: str


def _get_default_catalog_path() -> Path:
    current_dir = Path(__file__).resolve().parent
    # Check parent directory structures
    candidates = [
        current_dir.parents[2] / "data" / "drugs" / "drug_interaction_matrix.csv",
        current_dir.parents[1] / "data" / "drugs" / "drug_interaction_matrix.csv",
        Path("app/backend/data/drugs/drug_interaction_matrix.csv"),
        Path("data/drugs/drug_interaction_matrix.csv"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]


class DrugCatalogService:
    """Service to query drug interactions with symmetric bidirectional indexing."""

    def __init__(self, csv_path: Optional[Path] = None) -> None:
        self.csv_path = csv_path or _get_default_catalog_path()
        self._interactions: dict[tuple[str, str], CatalogInteraction] = {}
        self._known_drugs: set[str] = set()
        self._drug_regex: Optional[re.Pattern] = None
        self._load_catalog()

    def _load_catalog(self) -> None:
        if not self.csv_path.exists():
            logger.warning(
                "Drug interaction matrix file not found",
                extra={"path": str(self.csv_path)},
            )
            return

        try:
            with open(self.csv_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    drug_a = row.get("drug_a", "").strip().casefold()
                    drug_b = row.get("drug_b", "").strip().casefold()
                    if not drug_a or not drug_b:
                        continue

                    interaction_type = row.get("interaction_type", "interacts_with").strip().casefold()
                    severity = row.get("severity", "high").strip().casefold()
                    mechanism = row.get("mechanism_action", "").strip()
                    recommendation = row.get("clinical_recommendation", "").strip()

                    entry = CatalogInteraction(
                        drug_a=drug_a,
                        drug_b=drug_b,
                        interaction_type=interaction_type,
                        severity=severity,
                        mechanism_action=mechanism,
                        clinical_recommendation=recommendation,
                    )

                    key = (min(drug_a, drug_b), max(drug_a, drug_b))
                    self._interactions[key] = entry
                    self._known_drugs.add(drug_a)
                    self._known_drugs.add(drug_b)

            if self._known_drugs:
                sorted_drugs = sorted(self._known_drugs, key=len, reverse=True)
                escaped_drugs = [re.escape(d) for d in sorted_drugs]
                self._drug_regex = re.compile(
                    r"\b(" + "|".join(escaped_drugs) + r")\b",
                    re.IGNORECASE,
                )
        except Exception as e:
            logger.error("Failed to load drug interaction catalog: %s", e)

    @property
    def interactions(self) -> dict[tuple[str, str], CatalogInteraction]:
        return self._interactions

    @property
    def known_drugs(self) -> set[str]:
        return self._known_drugs

    def get_interaction(self, drug_a: str, drug_b: str) -> Optional[CatalogInteraction]:
        """Symmetric lookup for interaction between two drugs."""
        da = drug_a.strip().casefold()
        db = drug_b.strip().casefold()
        key = (min(da, db), max(da, db))
        return self._interactions.get(key)

    def extract_drug_mentions(self, text: str) -> list[str]:
        """Extract all known drug names mentioned in text."""
        if not self._drug_regex:
            return []
        matches = self._drug_regex.findall(text)
        # Unique preserving order
        seen = set()
        drugs = []
        for match in matches:
            norm = match.strip().casefold()
            if norm not in seen:
                seen.add(norm)
                drugs.append(norm)
        return drugs

    def find_interactions_in_text(self, text: str) -> list[ExtractedRelation]:
        """Identify mentioned drugs and return pairwise catalog interactions."""
        mentioned_drugs = self.extract_drug_mentions(text)
        if len(mentioned_drugs) < 2:
            return []

        relations: list[ExtractedRelation] = []
        for i in range(len(mentioned_drugs)):
            for j in range(i + 1, len(mentioned_drugs)):
                drug1 = mentioned_drugs[i]
                drug2 = mentioned_drugs[j]
                interaction = self.get_interaction(drug1, drug2)
                if interaction:
                    relations.append(
                        ExtractedRelation(
                            subject_label=interaction.drug_a,
                            object_label=interaction.drug_b,
                            relation_type="interacts_with",
                            normalized_value="interacts_with",
                            weight=1.0,
                            severity=interaction.severity,
                            source_layer="catalog",
                        )
                    )
        return relations


@functools.lru_cache(maxsize=1)
def get_drug_catalog_service() -> DrugCatalogService:
    """Cached singleton provider for DrugCatalogService."""
    return DrugCatalogService()
