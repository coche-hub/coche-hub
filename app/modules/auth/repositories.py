from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.modules.auth.models import Email2FACode, EmailValidationCode, TwoFAAttempt, User
from core.repositories.BaseRepository import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__(User)

    def create(self, commit: bool = True, **kwargs):
        password = kwargs.pop("password")
        instance = self.model(**kwargs)
        instance.set_password(password)
        self.session.add(instance)
        if commit:
            self.session.commit()
        else:
            self.session.flush()
        return instance

    def get_by_email(self, email: str):
        return self.model.query.filter_by(email=email).first()


class EmailValidationCodeRepository(BaseRepository):
    def __init__(self):
        super().__init__(EmailValidationCode)

    def is_code_valid_for_user(self, validation_code: UUID, user_id: int) -> bool:
        return (
            self.model.query.filter_by(user_id=user_id, id=validation_code)
            .filter(EmailValidationCode.valid_until > datetime.now(tz=timezone.utc))
            .first()
            is not None
        )


class Email2FACodeRepository(BaseRepository):
    def __init__(self):
        super().__init__(Email2FACode)

    def is_code_valid_for_user(self, code: str, user_id: int) -> bool:
        return (
            self.model.query.filter_by(user_id=user_id, code=code, invalidated=False)
            .filter(Email2FACode.valid_until > datetime.now(tz=timezone.utc))
            .first()
            is not None
        )

    def invalidate_all_codes_for_user(self, user_id: int) -> None:
        codes = self.model.query.filter_by(user_id=user_id, invalidated=False).all()
        for code in codes:
            code.invalidated = True
        self.session.commit()


class TwoFAAttemptRepository(BaseRepository):
    def __init__(self):
        super().__init__(TwoFAAttempt)

    def record_attempt(self, user_id: int, success: bool) -> TwoFAAttempt:
        attempt = self.create(user_id=user_id, success=success)
        return attempt

    def get_failed_attempts_in_window(self, user_id: int, window_minutes: int = 5) -> int:
        cutoff_time = datetime.now(tz=timezone.utc) - timedelta(minutes=window_minutes)
        count = (
            self.model.query.filter_by(user_id=user_id, success=False)
            .filter(TwoFAAttempt.created_at > cutoff_time)
            .count()
        )
        return count
