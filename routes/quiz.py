from flask import Blueprint, render_template, jsonify, request
from database.models import db, QuizResult
from services.gemini_service import generate_quiz
from services.progress_service import award_xp, check_badges
from utils import get_current_user
import json

quiz_bp = Blueprint('quiz', __name__)

QUIZ_SUBJECTS = [
    {'id': 'english', 'label': 'English Grammar', 'icon': '📝'},
    {'id': 'vocabulary', 'label': 'Vocabulary', 'icon': '📖'},
    {'id': 'aptitude', 'label': 'Aptitude', 'icon': '➗'},
    {'id': 'reasoning', 'label': 'Logical Reasoning', 'icon': '🧠'},
    {'id': 'verbal', 'label': 'Verbal Ability', 'icon': '🗣️'},
    {'id': 'programming', 'label': 'Programming', 'icon': '💻'},
    {'id': 'mixed', 'label': 'Mixed Quiz', 'icon': '🎯'},
]


@quiz_bp.route('/quiz')
def quiz_page():
    return render_template('quiz.html', subjects=QUIZ_SUBJECTS)


@quiz_bp.route('/api/quiz/generate', methods=['POST'])
def generate():
    data = request.get_json()
    subject = data.get('subject', 'mixed')
    difficulty = data.get('difficulty', 'medium')
    count = int(data.get('count', 10))

    # For mixed, pick from multiple subjects
    if subject == 'mixed':
        import random
        subjects = ['english', 'aptitude', 'reasoning', 'verbal', 'programming']
        questions = []
        per_subject = max(2, count // len(subjects))
        for s in random.sample(subjects, min(len(subjects), count)):
            q = generate_quiz(s, difficulty, per_subject)
            questions.extend(q)
        questions = questions[:count]
    else:
        questions = generate_quiz(subject, difficulty, count)

    return jsonify({'questions': questions, 'subject': subject, 'difficulty': difficulty})


@quiz_bp.route('/api/quiz/submit', methods=['POST'])
def submit():
    data = request.get_json()
    user = get_current_user()

    subject = data.get('subject', 'mixed')
    difficulty = data.get('difficulty', 'medium')
    answers = data.get('answers', [])  # [{'question_index': 0, 'selected': 1, 'correct': 2}, ...]
    time_taken = data.get('time_taken', 0)
    questions = data.get('questions', [])

    if not answers:
        return jsonify({'error': 'No answers provided'}), 400

    # Calculate results
    correct_count = sum(1 for a in answers if a.get('selected') == a.get('correct'))
    total = len(answers)
    accuracy = round((correct_count / total) * 100, 1) if total > 0 else 0

    # Find weak topics
    weak_topics = list(set(
        questions[a['question_index']].get('topic', subject)
        for a in answers
        if a.get('selected') != a.get('correct') and a['question_index'] < len(questions)
    ))

    # Save result
    result = QuizResult(
        user_id=user.id,
        subject=subject,
        difficulty=difficulty,
        score=correct_count,
        total=total,
        accuracy=accuracy,
        time_taken=time_taken,
        weak_topics=json.dumps(weak_topics),
        answers_json=json.dumps(answers),
    )
    db.session.add(result)
    db.session.commit()

    # Award XP
    bonus = correct_count * 5
    xp_result = award_xp(user, 'quiz_completed', bonus)
    new_badges = check_badges(user)

    return jsonify({
        'score': correct_count,
        'total': total,
        'accuracy': accuracy,
        'time_taken': time_taken,
        'weak_topics': weak_topics,
        'xp_result': xp_result,
        'new_badges': new_badges,
    })


@quiz_bp.route('/api/quiz/history')
def history():
    user = get_current_user()
    results = QuizResult.query.filter_by(user_id=user.id)\
        .order_by(QuizResult.date.desc()).limit(20).all()
    return jsonify([r.to_dict() for r in results])


@quiz_bp.route('/api/quiz/weak-areas')
def weak_areas():
    user = get_current_user()
    results = QuizResult.query.filter_by(user_id=user.id)\
        .order_by(QuizResult.date.desc()).limit(10).all()

    all_weak = []
    for r in results:
        all_weak.extend(json.loads(r.weak_topics))

    # Count frequency
    from collections import Counter
    topic_counts = Counter(all_weak).most_common(10)
    return jsonify([{'topic': t, 'count': c} for t, c in topic_counts])
