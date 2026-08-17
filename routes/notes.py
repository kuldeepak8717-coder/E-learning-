from flask import Blueprint, render_template, jsonify, request
from services.gemini_service import generate_notes

notes_bp = Blueprint('notes', __name__)

NOTES_CATEGORIES = {
    'english': {
        'label': 'English Grammar',
        'icon': '📝',
        'topics': ['Parts of Speech', 'Tenses', 'Active & Passive Voice', 'Direct & Indirect Speech',
                   'Articles', 'Prepositions', 'Conjunctions', 'Subject-Verb Agreement',
                   'Modals', 'Conditional Sentences']
    },
    'vocabulary': {
        'label': 'Vocabulary',
        'icon': '📖',
        'topics': ['Common Words', 'Synonyms & Antonyms', 'Word Formation', 'Phrasal Verbs',
                   'Idioms & Phrases', 'Root Words', 'Prefixes & Suffixes', 'Collocations']
    },
    'aptitude': {
        'label': 'Aptitude',
        'icon': '➗',
        'topics': ['Number System', 'Percentage', 'Profit & Loss', 'Ratio & Proportion',
                   'Average', 'Time & Work', 'Speed Distance Time', 'Simple Interest',
                   'Compound Interest', 'Probability', 'Data Interpretation']
    },
    'reasoning': {
        'label': 'Logical Reasoning',
        'icon': '🧠',
        'topics': ['Number Series', 'Alphabet Series', 'Coding-Decoding', 'Analogy',
                   'Classification', 'Blood Relations', 'Direction Sense', 'Syllogism',
                   'Statement & Conclusion', 'Seating Arrangement', 'Odd One Out']
    },
    'verbal': {
        'label': 'Verbal Ability',
        'icon': '🗣️',
        'topics': ['Synonyms', 'Antonyms', 'Fill in the Blanks', 'Sentence Correction',
                   'Para Jumbles', 'Reading Comprehension', 'Sentence Completion', 'Error Detection']
    },
    'python': {
        'label': 'Python',
        'icon': '🐍',
        'topics': ['Variables & Data Types', 'Operators', 'Control Flow', 'Loops',
                   'Functions', 'Lists', 'Dictionaries', 'Strings', 'OOP Concepts',
                   'File Handling', 'Exception Handling', 'Modules']
    },
    'cpp': {
        'label': 'C/C++',
        'icon': '⚙️',
        'topics': ['Variables & Data Types', 'Operators', 'Control Statements', 'Loops',
                   'Functions', 'Arrays', 'Pointers', 'Strings', 'OOP in C++',
                   'Structures', 'File Handling']
    },
    'java': {
        'label': 'Java',
        'icon': '☕',
        'topics': ['Java Basics', 'OOP Concepts', 'Arrays', 'Strings', 'Collections',
                   'Exception Handling', 'Interfaces', 'Inheritance', 'Polymorphism']
    },
    'javascript': {
        'label': 'JavaScript',
        'icon': '🌐',
        'topics': ['Variables & Scope', 'Data Types', 'Functions', 'Arrays', 'Objects',
                   'DOM Manipulation', 'Events', 'Promises & Async', 'ES6+ Features']
    },
    'dsa': {
        'label': 'DSA',
        'icon': '🔗',
        'topics': ['Arrays', 'Linked Lists', 'Stacks & Queues', 'Trees', 'Graphs',
                   'Searching Algorithms', 'Sorting Algorithms', 'Recursion', 'Dynamic Programming']
    },
    'oop': {
        'label': 'OOP',
        'icon': '🏗️',
        'topics': ['Classes & Objects', 'Inheritance', 'Polymorphism', 'Encapsulation',
                   'Abstraction', 'Interfaces', 'Design Patterns']
    },
    'dbms': {
        'label': 'DBMS',
        'icon': '🗄️',
        'topics': ['Database Basics', 'ER Model', 'Relational Model', 'Normalization',
                   'Transactions', 'SQL Basics', 'Joins', 'Indexing', 'ACID Properties']
    },
    'sql': {
        'label': 'SQL',
        'icon': '📊',
        'topics': ['SELECT Queries', 'WHERE Clause', 'JOINs', 'GROUP BY', 'ORDER BY',
                   'Subqueries', 'Aggregate Functions', 'CREATE/ALTER/DROP', 'INSERT/UPDATE/DELETE']
    },
}


@notes_bp.route('/notes')
def notes_page():
    return render_template('notes.html', categories=NOTES_CATEGORIES)


@notes_bp.route('/api/notes/categories')
def get_categories():
    return jsonify(NOTES_CATEGORIES)


@notes_bp.route('/api/notes/generate', methods=['POST'])
def get_notes():
    data = request.get_json()
    topic = data.get('topic', '')
    subject = data.get('subject', '')

    if not topic:
        return jsonify({'error': 'Topic is required'}), 400

    notes = generate_notes(topic, subject)
    return jsonify(notes)
