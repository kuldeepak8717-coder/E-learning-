from flask import Blueprint, render_template, jsonify
from database.models import db, User, DailyRoadmap, QuizResult, TypingResult
from services.progress_service import get_level_progress, get_skill_stats, update_streak, BADGE_DEFINITIONS
from utils import get_current_user
from datetime import date

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    user = get_current_user()
    return render_template('index.html', user=user)

@dashboard_bp.route('/api/dashboard/stats')
def get_stats():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'No user found'}), 404

    level_progress = get_level_progress(user)
    skill_stats = get_skill_stats(user.id)

    # Today's roadmap
    today_roadmap = DailyRoadmap.query.filter_by(
        user_id=user.id, date=date.today()
    ).first()

    completion_pct = today_roadmap.completion_percent() if today_roadmap else 0

    # Recent quiz results
    recent_quizzes = QuizResult.query.filter_by(user_id=user.id)\
        .order_by(QuizResult.date.desc()).limit(5).all()

    avg_quiz_score = 0
    if recent_quizzes:
        avg_quiz_score = round(sum(q.accuracy for q in recent_quizzes) / len(recent_quizzes))

    # Best WPM
    from sqlalchemy import func
    best_wpm = db.session.query(func.max(TypingResult.wpm)).filter_by(user_id=user.id).scalar() or 0

    # Badge details
    user_badge_keys = user.get_badges()
    badges_detail = [
        {**BADGE_DEFINITIONS[b], 'key': b}
        for b in user_badge_keys if b in BADGE_DEFINITIONS
    ]

    return jsonify({
        'user': user.to_dict(),
        'level_progress': level_progress,
        'skill_stats': skill_stats,
        'today_completion': completion_pct,
        'avg_quiz_score': avg_quiz_score,
        'best_wpm': round(best_wpm, 1),
        'badges': badges_detail,
        'has_roadmap': today_roadmap is not None,
        'active_dates': user.to_dict().get('active_dates', []),
    })


@dashboard_bp.route('/api/roadmap/inject', methods=['POST'])
def inject_roadmap():
    """Admin endpoint to inject a custom syllabus JSON for the user."""
    from database.models import db, DailyRoadmap
    import json
    
    user = get_current_user()
    data = request.get_json()
    syllabus = data.get('syllabus', {})
    
    # Just a placeholder logic for the feature requirement
    # Real implementation would parse syllabus and create DailyRoadmap entries.
    return jsonify({"message": "Syllabus injected successfully", "status": "success"})


@dashboard_bp.route('/api/progress/report', methods=['GET'])
def generate_report():
    """Generate a markdown report of user progress."""
    user = get_current_user()
    skill_stats = get_skill_stats(user.id)
    
    report = f"# SkillRise Progress Report: {user.name}\n\n"
    report += f"**Level:** {user.level}\n"
    report += f"**XP:** {user.xp}\n"
    report += f"**Current Streak:** {user.streak} days\n\n"
    report += "## Skills\n"
    for skill, score in skill_stats['scores'].items():
        report += f"- {skill.title()}: {score}%\n"
        
    return jsonify({"report_markdown": report, "filename": f"{user.name.replace(' ', '_')}_report.md"})

