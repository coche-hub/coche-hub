from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from app.modules.auth import auth_bp
from app.modules.auth.forms import LoginForm, SignupForm
from app.modules.auth.services import AuthenticationService, EmailValidationService
from app.modules.profile.services import UserProfileService

authentication_service = AuthenticationService()
email_validation_service = EmailValidationService()
user_profile_service = UserProfileService()


@auth_bp.route("/signup/", methods=["GET", "POST"])
def show_signup_form():
    print("1")

    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    print("2")

    form = SignupForm()
    if form.validate_on_submit():
        print("3")

        email = form.email.data
        if not authentication_service.is_email_available(email):
            return render_template("auth/signup_form.html", form=form, error=f"Email {email} in use")

        print("4")

        try:
            user = authentication_service.create_with_profile(**form.data)
        except Exception as exc:
            return render_template("auth/signup_form.html", form=form, error=f"Error creating user: {exc}")

        print("5")

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
        if authentication_service.login(form.email.data, form.password.data):
            return redirect(url_for("public.index"))

        return render_template("auth/login_form.html", form=form, error="Invalid credentials")

    return render_template("auth/login_form.html", form=form)


@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("public.index"))


@auth_bp.route("/validate_email/<code>")
def validate_email(code: str):
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))

    email_validated = email_validation_service.validate_email(current_user.id, code)

    return render_template("auth/email_validation_result.html", success=email_validated)
