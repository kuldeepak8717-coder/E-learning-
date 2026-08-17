"""
SkillRise AI — Progress & Gamification Service
Handles XP, streaks, badges, and level calculations.
"""

from datetime import date, timedelta
from database.models import db, User, ProgressEntry, QuizResult, TypingResult


BADGE_DEFINITIONS = {
    'first_quiz': {'name': 'First Quiz', 'icon': '🏆', 'description': 'Completed your first quiz'},
    'streak_7': {'name': '7-Day Streak', 'icon': '🔥', 'description': 'Studied 7 days in a row'},
    'streak_30': {'name': '30-Day Streak', 'icon': '💎', 'description': 'Studied 30 days in a row'},
    'wpm_40': {'name': 'Speed Typist', 'icon': '⌨️', 'description': 'Reached 40 WPM typing speed'},
    'wpm_60': {'name': 'Fast Typist', 'icon': '🚀', 'description': 'Reached 60 WPM typing speed'},
    'questions_100': {'name': 'Quiz Master', 'icon': '🧠', 'description': 'Answered 100 quiz questions'},
    'coding_10': {'name': 'Code Ninja', 'icon': '💻', 'description': 'Solved 10 coding problems'},
    'communication_7': {'name': 'Communicator', 'icon': '🗣️', 'description': 'Completed 7 communication sessions'},
    'perfect_quiz': {'name': 'Perfect Score', 'icon': '⭐', 'description': 'Got 100% on a quiz'},
    'early_bird': {'name': 'Early Bird', 'icon': '🌅', 'description': 'Studied before 8 AM'},
}

LEVEL_NAMES = {
    1: "Beginner", 2: "Learner", 3: "Practitioner", 4: "Skilled",
    5: "Advanced", 6: "Expert", 7: "Master", 8: "Champion",
    9: "Elite", 10: "Legend"
}

XP_REWARDS = {
    'quiz_question_correct': 5,
    'quiz_completed': 20,
    'typing_test': 15,
    'typing_personal_best': 10,  # bonus
    'communication_session': 25,
    'lesson_completed': 15,
    'roadmap_task': 20,
    'roadmap_day_complete': 50,
    'login_streak': 10,
}


def update_streak(user: User) -> int:
    """Update user streak and return new streak count."""
    import json
    today = date.today()
    last = user.last_activity_date

    # Record active date
    active_list = json.loads(user.active_dates) if user.active_dates else []
    today_str = today.isoformat()
    if today_str not in active_list:
        active_list.append(today_str)
        user.active_dates = json.dumps(active_list)

    if last == today:
        db.session.commit()
        return user.streak  # Already logged today

    if last == today - timedelta(days=1):
        user.streak += 1
    else:
        user.streak = 1  # Reset streak

    user.last_activity_date = today

    # Award streak XP
    user.add_xp(XP_REWARDS['login_streak'])

    # Check streak badges
    if user.streak >= 7:
        if user.add_badge('streak_7'):
            pass  # Badge unlocked
    if user.streak >= 30:
        user.add_badge('streak_30')

    db.session.commit()
    return user.streak


def award_xp(user: User, action: str, bonus: int = 0) -> dict:
    """Award XP for an action and check for level ups."""
    old_level = user.level
    points = XP_REWARDS.get(action, 10) + bonus
    user.add_xp(points)
    new_level = user.level

    result = {
        'xp_awarded': points,
        'total_xp': user.xp,
        'new_level': new_level,
        'level_up': new_level > old_level,
        'level_name': LEVEL_NAMES.get(new_level, 'Legend'),
    }

    db.session.commit()
    return result


def check_badges(user: User) -> list:
    """Check and award any newly earned badges. Returns list of new badge names."""
    new_badges = []

    # Quiz badges
    quiz_count = QuizResult.query.filter_by(user_id=user.id).count()
    if quiz_count >= 1 and user.add_badge('first_quiz'):
        new_badges.append('first_quiz')

    # Total questions answered
    total_questions = db.session.query(db.func.sum(QuizResult.total)).filter_by(user_id=user.id).scalar() or 0
    if total_questions >= 100 and user.add_badge('questions_100'):
        new_badges.append('questions_100')

    # Perfect quiz
    perfect = QuizResult.query.filter_by(user_id=user.id, accuracy=100.0).first()
    if perfect and user.add_badge('perfect_quiz'):
        new_badges.append('perfect_quiz')

    # Typing badges
    best_wpm = db.session.query(db.func.max(TypingResult.wpm)).filter_by(user_id=user.id).scalar() or 0
    if best_wpm >= 40 and user.add_badge('wpm_40'):
        new_badges.append('wpm_40')
    if best_wpm >= 60 and user.add_badge('wpm_60'):
        new_badges.append('wpm_60')

    if new_badges:
        db.session.commit()

    return new_badges


def get_level_progress(user: User) -> dict:
    """Get XP progress towards next level."""
    xp_per_level = 500
    level_xp = user.xp % xp_per_level
    return {
        'current_level': user.level,
        'level_name': LEVEL_NAMES.get(user.level, 'Legend'),
        'current_xp': user.xp,
        'level_xp': level_xp,
        'xp_to_next': xp_per_level - level_xp,
        'progress_percent': round((level_xp / xp_per_level) * 100),
        'next_level_name': LEVEL_NAMES.get(user.level + 1, 'Legend'),
    }


def get_skill_stats(user_id: int) -> dict:
    """Compute overall skill statistics for a user."""
    # Recent quiz accuracy per subject
    subjects = ['english', 'aptitude', 'reasoning', 'verbal', 'programming']
    skill_scores = {}

    for subject in subjects:
        recent = QuizResult.query.filter_by(
            user_id=user_id, subject=subject
        ).order_by(QuizResult.date.desc()).limit(5).all()

        if recent:
            avg_acc = sum(r.accuracy for r in recent) / len(recent)
            skill_scores[subject] = round(avg_acc)
        else:
            skill_scores[subject] = 0

    # Typing best
    best_wpm = db.session.query(db.func.max(TypingResult.wpm)).filter_by(user_id=user_id).scalar() or 0

    skill_scores['typing'] = min(100, round((best_wpm / 80) * 100))

    if skill_scores:
        best_skill = max(skill_scores, key=skill_scores.get)
        worst_skill = min(skill_scores, key=skill_scores.get)
    else:
        best_skill = 'typing'
        worst_skill = 'aptitude'

    return {
        'scores': skill_scores,
        'best_skill': best_skill,
        'worst_skill': worst_skill,
        'best_wpm': round(best_wpm, 1),
    }
