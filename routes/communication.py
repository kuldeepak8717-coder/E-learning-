from flask import Blueprint, render_template, jsonify, request
from database.models import db, CommunicationSession
from services.gemini_service import evaluate_communication, ask_gemini
from services.progress_service import award_xp, check_badges
from utils import get_current_user
import json

communication_bp = Blueprint('communication', __name__)

COMM_MODES = [
    {'id': 'daily_conversation', 'label': 'Daily Conversation', 'icon': '💬', 'description': 'Practice everyday English talking'},
    {'id': 'self_introduction', 'label': 'Self Introduction', 'icon': '👋', 'description': 'Introduce yourself in English'},
    {'id': 'interview', 'label': 'Interview Practice', 'icon': '🎯', 'description': 'Practice common interview questions'},
    {'id': 'college', 'label': 'College Talk', 'icon': '🎓', 'description': 'Conversations for college students'},
    {'id': 'office', 'label': 'Office Communication', 'icon': '💼', 'description': 'Professional workplace communication'},
    {'id': 'customer', 'label': 'Customer Service', 'icon': '🤝', 'description': 'Handle customer conversations'},
    {'id': 'asking_help', 'label': 'Asking for Help', 'icon': '🙋', 'description': 'Learn to ask questions politely'},
    {'id': 'daily_life', 'label': 'Daily Life Situations', 'icon': '🌍', 'description': 'Shopping, travel, and more'},
]

DAILY_TOPICS = {
    '30sec': [
        "Tell me about your morning routine.",
        "What is your favorite food and why?",
        "Describe your hometown in 3 sentences.",
        "What is one thing you want to improve?",
    ],
    '1min': [
        "Introduce yourself like you're meeting someone new at college.",
        "Describe your ideal study day.",
        "What is your biggest strength and why?",
        "Talk about a skill you are currently learning.",
    ],
    '2min': [
        "Where do you see yourself in 5 years?",
        "Describe a challenge you faced and how you solved it.",
        "What are your hobbies and how do they help you grow?",
        "Talk about the importance of communication skills in your career.",
    ]
}


@communication_bp.route('/communication')
def communication_page():
    return render_template('communication.html', modes=COMM_MODES, daily_topics=DAILY_TOPICS)


@communication_bp.route('/api/communication/evaluate', methods=['POST'])
def evaluate():
    data = request.get_json()
    user = get_current_user()

    user_text = data.get('text', '').strip()
    mode = data.get('mode', 'daily_conversation')

    if not user_text:
        return jsonify({'error': 'Please write something first'}), 400

    if len(user_text) < 5:
        return jsonify({'error': 'Write at least a few words'}), 400

    feedback = evaluate_communication(user_text, mode)

    # Save session
    session = CommunicationSession(
        user_id=user.id,
        mode=mode,
        user_text=user_text,
        ai_feedback=json.dumps(feedback),
        grammar_score=feedback.get('grammar_score', 7.0),
        vocabulary_score=feedback.get('vocabulary_score', 7.0),
        clarity_score=feedback.get('clarity_score', 7.0),
    )
    db.session.add(session)
    db.session.commit()

    # Award XP
    xp_result = award_xp(user, 'communication_session')
    new_badges = check_badges(user)

    return jsonify({
        'feedback': feedback,
        'xp_result': xp_result,
        'new_badges': new_badges,
        'session_id': session.id,
    })


@communication_bp.route('/api/communication/topic-prompt', methods=['POST'])
def get_topic_prompt():
    data = request.get_json()
    topic = data.get('topic', '')
    duration = data.get('duration', '1min')

    prompt = f"""Generate 3 speaking bullet points to help a beginner English student talk about: "{topic}" for {duration}.
Make them simple, practical, and encouraging. Return as a JSON list of strings."""

    try:
        from services.gemini_service import _get_model, _clean_json
        import json as _json
        model = _get_model()
        resp = model.generate_content(prompt)
        points = _json.loads(_clean_json(resp.text))
        return jsonify({'points': points})
    except Exception:
        return jsonify({'points': [
            f"Start with a greeting about {topic}",
            "Give 2-3 details or examples",
            "End with your personal opinion or feeling"
        ]})


@communication_bp.route('/api/communication/history')
def history():
    user = get_current_user()
    sessions = CommunicationSession.query.filter_by(user_id=user.id)\
        .order_by(CommunicationSession.date.desc()).limit(10).all()
    return jsonify([s.to_dict() for s in sessions])
