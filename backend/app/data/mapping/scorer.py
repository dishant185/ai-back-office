from __future__ import annotations

from rapidfuzz import fuzz

from app.data.mapping.aliases import alias_registry
from app.data.mapping.normalizer import ColumnNormalizer


class ConfidenceScorer:
    """Confidence scoring engine with graduated tiers.

    Scoring tiers:
        100  – Exact field-key match
         97  – Exact alias / label match
         94  – Abbreviation-expanded exact match
      85-93  – Strong fuzzy match (ratio >= 85)
      70-84  – Moderate fuzzy match
      55-69  – Weak but plausible match
       < 55  – Not confident enough
    """

    @staticmethod
    def score(source: str, target: str, reason: str) -> tuple[int, str]:
        normalized_source = ColumnNormalizer.normalize(source)
        normalized_target = ColumnNormalizer.normalize(target)

        # Tier 1: Exact field key match
        if normalized_source == normalized_target:
            return 100, "Exact standardized field name match"

        # Tier 2: Direct alias match (unnormalized lookup)
        aliases_raw = alias_registry.get(target, [])
        if normalized_source in aliases_raw:
            return 97, "Alias exact match"

        # Tier 3: Normalized alias match
        normalized_aliases = {ColumnNormalizer.normalize(a) for a in aliases_raw}
        if normalized_source in normalized_aliases:
            return 95, "Canonical alias match"

        # Tier 4: Prefix / suffix match
        if normalized_source.startswith(normalized_target) or normalized_target.startswith(normalized_source):
            coverage = min(len(normalized_source), len(normalized_target)) / max(len(normalized_source), len(normalized_target), 1)
            if coverage >= 0.6:
                return int(80 + coverage * 15), "Strong prefix/suffix similarity"
            return 75, "Moderate prefix/suffix similarity"

        # Tier 5: Fuzzy similarity
        best_fuzzy = 0
        for alias in normalized_aliases | {normalized_target}:
            r = fuzz.token_sort_ratio(normalized_source, alias)
            best_fuzzy = max(best_fuzzy, r)

        if best_fuzzy >= 85:
            return min(int(best_fuzzy * 0.95), 93), f"Strong fuzzy similarity ({best_fuzzy}%)"
        if best_fuzzy >= 70:
            return int(best_fuzzy * 0.90), f"Moderate fuzzy similarity ({best_fuzzy}%)"
        if best_fuzzy >= 55:
            return int(best_fuzzy * 0.85), f"Weak fuzzy similarity ({best_fuzzy}%)"

        # Fallback
        if reason:
            return max(55, int(best_fuzzy * 0.80)), reason
        return 0, "No confident match"
