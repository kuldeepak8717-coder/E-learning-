"""
SkillRise AI — Flask Application Entry Point
"""

import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from database.models import db, User
from datetime import date, timedelta

load_dotenv()


def get_current_user():
    """Get or create the current user (single-user mode for now)."""
    from database.models import User
    user = User.query.first()
    if user:
        # Update streak
        today = date.today()
        last = user.last_activity_date
        if last != today:
            if last == today - timedelta(days=1):
                user.streak += 1
            else:
                user.streak = 1
            user.last_activity_date = today
            user.add_xp(10)  # Login XP
            db.session.commit()
    return user


def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'skillrise-dev-secret-2024')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///skillrise.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    CORS(app)

    # Register blueprints
    from routes.dashboard import dashboard_bp
    from routes.notes import notes_bp
    from routes.quiz import quiz_bp
    from routes.typing_test import typing_bp
    from routes.communication import communication_bp
    from routes.reasoning import reasoning_bp
    from routes.aptitude import aptitude_bp
    from routes.verbal import verbal_bp
    from routes.programming import programming_bp
    from routes.roadmap import roadmap_bp
    from routes.ai_coach import coach_bp
    from routes.image_gen import image_gen_bp
    from routes.progress import progress_bp
    from routes.profile import profile_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(notes_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(typing_bp)
    app.register_blueprint(communication_bp)
    app.register_blueprint(reasoning_bp)
    app.register_blueprint(aptitude_bp)
    app.register_blueprint(verbal_bp)
    app.register_blueprint(programming_bp)
    app.register_blueprint(roadmap_bp)
    app.register_blueprint(coach_bp)
    app.register_blueprint(image_gen_bp)
    app.register_blueprint(progress_bp)
    app.register_blueprint(profile_bp)

    # Create tables
    with app.app_context():
        db.create_all()
        _ensure_default_user()

    return app


def _ensure_default_user():
    """Create a default user if none exists."""
    user = User.query.first()
    if not user:
        user = User(
            name='Student',
            goal='Become job-ready in 90 days',
        )
        db.session.add(user)
        db.session.commit()


app = create_app()

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', 'True') == 'True', port=5000)
