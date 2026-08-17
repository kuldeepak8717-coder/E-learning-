from flask import Blueprint, render_template, jsonify, request
from services.gemini_service import generate_quiz, generate_notes

reasoning_bp = Blueprint('reasoning', __name__)

REASONING_TOPICS = [
    {'id': 'number_series', 'label': 'Number Series', 'icon': '🔢', 'description': 'Find the pattern in number sequences'},
    {'id': 'alphabet_series', 'label': 'Alphabet Series', 'icon': '🔤', 'description': 'Letter and alphabet patterns'},
    {'id': 'coding_decoding', 'label': 'Coding-Decoding', 'icon': '🔐', 'description': 'Decode hidden patterns'},
    {'id': 'analogy', 'label': 'Analogy', 'icon': '🔗', 'description': 'Find relationships between pairs'},
    {'id': 'classification', 'label': 'Classification', 'icon': '📂', 'description': 'Group and identify categories'},
    {'id': 'blood_relations', 'label': 'Blood Relations', 'icon': '👨‍👩‍👧', 'description': 'Family relationship puzzles'},
    {'id': 'direction_sense', 'label': 'Direction Sense', 'icon': '🧭', 'description': 'Navigate direction problems'},
    {'id': 'syllogism', 'label': 'Syllogism', 'icon': '💭', 'description': 'Logical deduction from statements'},
    {'id': 'statement_conclusion', 'label': 'Statement & Conclusion', 'icon': '📋', 'description': 'Draw conclusions from statements'},
    {'id': 'seating_arrangement', 'label': 'Seating Arrangement', 'icon': '💺', 'description': 'Arrange people based on conditions'},
    {'id': 'odd_one_out', 'label': 'Odd One Out', 'icon': '❓', 'description': 'Find the odd element'},
]


@reasoning_bp.route('/reasoning')
def reasoning_page():
    return render_template('reasoning.html', topics=REASONING_TOPICS)


@reasoning_bp.route('/api/reasoning/notes', methods=['POST'])
def get_notes():
    data = request.get_json()
    topic = data.get('topic', '')
    notes = generate_notes(topic, 'Logical Reasoning')
    return jsonify(notes)


@reasoning_bp.route('/api/reasoning/quiz', methods=['POST'])
def get_quiz():
    data = request.get_json()
    topic = data.get('topic', 'logical reasoning')
    difficulty = data.get('difficulty', 'medium')
    count = int(data.get('count', 5))

    subject = f"Logical Reasoning - {topic.replace('_', ' ').title()}"
    questions = generate_quiz(subject, difficulty, count)
    return jsonify({'questions': questions})
