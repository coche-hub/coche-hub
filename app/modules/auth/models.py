import uuid
from datetime import datetime, timedelta, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(256), unique=True, nullable=False)
    email_validated = db.Column(db.Boolean, nullable=False, default=False)
    email_2fa_enabled = db.Column(db.Boolean, nullable=False, default=False)
    password = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    data_sets = db.relationship("DataSet", backref="user", lazy=True)
    profile = db.relationship("UserProfile", backref="user", uselist=False)
    email_validation_codes = db.relationship("EmailValidationCode", backref="user", lazy=True)
    email_2fa_codes = db.relationship("Email2FACode", backref="user", lazy=True)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if "password" in kwargs:
            self.set_password(kwargs["password"])

    def __repr__(self):
        return f"<User {self.email}>"

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def temp_folder(self) -> str:
        from app.modules.auth.services import AuthenticationService

        return AuthenticationService().temp_folder_by_user(self)


class EmailValidationCode(db.Model):
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    valid_until = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc) + timedelta(minutes=15),
    )


class Email2FACode(db.Model):
    __tablename__ = "email_2fa_code"

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    invalidated = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    valid_until = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc) + timedelta(minutes=5),
    )


class TwoFAAttempt(db.Model):
    __tablename__ = "two_fa_attempt"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    success = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    MAX_ATTEMPTS = 5
    RATE_LIMIT_WINDOW_MINUTES = 5
