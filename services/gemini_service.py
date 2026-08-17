"""
SkillRise AI — Gemini Service
All AI interactions go through this service layer.
API key is loaded from environment — never exposed to frontend.
Uses google.genai (modern SDK).
"""

import os
import json
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

_api_key = os.getenv('GEMINI_API_KEY', '')
_client = None


def _get_client():
    global _client
    if _client is None and _api_key and _api_key != 'your_gemini_api_key_here':
        _client = genai.Client(api_key=_api_key)
    return _client


def _generate_content_with_fallback(client, contents):
    """Generate content with automatic fallback for rate limits and downtime."""
    models = ['gemini-3.5-flash', 'gemini-3.6-flash', 'gemini-flash-latest', 'gemini-3.5-flash-lite', 'gemini-flash-lite-latest']
    last_error = None
    for model in models:
        try:
            return client.models.generate_content(model=model, contents=contents)
        except Exception as e:
            last_error = e
            error_msg = str(e)
            if any(code in error_msg for code in ['429', '503', '404', 'RESOURCE_EXHAUSTED', 'UNAVAILABLE', 'NOT_FOUND']):
                continue
            raise e
    raise last_error


def _clean_json(text: str) -> str:
    """Strip markdown code fences from Gemini JSON responses."""
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return text.strip()


def ask_gemini(prompt: str, system_context: str = "") -> str:
    """Generic Gemini call — returns plain text."""
    client = _get_client()
    if not client:
        return "⚠️ Gemini API key not configured. Please add your GEMINI_API_KEY to the .env file."
    try:
        full_prompt = f"{system_context}\n\n{prompt}" if system_context else prompt
        response = _generate_content_with_fallback(client, full_prompt)
        return response.text
    except Exception as e:
        return f"I'm having trouble connecting right now. Error: {str(e)}"


def generate_quiz(subject: str, difficulty: str = 'medium', count: int = 10) -> list:
    """Generate quiz questions using Gemini. Returns list of question dicts."""
    prompt = f"""Generate exactly {count} multiple-choice quiz questions about "{subject}" at {difficulty} difficulty level.

Return ONLY a valid JSON array with no extra text. Each object must have:
- "question": the question text
- "options": array of exactly 4 options (strings)
- "correct": index of correct answer (0-3)
- "explanation": brief explanation of why the answer is correct
- "topic": specific sub-topic this question covers

Example format:
[
  {{
    "question": "What is...",
    "options": ["A", "B", "C", "D"],
    "correct": 2,
    "explanation": "Because...",
    "topic": "sub-topic name"
  }}
]

Generate questions now:"""

    client = _get_client()
    if not client:
        return _fallback_questions(subject, count)
    try:
        response = _generate_content_with_fallback(client, prompt)
        cleaned = _clean_json(response.text)
        questions = json.loads(cleaned)
        return questions[:count]
    except Exception as e:
        return _fallback_questions(subject, count)


def _fallback_questions(subject: str, count: int) -> list:
    """Fallback questions when Gemini is unavailable."""
    questions = []
    for i in range(min(count, 5)):
        questions.append({
            "question": f"Sample {subject} question {i+1}: Which of the following is correct?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct": 0,
            "explanation": "This is a sample question. Add your Gemini API key in .env for real questions.",
            "topic": subject
        })
    return questions


