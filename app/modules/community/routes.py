from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.modules.auth.models import User
from app.modules.community.forms import CommunityForm
from app.modules.community.services import CommunityService
from app.modules.profile.models import UserProfile

community_bp = Blueprint("community", __name__, template_folder="templates")


@community_bp.route("/community", methods=["GET"])
def index():
    service = CommunityService()
    communities = service.get_all_communities()
    return render_template("community/index.html", communities=communities)


@community_bp.route("/community/create", methods=["GET", "POST"])
@login_required
def create():
    form = CommunityForm()

    if request.method == "POST":
        print("=" * 50)
        print("POST REQUEST RECEIVED")
        print(f"Form data: {request.form}")
        print(f"Form validate_on_submit: {form.validate_on_submit()}")
        print(f"Form errors: {form.errors}")
        print(f"CSRF valid: {form.csrf_token.current_token if hasattr(form, 'csrf_token') else 'N/A'}")
        print("=" * 50)

        if form.validate_on_submit():
            service = CommunityService()
            try:
                print(f"Creating community with name: {form.name.data}")
                community = service.create_community(
                    name=form.name.data,
                    description=form.description.data,
                    creator_id=current_user.id,
                    logo=form.logo.data if form.logo.data else None,
                )
                print(f"Community created successfully with ID: {community.id}")
                curator_names = request.form.getlist("curator_name")
                curator_affs = request.form.getlist("curator_affiliation")
                curator_orcids = request.form.getlist("curator_orcid")

                try:
                    max_len = 0
                    if curator_names or curator_affs or curator_orcids:
                        max_len = max(len(curator_names), len(curator_affs), len(curator_orcids))

                    unresolved = []
                    for i in range(max_len):
                        name = curator_names[i].strip() if i < len(curator_names) else ""
                        orcid = curator_orcids[i].strip() if i < len(curator_orcids) else ""

                        profile = None
                        if orcid:
                            profile = UserProfile.query.filter_by(orcid=orcid).first()
                        if not profile and name:
                            name_query = f"%{name}%"
                            try:
                                from sqlalchemy import func

                                concat_field = func.concat(UserProfile.name, " ", UserProfile.surname)
                                profile = UserProfile.query.filter(
                                    (UserProfile.name.ilike(name_query))
                                    | (UserProfile.surname.ilike(name_query))
                                    | (concat_field.ilike(name_query))
                                ).first()
                            except Exception:
                                profile = UserProfile.query.filter(
                                    (UserProfile.name.ilike(name_query)) | (UserProfile.surname.ilike(name_query))
                                ).first()

                        if profile:
                            if not service.is_curator(profile.user_id, community.id):
                                service.add_curator(community.id, profile.user_id, current_user.id)
                        else:
                            unresolved.append(orcid or name or "<unknown>")
                    if unresolved:
                        msg = "Some curators could not be resolved and were not added: "
                        msg += ", ".join(unresolved)
                        flash(msg, "warning")
                except Exception as e:
                    try:
                        service.delete_community(community.id)
                    except Exception:
                        pass
                    from app import db

                    db.session.rollback()
                    form.errors["general"] = [str(e)]
                    return render_template("community/create.html", form=form)

                return redirect(url_for("community.detail", community_id=community.id))

            except Exception as e:
                from app import db

                db.session.rollback()
                print(f"ERROR creating community: {str(e)}")
                import traceback

                traceback.print_exc()

                form.errors["general"] = [str(e)]
        else:
            print("FORM VALIDATION FAILED!")
            print(f"Errors: {form.errors}")

    return render_template("community/create.html", form=form)


@community_bp.route("/community/<int:community_id>", methods=["GET"])
def detail(community_id):
    service = CommunityService()
    community = service.get_by_id(community_id)

    if not community:
        abort(404)

    curators = service.get_community_curators(community_id)
    is_curator = current_user.is_authenticated and service.is_curator(current_user.id, community_id)

    return render_template("community/detail.html", community=community, curators=curators, is_curator=is_curator)


