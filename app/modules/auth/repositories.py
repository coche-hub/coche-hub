from datetime import datetime, timezone
from uuid import UUID

from app.modules.auth.models import EmailValidationCode, User
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
            .filter(EmailValidationCode.valid_until > datetime.now(tz=timezone.utc).isoformat())
            .first()
            is not None
        )