def evaluate_communication(user_text: str, mode: str = "daily_conversation") -> dict:
    """Evaluate user's communication and return structured feedback."""
    prompt = f"""You are a supportive English communication coach helping a beginner student.

The student wrote this in a "{mode}" context:
"{user_text}"

Evaluate their English and return ONLY valid JSON with this exact structure:
{{
  "better_sentence": "improved version of their sentence",
  "grammar_score": 7.5,
  "vocabulary_score": 6.0,
  "clarity_score": 8.0,
  "naturalness_score": 7.0,
  "grammar_issues": ["list of specific grammar mistakes found"],
  "vocabulary_issues": ["list of vocabulary improvement suggestions"],
  "simple_explanation": "In simple English: what was wrong and how to fix it",
  "hindi_tip": "Ek chhota sa tip Hindi mein (optional, if helpful)",
  "new_words": [
    {{"word": "example", "meaning": "definition", "usage": "example sentence"}}
  ],
  "encouragement": "A warm, motivating message for the student"
}}

Be supportive and beginner-friendly. Scores are out of 10."""

    client = _get_client()
    if not client:
        return {
            "better_sentence": user_text,
            "grammar_score": 7.0, "vocabulary_score": 7.0,
            "clarity_score": 7.0, "naturalness_score": 7.0,
            "grammar_issues": [], "vocabulary_issues": [],
            "simple_explanation": "Add your Gemini API key to get real feedback!",
            "hindi_tip": "", "new_words": [],
            "encouragement": "Keep practicing! You're doing great! 🌟"
        }
    try:
        response = _generate_content_with_fallback(client, prompt)
        cleaned = _clean_json(response.text)
        return json.loads(cleaned)
    except Exception as e:
        return {
            "better_sentence": user_text,
            "grammar_score": 7.0, "vocabulary_score": 7.0,
            "clarity_score": 7.0, "naturalness_score": 7.0,
            "grammar_issues": [], "vocabulary_issues": [],
            "simple_explanation": "Great effort! Keep practicing.",
            "hindi_tip": "", "new_words": [],
            "encouragement": "You're doing great! Keep it up! 🌟"
        }


def explain_code(code: str, language: str, question: str = "Explain this code") -> str:
    """Explain code or debug errors in beginner-friendly language."""
    prompt = f"""You are a friendly programming tutor for beginners.

Language: {language}
Code:
```{language}
{code}
```

Student's question: {question}

Explain in simple, beginner-friendly English. Use:
- Short sentences
- Simple words
- Practical examples
- Encourage the student

If there's an error, explain what went wrong and how to fix it step by step."""

    return ask_gemini(prompt)


def generate_notes(topic: str, subject: str) -> dict:
    """Generate structured notes for a topic."""
    prompt = f"""Create comprehensive beginner-friendly notes for "{topic}" in the subject of "{subject}".

Return ONLY valid JSON with this structure:
{{
  "title": "{topic}",
  "simple_explanation": "2-3 sentence explanation in very simple English",
  "hindi_meaning": "Simple Hindi/Hinglish explanation",
  "key_points": ["point 1", "point 2", "point 3", "point 4", "point 5"],
  "examples": [
    {{"title": "Example 1", "content": "detailed example"}}
  ],
  "common_mistakes": ["mistake 1", "mistake 2", "mistake 3"],
  "practice_questions": [
    {{"question": "Q1", "answer": "A1"}}
  ],
  "quick_revision": ["one-liner 1", "one-liner 2", "one-liner 3", "one-liner 4"]
}}"""

    client = _get_client()
    if not client:
        return {
            "title": topic,
            "simple_explanation": f"Notes for {topic} in {subject}. Add Gemini API key for AI-generated content.",
            "hindi_meaning": "Gemini API key add karein detailed notes ke liye.",
            "key_points": [f"{topic} is an important concept", "Practice regularly", "Use examples to understand"],
            "examples": [{"title": "Example", "content": "Add your Gemini API key to see examples"}],
            "common_mistakes": ["Not practicing enough", "Skipping fundamentals"],
            "practice_questions": [{"question": f"What is {topic}?", "answer": "Add Gemini API key for answers"}],
            "quick_revision": [f"{topic} overview", "Key concepts", "Practice daily"]
        }
    try:
        response = _generate_content_with_fallback(client, prompt)
        cleaned = _clean_json(response.text)
        return json.loads(cleaned)
    except Exception as e:
        return {
            "title": topic,
            "simple_explanation": f"Notes for {topic}. There was an error: {str(e)}",
            "hindi_meaning": "", "key_points": [], "examples": [],
            "common_mistakes": [], "practice_questions": [], "quick_revision": []
        }


