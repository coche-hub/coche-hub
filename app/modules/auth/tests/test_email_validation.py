from datetime import datetime, timedelta, timezone

import pytest

from app import db
from app.modules.auth.models import EmailValidationCode, User
from app.modules.auth.services import EmailValidationService
from app.modules.profile.models import UserProfile


@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    """
    with test_client.application.app_context():
        # Create a test user with profile for email validation tests
        user = User(email="validation_test@example.com", password="test1234")
        db.session.add(user)
        db.session.flush()

        profile = UserProfile(user_id=user.id, name="Validation", surname="Test")
        db.session.add(profile)
        db.session.commit()

    yield test_client


def test_send_validation_email(test_client):
    """Test that validation email is sent successfully"""
    with test_client.application.app_context():
        user = User.query.filter_by(email="validation_test@example.com").first()
        assert user is not None

        service = EmailValidationService()
        service.send_validation_email(user.id)

        code = EmailValidationCode.query.filter_by(user_id=user.id).first()
        assert code is not None
        current_time = datetime.now(tz=timezone.utc)
        code_valid_until = (
            code.valid_until if code.valid_until.tzinfo else code.valid_until.replace(tzinfo=timezone.utc)
        )
        assert code_valid_until > current_time


def test_validate_email_with_valid_code(test_client):
    """Test email validation with a valid code"""
    with test_client.application.app_context():
        user = User.query.filter_by(email="validation_test@example.com").first()
        assert user is not None
        assert not user.email_validated

        service = EmailValidationService()
        service.send_validation_email(user.id)

        code = EmailValidationCode.query.filter_by(user_id=user.id).first()
        assert code is not None

        result = service.validate_email(user.id, str(code.id))
        assert result is True

        db.session.refresh(user)
        assert user.email_validated is True


def test_validate_email_with_invalid_code(test_client):
    """Test email validation with an invalid code"""
    with test_client.application.app_context():
        user = User(email="invalid_code_test@example.com", password="test1234")
        db.session.add(user)
        db.session.flush()

        profile = UserProfile(user_id=user.id, name="Invalid", surname="Code")
        db.session.add(profile)
        db.session.commit()

        service = EmailValidationService()
        result = service.validate_email(user.id, "00000000-0000-0000-0000-000000000000")
        assert result is False

        db.session.refresh(user)
        assert user.email_validated is False


def test_validate_email_with_malformed_code(test_client):
    """Test email validation with a malformed code"""
    with test_client.application.app_context():
        user = User(email="malformed_code_test@example.com", password="test1234")
        db.session.add(user)
        db.session.flush()

        profile = UserProfile(user_id=user.id, name="Malformed", surname="Code")
        db.session.add(profile)
        db.session.commit()

        service = EmailValidationService()
        result = service.validate_email(user.id, "not-a-valid-uuid")
        assert result is False

        db.session.refresh(user)
        assert user.email_validated is False


def test_validate_email_with_expired_code(test_client):
    """Test email validation with an expired code"""
    with test_client.application.app_context():
        user = User(email="expired_code_test@example.com", password="test1234")
        db.session.add(user)
        db.session.flush()

        profile = UserProfile(user_id=user.id, name="Expired", surname="Code")
        db.session.add(profile)
        db.session.commit()

        expired_code = EmailValidationCode(
            user_id=user.id,
            created_at=datetime.now(tz=timezone.utc) - timedelta(hours=1),
            valid_until=datetime.now(tz=timezone.utc) - timedelta(minutes=1),
        )
        db.session.add(expired_code)
        db.session.commit()

        service = EmailValidationService()
        result = service.validate_email(user.id, str(expired_code.id))
        assert result is False

        db.session.refresh(user)
        assert user.email_validated is False


def test_validate_email_already_validated(test_client):
    """Test email validation when email is already validated"""
    with test_client.application.app_context():
        user = User(email="already_validated_test@example.com", password="test1234")
        db.session.add(user)
        db.session.flush()

        profile = UserProfile(user_id=user.id, name="Already", surname="Validated")
        db.session.add(profile)
        db.session.commit()

        user.email_validated = True
        db.session.commit()

        service = EmailValidationService()
        result = service.validate_email(user.id, "any-code")
        assert result is True


def test_validation_endpoint_requires_authentication(test_client):
    """Test that the validation endpoint requires authentication"""
    response = test_client.get("/validate_email/some-code")

    assert response.status_code == 302
    assert "/login" in response.location


def test_validation_endpoint_with_valid_code(test_client):
    """Test the validation endpoint with a valid code"""
    with test_client.application.app_context():
        user = User(email="endpoint_test@example.com", password="test1234")
        db.session.add(user)
        db.session.flush()

        profile = UserProfile(user_id=user.id, name="Endpoint", surname="Test")
        db.session.add(profile)
        db.session.commit()

        service = EmailValidationService()
        service.send_validation_email(user.id)

        code = EmailValidationCode.query.filter_by(user_id=user.id).first()

    test_client.post("/login", data=dict(email="endpoint_test@example.com", password="test1234"), follow_redirects=True)
    response = test_client.get(f"/validate_email/{code.id}", follow_redirects=True)

    assert response.status_code == 200
    assert b"Email Validation" in response.data or b"successfully validated" in response.data

    test_client.get("/logout", follow_redirects=True)


def test_validation_endpoint_with_invalid_code(test_client):
    """Test the validation endpoint with an invalid code"""
    test_client.post("/login", data=dict(email="test@example.com", password="test1234"), follow_redirects=True)
    response = test_client.get("/validate_email/00000000-0000-0000-0000-000000000000", follow_redirects=True)

    assert response.status_code == 200
    assert b"Email Validation" in response.data or b"could not validate" in response.data

    test_client.get("/logout", follow_redirects=True)
