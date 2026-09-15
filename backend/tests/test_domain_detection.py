from __future__ import annotations

import pandas as pd
from app.reporting.domain_detector import DomainDetector
from app.reporting.semantic_detector import SemanticDetector


def test_hr_domain_detection() -> None:
    df = pd.DataFrame({
        "Education": ["Bachelors", "Masters"],
        "JoiningYear": [2017, 2018],
        "City": ["Bangalore", "Pune"],
        "PaymentTier": [3, 2],
        "Age": [28, 31],
        "LeaveOrNot": [0, 1],
    })
    fields = SemanticDetector.detect_all(df)
    domain, conf, _ = DomainDetector.detect(fields)
    assert domain == "hr"
    assert conf > 0.5


def test_sales_domain_detection() -> None:
    df = pd.DataFrame({
        "Revenue": [100.0, 200.0],
        "Profit": [20.0, 40.0],
        "Quantity": [1, 2],
        "Product": ["Widget A", "Widget B"],
    })
    fields = SemanticDetector.detect_all(df)
    domain, conf, _ = DomainDetector.detect(fields)
    assert domain == "sales"
    assert conf > 0.5


def test_generic_fallback_detection() -> None:
    df = pd.DataFrame({
        "Alpha": [1, 2, 3],
        "Beta": ["A", "B", "C"],
        "Gamma": [10.5, 20.5, 30.5],
    })
    fields = SemanticDetector.detect_all(df)
    domain, conf, _ = DomainDetector.detect(fields)
    assert domain == "generic"
