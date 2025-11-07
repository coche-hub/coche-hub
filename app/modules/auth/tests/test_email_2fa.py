from datetime import datetime, timedelta, timezone

import pytest

from app import db, mail
from app.modules.auth.models import Email2FACode, TwoFAAttempt, User
from app.modules.auth.services import Email2FAService, TwoFARateLimitExceeded
from app.modules.profile.models import UserProfile


@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    """
    with test_client.application.app_context():
        # Create a test user with validated email for 2FA tests
        user = User(email="2fa_test@example.com", password="test1234")
        user.email_validated = True
        db.session.add(user)
        db.session.flush()

        profile = UserProfile(user_id=user.id, name="TwoFA", surname="Test")
        db.session.add(profile)
        db.session.commit()

    yield test_client


def test_generate_code(test_client):
    """Test that code generation produces a 6-digit string"""
    with test_client.application.app_context():
        service = Email2FAService()
        code = service.generate_code()

        assert len(code) == 6
        assert code.isdigit()
        assert 0 <= int(code) <= 999999


def test_send_2fa_code(test_client):
    """Test that 2FA code is sent successfully"""
    with test_client.application.app_context():
        user = User.query.filter_by(email="2fa_test@example.com").first()
        assert user is not None
        assert user.email_validated is True

        with mail.record_messages() as outbox:
            service = Email2FAService()
            code = service.send_2fa_code(user.id)

            assert len(outbox) == 1
            assert outbox[0].subject == "Your Coche-Hub 2FA Code"
            assert code in outbox[0].html
            assert len(code) == 6

        # Verify code was stored in database
        db_code = Email2FACode.query.filter_by(user_id=user.id, code=code).first()
        assert db_code is not None
        current_time = datetime.now(tz=timezone.utc)
        code_valid_until = (
            db_code.valid_until if db_code.valid_until.tzinfo else db_code.valid_until.replace(tzinfo=timezone.utc)
        )
        assert code_valid_until > current_time


def test_verify_2fa_code_with_valid_code(test_client):
    """Test 2FA verification with a valid code"""
    with test_client.application.app_context():
        user = User.query.filter_by(email="2fa_test@example.com").first()
        assert user is not None

        service = Email2FAService()
        code = service.send_2fa_code(user.id)

        result = service.verify_2fa_code(user.id, code)
        assert result is True


def test_verify_2fa_code_with_invalid_code(test_client):
    """Test 2FA verification with an invalid code"""
    with test_client.application.app_context():
        user = User(email="invalid_2fa_code_test@example.com", password="test1234")
        user.email_validated = True
        db.session.add(user)
        db.session.flush()

        profile = UserProfile(user_id=user.id, name="Invalid", surname="Code")
        db.session.add(profile)
        db.session.commit()

        service = Email2FAService()
        result = service.verify_2fa_code(user.id, "999999")
        assert result is False


def test_verify_2fa_code_with_malformed_code(test_client):
    """Test 2FA verification with a malformed code"""
    with test_client.application.app_context():
        user = User(email="malformed_2fa_code_test@example.com", password="test1234")
        user.email_validated = True
        db.session.add(user)
        db.session.flush()

        profile = UserProfile(user_id=user.id, name="Malformed", surname="Code")
        db.session.add(profile)
        db.session.commit()

        service = Email2FAService()

        # Test various malformed codes
        assert service.verify_2fa_code(user.id, "12345") is False  # Too short
        assert service.verify_2fa_code(user.id, "1234567") is False  # Too long
        assert service.verify_2fa_code(user.id, "abcdef") is False  # Not digits
        assert service.verify_2fa_code(user.id, "12-456") is False  # Contains dash
        assert service.verify_2fa_code(user.id, "") is False  # Empty string


def test_verify_2fa_code_with_expired_code(test_client):
    """Test 2FA verification with an expired code"""
    with test_client.application.app_context():
        user = User(email="expired_2fa_code_test@example.com", password="test1234")
        user.email_validated = True
        db.session.add(user)
        db.session.flush()

        profile = UserProfile(user_id=user.id, name="Expired", surname="Code")
        db.session.add(profile)
        db.session.commit()

        # Create an expired code manually
        expired_code = Email2FACode(
            user_id=user.id,
            code="123456",
            created_at=datetime.now(tz=timezone.utc) - timedelta(minutes=10),
            valid_until=datetime.now(tz=timezone.utc) - timedelta(minutes=1),
        )
        db.session.add(expired_code)
        db.session.commit()

        service = Email2FAService()
        result = service.verify_2fa_code(user.id, "123456")
        assert result is False


def test_enable_email_2fa_with_validated_email(test_client):
    """Test enabling 2FA with a validated email"""
    with test_client.application.app_context():
        user = User(email="enable_2fa_test@example.com", password="test1234")
        user.email_validated = True
        db.session.add(user)
        db.session.flush()

        profile = UserProfile(user_id=user.id, name="Enable", surname="2FA")
        db.session.add(profile)
        db.session.commit()

        assert user.email_2fa_enabled is False

        service = Email2FAService()
        result = service.enable_email_2fa(user.id)
        assert result is True

        db.session.refresh(user)
        assert user.email_2fa_enabled is True


def test_enable_email_2fa_without_validated_email(test_client):
    """Test that enabling 2FA fails without validated email"""
    with test_client.application.app_context():
        user = User(email="no_validation_2fa_test@example.com", password="test1234")
        user.email_validated = False
        db.session.add(user)
        db.session.flush()

        profile = UserProfile(user_id=user.id, name="NoValidation", surname="2FA")
        db.session.add(profile)
        db.session.commit()

        service = Email2FAService()
        with pytest.raises(ValueError, match="Email must be validated before enabling 2FA"):
            service.enable_email_2fa(user.id)

        db.session.refresh(user)
        assert user.email_2fa_enabled is False


def test_disable_email_2fa(test_client):
    """Test disabling 2FA"""
    with test_client.application.app_context():
        user = User(email="disable_2fa_test@example.com", password="test1234")
        user.email_validated = True
        user.email_2fa_enabled = True
        db.session.add(user)
        db.session.flush()

        profile = UserProfile(user_id=user.id, name="Disable", surname="2FA")
        db.session.add(profile)
        db.session.commit()

        assert user.email_2fa_enabled is True

        service = Email2FAService()
        result = service.disable_email_2fa(user.id)
        assert result is True

        db.session.refresh(user)
        assert user.email_2fa_enabled is False


def test_send_2fa_code_nonexistent_user(test_client):
    """Test that sending 2FA code fails for non-existent user"""
    with test_client.application.app_context():
        service = Email2FAService()
        with pytest.raises(ValueError, match="User with id 99999 not found"):
            service.send_2fa_code(99999)


def test_verify_2fa_code_nonexistent_user(test_client):
    """Test that verifying 2FA code fails for non-existent user"""
    with test_client.application.app_context():
        service = Email2FAService()
        with pytest.raises(ValueError, match="User with id 99999 not found"):
            service.verify_2fa_code(99999, "123456")


def test_enable_2fa_nonexistent_user(test_client):
    """Test that enabling 2FA fails for non-existent user"""
    with test_client.application.app_context():
        service = Email2FAService()
        with pytest.raises(ValueError, match="User with id 99999 not found"):
            service.enable_email_2fa(99999)


def test_disable_2fa_nonexistent_user(test_client):
    """Test that disabling 2FA fails for non-existent user"""
    with test_client.application.app_context():
        service = Email2FAService()
        with pytest.raises(ValueError, match="User with id 99999 not found"):
            service.disable_email_2fa(99999)


# Integration tests for endpoints


def test_verify_2fa_endpoint_requires_pending_session(test_client):
    """Test that the 2FA verification endpoint requires a pending session"""
    response = test_client.get("/login/verify_2fa")
    assert response.status_code == 302
    assert "/login" in response.location


def test_login_with_2fa_enabled(test_client):
    """Test login flow with 2FA enabled"""
    with test_client.application.app_context():
        # Create a user with 2FA enabled
        user = User(email="2fa_login_test@example.com", password="test1234")
        user.email_validated = True
        user.email_2fa_enabled = True
        db.session.add(user)
        db.session.flush()

        profile = UserProfile(user_id=user.id, name="2FALogin", surname="Test")
        db.session.add(profile)
        db.session.commit()

    # Attempt to log in
    with mail.record_messages() as outbox:
        response = test_client.post(
            "/login",
            data=dict(email="2fa_login_test@example.com", password="test1234"),
            follow_redirects=False,
        )

        # Should redirect to 2FA verification page
        assert response.status_code == 302
        assert "/login/verify_2fa" in response.location

        # Should have sent an email with the 2FA code
        assert len(outbox) == 1
        assert outbox[0].subject == "Your Coche-Hub 2FA Code"

        # Extract the code from the email
        code = None
        with test_client.application.app_context():
            user = User.query.filter_by(email="2fa_login_test@example.com").first()
            code_obj = Email2FACode.query.filter_by(user_id=user.id).order_by(Email2FACode.created_at.desc()).first()
            code = code_obj.code

        # Now verify the 2FA code
        response = test_client.post("/login/verify_2fa", data=dict(code=code), follow_redirects=True)

        # Should redirect to home after successful verification
        assert response.status_code == 200
        assert response.request.path == "/"


def test_login_without_2fa(test_client):
    """Test that login works normally without 2FA"""
    with test_client.application.app_context():
        user = User(email="no_2fa_login_test@example.com", password="test1234")
        user.email_validated = True
        user.email_2fa_enabled = False
        db.session.add(user)
        db.session.flush()

        profile = UserProfile(user_id=user.id, name="No2FA", surname="Test")
        db.session.add(profile)
        db.session.commit()

    response = test_client.post(
        "/login",
        data=dict(email="no_2fa_login_test@example.com", password="test1234"),
        follow_redirects=True,
    )

    # Should log in directly without 2FA
    assert response.status_code == 200
    assert response.request.path == "/"

    test_client.get("/logout", follow_redirects=True)


def test_enable_2fa_without_validated_email_endpoint(test_client):
    """Test that enabling 2FA fails without validated email via endpoint"""
    with test_client.application.app_context():
        user = User(email="no_validate_endpoint_test@example.com", password="test1234")
        user.email_validated = False
        db.session.add(user)
        db.session.flush()

        profile = UserProfile(user_id=user.id, name="NoValidateEndpoint", surname="Test")
        db.session.add(profile)
        db.session.commit()

    # Log in
    test_client.post(
        "/login",
        data=dict(email="no_validate_endpoint_test@example.com", password="test1234"),
        follow_redirects=True,
    )

    # Try to enable 2FA
    response = test_client.post("/profile/enable_email_2fa", follow_redirects=True)

    assert response.status_code == 200

    # Verify 2FA was not enabled
    with test_client.application.app_context():
        user = User.query.filter_by(email="no_validate_endpoint_test@example.com").first()
        assert user.email_2fa_enabled is False

    test_client.get("/logout", follow_redirects=True)


# Security Tests


def test_code_cannot_be_reused_after_successful_verification(test_client):
    """Test that a code cannot be used twice"""
    with test_client.application.app_context():
        user = User(email="reuse_test@example.com", password="test1234")
        user.email_validated = True
        db.session.add(user)
        db.session.flush()

        profile = UserProfile(user_id=user.id, name="Reuse", surname="Test")
        db.session.add(profile)
        db.session.commit()

        service = Email2FAService()
        code = service.send_2fa_code(user.id)

        # First verification should succeed
        result = service.verify_2fa_code(user.id, code)
        assert result is True

        # Second verification with same code should fail
        result = service.verify_2fa_code(user.id, code)
        assert result is False


def test_code_deleted_from_database_after_use(test_client):
    """Test that code is invalidated in database after successful verification"""
    with test_client.application.app_context():
        user = User(email="deletion_test@example.com", password="test1234")
        user.email_validated = True
        db.session.add(user)
        db.session.flush()

        profile = UserProfile(user_id=user.id, name="Deletion", surname="Test")
        db.session.add(profile)
        db.session.commit()

        service = Email2FAService()
        code = service.send_2fa_code(user.id)

        # Verify code exists in database
        db_code = Email2FACode.query.filter_by(user_id=user.id, code=code).first()
        assert db_code is not None
        assert db_code.invalidated is False

        # Verify the code
        result = service.verify_2fa_code(user.id, code)
        assert result is True

        # Verify code is invalidated in database (not deleted)
        db_code = Email2FACode.query.filter_by(user_id=user.id, code=code).first()
        assert db_code is not None
        assert db_code.invalidated is True


def test_requesting_new_code_invalidates_previous_codes(test_client):
    """Test that requesting a new code invalidates old ones"""
    with test_client.application.app_context():
        user = User(email="multi_code_test@example.com", password="test1234")
        user.email_validated = True
        db.session.add(user)
        db.session.flush()

        profile = UserProfile(user_id=user.id, name="MultiCode", surname="Test")
        db.session.add(profile)
        db.session.commit()

        service = Email2FAService()

        # Send first code
        first_code = service.send_2fa_code(user.id)

        # Send second code (should invalidate first)
        second_code = service.send_2fa_code(user.id)

        # Verify first code is invalidated in database
        first_code_obj = Email2FACode.query.filter_by(user_id=user.id, code=first_code).first()
        assert first_code_obj is not None
        assert first_code_obj.invalidated is True

        # First code should fail verification
        result = service.verify_2fa_code(user.id, first_code)
        assert result is False

        # Second code should work
        result = service.verify_2fa_code(user.id, second_code)
        assert result is True


def test_multiple_old_codes_all_invalidated(test_client):
    """Test that multiple old codes are all invalidated when a new one is sent"""
    with test_client.application.app_context():
        user = User(email="many_codes_test@example.com", password="test1234")
        user.email_validated = True
        db.session.add(user)
        db.session.flush()

        profile = UserProfile(user_id=user.id, name="ManyCodes", surname="Test")
        db.session.add(profile)
        db.session.commit()

        # Manually create 3 old codes
        from datetime import datetime, timedelta, timezone

        for i in range(3):
            old_code = Email2FACode(
                user_id=user.id,
                code=f"99999{i}",
                created_at=datetime.now(tz=timezone.utc),
                valid_until=datetime.now(tz=timezone.utc) + timedelta(minutes=5),
            )
            db.session.add(old_code)
        db.session.commit()

        # Now send a new code via service
        service = Email2FAService()
        new_code = service.send_2fa_code(user.id)

        # All old codes should still exist but be invalidated
        for i in range(3):
            old_code_check = Email2FACode.query.filter_by(user_id=user.id, code=f"99999{i}").first()
            assert old_code_check is not None
            assert old_code_check.invalidated is True

        # New code should work
        result = service.verify_2fa_code(user.id, new_code)
        assert result is True


def test_rate_limit_blocks_after_5_failed_attempts(test_client):
    """Test that 5 failed attempts block further attempts"""
    with test_client.application.app_context():
        user = User(email="rate_limit_test@example.com", password="test1234")
        user.email_validated = True
        db.session.add(user)
        db.session.flush()

        profile = UserProfile(user_id=user.id, name="RateLimit", surname="Test")
        db.session.add(profile)
        db.session.commit()

        service = Email2FAService()
        code = service.send_2fa_code(user.id)

        # Make 5 failed attempts
        for i in range(5):
            result = service.verify_2fa_code(user.id, "000000")
            assert result is False

        # Verify we have 5 failed attempts recorded
        failed_count = TwoFAAttempt.query.filter_by(user_id=user.id, success=False).count()
        assert failed_count == 5

        # 6th attempt should raise TwoFARateLimitExceeded even with correct code
        with pytest.raises(TwoFARateLimitExceeded):
            service.verify_2fa_code(user.id, code)


def test_rate_limit_counts_across_all_user_codes(test_client):
    """Test that rate limit persists across code requests within the 5-minute window"""
    with test_client.application.app_context():
        user = User(email="multi_code_rate_limit@example.com", password="test1234")
        user.email_validated = True
        db.session.add(user)
        db.session.flush()

        profile = UserProfile(user_id=user.id, name="MultiRate", surname="Test")
        db.session.add(profile)
        db.session.commit()

        service = Email2FAService()

        # Send code and make 5 failed attempts on it
        code = service.send_2fa_code(user.id)
        for i in range(5):
            result = service.verify_2fa_code(user.id, "000000")
            assert result is False

        # Verify we have 5 failed attempts
        failed_count = TwoFAAttempt.query.filter_by(user_id=user.id, success=False).count()
        assert failed_count == 5

        # Rate limit should raise exception on next attempt
        with pytest.raises(TwoFARateLimitExceeded):
            service.verify_2fa_code(user.id, code)

        # Requesting a new code invalidates old codes but attempts still count (within 5-min window)
        new_code = service.send_2fa_code(user.id)
        # Old code should be invalidated
        old_code_obj = Email2FACode.query.filter_by(user_id=user.id, code=code).first()
        assert old_code_obj is not None
        assert old_code_obj.invalidated is True

        # Should still be rate limited because old attempts are within 5-minute window
        with pytest.raises(TwoFARateLimitExceeded):
            service.verify_2fa_code(user.id, new_code)


def test_rate_limit_only_counts_recent_attempts(test_client):
    """Test that rate limit only counts attempts in last 5 minutes"""
    from datetime import datetime, timedelta, timezone

    with test_client.application.app_context():
        user = User(email="time_window_test@example.com", password="test1234")
        user.email_validated = True
        db.session.add(user)
        db.session.flush()

        profile = UserProfile(user_id=user.id, name="TimeWindow", surname="Test")
        db.session.add(profile)
        db.session.commit()

        service = Email2FAService()

        base_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Create 3 old failed attempts manually with timestamps > 5 minutes ago
        old_time = base_time - timedelta(minutes=6)
        for i in range(3):
            old_attempt = TwoFAAttempt(user_id=user.id, success=False, created_at=old_time)
            db.session.add(old_attempt)
        db.session.commit()

        # Now with current time, make 3 more failed attempts
        code = service.send_2fa_code(user.id)
        for i in range(3):
            result = service.verify_2fa_code(user.id, "000000")
            assert result is False

        # We should have 6 total attempts but only 3 in the window
        total_attempts = TwoFAAttempt.query.filter_by(user_id=user.id, success=False).count()
        assert total_attempts == 6

        # 4th attempt (in current window) should succeed with correct code
        result = service.verify_2fa_code(user.id, code)
        assert result is True


def test_successful_verification_allows_new_attempts(test_client):
    """Test that successful verification allows new codes immediately"""
    with test_client.application.app_context():
        user = User(email="reset_limit_test@example.com", password="test1234")
        user.email_validated = True
        db.session.add(user)
        db.session.flush()

        profile = UserProfile(user_id=user.id, name="ResetLimit", surname="Test")
        db.session.add(profile)
        db.session.commit()

        service = Email2FAService()

        # Send code and make 3 failed attempts
        code1 = service.send_2fa_code(user.id)
        for i in range(3):
            result = service.verify_2fa_code(user.id, "000000")
            assert result is False

        # Now succeed with correct code
        result = service.verify_2fa_code(user.id, code1)
        assert result is True

        # Send a new code immediately - should work fine
        code2 = service.send_2fa_code(user.id)
        result = service.verify_2fa_code(user.id, code2)
        assert result is True


def test_rate_limit_window_is_5_minutes(test_client):
    """Test that rate limit expires after 5 minutes"""
    from datetime import datetime, timedelta, timezone

    with test_client.application.app_context():
        user = User(email="five_min_window@example.com", password="test1234")
        user.email_validated = True
        db.session.add(user)
        db.session.flush()

        profile = UserProfile(user_id=user.id, name="FiveMin", surname="Test")
        db.session.add(profile)
        db.session.commit()

        service = Email2FAService()

        base_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Create 5 old failed attempts manually (> 5 minutes ago)
        old_time = base_time - timedelta(minutes=6)
        for i in range(5):
            old_attempt = TwoFAAttempt(user_id=user.id, success=False, created_at=old_time)
            db.session.add(old_attempt)
        db.session.commit()

        # Verify we have 5 old failed attempts
        total_attempts = TwoFAAttempt.query.filter_by(user_id=user.id, success=False).count()
        assert total_attempts == 5

        # Should work now because attempts are > 5 minutes old
        code = service.send_2fa_code(user.id)
        result = service.verify_2fa_code(user.id, code)
        assert result is True