def generate_roadmap(user_profile: dict) -> dict:
    """Generate a personalized daily study roadmap based on user profile."""
    prompt = f"""You are an expert AI study planner. Create a personalized Day 1 study plan for this student.

Student Profile:
- Name: {user_profile.get('name', 'Student')}
- English Level: {user_profile.get('english_level', 1)}/10
- Typing Speed: {user_profile.get('typing_speed', 20)} WPM
- Communication Level: {user_profile.get('communication_level', 1)}/10
- Aptitude Level: {user_profile.get('aptitude_level', 1)}/10
- Reasoning Level: {user_profile.get('reasoning_level', 1)}/10
- Programming Level: {user_profile.get('programming_level', 1)}/10
- Daily Available Time: {user_profile.get('daily_target_minutes', 60)} minutes
- Main Goal: {user_profile.get('goal', 'Improve skills')}

Return ONLY valid JSON with this structure:
{{
  "day_number": 1,
  "phase": "Beginner",
  "theme": "Building Foundations",
  "total_minutes": {user_profile.get('daily_target_minutes', 60)},
  "tasks": [
    {{
      "id": "task_1",
      "subject": "English",
      "icon": "📝",
      "title": "5 Vocabulary Words",
      "description": "Learn 5 new English words with meanings and examples",
      "duration_minutes": 10,
      "type": "lesson",
      "link": "/notes",
      "xp_reward": 20
    }}
  ],
  "daily_quote": "A motivating quote for the student",
  "focus_areas": ["area1", "area2"],
  "tomorrow_preview": "Brief hint about tomorrow's plan"
}}

Create 6-8 tasks covering: English, Typing, Communication, Reasoning/Aptitude, Programming, Quiz.
Make tasks appropriate for the student's current levels."""

    client = _get_client()
    if not client:
        return _default_roadmap(user_profile)
    try:
        response = _generate_content_with_fallback(client, prompt)
        cleaned = _clean_json(response.text)
        return json.loads(cleaned)
    except Exception as e:
        return _default_roadmap(user_profile)


def _default_roadmap(user_profile: dict) -> dict:
    return {
        "day_number": 1, "phase": "Beginner", "theme": "Building Foundations",
        "total_minutes": user_profile.get('daily_target_minutes', 60),
        "tasks": [
            {"id": "task_1", "subject": "English", "icon": "📝", "title": "5 Vocabulary Words",
             "description": "Learn 5 new English words", "duration_minutes": 10,
             "type": "lesson", "link": "/notes", "xp_reward": 20},
            {"id": "task_2", "subject": "Typing", "icon": "⌨️", "title": "5-Minute Typing Test",
             "description": "Practice typing for 5 minutes", "duration_minutes": 5,
             "type": "practice", "link": "/typing", "xp_reward": 15},
            {"id": "task_3", "subject": "Aptitude", "icon": "➗", "title": "Percentage Basics",
             "description": "Learn percentage formulas and solve 5 questions", "duration_minutes": 15,
             "type": "lesson", "link": "/aptitude", "xp_reward": 25},
            {"id": "task_4", "subject": "Reasoning", "icon": "🧠", "title": "Number Series",
             "description": "Practice 5 number series questions", "duration_minutes": 10,
             "type": "practice", "link": "/reasoning", "xp_reward": 20},
            {"id": "task_5", "subject": "Programming", "icon": "💻", "title": "Python Variables",
             "description": "Learn about Python variables and data types", "duration_minutes": 15,
             "type": "lesson", "link": "/programming", "xp_reward": 25},
            {"id": "task_6", "subject": "Quiz", "icon": "📊", "title": "10 Mixed Questions",
             "description": "Take a mixed quiz to test today's learning", "duration_minutes": 10,
             "type": "quiz", "link": "/quiz", "xp_reward": 30},
        ],
        "daily_quote": "Every expert was once a beginner. Start today!",
        "focus_areas": ["Vocabulary", "Typing Speed"],
        "tomorrow_preview": "Grammar rules + Aptitude: Profit & Loss basics"
    }


