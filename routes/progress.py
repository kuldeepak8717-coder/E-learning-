from flask import Blueprint, render_template, jsonify, request
from database.models import db, QuizResult, TypingResult, CommunicationSession, DailyRoadmap, ProgressEntry
from services.gemini_service import analyze_performance
from utils import get_current_user
from sqlalchemy import func
from datetime import date, timedelta
import json

progress_bp = Blueprint('progress', __name__)


@progress_bp.route('/progress')
def progress_page():
    return render_template('progress.html')


@progress_bp.route('/api/progress/overview')
def overview():
    user = get_current_user()

    # Quiz stats per subject
    subjects = ['english', 'vocabulary', 'aptitude', 'reasoning', 'verbal', 'programming', 'mixed']
    quiz_stats = {}
    for subject in subjects:
        results = QuizResult.query.filter_by(user_id=user.id, subject=subject)\
            .order_by(QuizResult.date.desc()).limit(10).all()
        if results:
            quiz_stats[subject] = {
                'count': len(results),
                'avg_accuracy': round(sum(r.accuracy for r in results) / len(results), 1),
                'best_accuracy': round(max(r.accuracy for r in results), 1),
                'total_questions': sum(r.total for r in results),
            }

    # Typing stats
    typing_results = TypingResult.query.filter_by(user_id=user.id)\
        .order_by(TypingResult.date.desc()).limit(20).all()
    typing_stats = {}
    if typing_results:
        typing_stats = {
            'best_wpm': round(max(r.wpm for r in typing_results), 1),
            'avg_wpm': round(sum(r.wpm for r in typing_results) / len(typing_results), 1),
            'avg_accuracy': round(sum(r.accuracy for r in typing_results) / len(typing_results), 1),
            'total_tests': len(typing_results),
        }

    # Communication stats
    comm_sessions = CommunicationSession.query.filter_by(user_id=user.id).all()
    comm_stats = {}
    if comm_sessions:
        comm_stats = {
            'total_sessions': len(comm_sessions),
            'avg_grammar': round(sum(s.grammar_score for s in comm_sessions) / len(comm_sessions), 1),
            'avg_vocabulary': round(sum(s.vocabulary_score for s in comm_sessions) / len(comm_sessions), 1),
            'avg_clarity': round(sum(s.clarity_score for s in comm_sessions) / len(comm_sessions), 1),
        }

    # Roadmap completion
    roadmaps = DailyRoadmap.query.filter_by(user_id=user.id).all()
    roadmap_stats = {
        'total_days': len(roadmaps),
        'completed_days': sum(1 for r in roadmaps if r.completed),
        'total_xp_earned': sum(r.xp_earned for r in roadmaps),
    }

    return jsonify({
        'user': user.to_dict(),
        'quiz_stats': quiz_stats,
        'typing_stats': typing_stats,
        'comm_stats': comm_stats,
        'roadmap_stats': roadmap_stats,
    })


@progress_bp.route('/api/progress/weekly-chart')
def weekly_chart():
    user = get_current_user()
    today = date.today()

    labels = []
    quiz_scores = []
    wpm_values = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        labels.append(day.strftime('%a'))

        # Quiz accuracy for the day
        day_quizzes = QuizResult.query.filter_by(user_id=user.id)\
            .filter(func.date(QuizResult.date) == day).all()
        avg_acc = round(sum(q.accuracy for q in day_quizzes) / len(day_quizzes)) if day_quizzes else 0
        quiz_scores.append(avg_acc)

        # Typing WPM for the day
        day_typing = TypingResult.query.filter_by(user_id=user.id)\
            .filter(func.date(TypingResult.date) == day).all()
        avg_wpm = round(max((t.wpm for t in day_typing), default=0))
        wpm_values.append(avg_wpm)

    return jsonify({
        'labels': labels,
        'quiz_scores': quiz_scores,
        'wpm_values': wpm_values,
    })


@progress_bp.route('/api/progress/skill-radar')
def skill_radar():
    user = get_current_user()

    def subject_score(subject):
        results = QuizResult.query.filter_by(user_id=user.id, subject=subject)\
            .order_by(QuizResult.date.desc()).limit(5).all()
        if results:
            return round(sum(r.accuracy for r in results) / len(results))
        return 0

    best_wpm = db.session.query(func.max(TypingResult.wpm)).filter_by(user_id=user.id).scalar() or 0

    return jsonify({
        'labels': ['English', 'Aptitude', 'Reasoning', 'Verbal', 'Programming', 'Typing', 'Communication'],
        'scores': [
            subject_score('english'),
            subject_score('aptitude'),
            subject_score('reasoning'),
            subject_score('verbal'),
            subject_score('programming'),
            min(100, round((best_wpm / 80) * 100)),
            min(100, round(user.communication_level * 10)),
        ]
    })


@progress_bp.route('/api/progress/analyze', methods=['POST'])
def analyze():
    user = get_current_user()

    # Gather stats for AI analysis
    from sqlalchemy import func
    stats = {
        'name': user.name,
        'day_number': user.day_number,
        'streak': user.streak,
        'xp': user.xp,
        'level': user.level,
        'quiz_count': QuizResult.query.filter_by(user_id=user.id).count(),
        'typing_best_wpm': round(db.session.query(func.max(TypingResult.wpm)).filter_by(user_id=user.id).scalar() or 0, 1),
        'comm_sessions': CommunicationSession.query.filter_by(user_id=user.id).count(),
    }

    recommendation = analyze_performance(stats)
    return jsonify(recommendation)
