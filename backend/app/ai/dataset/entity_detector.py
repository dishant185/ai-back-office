"""Entity Detector for AI Back-Office Copilot.

Identifies the primary business entity (grain) and categorical dimension entities
present in the tabular dataset (e.g., Employee, Order, Store, Vehicle, Customer).
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from app.ai.dataset.semantic_mapper import SemanticColumnMapping


class DetectedEntity(BaseModel):
    name: str
    entity_type: str  # primary_grain, dimension_entity, geographic_entity, temporal_entity
    column_name: str
    semantic_name: str
    unique_count: int | None = None


class EntityDetector:
    """Detects primary business entity and dimension entities."""

    PRIMARY_ENTITY_HEURISTICS = [
        ("employee", ["employee_id", "employee_age", "education_level", "leave_indicator"], "Employee"),
        ("order", ["order_id", "sales_amount", "quantity_ordered", "invoice"], "Sales Order"),
        ("inventory", ["sku", "stock_quantity", "pallet", "warehouse"], "Inventory Item"),
        ("customer", ["customer_id", "clv", "churn"], "Customer"),
        ("vehicle", ["vin", "dealer", "mileage", "make"], "Vehicle"),
    ]

    @classmethod
    def detect_entities(
        cls,
        columns: list[SemanticColumnMapping],
        domain: str = "generic",
    ) -> list[DetectedEntity]:
        entities: list[DetectedEntity] = []
        sem_names = {c.semantic_name: c for c in columns}

        # 1. Primary grain detection
        primary_assigned = False
        for entity_key, required_signals, display_name in cls.PRIMARY_ENTITY_HEURISTICS:
            if any(sig in sem_names for sig in required_signals):
                id_col = sem_names.get(f"{entity_key}_id")
                rep_col = id_col or list(sem_names.values())[0]
                entities.append(DetectedEntity(
                    name=display_name,
                    entity_type="primary_grain",
                    column_name=rep_col.original_name,
                    semantic_name=rep_col.semantic_name,
                ))
                primary_assigned = True
                break

        if not primary_assigned:
            # Fallback to first identifier or generic Record
            ident = next((c for c in columns if c.role == "identifier"), None)
            if ident:
                entities.append(DetectedEntity(
                    name=ident.original_name.replace("_", " ").title(),
                    entity_type="primary_grain",
                    column_name=ident.original_name,
                    semantic_name=ident.semantic_name,
                ))
            else:
                entities.append(DetectedEntity(
                    name="Record",
                    entity_type="primary_grain",
                    column_name=columns[0].original_name if columns else "record",
                    semantic_name="record",
                ))

        # 2. Dimension entities
        for c in columns:
            if c.role in ("dimension", "geographic_dimension"):
                etype = "geographic_entity" if c.role == "geographic_dimension" else "dimension_entity"
                entities.append(DetectedEntity(
                    name=c.original_name.replace("_", " ").title(),
                    entity_type=etype,
                    column_name=c.original_name,
                    semantic_name=c.semantic_name,
                ))
            elif c.role == "temporal_dimension":
                entities.append(DetectedEntity(
                    name=c.original_name.replace("_", " ").title(),
                    entity_type="temporal_entity",
                    column_name=c.original_name,
                    semantic_name=c.semantic_name,
                ))

        return entities
