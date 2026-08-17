from flask import Blueprint, render_template, jsonify, request
from database.models import db, CoachMessage
from services.gemini_service import chat_with_coach
from utils import get_current_user

coach_bp = Blueprint('coach', __name__)

QUICK_ACTIONS = [
    {'label': 'Explain a Topic', 'prompt': 'Can you explain [topic] in simple English?', 'icon': '📚'},
    {'label': 'Quiz Me', 'prompt': 'Give me 5 practice questions on [topic]', 'icon': '🧠'},
    {'label': 'Correct My English', 'prompt': 'Please correct this English: [your sentence]', 'icon': '✏️'},
    {'label': 'Help with Code', 'prompt': 'Can you help me fix this code: [paste code]', 'icon': '💻'},
    {'label': 'Study Plan', 'prompt': 'Create a 1-week study plan for me to improve my [skill]', 'icon': '📅'},
    {'label': 'What to Study Next', 'prompt': 'Based on my learning, what should I focus on next?', 'icon': '🎯'},
]


@coach_bp.route('/coach')
def coach_page():
    user = get_current_user()
    return render_template('coach.html', quick_actions=QUICK_ACTIONS, user=user)


@coach_bp.route('/api/coach/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user = get_current_user()
    message = data.get('message', '').strip()

    if not message:
        return jsonify({'error': 'Message is empty'}), 400

    # Load recent history
    recent_messages = CoachMessage.query.filter_by(user_id=user.id)\
        .order_by(CoachMessage.date.desc()).limit(10).all()
    history = [{'role': m.role, 'content': m.content}
               for m in reversed(recent_messages)]

    # Get AI response
    response = chat_with_coach(message, history)

    # Save both messages
    user_msg = CoachMessage(user_id=user.id, role='user', content=message)
    ai_msg = CoachMessage(user_id=user.id, role='assistant', content=response)
    db.session.add(user_msg)
    db.session.add(ai_msg)
    db.session.commit()

    return jsonify({
        'response': response,
        'message_id': ai_msg.id,
    })


@coach_bp.route('/api/coach/history')
def get_history():
    user = get_current_user()
    messages = CoachMessage.query.filter_by(user_id=user.id)\
        .order_by(CoachMessage.date.asc()).limit(50).all()
    return jsonify([m.to_dict() for m in messages])


@coach_bp.route('/api/coach/clear', methods=['POST'])
def clear_history():
    user = get_current_user()
    CoachMessage.query.filter_by(user_id=user.id).delete()
    db.session.commit()
    return jsonify({'cleared': True})
