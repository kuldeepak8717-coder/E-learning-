from flask import Blueprint, render_template, jsonify, request
from services.gemini_service import generate_quiz, generate_notes

aptitude_bp = Blueprint('aptitude', __name__)

APTITUDE_TOPICS = [
    {'id': 'number_system', 'label': 'Number System', 'icon': '🔢',
     'formula': 'LCM × HCF = Product of two numbers',
     'description': 'Types of numbers, divisibility rules, LCM & HCF'},
    {'id': 'percentage', 'label': 'Percentage', 'icon': '📊',
     'formula': 'Percentage = (Value / Total) × 100',
     'description': 'Calculate percentages, increase/decrease'},
    {'id': 'profit_loss', 'label': 'Profit & Loss', 'icon': '💰',
     'formula': 'Profit% = (Profit / CP) × 100',
     'description': 'Cost price, selling price, profit/loss calculations'},
    {'id': 'ratio', 'label': 'Ratio & Proportion', 'icon': '⚖️',
     'formula': 'a:b = c:d → a×d = b×c',
     'description': 'Ratios, proportions, and partnerships'},
    {'id': 'average', 'label': 'Average', 'icon': '📈',
     'formula': 'Average = Sum of all items / Number of items',
     'description': 'Mean, weighted average, and averages in groups'},
    {'id': 'time_work', 'label': 'Time & Work', 'icon': '⏰',
     'formula': 'Work = Rate × Time; Combined Rate = 1/A + 1/B',
     'description': 'Efficiency, pipes & cisterns, combined work'},
    {'id': 'speed_distance', 'label': 'Speed, Distance & Time', 'icon': '🚀',
     'formula': 'Speed = Distance / Time',
     'description': 'Relative speed, trains, boats & streams'},
    {'id': 'simple_interest', 'label': 'Simple Interest', 'icon': '💳',
     'formula': 'SI = (P × R × T) / 100',
     'description': 'Principal, rate, time calculations'},
    {'id': 'compound_interest', 'label': 'Compound Interest', 'icon': '📉',
     'formula': 'A = P(1 + R/100)^T',
     'description': 'Compound interest with different periods'},
    {'id': 'probability', 'label': 'Probability', 'icon': '🎲',
     'formula': 'P(E) = Favorable Outcomes / Total Outcomes',
     'description': 'Basic probability, coins, cards, dice'},
    {'id': 'data_interpretation', 'label': 'Data Interpretation', 'icon': '📋',
     'formula': 'Read graphs, tables, and charts carefully',
     'description': 'Bar graphs, pie charts, line graphs, tables'},
]


@aptitude_bp.route('/aptitude')
def aptitude_page():
    return render_template('aptitude.html', topics=APTITUDE_TOPICS)


@aptitude_bp.route('/api/aptitude/notes', methods=['POST'])
def get_notes():
    data = request.get_json()
    topic = data.get('topic', '')
    notes = generate_notes(topic, 'Quantitative Aptitude')
    return jsonify(notes)


@aptitude_bp.route('/api/aptitude/quiz', methods=['POST'])
def get_quiz():
    data = request.get_json()
    topic = data.get('topic', 'aptitude')
    difficulty = data.get('difficulty', 'medium')
    count = int(data.get('count', 5))

    subject = f"Quantitative Aptitude - {topic.replace('_', ' ').title()}"
    questions = generate_quiz(subject, difficulty, count)
    return jsonify({'questions': questions})


@aptitude_bp.route('/api/aptitude/formulas')
def get_formulas():
    formulas = [{'topic': t['label'], 'formula': t['formula'], 'icon': t['icon']}
                for t in APTITUDE_TOPICS]
    return jsonify(formulas)
