"""
SkillRise AI — Shared Utilities
Provides get_current_user without circular imports.
"""

from datetime import date, timedelta
from database.models import db, User


def get_current_user():
    """Get or create the current user (single-user mode)."""
    user = User.query.first()
    if user:
        today = date.today()
        last = user.last_activity_date
        if last != today:
            if last == today - timedelta(days=1):
                user.streak += 1
            else:
                user.streak = 1
            user.last_activity_date = today
            user.add_xp(10)
            db.session.commit()
    return user
