import asyncio

import pytest
from fastapi import HTTPException
from jose import jwt
from pydantic import ValidationError

from app.auth.schemas import SignupRequest
from app.core.config import settings
from app.core.security import (
    JWT_ALGORITHM,
    CurrentUser,
    Role,
    create_access_token,
    hash_password,
    require_roles,
    verify_password,
)


def test_password_hash_is_not_plaintext_and_can_be_verified():
    password_hash = hash_password("strong-password")

    assert password_hash != "strong-password"
    assert verify_password("strong-password", password_hash)
    assert not verify_password("wrong-password", password_hash)


def test_access_token_contains_the_user_id():
    token = create_access_token("user-123")
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])

    assert payload["sub"] == "user-123"
    assert "exp" in payload


def test_public_signup_rejects_admin_role():
    with pytest.raises(ValidationError):
        SignupRequest(
            email="admin@example.com",
            password="strong-password",
            role="admin",
        )


def test_signup_accepts_an_iana_timezone():
    request = SignupRequest(
        email="student@example.com",
        password="strong-password",
        timezone="America/New_York",
    )

    assert request.timezone == "America/New_York"


def test_signup_rejects_invalid_timezone():
    with pytest.raises(ValidationError):
        SignupRequest(
            email="student@example.com",
            password="strong-password",
            timezone="Not/A_Timezone",
        )


def test_role_dependency_rejects_the_wrong_role():
    tutor_only = require_roles(Role.tutor)
    student = CurrentUser(
        id="student-123",
        email="student@example.com",
        role=Role.student,
    )

    with pytest.raises(HTTPException) as error:
        asyncio.run(tutor_only(student))

    assert error.value.status_code == 403
