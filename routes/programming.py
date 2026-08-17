from flask import Blueprint, render_template, jsonify, request
from services.gemini_service import explain_code, generate_quiz, generate_notes, ask_gemini
from services.progress_service import award_xp
from utils import get_current_user
import subprocess
import sys
import os
import tempfile
import uuid

programming_bp = Blueprint('programming', __name__)

LANGUAGES = [
    {'id': 'python', 'label': 'Python', 'icon': '🐍', 'color': '#3776ab'},
    {'id': 'c', 'label': 'C', 'icon': '⚙️', 'color': '#a8b9cc'},
    {'id': 'cpp', 'label': 'C++', 'icon': '🔧', 'color': '#00599c'},
    {'id': 'java', 'label': 'Java', 'icon': '☕', 'color': '#ed8b00'},
    {'id': 'javascript', 'label': 'JavaScript', 'icon': '🌐', 'color': '#f7df1e'},
]

SYLLABUS_LEVELS = [
    {
        'level': 1,
        'title': 'Level 1: Basics',
        'topics': ['Variables & Data Types', 'Operators', 'Conditions (if/else)', 'Loops (for/while)']
    },
    {
        'level': 2,
        'title': 'Level 2: Data Handle',
        'topics': ['Arrays / Lists', 'Strings', 'Matrices']
    },
    {
        'level': 3,
        'title': 'Level 3: Logic Strong',
        'topics': ['Functions', 'OOP Concepts']
    },
    {
        'level': 4,
        'title': 'Level 4: Advanced DSA 1',
        'topics': ['Recursion', 'Linked Lists', 'Stacks', 'Queues']
    },
    {
        'level': 5,
        'title': 'Level 5: Hardcore DSA',
        'topics': ['Trees', 'Graphs', 'Dynamic Programming']
    }
]

CODE_STARTERS = {
    'python': '# Write your Python code here\nprint("Hello, World!")\n',
    'c': '#include <stdio.h>\n\nint main() {\n    printf("Hello, World!\\n");\n    return 0;\n}\n',
    'cpp': '#include <iostream>\nusing namespace std;\n\nint main() {\n    cout << "Hello, World!" << endl;\n    return 0;\n}\n',
    'java': 'public class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello, World!");\n    }\n}\n',
    'javascript': '// Write your JavaScript code here\nconsole.log("Hello, World!");\n',
}


@programming_bp.route('/programming')
def programming_page():
    return render_template('programming.html',
                           languages=LANGUAGES,
                           syllabus=SYLLABUS_LEVELS,
                           code_starters=CODE_STARTERS)


@programming_bp.route('/api/programming/run', methods=['POST'])
def run_code():
    """Execute Python code safely (other languages get Gemini explanation)."""
    data = request.get_json()
    code = data.get('code', '')
    language = data.get('language', 'python')

    if not code.strip():
        return jsonify({'output': '', 'error': 'No code provided'})

    if language == 'python':
        return _run_python(code)
    else:
        # For other languages, use Gemini to simulate output
        prompt = f"""Simulate the output of this {language} code:
```{language}
{code}
```
Show only what would be printed to console. If there's a compile/runtime error, show the error message.
Format: Just the output, no extra explanation."""
        output = ask_gemini(prompt)
        return jsonify({'output': output, 'error': '', 'simulated': True})


def _run_python(code: str) -> dict:
    """Run Python code in a temp file with timeout."""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            tmp_path = f.name

        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True, text=True, timeout=10
        )
        os.unlink(tmp_path)

        return jsonify({
            'output': result.stdout,
            'error': result.stderr,
            'return_code': result.returncode,
        })
    except subprocess.TimeoutExpired:
        return jsonify({'output': '', 'error': 'Code took too long to run (timeout: 10s)'})
    except Exception as e:
        return jsonify({'output': '', 'error': str(e)})


@programming_bp.route('/api/programming/explain', methods=['POST'])
def explain():
    data = request.get_json()
    code = data.get('code', '')
    language = data.get('language', 'python')
    question = data.get('question', 'Explain this code')

    explanation = explain_code(code, language, question)
    return jsonify({'explanation': explanation})


@programming_bp.route('/api/programming/notes', methods=['POST'])
def get_notes():
    data = request.get_json()
    topic = data.get('topic', '')
    language = data.get('language', 'python')

    notes = generate_notes(f"{topic} in {language}", 'Programming')
    return jsonify(notes)


