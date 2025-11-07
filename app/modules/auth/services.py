import os
import secrets
from uuid import UUID

from flask import current_app, render_template, url_for
from flask_login import current_user, login_user
from flask_mail import Message

from app import mail
from app.modules.auth.models import User
from app.modules.auth.repositories import (
    Email2FACodeRepository,
    EmailValidationCodeRepository,
    TwoFAAttemptRepository,
    UserRepository,
)
from app.modules.profile.models import UserProfile
from app.modules.profile.repositories import UserProfileRepository
from core.configuration.configuration import uploads_folder_name
from core.services.BaseService import BaseService


class AuthenticationService(BaseService):
    def __init__(self):
        super().__init__(UserRepository())
        self.user_profile_repository = UserProfileRepository()
        self.email_validation_service = EmailValidationService()

    def login(self, email, password, remember=True):
        user = self.repository.get_by_email(email)
        if user is not None and user.check_password(password):
            login_user(user, remember=remember)
            return True
        return False

    def is_email_available(self, email: str) -> bool:
        return self.repository.get_by_email(email) is None

    def create_with_profile(self, **kwargs):
        try:
            email = kwargs.pop("email", None)
            password = kwargs.pop("password", None)
            name = kwargs.pop("name", None)
            surname = kwargs.pop("surname", None)

            if not email:
                raise ValueError("Email is required.")
            if not password:
                raise ValueError("Password is required.")
            if not name:
                raise ValueError("Name is required.")
            if not surname:
                raise ValueError("Surname is required.")

            user_data = {"email": email, "password": password}

            profile_data = {
                "name": name,
                "surname": surname,
            }

            user = self.create(commit=False, **user_data)
            profile_data["user_id"] = user.id
            self.user_profile_repository.create(**profile_data)
            self.repository.session.commit()

            # Send email validation after successful user creation
            try:
                self.email_validation_service.send_validation_email(user.id)
            except Exception as exc:
                print(f"Error sending validation email: {exc}")
        except Exception as exc:
            self.repository.session.rollback()
            raise exc
        return user

    def update_profile(self, user_profile_id, form):
        if form.validate():
            updated_instance = self.update(user_profile_id, **form.data)
            return updated_instance, None

        return None, form.errors

    def get_authenticated_user(self) -> User | None:
        if current_user.is_authenticated:
            return current_user
        return None

    def get_authenticated_user_profile(self) -> UserProfile | None:
        if current_user.is_authenticated:
            return current_user.profile
        return None

    def temp_folder_by_user(self, user: User) -> str:
        return os.path.join(uploads_folder_name(), "temp", str(user.id))


class EmailValidationService(BaseService):
    def __init__(self):
        super().__init__(EmailValidationCodeRepository())
        self.user_repository = UserRepository()

    def send_validation_email(self, user_id: int):
        email_validation_code = self.create(user_id=user_id)

        validation_code = str(email_validation_code.id)

        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise ValueError(f"User with id {user_id} not found")

        domain = os.getenv("DOMAIN", "localhost")
        http = current_app.config["DEBUG"] or current_app.config["TESTING"]
        endpoint = url_for("auth.validate_email", code=validation_code)
        link = f"{'http' if http else 'https'}://{domain}{endpoint}"

        html_body = render_template("auth/email_validation.html", validation_link=link)

        mail.send(
            Message(
                subject="Validate your Coche-Hub email",
                html=html_body,
                recipients=[user.email],
            )
        )

    def validate_email(self, user_id: int, validation_code: str) -> bool:
        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise ValueError(f"User with id {user_id} not found")

        if user.email_validated:
            return True

        try:
            validation_code_uuid = UUID(validation_code)
        except ValueError:
            return False

        valid = self.repository.is_code_valid_for_user(validation_code_uuid, user_id)

        if valid:
            self.user_repository.update(user_id, email_validated=True)
            return True
        else:
            return False


class Email2FAService(BaseService):
    MAX_ATTEMPTS = 5

    def __init__(self):
        super().__init__(Email2FACodeRepository())
        self.user_repository = UserRepository()
        self.two_fa_attempt_repository = TwoFAAttemptRepository()

    def generate_code(self):
        return str(secrets.randbelow(1000000)).zfill(6)

    def send_2fa_code(self, user_id: int):
        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise ValueError(f"User with id {user_id} not found")

        self.repository.invalidate_all_codes_for_user(user_id)

        code = self.generate_code()

        self.create(user_id=user_id, code=code)

        html_body = render_template("auth/email_2fa_code.html", code=code, user_name=user.profile.name)

        mail.send(
            Message(
                subject="Your Coche-Hub 2FA Code",
                html=html_body,
                recipients=[user.email],
            )
        )

        return code

    def verify_2fa_code(self, user_id: int, code: int | str) -> bool:
        code = str(code)
        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise ValueError(f"User with id {user_id} not found")

        if self.two_fa_attempt_repository.get_failed_attempts_in_window(user_id) >= self.MAX_ATTEMPTS:
            return False

        valid = self.repository.is_code_valid_for_user(code, user_id)

        if valid:
            valid = self.repository.is_code_valid_for_user(code, user_id)
            self.repository.invalidate_all_codes_for_user(user_id)
            self.two_fa_attempt_repository.record_attempt(user_id, True)
            return True
        else:
            self.two_fa_attempt_repository.record_attempt(user_id, False)
            return False

    def enable_email_2fa(self, user_id: int) -> bool:
        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise ValueError(f"User with id {user_id} not found")

        if user.email_2fa_enabled:
            return True

        if not user.email_validated:
            raise ValueError(
                f"User with id {user_id} does not have a validated email.\nEmail must be validated before enabling 2FA"
            )

        self.user_repository.update(user_id, email_2fa_enabled=True)
        return True

    def disable_email_2fa(self, user_id: int) -> bool:
        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise ValueError(f"User with id {user_id} not found")

        if not user.email_2fa_enabled:
            return True

        self.user_repository.update(user_id, email_2fa_enabled=False)
        return True
