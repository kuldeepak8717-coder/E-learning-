from flask import Blueprint, render_template, jsonify, request
from database.models import db, User
from services.progress_service import BADGE_DEFINITIONS, get_level_progress
from utils import get_current_user

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/profile')
def profile_page():
    user = get_current_user()
    return render_template('profile.html', user=user, badge_definitions=BADGE_DEFINITIONS)


@profile_bp.route('/api/profile/update', methods=['POST'])
def update():
    data = request.get_json()
    user = get_current_user()

    if 'name' in data:
        user.name = data['name'][:100]
    if 'goal' in data:
        user.goal = data['goal'][:200]
    if 'daily_target_minutes' in data:
        user.daily_target_minutes = int(data['daily_target_minutes'])
    if 'avatar' in data:
        user.avatar = data['avatar'][:10]

    db.session.commit()
    return jsonify({'success': True, 'user': user.to_dict()})


@profile_bp.route('/api/profile/data')
def get_profile():
    user = get_current_user()
    level_progress = get_level_progress(user)

    # Badge details
    user_badges = user.get_badges()
    all_badges = []
    for key, badge in BADGE_DEFINITIONS.items():
        all_badges.append({
            **badge,
            'key': key,
            'earned': key in user_badges,
        })

    return jsonify({
        'user': user.to_dict(),
        'level_progress': level_progress,
        'all_badges': all_badges,
    })
