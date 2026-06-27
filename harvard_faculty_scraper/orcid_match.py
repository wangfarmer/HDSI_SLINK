from __future__ import annotations

import csv
import re
from collections import defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

from .utils import clean_text


FOLDER_HASH_SUFFIX_RE = re.compile(r"__[\da-f]{8}$")
NON_ALNUM_RE = re.compile(r"[^\w\s]")
INSTITUTION_SUFFIXES = (
    "Radcliffe Institute for Advanced Study at Harvard University",
)


@dataclass(frozen=True)
class OrcidPerson:
    orcid: str
    full_name: str
    given_name: str
    family_name: str
    credit_name: str


@dataclass(frozen=True)
class OrcidMatch:
    orcid: str
    matched_name: str
    method: str
    score: float


def load_orcid_people(csv_path: Path) -> list[OrcidPerson]:
    people: list[OrcidPerson] = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            orcid = (row.get("ORCID") or "").strip()
            if not orcid:
                continue
            people.append(
                OrcidPerson(
                    orcid=orcid,
                    full_name=(row.get("full_name") or "").strip(),
                    given_name=(row.get("given_name") or "").strip(),
                    family_name=(row.get("family_name") or "").strip(),
                    credit_name=(row.get("credit_name") or "").strip(),
                )
            )
    return people


def strip_folder_artifacts(name: str) -> str:
    value = FOLDER_HASH_SUFFIX_RE.sub("", name).strip()
    if "|" in value:
        value = value.split("|", 1)[0].strip()
    for suffix in INSTITUTION_SUFFIXES:
        if value.endswith(suffix):
            value = value[: -len(suffix)].strip()
    return value


def normalize_name_key(name: str) -> str:
    value = strip_folder_artifacts(clean_text(name) or "")
    value = value.lower()
    value = NON_ALNUM_RE.sub(" ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def significant_tokens(name: str) -> list[str]:
    tokens = normalize_name_key(name).split()
    if len(tokens) <= 2:
        return tokens
    return [token for token in tokens if len(token) > 1]


def collapsed_name(name: str) -> str:
    return " ".join(significant_tokens(name))


def core_pair(name: str) -> tuple[str, str] | None:
    tokens = significant_tokens(name)
    if len(tokens) < 2:
        return None
    return tokens[0], tokens[-1]


def name_similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, collapsed_name(left), collapsed_name(right)).ratio()


def person_exact_variants(person: OrcidPerson) -> list[str]:
    return [person.full_name, person.credit_name]


def person_fuzzy_variants(person: OrcidPerson) -> list[str]:
    variants = person_exact_variants(person)
    composed = f"{person.given_name} {person.family_name}".strip()
    if composed:
        variants.append(composed)
    if person.given_name and person.family_name:
        variants.append(f"{person.given_name[0]} {person.family_name}")
    deduped: list[str] = []
    seen: set[str] = set()
    for variant in variants:
        normalized = normalize_name_key(variant)
        if normalized and normalized not in seen:
            seen.add(normalized)
            deduped.append(variant)
    return deduped


class OrcidNameIndex:
    """Lookup ORCID records by exact and fuzzy person-name variants."""

    def __init__(self, people: list[OrcidPerson]) -> None:
        self.people = people
        self.by_exact: dict[str, list[OrcidPerson]] = defaultdict(list)
        self.by_core: dict[tuple[str, str], list[OrcidPerson]] = defaultdict(list)
        for person in people:
            for variant in person_exact_variants(person):
                self.by_exact[normalize_name_key(variant)].append(person)
            pair = core_pair(person.full_name)
            if pair:
                self.by_core[pair].append(person)
            elif pair := core_pair(f"{person.given_name} {person.family_name}"):
                self.by_core[pair].append(person)

    def match(self, query_name: str, *, fuzzy_threshold: float = 0.86) -> OrcidMatch | None:
        cleaned = clean_text(query_name)
        if not cleaned:
            return None

        exact_key = normalize_name_key(cleaned)
        if exact_key in self.by_exact:
            person = self._pick_best_candidate(cleaned, self.by_exact[exact_key])
            return OrcidMatch(person.orcid, person.full_name, "exact", 1.0)

        pair = core_pair(cleaned)
        if pair is None:
            return None

        candidates = self._unique_people(self.by_core.get(pair, []))
        if not candidates:
            return None

        scored = sorted(
            ((name_similarity(cleaned, person.full_name), person) for person in candidates),
            key=lambda item: (item[0], item[1].orcid),
            reverse=True,
        )
        best_score, best_person = scored[0]
        if len(scored) > 1 and best_score - scored[1][0] < 0.03 and best_score < 0.95:
            return None

        collapsed_query = collapsed_name(cleaned)
        core_matches = self._unique_people(
            [
                person
                for person in candidates
                for variant in person_fuzzy_variants(person)
                if collapsed_name(variant) == collapsed_query
            ]
        )
        if len(core_matches) == 1:
            person = core_matches[0]
            return OrcidMatch(person.orcid, person.full_name, "core_name", 0.98)
        if len(core_matches) > 1:
            return None

        if best_score >= fuzzy_threshold:
            method = "fuzzy" if best_score < 0.98 else "core_name"
            return OrcidMatch(best_person.orcid, best_person.full_name, method, round(best_score, 4))

        return None

    def _pick_best_candidate(self, query_name: str, candidates: list[OrcidPerson]) -> OrcidPerson:
        unique = self._unique_people(candidates)
        if len(unique) == 1:
            return unique[0]
        return max(unique, key=lambda person: name_similarity(query_name, person.full_name))

    @staticmethod
    def _unique_people(candidates: list[OrcidPerson]) -> list[OrcidPerson]:
        seen: set[str] = set()
        unique: list[OrcidPerson] = []
        for person in candidates:
            if person.orcid in seen:
                continue
            seen.add(person.orcid)
            unique.append(person)
        return unique