@community_bp.route("/community/<int:community_id>/edit", methods=["GET", "POST"])
@login_required
def edit(community_id):
    service = CommunityService()

    community = service.get_by_id(community_id)
    if not community:
        abort(404)

    if not service.is_curator(current_user.id, community_id):
        abort(403)

    form = CommunityForm(obj=community)

    curators = service.get_community_curators(community_id)
    curators_data = []
    for c in curators:
        u = getattr(c, "user", None)
        profile = None
        if u:
            profile = UserProfile.query.filter_by(user_id=getattr(u, "id", None)).first()
        curators_data.append(
            {
                "user": {
                    "name": getattr(profile, "name", None) if profile else getattr(u, "email", None),
                    "email": getattr(u, "email", None),
                    "orcid": getattr(profile, "orcid", None) if profile else None,
                }
            }
        )

    if request.method == "POST" and form.validate_on_submit():
        try:
            service.update_community(
                community_id=community_id, name=form.name.data, description=form.description.data, logo=form.logo.data
            )

            curator_names = request.form.getlist("curator_name")
            curator_affs = request.form.getlist("curator_affiliation")
            curator_orcids = request.form.getlist("curator_orcid")

            max_len = 0
            if curator_names or curator_affs or curator_orcids:
                max_len = max(len(curator_names), len(curator_affs), len(curator_orcids))

            for i in range(max_len):
                name = curator_names[i].strip() if i < len(curator_names) else ""
                orcid = curator_orcids[i].strip() if i < len(curator_orcids) else ""

                profile = None
                if orcid:
                    profile = UserProfile.query.filter_by(orcid=orcid).first()
                if not profile and name:
                    name_query = f"%{name}%"
                    try:
                        from sqlalchemy import func

                        concat_field = func.concat(UserProfile.name, " ", UserProfile.surname)
                        profile = UserProfile.query.filter(
                            (UserProfile.name.ilike(name_query))
                            | (UserProfile.surname.ilike(name_query))
                            | (concat_field.ilike(name_query))
                        ).first()
                    except Exception:
                        profile = UserProfile.query.filter(
                            (UserProfile.name.ilike(name_query)) | (UserProfile.surname.ilike(name_query))
                        ).first()

                if profile:
                    if not service.is_curator(profile.user_id, community_id):
                        service.add_curator(community_id, profile.user_id, requester_id=current_user.id)

            return redirect(url_for("community.detail", community_id=community_id))
        except Exception as e:
            form.errors["general"] = [str(e)]

    return render_template(
        "community/edit.html", form=form, community=community, curators=curators, curators_data=curators_data
    )


@community_bp.route("/community/<int:community_id>/delete", methods=["POST"])
@login_required
def delete(community_id):
    service = CommunityService()

    if not service.is_curator(current_user.id, community_id):
        abort(403)

    try:
        service.delete_community(community_id)
        return redirect(url_for("community.index"))
    except Exception as e:
        from app import db

        db.session.rollback()
        import traceback

        traceback.print_exc()
        flash(f"Could not delete community: {str(e)}", "danger")
        return redirect(url_for("community.detail", community_id=community_id))


@community_bp.route("/community/<int:community_id>/curators", methods=["GET"])
def list_curators(community_id):
    service = CommunityService()
    curators = service.get_community_curators(community_id)
    return render_template("community/curators.html", community_id=community_id, curators=curators)


@community_bp.route("/community/<int:community_id>/curators/add", methods=["POST"])
@login_required
def add_curator(community_id):
    service = CommunityService()

    if not service.is_curator(current_user.id, community_id):
        abort(403)
    orcid = request.form.get("orcid")
    user_id = request.form.get("user_id")
    name = request.form.get("name")

    resolved_user_id = None

    if orcid:
        profile = UserProfile.query.filter_by(orcid=orcid).first()
        if profile:
            resolved_user_id = profile.user_id
        else:
            flash(f"No user found with the provided ORCID: {orcid}", "warning")
            return redirect(url_for("community.edit", community_id=community_id))
    elif user_id:
        try:
            resolved_user_id = int(user_id)
        except ValueError:
            flash("Invalid user identifier provided", "warning")
            return redirect(url_for("community.edit", community_id=community_id))
    elif name:
        profile = None
        name_query = f"%{name}%"
        try:
            from sqlalchemy import func

            concat_field = func.concat(UserProfile.name, " ", UserProfile.surname)
            profile = UserProfile.query.filter(
                (UserProfile.name.ilike(name_query))
                | (UserProfile.surname.ilike(name_query))
                | (concat_field.ilike(name_query))
            ).first()
        except Exception:
            profile = UserProfile.query.filter(
                (UserProfile.name.ilike(name_query)) | (UserProfile.surname.ilike(name_query))
            ).first()

        if profile:
            resolved_user_id = profile.user_id
        else:
            flash(f"No user found matching the provided name: {name}", "warning")
            return redirect(url_for("community.edit", community_id=community_id))
    else:
        abort(400, "Missing user identifier")

    target_user = User.query.get(resolved_user_id)
    if not target_user:
        flash("Resolved user not found in database", "warning")
        return redirect(url_for("community.edit", community_id=community_id))

    try:
        service.add_curator(community_id, resolved_user_id, current_user.id)
        return redirect(url_for("community.edit", community_id=community_id))
    except Exception:
        from app import db

        db.session.rollback()
        flash("An error occurred while adding curator", "danger")
        return redirect(url_for("community.edit", community_id=community_id))