@programming_bp.route('/api/programming/quiz', methods=['POST'])
def get_quiz():
    data = request.get_json()
    language = data.get('language', 'python')
    topic = data.get('topic', 'basics')
    difficulty = data.get('difficulty', 'medium')
    count = int(data.get('count', 5))

    subject = f"{language.title()} Programming - {topic}"
    questions = generate_quiz(subject, difficulty, count)
    return jsonify({'questions': questions})


@programming_bp.route('/api/programming/challenge', methods=['POST'])
def get_challenge():
    data = request.get_json()
    language = data.get('language', 'python')
    difficulty = data.get('difficulty', 'easy')

    prompt = f"""Create a completely unique beginner coding challenge in {language} at {difficulty} difficulty.
Make it creative and different from typical textbook examples.
Random seed for uniqueness: {uuid.uuid4()}

Return ONLY valid JSON:
{{
  "title": "Challenge name",
  "description": "What to build in simple words",
  "example_input": "Sample input",
  "example_output": "Expected output",
  "hint": "A helpful hint without giving away the solution",
  "starter_code": "// starter code for the student",
  "solution": "// complete solution"
}}"""

    try:
        from services.gemini_service import ask_gemini, _clean_json
        import json
        resp = ask_gemini(prompt)
        challenge = json.loads(_clean_json(resp))
        return jsonify(challenge)
    except Exception as e:
        return jsonify({
            'title': f'Hello {language.title()}',
            'description': f'Write a program that prints "Hello, World!" in {language}',
            'example_input': 'None',
            'example_output': 'Hello, World!',
            'hint': 'Use the print function',
            'starter_code': CODE_STARTERS.get(language, ''),
            'solution': CODE_STARTERS.get(language, '')
        })


@programming_bp.route('/api/programming/fix_bug', methods=['POST'])
def fix_bug():
    data = request.get_json()
    language = data.get('language', 'python')
    topic = data.get('topic', 'basics')
    
    prompt = f"""Generate a completely unique "Fix the Bug" challenge in {language} for the topic "{topic}".
Make sure the bug is subtle and the scenario is creative.
Random seed for uniqueness: {uuid.uuid4()}

Return ONLY valid JSON:
{{
  "title": "Fix the Bug: [Name]",
  "description": "What this code is supposed to do and what is wrong.",
  "buggy_code": "// the buggy code",
  "solution": "// the fixed code",
  "hint": "A subtle hint"
}}"""
    try:
        from services.gemini_service import ask_gemini, _clean_json
        import json
        resp = ask_gemini(prompt)
        return jsonify(json.loads(_clean_json(resp)))
    except Exception as e:
        return jsonify({'error': str(e)})


@programming_bp.route('/api/programming/predict_output', methods=['POST'])
def predict_output():
    data = request.get_json()
    language = data.get('language', 'python')
    topic = data.get('topic', 'basics')
    
    prompt = f"""Generate a completely unique "Predict Output" challenge in {language} for "{topic}".
Ensure the code is tricky but fair.
Random seed for uniqueness: {uuid.uuid4()}

Return ONLY valid JSON:
{{
  "title": "Predict Output: [Name]",
  "description": "Read the code and predict what will be printed.",
  "code": "// the code",
  "correct_output": "The exact output string",
  "explanation": "Why this is the output"
}}"""
    try:
        from services.gemini_service import ask_gemini, _clean_json
        import json
        resp = ask_gemini(prompt)
        return jsonify(json.loads(_clean_json(resp)))
    except Exception as e:
        return jsonify({'error': str(e)})


@programming_bp.route('/api/programming/extreme_test', methods=['POST'])
def extreme_test():
    data = request.get_json()
    language = data.get('language', 'python')
    code = data.get('code', '')
    
    prompt = f"""You are a strict code tester.
Test this {language} code with extreme edge cases (e.g., negative numbers, empty arrays, nulls, massive numbers).

Code:
```{language}
{code}
```

Return ONLY valid JSON:
{{
  "edge_cases_tested": ["Edge case 1", "Edge case 2"],
  "did_it_crash": true,
  "feedback": "Your code failed on negative numbers...",
  "improved_code": "// robust version of their code"
}}"""
    try:
        from services.gemini_service import ask_gemini, _clean_json
        import json
        resp = ask_gemini(prompt)
        return jsonify(json.loads(_clean_json(resp)))
    except Exception as e:
        return jsonify({'error': str(e)})

