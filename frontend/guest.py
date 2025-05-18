from flask import Blueprint, request, jsonify, make_response
import json

guest_bp = Blueprint('guest', __name__)

@guest_bp.route('/guest-cookie', methods=['POST', 'GET'])
def guest_cookie():
    """
    POST: сохраняет в cookies last_page и progress гостя
    GET: возвращает current last_page и progress из cookies
    """
    if request.method == 'POST':
        data = request.get_json() or {}
        last_page = data.get('last_page', '/')
        progress = data.get('progress', {})
        resp = make_response(jsonify(status='ok'))
        resp.set_cookie(
            'guest_last_page',
            value=last_page,
            max_age=7 * 24 * 3600,
            path='/',
            httponly=True
        )
        resp.set_cookie(
            'guest_progress',
            value=json.dumps(progress),
            max_age=7 * 24 * 3600,
            path='/',
            httponly=True
        )
        return resp

    last_page = request.cookies.get('guest_last_page', '/')
    raw_progress = request.cookies.get('guest_progress', '{}')
    try:
        progress = json.loads(raw_progress)
    except (ValueError, TypeError):
        progress = {}

    return jsonify(last_page=last_page, progress=progress)