@community_bp.route("/community/<int:community_id>/curators/<int:user_id>/remove", methods=["POST"])
@login_required
def remove_curator(community_id, user_id):
    abort(403)


@community_bp.route("/community/my-communities", methods=["GET"])
@login_required
def my_communities():
    service = CommunityService()
    communities = service.get_user_communities(current_user.id)
    return render_template("community/my_communities.html", communities=communities)


@community_bp.route("/community/<int:community_id>/datasets", methods=["GET"])
def view_datasets(community_id):
    """View all datasets assigned to a community"""
    service = CommunityService()
    community = service.get_by_id(community_id)

    if not community:
        abort(404)

    dataset_assignments = service.get_community_datasets(community_id)
    datasets = [assignment.dataset for assignment in dataset_assignments]

    is_curator = current_user.is_authenticated and service.is_curator(current_user.id, community_id)

    return render_template("community/datasets.html", community=community, datasets=datasets, is_curator=is_curator)


@community_bp.route("/community/<int:community_id>/datasets/manage", methods=["GET"])
@login_required
def manage_datasets(community_id):
    """Page for curators to manage dataset assignments"""
    service = CommunityService()
    community = service.get_by_id(community_id)

    if not community:
        abort(404)

    if not service.is_curator(current_user.id, community_id):
        abort(403)

    # Get currently assigned datasets
    dataset_assignments = service.get_community_datasets(community_id)
    assigned_datasets = [assignment.dataset for assignment in dataset_assignments]

    # Get available datasets to assign
    available_datasets = service.get_available_datasets_for_community(community_id)

    return render_template(
        "community/manage_datasets.html",
        community=community,
        assigned_datasets=assigned_datasets,
        available_datasets=available_datasets,
    )


@community_bp.route("/community/<int:community_id>/datasets/assign", methods=["POST"])
@login_required
def assign_dataset(community_id):
    """Assign a dataset to the community"""
    service = CommunityService()

    if not service.is_curator(current_user.id, community_id):
        abort(403)

    dataset_id = request.form.get("dataset_id")
    if not dataset_id:
        flash("Dataset ID is required", "danger")
        return redirect(url_for("community.manage_datasets", community_id=community_id))

    try:
        dataset_id = int(dataset_id)
        service.assign_dataset_to_community(community_id, dataset_id, current_user.id)
        flash("Dataset assigned successfully", "success")
    except PermissionError as e:
        flash(str(e), "danger")
    except ValueError as e:
        flash(str(e), "warning")
    except Exception as e:
        flash(f"Error assigning dataset: {str(e)}", "danger")

    return redirect(url_for("community.manage_datasets", community_id=community_id))


@community_bp.route("/community/<int:community_id>/datasets/<int:dataset_id>/unassign", methods=["POST"])
@login_required
def unassign_dataset(community_id, dataset_id):
    """Remove a dataset from the community"""
    service = CommunityService()

    if not service.is_curator(current_user.id, community_id):
        abort(403)

    try:
        service.unassign_dataset_from_community(community_id, dataset_id, current_user.id)
        flash("Dataset unassigned successfully", "success")
    except PermissionError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash(f"Error unassigning dataset: {str(e)}", "danger")

    return redirect(url_for("community.manage_datasets", community_id=community_id))
