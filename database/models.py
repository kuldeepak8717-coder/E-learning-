"""
SkillRise AI — Database Models
SQLAlchemy ORM models for the platform
"""

from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
import json

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, default='Student')
    goal = db.Column(db.String(200), default='Improve Skills')
    avatar = db.Column(db.String(10), default='🎓')
    current_level = db.Column(db.String(50), default='Beginner')
    day_number = db.Column(db.Integer, default=1)
    xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    streak = db.Column(db.Integer, default=0)
    last_activity_date = db.Column(db.Date, default=date.today)
    daily_target_minutes = db.Column(db.Integer, default=60)
    badges = db.Column(db.Text, default='[]')  # JSON list
    active_dates = db.Column(db.Text, default='[]')  # JSON list of dates ('YYYY-MM-DD')

    # Skill levels (1-10)
    english_level = db.Column(db.Integer, default=1)
    typing_speed = db.Column(db.Integer, default=20)  # WPM
    communication_level = db.Column(db.Integer, default=1)
    aptitude_level = db.Column(db.Integer, default=1)
    reasoning_level = db.Column(db.Integer, default=1)
    programming_level = db.Column(db.Integer, default=1)
    verbal_level = db.Column(db.Integer, default=1)

    # Onboarding completed
    onboarded = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_badges(self):
        return json.loads(self.badges)

    def add_badge(self, badge_name):
        badges = self.get_badges()
        if badge_name not in badges:
            badges.append(badge_name)
            self.badges = json.dumps(badges)
            return True
        return False

    def add_xp(self, points):
        self.xp += points
        new_level = (self.xp // 500) + 1
        self.level = new_level

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'goal': self.goal,
            'avatar': self.avatar,
            'current_level': self.current_level,
            'day_number': self.day_number,
            'xp': self.xp,
            'level': self.level,
            'streak': self.streak,
            'daily_target_minutes': self.daily_target_minutes,
            'badges': self.get_badges(),
            'english_level': self.english_level,
            'typing_speed': self.typing_speed,
            'communication_level': self.communication_level,
            'aptitude_level': self.aptitude_level,
            'reasoning_level': self.reasoning_level,
            'programming_level': self.programming_level,
            'verbal_level': self.verbal_level,
            'onboarded': self.onboarded,
            'active_dates': json.loads(self.active_dates) if self.active_dates else [],
        }


class DailyRoadmap(db.Model):
    __tablename__ = 'daily_roadmaps'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    day_number = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, default=date.today)
    plan_json = db.Column(db.Text, nullable=False)  # JSON plan
    completed_tasks = db.Column(db.Text, default='[]')  # JSON list
    total_tasks = db.Column(db.Integer, default=0)
    xp_earned = db.Column(db.Integer, default=0)
    completed = db.Column(db.Boolean, default=False)

    def get_plan(self):
        return json.loads(self.plan_json)

    def get_completed_tasks(self):
        return json.loads(self.completed_tasks)

    def complete_task(self, task_id):
        tasks = self.get_completed_tasks()
        if task_id not in tasks:
            tasks.append(task_id)
            self.completed_tasks = json.dumps(tasks)

    def completion_percent(self):
        if self.total_tasks == 0:
            return 0
        return round((len(self.get_completed_tasks()) / self.total_tasks) * 100)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'day_number': self.day_number,
            'date': str(self.date),
            'plan': self.get_plan(),
            'completed_tasks': self.get_completed_tasks(),
            'total_tasks': self.total_tasks,
            'completion_percent': self.completion_percent(),
            'xp_earned': self.xp_earned,
            'completed': self.completed,
        }


class QuizResult(db.Model):
    __tablename__ = 'quiz_results'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(20), default='medium')
    score = db.Column(db.Integer, default=0)
    total = db.Column(db.Integer, default=10)
    accuracy = db.Column(db.Float, default=0.0)
    time_taken = db.Column(db.Integer, default=0)  # seconds
    weak_topics = db.Column(db.Text, default='[]')  # JSON
    answers_json = db.Column(db.Text, default='[]')  # JSON
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'subject': self.subject,
            'difficulty': self.difficulty,
            'score': self.score,
            'total': self.total,
            'accuracy': self.accuracy,
            'time_taken': self.time_taken,
            'weak_topics': json.loads(self.weak_topics),
            'date': self.date.isoformat(),
        }


class TypingResult(db.Model):
    __tablename__ = 'typing_results'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    wpm = db.Column(db.Float, default=0.0)
    accuracy = db.Column(db.Float, default=0.0)
    correct_chars = db.Column(db.Integer, default=0)
    wrong_chars = db.Column(db.Integer, default=0)
    mode = db.Column(db.String(50), default='sentences')
    duration = db.Column(db.Integer, default=60)  # seconds
    is_personal_best = db.Column(db.Boolean, default=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'wpm': self.wpm,
            'accuracy': self.accuracy,
            'correct_chars': self.correct_chars,
            'wrong_chars': self.wrong_chars,
            'mode': self.mode,
            'duration': self.duration,
            'is_personal_best': self.is_personal_best,
            'date': self.date.isoformat(),
        }


class CommunicationSession(db.Model):
    __tablename__ = 'communication_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mode = db.Column(db.String(50), default='daily_conversation')
    user_text = db.Column(db.Text, nullable=False)
    ai_feedback = db.Column(db.Text, nullable=False)  # JSON
    grammar_score = db.Column(db.Float, default=0.0)
    vocabulary_score = db.Column(db.Float, default=0.0)
    clarity_score = db.Column(db.Float, default=0.0)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'mode': self.mode,
            'user_text': self.user_text,
            'feedback': json.loads(self.ai_feedback),
            'grammar_score': self.grammar_score,
            'vocabulary_score': self.vocabulary_score,
            'clarity_score': self.clarity_score,
            'date': self.date.isoformat(),
        }


class ProgressEntry(db.Model):
    __tablename__ = 'progress_entries'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    metric_name = db.Column(db.String(50), nullable=False)
    value = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, default=date.today)

    def to_dict(self):
        return {
            'subject': self.subject,
            'metric_name': self.metric_name,
            'value': self.value,
            'date': str(self.date),
        }


class AIRecommendation(db.Model):
    __tablename__ = 'ai_recommendations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recommendation_json = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def get_recommendation(self):
        return json.loads(self.recommendation_json)


class CoachMessage(db.Model):
    __tablename__ = 'coach_messages'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'date': self.date.isoformat(),
        }
