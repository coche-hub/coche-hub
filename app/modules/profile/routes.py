from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.modules.auth.services import (
    AuthenticationService,
    Email2FAService,
    EmailValidationService,
)
from app.modules.dataset.models import DataSet
from app.modules.profile import profile_bp
from app.modules.profile.forms import UserProfileForm
from app.modules.profile.services import UserProfileService


@profile_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    auth_service = AuthenticationService()
    profile = auth_service.get_authenticated_user_profile
    if not profile:
        return redirect(url_for("public.index"))

    form = UserProfileForm()
    if request.method == "POST":
        service = UserProfileService()
        result, errors = service.update_profile(profile.id, form)
        return service.handle_service_response(
            result,
            errors,
            "profile.edit_profile",
            "Profile updated successfully",
            "profile/edit.html",
            form,
        )

    return render_template("profile/edit.html", form=form)


@profile_bp.route("/profile/summary")
@login_required
def my_profile():
    page = request.args.get("page", 1, type=int)
    per_page = 5

    user_datasets_pagination = (
        db.session.query(DataSet)
        .filter(DataSet.user_id == current_user.id)
        .order_by(DataSet.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    total_datasets_count = db.session.query(DataSet).filter(DataSet.user_id == current_user.id).count()

    print(user_datasets_pagination.items)

    return render_template(
        "profile/summary.html",
        user_profile=current_user.profile,
        user=current_user,
        datasets=user_datasets_pagination.items,
        pagination=user_datasets_pagination,
        total_datasets=total_datasets_count,
    )


@profile_bp.route("/profile/send_validation_email", methods=["POST"])
@login_required
def send_validation_email():
    if current_user.email_validated:
        flash("Your email is already validated.", "info")
        return redirect(url_for("profile.my_profile"))

    try:
        email_validation_service = EmailValidationService()
        email_validation_service.send_validation_email(current_user.id)
        flash("Validation email sent successfully. Please check your inbox.", "success")
    except Exception as e:
        flash(f"Error sending validation email: {str(e)}", "error")

    return redirect(url_for("profile.my_profile"))


@profile_bp.route("/profile/enable_email_2fa", methods=["POST"])
@login_required
def enable_email_2fa():
    if not current_user.email_validated:
        flash("Your email is not validated.", "info")
        return redirect(url_for("profile.my_profile"))

    try:
        email_2fa_service = Email2FAService()
        email_2fa_service.enable_email_2fa(current_user.id)
        flash("Email 2FA is now enabled!", "success")
    except Exception as e:
        flash(f"Error enabling Email 2FA for your account: {str(e)}", "error")

    return redirect(url_for("profile.my_profile"))


@profile_bp.route("/profile/disable_email_2fa", methods=["POST"])
@login_required
def disable_email_2fa():
    try:
        email_2fa_service = Email2FAService()
        email_2fa_service.disable_email_2fa(current_user.id)
        flash("Email 2FA has been disabled.", "success")
    except Exception as e:
        flash(f"Error disabling Email 2FA for your account: {str(e)}", "error")

    return redirect(url_for("profile.my_profile"))
