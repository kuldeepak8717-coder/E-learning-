from flask import Blueprint, render_template, jsonify, request
from database.models import db, TypingResult
from services.gemini_service import generate_typing_text
from services.progress_service import award_xp, check_badges
from utils import get_current_user
from sqlalchemy import func

typing_bp = Blueprint('typing', __name__)

TYPING_MODES = [
    {'id': 'easy_words', 'label': 'Easy Words', 'icon': '🔤'},
    {'id': 'sentences', 'label': 'English Sentences', 'icon': '📄'},
    {'id': 'vocabulary', 'label': 'Vocabulary', 'icon': '📚'},
    {'id': 'conversation', 'label': 'Daily Conversation', 'icon': '💬'},
    {'id': 'programming', 'label': 'Programming Code', 'icon': '💻'},
]

DURATIONS = [30, 60, 180, 300]  # seconds

# Static fallback texts per mode
FALLBACK_TEXTS = {
    'easy_words': 'the cat sat on the mat the dog ran fast in the park she likes to eat apples and oranges every morning time flies when you are having fun',
    'sentences': 'Learning new skills every day is the key to success. Hard work and dedication will take you far in life. Practice makes perfect when you stay consistent. Never give up on your dreams no matter how difficult things seem. Small steps taken daily lead to big achievements over time.',
    'vocabulary': 'The diligent student persevered through every challenge with remarkable resilience. Her eloquent speech demonstrated an extraordinary command of the English language. Professionals who demonstrate integrity and competence are highly regarded in their fields. The proliferation of technology has revolutionized how we communicate and collaborate.',
    'conversation': 'Good morning! How are you doing today? I am doing quite well, thank you for asking. Did you have a chance to complete the assignment? Yes, I finished it last night. It was a bit challenging but I managed to figure it out.',
    'programming': 'print("Hello World") x = 10 y = 20 result = x + y print(result) for i in range(5): print(i) def greet(name): return "Hello " + name',
}


@typing_bp.route('/typing')
def typing_page():
    return render_template('typing.html', modes=TYPING_MODES, durations=DURATIONS)


@typing_bp.route('/api/typing/text', methods=['POST'])
def get_text():
    data = request.get_json()
    mode = data.get('mode', 'sentences')

    # Try Gemini, fall back to static text
    try:
        text = generate_typing_text(mode)
        if not text or len(text) < 20:
            text = FALLBACK_TEXTS.get(mode, FALLBACK_TEXTS['sentences'])
    except Exception:
        text = FALLBACK_TEXTS.get(mode, FALLBACK_TEXTS['sentences'])

    return jsonify({'text': text.strip()})


@typing_bp.route('/api/typing/submit', methods=['POST'])
def submit():
    data = request.get_json()
    user = get_current_user()

    wpm = float(data.get('wpm', 0))
    accuracy = float(data.get('accuracy', 0))
    correct_chars = int(data.get('correct_chars', 0))
    wrong_chars = int(data.get('wrong_chars', 0))
    mode = data.get('mode', 'sentences')
    duration = int(data.get('duration', 60))

    # Check personal best
    best_wpm = db.session.query(func.max(TypingResult.wpm)).filter_by(user_id=user.id).scalar() or 0
    is_pb = wpm > best_wpm

    result = TypingResult(
        user_id=user.id,
        wpm=wpm,
        accuracy=accuracy,
        correct_chars=correct_chars,
        wrong_chars=wrong_chars,
        mode=mode,
        duration=duration,
        is_personal_best=is_pb,
    )
    db.session.add(result)
    db.session.commit()

    # Award XP
    xp_result = award_xp(user, 'typing_test', 10 if is_pb else 0)
    new_badges = check_badges(user)

    # Update user's tracked typing speed
    if wpm > user.typing_speed:
        user.typing_speed = int(wpm)
        db.session.commit()

    return jsonify({
        'saved': True,
        'is_personal_best': is_pb,
        'previous_best': round(best_wpm, 1),
        'xp_result': xp_result,
        'new_badges': new_badges,
    })


@typing_bp.route('/api/typing/history')
def history():
    user = get_current_user()
    results = TypingResult.query.filter_by(user_id=user.id)\
        .order_by(TypingResult.date.desc()).limit(20).all()
    best = db.session.query(func.max(TypingResult.wpm)).filter_by(user_id=user.id).scalar() or 0
    return jsonify({
        'results': [r.to_dict() for r in results],
        'personal_best': round(best, 1),
    })
