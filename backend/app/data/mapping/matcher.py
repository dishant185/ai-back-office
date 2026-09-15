from __future__ import annotations

import re
from itertools import chain

from rapidfuzz import fuzz

from app.data.mapping.aliases import alias_registry
from app.data.mapping.normalizer import ColumnNormalizer
from app.data.mapping.schema import STANDARD_SCHEMA


# ── Constants ─────────────────────────────────────────────────────────────────

AMBIGUOUS_GENERIC_FIELDS = {
    "amount", "date", "value", "total", "status", "description", "category",
}

# Minimum fuzzy score to consider a match viable
_FUZZY_ACCEPT_THRESHOLD = 62

# Minimum score gap between top-1 and top-2 to auto-accept
_AMBIGUITY_GAP = 8

# Common abbreviation expansions for business columns
_ABBREVIATIONS: dict[str, str] = {
    "qty": "quantity",
    "amt": "amount",
    "desc": "description",
    "dept": "department",
    "emp": "employee",
    "cust": "customer",
    "txn": "transaction",
    "inv": "invoice",
    "yr": "year",
    "mo": "month",
    "num": "number",
    "no": "number",
    "pct": "percentage",
    "perc": "percentage",
    "id": "identifier",
    "sal": "salary",
    "mgr": "manager",
    "org": "organization",
    "loc": "location",
    "addr": "address",
    "tel": "telephone",
    "ph": "phone",
    "dt": "date",
    "curr": "current",
    "prev": "previous",
    "avg": "average",
    "tot": "total",
    "min": "minimum",
    "max": "maximum",
    "exp": "experience",
    "edu": "education",
    "pos": "position",
    "lvl": "level",
    "grp": "group",
    "cat": "category",
    "sub": "subcategory",
    "prod": "product",
    "rev": "revenue",
    "comp": "compensation",
    "ben": "benefit",
    "elig": "eligible",
    "stat": "status",
    "reg": "region",
    "terr": "territory",
    "acct": "account",
    "src": "source",
    "tgt": "target",
    "ach": "achievement",
    "sku": "sku",
    "stk": "stock",
    "rcv": "received",
    "sld": "sold",
    "cls": "closing",
    "opn": "opening",
    "pmnt": "payment",
    "mthd": "method",
    "dlr": "dealer",
    "br": "branch",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _expand_abbreviations(text: str) -> str:
    """Expand known abbreviations in a normalized string."""
    tokens = text.split()
    expanded = [_ABBREVIATIONS.get(tok, tok) for tok in tokens]
    return " ".join(expanded)


def _ngrams(text: str, n: int = 3) -> set[str]:
    """Return character n-grams for a string."""
    if len(text) < n:
        return {text}
    return {text[i:i + n] for i in range(len(text) - n + 1)}


def _ngram_similarity(a: str, b: str, n: int = 3) -> float:
    """Jaccard similarity of character n-grams."""
    if not a or not b:
        return 0.0
    grams_a = _ngrams(a, n)
    grams_b = _ngrams(b, n)
    intersection = len(grams_a & grams_b)
    union = len(grams_a | grams_b)
    return intersection / max(union, 1)


def _substring_score(source: str, target: str) -> float:
    """Check if one string is a substring of the other.

    Returns a score 0-100 based on how much of the longer string is covered.
    """
    if not source or not target:
        return 0.0
    if source in target:
        return (len(source) / len(target)) * 100
    if target in source:
        return (len(target) / len(source)) * 100
    return 0.0


def _build_candidate_strings(field_key: str) -> list[str]:
    """Build all candidate normalized strings for a standard field.

    This consolidates the field key, label, and all aliases into a single
    flat list of normalized strings used for matching.
    """
    field = STANDARD_SCHEMA[field_key]
    candidates: list[str] = []

    # Primary candidates
    candidates.append(ColumnNormalizer.normalize(field_key))
    candidates.append(ColumnNormalizer.normalize(field_key.replace("_", " ")))
    candidates.append(ColumnNormalizer.normalize(field.label))

    # Schema-defined aliases
    for alias in field.aliases:
        candidates.append(ColumnNormalizer.normalize(alias))

    # Registry aliases (includes schema aliases + extra_aliases)
    for alias in alias_registry.get(field_key, []):
        candidates.append(ColumnNormalizer.normalize(alias))

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            unique.append(c)
    return unique


# ── Pre-built lookup table (built once at import time) ────────────────────────

_FIELD_CANDIDATES: dict[str, list[str]] = {
    field_key: _build_candidate_strings(field_key)
    for field_key in STANDARD_SCHEMA
}


# ── Main Matcher ──────────────────────────────────────────────────────────────

class ColumnMatcher:
    """Production-grade column matcher using multi-strategy fuzzy matching.

    Matching strategies (applied in order of confidence):
      1. Exact key match
      2. Normalized label / alias exact match
      3. Abbreviation-expanded exact match
      4. RapidFuzz ratio, partial_ratio, token_sort_ratio
      5. Substring containment scoring
      6. Character n-gram Jaccard similarity
      7. Abbreviation-expanded fuzzy match
    """

    def match_columns(self, source_columns: list[str]) -> list[dict[str, object]]:
        """Match a list of source columns, ensuring no duplicate target assignments.

        Uses a greedy best-first assignment strategy to prevent two source columns
        from mapping to the same target field.
        """
        # Phase 1: Score every source against every target
        all_results: list[tuple[int, dict[str, object]]] = []
        for col in source_columns:
            result = self._score_column(col)
            all_results.append((source_columns.index(col), result))

        # Phase 2: Greedy assignment — highest confidence first
        scored = [
            (idx, res) for idx, res in all_results
            if res["suggested_target"] is not None
        ]
        scored.sort(key=lambda x: -x[1]["confidence"])

        assigned_targets: set[str] = set()
        final_results: dict[int, dict[str, object]] = {}

        for idx, res in scored:
            target = res["suggested_target"]
            if target not in assigned_targets:
                assigned_targets.add(target)
                final_results[idx] = res
            else:
                # Target already taken — demote to needs_review
                final_results[idx] = {
                    "source": res["source"],
                    "suggested_target": None,
                    "confidence": 0,
                    "status": "needs_review",
                    "reason": f"Target '{target}' already assigned to another column",
                }

        # Phase 3: Add unmatched columns
        for idx, res in all_results:
            if idx not in final_results:
                final_results[idx] = res

        return [final_results[i] for i in range(len(source_columns))]

    def match_column(self, source_name: str) -> dict[str, object]:
        """Match a single column name to the best standard field."""
        return self._score_column(source_name)

    def _score_column(self, source_name: str) -> dict[str, object]:
        """Internal scoring engine for a single column."""
        normalized = ColumnNormalizer.normalize(source_name)

        if not normalized:
            return self._no_match(source_name, "Empty column name")

        # Strategy 0: Ambiguous generic field guard
        if normalized in AMBIGUOUS_GENERIC_FIELDS:
            # Still try exact key match first
            if normalized in STANDARD_SCHEMA:
                return self._make_result(source_name, normalized, 70, "Generic field with exact key match")
            return self._no_match(source_name, "Generic field name requires human review")

        # Expand abbreviations for the source
        expanded = _expand_abbreviations(normalized)

        best_matches: list[tuple[str, int, str]] = []

        for field_key, candidates in _FIELD_CANDIDATES.items():
            score, reason = self._multi_strategy_score(
                normalized, expanded, field_key, candidates
            )
            if score > 0:
                best_matches.append((field_key, score, reason))

        if not best_matches:
            return self._no_match(source_name, "No confident match found")

        # Sort by score descending, then field_key for stability
        best_matches.sort(key=lambda item: (-item[1], item[0]))
        top_field, top_score, top_reason = best_matches[0]

        # Ambiguity check: if top-2 are very close and score is moderate
        if len(best_matches) > 1:
            second_score = best_matches[1][1]
            if top_score - second_score < _AMBIGUITY_GAP and top_score < 88:
                return {
                    "source": source_name,
                    "suggested_target": top_field,
                    "confidence": top_score,
                    "status": "needs_review",
                    "reason": f"Ambiguous: close match with '{best_matches[1][0]}' (gap={top_score - second_score})",
                }

        status = "suggested" if top_score >= 55 else "needs_review"
        return self._make_result(source_name, top_field, top_score, top_reason, status)

    def _multi_strategy_score(
        self,
        normalized: str,
        expanded: str,
        field_key: str,
        candidates: list[str],
    ) -> tuple[int, str]:
        """Run all matching strategies and return the best (score, reason)."""
        best_score = 0
        best_reason = ""

        # --- Strategy 1: Exact match against key ---
        if normalized == ColumnNormalizer.normalize(field_key):
            return 100, "Exact standardized field name match"

        # --- Strategy 2: Exact match against any candidate ---
        if normalized in candidates:
            return 97, "Exact alias / label match"

        # --- Strategy 3: Abbreviation-expanded exact match ---
        expanded_candidates = [_expand_abbreviations(c) for c in candidates]
        if expanded in expanded_candidates:
            return 94, "Abbreviation-expanded exact match"
        if expanded in candidates:
            return 94, "Abbreviation-expanded match"

        # --- Strategy 4: RapidFuzz scoring against all candidates ---
        source_len = len(normalized)
        for candidate in chain(candidates, expanded_candidates):
            cand_len = len(candidate)
            # Length ratio: penalize when lengths are very different
            len_ratio = min(source_len, cand_len) / max(source_len, cand_len, 1)

            # Standard ratio (full string similarity) — most reliable
            ratio = fuzz.ratio(normalized, candidate)
            if ratio > best_score:
                best_score = ratio
                best_reason = f"Fuzzy ratio match ({ratio}%)"

            # Partial ratio — dampen based on length difference to prevent
            # short substrings matching ("age" in "achievement percentage")
            partial = fuzz.partial_ratio(normalized, candidate)
            # Apply length penalty: if source is much shorter, partial_ratio
            # is unreliable. Scale partial score by length ratio.
            if len_ratio < 0.5:
                partial = int(partial * len_ratio * 1.2)  # Heavy penalty
            elif len_ratio < 0.75:
                partial = int(partial * (0.6 + len_ratio * 0.4))  # Moderate penalty
            if partial > best_score:
                best_score = partial
                best_reason = f"Fuzzy partial match ({partial}%)"

            # Token sort ratio (order-independent)
            token_sort = fuzz.token_sort_ratio(normalized, candidate)
            if token_sort > best_score:
                best_score = token_sort
                best_reason = f"Fuzzy token-sort match ({token_sort}%)"

            # Token set ratio — powerful but can over-match when strings share
            # only a subset of words. Apply graduated penalty based on overlap.
            token_set = fuzz.token_set_ratio(normalized, candidate)
            source_words = set(normalized.split())
            cand_words = set(candidate.split())
            word_overlap = len(source_words & cand_words)
            total_words = max(len(source_words | cand_words), 1)
            word_ratio = word_overlap / total_words
            # Graduated penalty: if fewer than 75% of words overlap, penalize
            if word_ratio < 0.4:
                token_set = int(token_set * word_ratio * 1.1)  # Heavy penalty
            elif word_ratio < 0.75:
                token_set = int(token_set * (0.3 + word_ratio * 0.7))  # Moderate penalty
            if token_set > best_score:
                best_score = token_set
                best_reason = f"Fuzzy token-set match ({token_set}%)"

            # Check expanded source vs candidate
            if expanded != normalized:
                exp_ratio = fuzz.token_sort_ratio(expanded, candidate)
                if exp_ratio > best_score:
                    best_score = exp_ratio
                    best_reason = f"Abbreviation-expanded fuzzy match ({exp_ratio}%)"

        # --- Strategy 5: Substring containment ---
        for candidate in candidates:
            sub_score = _substring_score(normalized, candidate)
            if sub_score > 70:  # Only accept strong substring matches
                adj_score = int(min(sub_score * 0.85, 88))
                if adj_score > best_score:
                    best_score = adj_score
                    best_reason = f"Substring containment match ({sub_score:.0f}%)"

        # --- Strategy 6: N-gram similarity (fallback) ---
        for candidate in candidates:
            ngram_sim = _ngram_similarity(normalized, candidate)
            if ngram_sim > 0.45:
                adj_score = int(min(ngram_sim * 95, 82))
                if adj_score > best_score:
                    best_score = adj_score
                    best_reason = f"N-gram similarity match ({ngram_sim:.2f})"

        # Apply threshold
        if best_score < _FUZZY_ACCEPT_THRESHOLD:
            return 0, ""

        return best_score, best_reason

    @staticmethod
    def _make_result(
        source: str,
        target: str,
        confidence: int,
        reason: str,
        status: str | None = None,
    ) -> dict[str, object]:
        if status is None:
            status = "suggested" if confidence >= 55 else "needs_review"
        return {
            "source": source,
            "suggested_target": target,
            "confidence": confidence,
            "status": status,
            "reason": reason,
        }

    @staticmethod
    def _no_match(source: str, reason: str) -> dict[str, object]:
        return {
            "source": source,
            "suggested_target": None,
            "confidence": 0,
            "status": "needs_review",
            "reason": reason,
        }
