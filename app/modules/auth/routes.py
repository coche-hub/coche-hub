from flask import redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user

from app.modules.auth import auth_bp
from app.modules.auth.forms import Email2FAVerificationForm, LoginForm, SignupForm
from app.modules.auth.services import (
    AuthenticationService,
    Email2FAService,
    EmailValidationService,
    TwoFARateLimitExceeded,
)
from app.modules.profile.services import UserProfileService

authentication_service = AuthenticationService()
email_validation_service = EmailValidationService()
email_2fa_service = Email2FAService()
user_profile_service = UserProfileService()


@auth_bp.route("/signup/", methods=["GET", "POST"])
def show_signup_form():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = SignupForm()
    if form.validate_on_submit():
        email = form.email.data
        if not authentication_service.is_email_available(email):
            return render_template("auth/signup_form.html", form=form, error=f"Email {email} in use")

        try:
            user = authentication_service.create_with_profile(**form.data)
        except Exception as exc:
            return render_template("auth/signup_form.html", form=form, error=f"Error creating user: {exc}")

        # Log user
        login_user(user, remember=True)
        return redirect(url_for("public.index"))

    return render_template("auth/signup_form.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        # First, verify the credentials
        user = authentication_service.repository.get_by_email(form.email.data)
        if user is not None and user.check_password(form.password.data):
            # Check if 2FA is enabled for this user
            if user.email_2fa_enabled:
                # Store pending user_id in session and send 2FA code
                session["pending_2fa_user_id"] = user.id
                try:
                    email_2fa_service.send_2fa_code(user.id)
                    return redirect(url_for("auth.verify_2fa"))
                except Exception as exc:
                    return render_template("auth/login_form.html", form=form, error=f"Error sending 2FA code: {exc}")
            else:
                # No 2FA, log in directly
                login_user(user, remember=form.remember_me.data)
                return redirect(url_for("public.index"))

        return render_template("auth/login_form.html", form=form, error="Invalid credentials")

    return render_template("auth/login_form.html", form=form)


@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("public.index"))


@auth_bp.route("/login/verify_2fa", methods=["GET", "POST"])
def verify_2fa():
    # Check if user has pending 2FA verification
    if "pending_2fa_user_id" not in session:
        return redirect(url_for("auth.login"))

    form = Email2FAVerificationForm()
    if request.method == "POST" and form.validate_on_submit():
        user_id = session["pending_2fa_user_id"]
        code = form.code.data

        try:
            if email_2fa_service.verify_2fa_code(user_id, code):
                # Code is valid, log the user in
                user = authentication_service.repository.get_by_id(user_id)
                if user:
                    login_user(user, remember=True)
                    # Clear the pending 2FA session
                    session.pop("pending_2fa_user_id", None)
                    return redirect(url_for("public.index"))

            return render_template("auth/email_2fa_verification_form.html", form=form, error="Invalid or expired code")
        except TwoFARateLimitExceeded:
            return render_template(
                "auth/email_2fa_verification_form.html",
                form=form,
                error="Too many failed attempts. Please try again later.",
            )

    return render_template("auth/email_2fa_verification_form.html", form=form)


@auth_bp.route("/validate_email/<code>")
def validate_email(code: str):
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))

    email_validated = email_validation_service.validate_email(current_user.id, code)

    return render_template("auth/email_validation_result.html", success=email_validated)
