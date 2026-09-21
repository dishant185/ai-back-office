"""Duplicate Claim Detector Re-export for AI Validation layer."""
from app.reporting.duplicate_claim_detector import (
    DuplicateClaimDetector,
    DuplicateDetectionResult,
)

__all__ = [
    "DuplicateClaimDetector",
    "DuplicateDetectionResult",
]
