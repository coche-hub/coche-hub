import os
from uuid import UUID

from flask import current_app, render_template, url_for
from flask_login import current_user, login_user
from flask_mail import Message

from app import mail
from app.modules.auth.models import User
from app.modules.auth.repositories import EmailValidationCodeRepository, UserRepository
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

            print("We got here!")

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
        http = current_app.config["DEBUG"] | current_app.config["TESTING"]
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
