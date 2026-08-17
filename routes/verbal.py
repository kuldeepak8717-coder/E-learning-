from flask import Blueprint, render_template, jsonify, request
from services.gemini_service import generate_quiz

verbal_bp = Blueprint('verbal', __name__)

VERBAL_TOPICS = [
    {'id': 'synonyms', 'label': 'Synonyms', 'icon': '🔄'},
    {'id': 'antonyms', 'label': 'Antonyms', 'icon': '↔️'},
    {'id': 'vocabulary', 'label': 'Vocabulary Building', 'icon': '📚'},
    {'id': 'sentence_correction', 'label': 'Sentence Correction', 'icon': '✏️'},
    {'id': 'fill_blanks', 'label': 'Fill in the Blanks', 'icon': '⬜'},
    {'id': 'para_jumbles', 'label': 'Para Jumbles', 'icon': '🔀'},
    {'id': 'reading_comprehension', 'label': 'Reading Comprehension', 'icon': '📖'},
    {'id': 'sentence_completion', 'label': 'Sentence Completion', 'icon': '✅'},
    {'id': 'idioms_phrases', 'label': 'Idioms & Phrases', 'icon': '💭'},
]


@verbal_bp.route('/verbal')
def verbal_page():
    return render_template('verbal.html', topics=VERBAL_TOPICS)


@verbal_bp.route('/api/verbal/quiz', methods=['POST'])
def get_quiz():
    data = request.get_json()
    topic = data.get('topic', 'verbal ability')
    difficulty = data.get('difficulty', 'medium')
    count = int(data.get('count', 10))

    subject = f"Verbal Ability - {topic.replace('_', ' ').title()}"
    questions = generate_quiz(subject, difficulty, count)
    return jsonify({'questions': questions})


@verbal_bp.route('/api/verbal/daily', methods=['GET'])
def daily_practice():
    """Generate 10 mixed verbal questions for daily practice."""
    topics = ['synonyms', 'antonyms', 'fill_blanks', 'sentence_correction']
    import random
    topic = random.choice(topics)
    subject = f"Verbal Ability - {topic.replace('_', ' ').title()}"
    questions = generate_quiz(subject, 'medium', 10)
    return jsonify({'questions': questions, 'topic': topic})
