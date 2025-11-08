from flask import Blueprint, render_template, request, jsonify, redirect, url_for, abort
from flask_login import login_required, current_user
from app.modules.community.services import CommunityService
from app.modules.profile.models import UserProfile
from app.modules.auth.models import User
from app.modules.community.forms import CommunityForm

community_bp = Blueprint('community', __name__, template_folder='templates')

@community_bp.route('/community', methods=['GET'])
def index():
    service = CommunityService()
    communities = service.get_all_communities()
    return render_template('community/index.html', communities=communities)

@community_bp.route('/community/create', methods=['GET', 'POST'])
@login_required
def create():
    form = CommunityForm()
    
    if request.method == 'POST':
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
                    logo=form.logo.data if form.logo.data else None
                )
                print(f"Community created successfully with ID: {community.id}")
                # Process any curators submitted in the create form (fields: curator_orcid, curator_name, curator_affiliation)
                curator_orcids = request.form.getlist('curator_orcid')
                # if any curators were provided, try to resolve them by ORCID and add
                if curator_orcids:
                    try:
                        for orcid in curator_orcids:
                            orcid = (orcid or '').strip()
                            if not orcid:
                                continue
                            profile = UserProfile.query.filter_by(orcid=orcid).first()
                            if not profile:
                                raise ValueError(f'No user found for ORCID {orcid}')
                            service.add_curator(community.id, profile.user_id, current_user.id)
                    except Exception as e:
                        # If curator addition fails, remove the created community to avoid partial state
                        try:
                            service.delete_community(community.id)
                        except Exception:
                            pass
                        from app import db
                        db.session.rollback()
                        form.errors['general'] = [str(e)]
                        return render_template('community/create.html', form=form)

                return redirect(url_for('community.detail', community_id=community.id))
                
            except Exception as e:
                from app import db
                db.session.rollback()
                print(f"ERROR creating community: {str(e)}")
                import traceback
                traceback.print_exc()
                
                form.errors['general'] = [str(e)]
        else:
            print(f"FORM VALIDATION FAILED!")
            print(f"Errors: {form.errors}")
    
    return render_template('community/create.html', form=form)

@community_bp.route('/community/<int:community_id>', methods=['GET'])
def detail(community_id):
    service = CommunityService()
    community = service.get_by_id(community_id)
    
    if not community:
        abort(404)
    
    curators = service.get_community_curators(community_id)
    is_curator = current_user.is_authenticated and service.is_curator(current_user.id, community_id)
    
    return render_template('community/detail.html', 
                         community=community, 
                         curators=curators,
                         is_curator=is_curator)

@community_bp.route('/community/<int:community_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(community_id):
    service = CommunityService()

    community = service.get_by_id(community_id)
    if not community:
        abort(404)

    # Check if user is curator
    if not service.is_curator(current_user.id, community_id):
        abort(403)  
    
    form = CommunityForm(obj=community)
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            service.update_community(
                community_id=community_id,
                name=form.name.data,
                description=form.description.data,
                logo=form.logo.data
            )
            return redirect(url_for('community.detail', community_id=community_id))
        except Exception as e:
            form.errors['general'] = [str(e)]
    
    return render_template('community/edit.html', form=form, community=community)

@community_bp.route('/community/<int:community_id>/delete', methods=['POST'])
@login_required
def delete(community_id):
    service = CommunityService()
    
    # Check if user is curator
    if not service.is_curator(current_user.id, community_id):
        abort(403)
    
    try:
        service.delete_community(community_id)
        return redirect(url_for('community.index'))
    except Exception as e:
        abort(500)

@community_bp.route('/community/<int:community_id>/curators', methods=['GET'])
def list_curators(community_id):
    service = CommunityService()
    curators = service.get_community_curators(community_id)
    return render_template('community/curators.html', 
                         community_id=community_id, 
                         curators=curators)

@community_bp.route('/community/<int:community_id>/curators/add', methods=['POST'])
@login_required
def add_curator(community_id):
    service = CommunityService()
    
    # Check if requester is curator
    if not service.is_curator(current_user.id, community_id):
        abort(403)
    # Prefer ORCID when provided (lookup existing user by profile)
    orcid = request.form.get('orcid')
    user_id = request.form.get('user_id')

    resolved_user_id = None

    if orcid:
        profile = UserProfile.query.filter_by(orcid=orcid).first()
        if profile:
            resolved_user_id = profile.user_id
        else:
            # No user found with ORCID
            abort(400, 'No user with the provided ORCID')
    elif user_id:
        try:
            resolved_user_id = int(user_id)
        except ValueError:
            abort(400, 'Invalid user_id')
    else:
        abort(400, 'Missing user identifier')

    # Ensure the target user exists
    target_user = User.query.get(resolved_user_id)
    if not target_user:
        abort(400, 'User not found')

    try:
        # pass current_user.id as requester_id to the service
        service.add_curator(community_id, resolved_user_id, current_user.id)
        return redirect(url_for('community.detail', community_id=community_id))
    except Exception as e:
        from app import db
        db.session.rollback()
        abort(500, str(e))

@community_bp.route('/community/<int:community_id>/curators/<int:user_id>/remove', methods=['POST'])
@login_required
def remove_curator(community_id, user_id):
    service = CommunityService()
    
    # Check if requester is curator
    if not service.is_curator(current_user.id, community_id):
        abort(403)
    
    try:
        service.remove_curator(community_id, user_id)
        return redirect(url_for('community.detail', community_id=community_id))
    except ValueError as e:
        # Cannot remove last curator
        abort(400, str(e))
    except Exception as e:
        abort(500)

@community_bp.route('/community/my-communities', methods=['GET'])
@login_required
def my_communities():
    service = CommunityService()
    communities = service.get_user_communities(current_user.id)
    return render_template('community/my_communities.html', communities=communities)