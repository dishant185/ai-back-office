"""Pytest configuration and shared fixtures for AI Back-Office Copilot."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.db.database import get_accounts_collection
from app.db.mongodb import get_users_collection
from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def test_user() -> dict[str, str]:
    user_id = "usr_test_fixture_01"
    account_id = "acc_test_fixture_01"
    email = "testfixture@example.com"

    users_col = get_users_collection()
    users_col.update_one(
        {"id": user_id},
        {
            "$set": {
                "id": user_id,
                "user_id": user_id,
                "account_id": account_id,
                "workspace_id": "default",
                "email": email,
                "hashed_password": hash_password("secret123"),
                "name": "Test Fixture",
                "role": "user",
            }
        },
        upsert=True,
    )

    accounts_col = get_accounts_collection()
    accounts_col.update_one(
        {"account_id": account_id},
        {
            "$set": {
                "account_id": account_id,
                "name": "Test Workspace",
                "owner_user_id": user_id,
            }
        },
        upsert=True,
    )

    token = create_access_token({"sub": user_id, "email": email})
    return {
        "user_id": user_id,
        "account_id": account_id,
        "email": email,
        "token": token,
    }


@pytest.fixture
def auth_headers(test_user: dict[str, str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {test_user['token']}"}
