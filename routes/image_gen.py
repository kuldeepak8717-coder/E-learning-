from flask import Blueprint, render_template, jsonify, request
import requests
import json

image_gen_bp = Blueprint('image_gen', __name__)

PRESETS = [
    {'id': 'study_poster', 'label': 'Study Poster', 'icon': '📚',
     'prefix': 'educational study poster about', 'style': 'flat design, clean, colorful'},
    {'id': 'vocab_card', 'label': 'Vocabulary Card', 'icon': '📝',
     'prefix': 'vocabulary flashcard illustration for the word', 'style': 'minimal, clean, educational'},
    {'id': 'programming', 'label': 'Programming Diagram', 'icon': '💻',
     'prefix': 'programming concept diagram showing', 'style': 'tech, dark background, code-themed'},
    {'id': 'reasoning', 'label': 'Reasoning Diagram', 'icon': '🧠',
     'prefix': 'logical reasoning visual puzzle showing', 'style': 'clean, geometric, educational'},
    {'id': 'infographic', 'label': 'Educational Infographic', 'icon': '📊',
     'prefix': 'educational infographic about', 'style': 'modern, colorful, professional'},
    {'id': 'motivational', 'label': 'Motivational Poster', 'icon': '🌟',
     'prefix': 'motivational study poster with quote about', 'style': 'inspirational, vibrant, bold typography'},
]

SIZES = [
    {'id': '512x512', 'label': 'Square (512×512)', 'width': 512, 'height': 512},
    {'id': '768x512', 'label': 'Landscape (768×512)', 'width': 768, 'height': 512},
    {'id': '512x768', 'label': 'Portrait (512×768)', 'width': 512, 'height': 768},
]


@image_gen_bp.route('/image-gen')
def image_gen_page():
    return render_template('image_gen.html', presets=PRESETS, sizes=SIZES)


@image_gen_bp.route('/api/image-gen/generate', methods=['POST'])
def generate():
    data = request.get_json()
    prompt = data.get('prompt', '').strip()
    preset_id = data.get('preset', '')
    size = data.get('size', '512x512')
    style = data.get('style', '')

    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400

    # Build full prompt
    preset = next((p for p in PRESETS if p['id'] == preset_id), None)
    if preset:
        full_prompt = f"{preset['prefix']} {prompt}, {preset['style']}, high quality"
    else:
        full_prompt = f"{prompt}, {style}, high quality educational illustration"

    # Use Pollinations.ai (free, no API key needed)
    import urllib.parse
    encoded_prompt = urllib.parse.quote(full_prompt)
    width, height = 512, 512
    size_obj = next((s for s in SIZES if s['id'] == size), SIZES[0])
    width = size_obj['width']
    height = size_obj['height']

    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&seed={hash(prompt) % 10000}"

    return jsonify({
        'image_url': image_url,
        'prompt': full_prompt,
        'width': width,
        'height': height,
    })
