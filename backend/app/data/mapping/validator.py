from __future__ import annotations

from app.data.mapping.schema import DATASET_PROFILES, STANDARD_SCHEMA


class MappingValidator:
    """Validate mapping decisions against schema, duplicate, and profile-aware required-field rules."""

    @staticmethod
    def validate(
        mapping: list[dict[str, object]],
        dataset_profile: str = "generic",
    ) -> dict[str, object]:
        errors: list[str] = []
        warnings: list[str] = []
        mapped_fields: dict[str, str] = {}

        for item in mapping:
            target = item.get("target")
            ignored = bool(item.get("ignored", False))

            if ignored:
                continue

            if not target:
                continue

            if target not in STANDARD_SCHEMA:
                errors.append(f"Unknown target field: {target}")
                continue

            if target in mapped_fields:
                errors.append(f"Multiple columns mapped to {target}.")
                continue

            mapped_fields[target] = str(item.get("source", ""))

        profile_recommendations = set(DATASET_PROFILES.get(dataset_profile, set()))
        recommended_missing = [
            field_key
            for field_key in profile_recommendations
            if field_key in STANDARD_SCHEMA and field_key not in mapped_fields
        ]
        if recommended_missing and len(mapped_fields) < 3:
            errors.append(f"Missing required fields: {', '.join(recommended_missing)}")

        minimum_viable_mapping = 3
        if len(mapped_fields) < minimum_viable_mapping:
            errors.append("Missing required fields: at least 3 mapped columns are required for a valid dataset review")

        if recommended_missing and len(mapped_fields) >= minimum_viable_mapping:
            warnings.extend(f"Recommended field missing for {dataset_profile} profile: {field_key}" for field_key in recommended_missing)

        valid = not errors
        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "mapped_fields": mapped_fields,
        }