def analyze_performance(stats: dict) -> dict:
    """Analyze user performance and recommend what to study next."""
    prompt = f"""Analyze this student's performance data and provide recommendations.

Performance Data:
{json.dumps(stats, indent=2)}

Return ONLY valid JSON:
{{
  "strong_skills": ["skill1", "skill2"],
  "weak_skills": ["skill1", "skill2"],
  "improvement_tips": [
    {{"skill": "English", "tip": "specific actionable tip"}}
  ],
  "recommended_practice": ["specific practice 1", "specific practice 2"],
  "tomorrow_focus": "What to focus on tomorrow",
  "motivational_message": "Personalized encouraging message"
}}"""

    client = _get_client()
    if not client:
        return {
            "strong_skills": ["Dedication"],
            "weak_skills": ["Add API key for analysis"],
            "improvement_tips": [{"skill": "All", "tip": "Practice daily for best results"}],
            "recommended_practice": ["Complete today's roadmap tasks"],
            "tomorrow_focus": "Continue with daily roadmap",
            "motivational_message": "Keep going! Consistency is the key to success! 🚀"
        }
    try:
        response = _generate_content_with_fallback(client, prompt)
        cleaned = _clean_json(response.text)
        return json.loads(cleaned)
    except Exception as e:
        return {
            "strong_skills": ["Dedication"],
            "weak_skills": ["Need more data"],
            "improvement_tips": [{"skill": "All", "tip": "Practice daily for best results"}],
            "recommended_practice": ["Complete today's roadmap tasks"],
            "tomorrow_focus": "Continue with daily roadmap",
            "motivational_message": "Keep going! Consistency is the key to success! 🚀"
        }


def chat_with_coach(message: str, history: list) -> str:
    """AI Coach chat — maintains conversation history."""
    system_prompt = """Tum SkillRise AI ke ek elite coding coach ho. Tumhe student ko aasan bhasha (Hindi-English mix) mein padhana hai. Pehle concept samjhao, fir ek choti real-life kahani (analogy) sunao, aur fir ek chota sa code ka example do. Kabhi bhi poora solution ek baar mein mat batana. Jab bhi test case do, toh 3 test case dena jisme se ek dimaag ghumane wala (edge case) ho. Apna output humesha JSON format mein dena taaki hamara app use screen par sahi se dikha sake.
    
    EXPECTED JSON SCHEMA:
    {
      "concept": "concept explanation here",
      "analogy": "real-life analogy here",
      "code": "code snippet here",
      "test_cases": ["test 1", "test 2", "edge case 3"]
    }"""

    client = _get_client()
    if not client:
        return "⚠️ Please add your GEMINI_API_KEY to the .env file to use the AI Coach!"

    try:
        # Build conversation
        contents = []
        for msg in history[-10:]:
            contents.append({
                "role": msg["role"],
                "parts": [{"text": msg["content"]}]
            })
        contents.append({
            "role": "user",
            "parts": [{"text": f"{system_prompt}\n\nStudent: {message}" if not history else message}]
        })

        response = _generate_content_with_fallback(client, contents)
        return response.text
    except Exception as e:
        return f"Sorry, I had a problem: {str(e)}. Please try again! 😊"


def generate_typing_text(mode: str) -> str:
    """Generate text for typing practice based on mode."""
    prompts = {
        'easy_words': "Give me 50 simple common English words separated by spaces. Only words, no punctuation.",
        'sentences': "Write 5 natural English sentences of medium length for typing practice. Return only the sentences joined with spaces.",
        'vocabulary': "Create 5 sentences using intermediate English vocabulary words. Return only sentences joined with spaces.",
        'conversation': "Write a short natural conversation passage (5-6 sentences) for typing practice. Return only the text.",
        'programming': "Write 3 short Python code snippets (print statements and variables) for typing practice. Return only the code.",
    }
    prompt = prompts.get(mode, prompts['sentences'])
    return ask_gemini(prompt)
